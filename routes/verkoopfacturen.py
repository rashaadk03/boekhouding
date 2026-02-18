from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from models import (db, Verkoopfactuur, VerkoopfactuurRegel, Klant, Valuta,
                     Grootboekrekening, Journaalpost, JournaalpostRegel)
from utils.btw import bereken_btw
from utils.pdf import genereer_factuur_pdf
from datetime import date, timedelta

verkoopfacturen_bp = Blueprint('verkoopfacturen', __name__, url_prefix='/verkoop')


def genereer_factuurnummer():
    jaar = date.today().year
    laatste = Verkoopfactuur.query.filter(
        Verkoopfactuur.factuurnummer.like(f'VF{jaar}%')
    ).order_by(Verkoopfactuur.factuurnummer.desc()).first()
    if laatste:
        nr = int(laatste.factuurnummer[-4:]) + 1
    else:
        nr = 1
    return f'VF{jaar}{nr:04d}'


def maak_journaalpost_verkoop(factuur):
    """Maak journaalpost voor een verkoopfactuur."""
    jp = Journaalpost(
        datum=factuur.factuurdatum,
        omschrijving=f'Verkoopfactuur {factuur.factuurnummer}',
        referentie=factuur.factuurnummer
    )
    db.session.add(jp)
    db.session.flush()

    # Debet: Debiteuren (1200)
    deb_rek = Grootboekrekening.query.filter_by(code='1200').first()
    if deb_rek:
        db.session.add(JournaalpostRegel(
            journaalpost_id=jp.id,
            grootboekrekening_id=deb_rek.id,
            debet=factuur.totaal,
            credit=0
        ))

    # Credit: Omzet (8000) voor subtotaal
    omzet_rek = Grootboekrekening.query.filter_by(code='8000').first()
    if omzet_rek:
        db.session.add(JournaalpostRegel(
            journaalpost_id=jp.id,
            grootboekrekening_id=omzet_rek.id,
            debet=0,
            credit=factuur.subtotaal
        ))

    # Credit: BTW af te dragen (2100)
    if factuur.btw_bedrag > 0:
        btw_rek = Grootboekrekening.query.filter_by(code='2100').first()
        if btw_rek:
            db.session.add(JournaalpostRegel(
                journaalpost_id=jp.id,
                grootboekrekening_id=btw_rek.id,
                debet=0,
                credit=factuur.btw_bedrag
            ))


@verkoopfacturen_bp.route('/')
def lijst():
    status = request.args.get('status', '')
    query = Verkoopfactuur.query
    if status:
        query = query.filter_by(status=status)
    facturen = query.order_by(Verkoopfactuur.factuurdatum.desc()).all()

    # Update vervallen status
    for f in facturen:
        if f.status == 'verzonden' and f.vervaldatum < date.today():
            f.status = 'vervallen'
    db.session.commit()

    return render_template('verkoopfacturen/lijst.html', facturen=facturen, status=status)


@verkoopfacturen_bp.route('/nieuw', methods=['GET', 'POST'])
def nieuw():
    if request.method == 'POST':
        klant_id = request.form['klant_id']
        factuurdatum = date.fromisoformat(request.form['factuurdatum'])
        vervaldatum = date.fromisoformat(request.form['vervaldatum'])
        valuta = request.form.get('valuta', 'EUR')

        factuur = Verkoopfactuur(
            factuurnummer=genereer_factuurnummer(),
            klant_id=klant_id,
            factuurdatum=factuurdatum,
            vervaldatum=vervaldatum,
            valuta=valuta,
            opmerkingen=request.form.get('opmerkingen', ''),
            status='concept'
        )

        subtotaal = 0
        btw_totaal = 0
        omschrijvingen = request.form.getlist('omschrijving[]')
        aantallen = request.form.getlist('aantal[]')
        prijzen = request.form.getlist('prijs_per_stuk[]')
        btw_percentages = request.form.getlist('btw_percentage[]')
        gb_rekeningen = request.form.getlist('grootboekrekening_id[]')

        for i in range(len(omschrijvingen)):
            if not omschrijvingen[i].strip():
                continue
            aantal = float(aantallen[i])
            prijs = float(prijzen[i])
            btw_pct = float(btw_percentages[i])
            netto = aantal * prijs
            btw = bereken_btw(netto, btw_pct)
            totaal_regel = netto + btw

            gb_id = int(gb_rekeningen[i]) if gb_rekeningen[i] else None

            regel = VerkoopfactuurRegel(
                omschrijving=omschrijvingen[i],
                aantal=aantal,
                prijs_per_stuk=prijs,
                btw_percentage=btw_pct,
                totaal=totaal_regel,
                grootboekrekening_id=gb_id
            )
            factuur.regels.append(regel)
            subtotaal += netto
            btw_totaal += btw

        factuur.subtotaal = round(subtotaal, 2)
        factuur.btw_bedrag = round(btw_totaal, 2)
        factuur.totaal = round(subtotaal + btw_totaal, 2)

        db.session.add(factuur)
        db.session.commit()
        flash(f'Verkoopfactuur {factuur.factuurnummer} is aangemaakt.', 'success')
        return redirect(url_for('verkoopfacturen.detail', id=factuur.id))

    klanten = Klant.query.order_by(Klant.naam).all()
    valutas = Valuta.query.order_by(Valuta.code).all()
    rekeningen = Grootboekrekening.query.filter_by(type='opbrengsten').order_by(Grootboekrekening.code).all()
    return render_template('verkoopfacturen/form.html',
                           factuur=None, klanten=klanten, valutas=valutas,
                           rekeningen=rekeningen, vandaag=date.today(),
                           vervaldatum=date.today() + timedelta(days=30))


@verkoopfacturen_bp.route('/<int:id>')
def detail(id):
    factuur = Verkoopfactuur.query.get_or_404(id)
    return render_template('verkoopfacturen/detail.html', factuur=factuur)


@verkoopfacturen_bp.route('/<int:id>/verzend', methods=['POST'])
def verzend(id):
    factuur = Verkoopfactuur.query.get_or_404(id)
    if factuur.status == 'concept':
        factuur.status = 'verzonden'
        maak_journaalpost_verkoop(factuur)
        db.session.commit()
        flash(f'Factuur {factuur.factuurnummer} is verzonden.', 'success')
    return redirect(url_for('verkoopfacturen.detail', id=id))


@verkoopfacturen_bp.route('/<int:id>/pdf')
def pdf(id):
    factuur = Verkoopfactuur.query.get_or_404(id)
    klant = Klant.query.get(factuur.klant_id)
    buffer, mimetype = genereer_factuur_pdf(factuur, klant)
    ext = 'pdf' if mimetype == 'application/pdf' else 'html'
    return send_file(buffer, mimetype=mimetype,
                     download_name=f'{factuur.factuurnummer}.{ext}')


@verkoopfacturen_bp.route('/<int:id>/verwijder', methods=['POST'])
def verwijder(id):
    factuur = Verkoopfactuur.query.get_or_404(id)
    if factuur.status != 'concept':
        flash('Alleen conceptfacturen kunnen verwijderd worden.', 'danger')
        return redirect(url_for('verkoopfacturen.detail', id=id))
    nr = factuur.factuurnummer
    db.session.delete(factuur)
    db.session.commit()
    flash(f'Factuur {nr} is verwijderd.', 'success')
    return redirect(url_for('verkoopfacturen.lijst'))


@verkoopfacturen_bp.route('/herinneringen')
def herinneringen():
    facturen = Verkoopfactuur.query.filter(
        Verkoopfactuur.status.in_(['verzonden', 'vervallen']),
        Verkoopfactuur.vervaldatum < date.today()
    ).order_by(Verkoopfactuur.vervaldatum).all()
    return render_template('verkoopfacturen/herinneringen.html', facturen=facturen)


@verkoopfacturen_bp.route('/openstaand')
def openstaand():
    facturen = Verkoopfactuur.query.filter(
        Verkoopfactuur.status.in_(['verzonden', 'vervallen'])
    ).order_by(Verkoopfactuur.vervaldatum).all()
    totaal = sum(f.openstaand_bedrag for f in facturen)
    return render_template('verkoopfacturen/openstaand.html', facturen=facturen, totaal=totaal)
