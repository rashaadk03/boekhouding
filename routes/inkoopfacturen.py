import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, current_app
from flask_login import login_required
from werkzeug.utils import secure_filename
from models import (db, Inkoopfactuur, InkoopfactuurRegel, Leverancier, Valuta,
                     Grootboekrekening, Journaalpost, JournaalpostRegel)
from utils.btw import bereken_btw
from datetime import date, timedelta

TOEGESTANE_EXTENSIES = {'pdf', 'png', 'jpg', 'jpeg'}


def toegestaan_bestand(bestandsnaam):
    return '.' in bestandsnaam and bestandsnaam.rsplit('.', 1)[1].lower() in TOEGESTANE_EXTENSIES

inkoopfacturen_bp = Blueprint('inkoopfacturen', __name__, url_prefix='/inkoop')


@inkoopfacturen_bp.before_request
@login_required
def vereist_login():
    pass


def maak_journaalpost_inkoop(factuur):
    """Maak journaalpost voor een inkoopfactuur."""
    jp = Journaalpost(
        datum=factuur.factuurdatum,
        omschrijving=f'Inkoopfactuur {factuur.factuurnummer}',
        referentie=factuur.factuurnummer
    )
    db.session.add(jp)
    db.session.flush()

    # Debet: Inkoopkosten (4000) voor subtotaal
    kosten_rek = Grootboekrekening.query.filter_by(code='4000').first()
    if kosten_rek:
        db.session.add(JournaalpostRegel(
            journaalpost_id=jp.id,
            grootboekrekening_id=kosten_rek.id,
            debet=factuur.subtotaal,
            credit=0
        ))

    # Debet: BTW te vorderen (2200)
    if factuur.btw_bedrag > 0:
        btw_rek = Grootboekrekening.query.filter_by(code='2200').first()
        if btw_rek:
            db.session.add(JournaalpostRegel(
                journaalpost_id=jp.id,
                grootboekrekening_id=btw_rek.id,
                debet=factuur.btw_bedrag,
                credit=0
            ))

    # Credit: Crediteuren (2000)
    cred_rek = Grootboekrekening.query.filter_by(code='2000').first()
    if cred_rek:
        db.session.add(JournaalpostRegel(
            journaalpost_id=jp.id,
            grootboekrekening_id=cred_rek.id,
            debet=0,
            credit=factuur.totaal
        ))


@inkoopfacturen_bp.route('/')
def lijst():
    status = request.args.get('status', '')
    query = Inkoopfactuur.query
    if status:
        query = query.filter_by(status=status)
    facturen = query.order_by(Inkoopfactuur.factuurdatum.desc()).all()

    # Update vervallen status
    for f in facturen:
        if f.status in ('ontvangen', 'goedgekeurd') and f.vervaldatum < date.today():
            f.status = 'vervallen'
    db.session.commit()

    return render_template('inkoopfacturen/lijst.html', facturen=facturen, status=status)


@inkoopfacturen_bp.route('/nieuw', methods=['GET', 'POST'])
def nieuw():
    if request.method == 'POST':
        leverancier_id = request.form['leverancier_id']
        factuurnummer = request.form['factuurnummer']
        factuurdatum = date.fromisoformat(request.form['factuurdatum'])
        vervaldatum = date.fromisoformat(request.form['vervaldatum'])
        valuta = request.form.get('valuta', 'EUR')

        factuur = Inkoopfactuur(
            factuurnummer=factuurnummer,
            leverancier_id=leverancier_id,
            factuurdatum=factuurdatum,
            vervaldatum=vervaldatum,
            valuta=valuta,
            opmerkingen=request.form.get('opmerkingen', ''),
            status='ontvangen'
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

            regel = InkoopfactuurRegel(
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

        # PDF upload
        bestand = request.files.get('pdf_bestand')
        if bestand and bestand.filename and toegestaan_bestand(bestand.filename):
            upload_map = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_map, exist_ok=True)
            bestandsnaam = secure_filename(f"{factuurnummer}_{bestand.filename}")
            bestand.save(os.path.join(upload_map, bestandsnaam))
            factuur.pdf_bestand = bestandsnaam

        db.session.add(factuur)
        maak_journaalpost_inkoop(factuur)
        db.session.commit()
        flash(f'Inkoopfactuur {factuur.factuurnummer} is aangemaakt.', 'success')
        return redirect(url_for('inkoopfacturen.detail', id=factuur.id))

    leveranciers = Leverancier.query.order_by(Leverancier.naam).all()
    valutas = Valuta.query.order_by(Valuta.code).all()
    rekeningen = Grootboekrekening.query.filter_by(type='kosten').order_by(Grootboekrekening.code).all()
    return render_template('inkoopfacturen/form.html',
                           factuur=None, leveranciers=leveranciers, valutas=valutas,
                           rekeningen=rekeningen, vandaag=date.today(),
                           vervaldatum=date.today() + timedelta(days=30))


@inkoopfacturen_bp.route('/<int:id>')
def detail(id):
    factuur = Inkoopfactuur.query.get_or_404(id)
    return render_template('inkoopfacturen/detail.html', factuur=factuur)


@inkoopfacturen_bp.route('/<int:id>/goedkeuren', methods=['POST'])
def goedkeuren(id):
    factuur = Inkoopfactuur.query.get_or_404(id)
    if factuur.status == 'ontvangen':
        factuur.status = 'goedgekeurd'
        db.session.commit()
        flash(f'Inkoopfactuur {factuur.factuurnummer} is goedgekeurd.', 'success')
    return redirect(url_for('inkoopfacturen.detail', id=id))


@inkoopfacturen_bp.route('/<int:id>/verwijder', methods=['POST'])
def verwijder(id):
    factuur = Inkoopfactuur.query.get_or_404(id)
    nr = factuur.factuurnummer
    db.session.delete(factuur)
    db.session.commit()
    flash(f'Inkoopfactuur {nr} is verwijderd.', 'success')
    return redirect(url_for('inkoopfacturen.lijst'))


@inkoopfacturen_bp.route('/<int:id>/upload', methods=['POST'])
def upload_pdf(id):
    factuur = Inkoopfactuur.query.get_or_404(id)
    bestand = request.files.get('pdf_bestand')
    if not bestand or not bestand.filename:
        flash('Geen bestand geselecteerd.', 'danger')
        return redirect(url_for('inkoopfacturen.detail', id=id))

    if not toegestaan_bestand(bestand.filename):
        flash('Alleen PDF, PNG en JPG bestanden zijn toegestaan.', 'danger')
        return redirect(url_for('inkoopfacturen.detail', id=id))

    upload_map = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_map, exist_ok=True)

    # Verwijder oud bestand als dat bestaat
    if factuur.pdf_bestand:
        oud_pad = os.path.join(upload_map, factuur.pdf_bestand)
        if os.path.exists(oud_pad):
            os.remove(oud_pad)

    bestandsnaam = secure_filename(f"{factuur.factuurnummer}_{bestand.filename}")
    bestand.save(os.path.join(upload_map, bestandsnaam))
    factuur.pdf_bestand = bestandsnaam
    db.session.commit()
    flash('Factuurbestand is geüpload.', 'success')
    return redirect(url_for('inkoopfacturen.detail', id=id))


@inkoopfacturen_bp.route('/<int:id>/download')
def download_pdf(id):
    factuur = Inkoopfactuur.query.get_or_404(id)
    if not factuur.pdf_bestand:
        flash('Geen bestand beschikbaar.', 'warning')
        return redirect(url_for('inkoopfacturen.detail', id=id))
    upload_map = current_app.config['UPLOAD_FOLDER']
    return send_from_directory(upload_map, factuur.pdf_bestand)


@inkoopfacturen_bp.route('/openstaand')
def openstaand():
    facturen = Inkoopfactuur.query.filter(
        Inkoopfactuur.status.in_(['ontvangen', 'goedgekeurd', 'vervallen'])
    ).order_by(Inkoopfactuur.vervaldatum).all()
    totaal = sum(f.openstaand_bedrag for f in facturen)
    return render_template('inkoopfacturen/openstaand.html', facturen=facturen, totaal=totaal)
