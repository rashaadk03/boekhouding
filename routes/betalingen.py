from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import (db, Betaling, Verkoopfactuur, Inkoopfactuur,
                     Journaalpost, JournaalpostRegel, Grootboekrekening)
from datetime import date

betalingen_bp = Blueprint('betalingen', __name__, url_prefix='/betalingen')


def maak_journaalpost_betaling(betaling):
    """Maak journaalpost voor een betaling."""
    jp = Journaalpost(
        datum=betaling.datum,
        omschrijving=f'Betaling {betaling.referentie or betaling.id}',
        referentie=betaling.referentie
    )
    db.session.add(jp)
    db.session.flush()

    bank_rek = Grootboekrekening.query.filter_by(code='1100').first()

    if betaling.type == 'inkomend':
        # Debet: Bank, Credit: Debiteuren
        deb_rek = Grootboekrekening.query.filter_by(code='1200').first()
        if bank_rek:
            db.session.add(JournaalpostRegel(
                journaalpost_id=jp.id,
                grootboekrekening_id=bank_rek.id,
                debet=betaling.bedrag,
                credit=0
            ))
        if deb_rek:
            db.session.add(JournaalpostRegel(
                journaalpost_id=jp.id,
                grootboekrekening_id=deb_rek.id,
                debet=0,
                credit=betaling.bedrag
            ))
    else:
        # Debet: Crediteuren, Credit: Bank
        cred_rek = Grootboekrekening.query.filter_by(code='2000').first()
        if cred_rek:
            db.session.add(JournaalpostRegel(
                journaalpost_id=jp.id,
                grootboekrekening_id=cred_rek.id,
                debet=betaling.bedrag,
                credit=0
            ))
        if bank_rek:
            db.session.add(JournaalpostRegel(
                journaalpost_id=jp.id,
                grootboekrekening_id=bank_rek.id,
                debet=0,
                credit=betaling.bedrag
            ))


def update_factuur_status(betaling):
    """Update factuurstatus na betaling."""
    if betaling.factuur_type == 'verkoop':
        factuur = Verkoopfactuur.query.get(betaling.factuur_id)
        if factuur and factuur.openstaand_bedrag <= 0.01:
            factuur.status = 'betaald'
    elif betaling.factuur_type == 'inkoop':
        factuur = Inkoopfactuur.query.get(betaling.factuur_id)
        if factuur and factuur.openstaand_bedrag <= 0.01:
            factuur.status = 'betaald'


@betalingen_bp.route('/')
def lijst():
    type_filter = request.args.get('type', '')
    query = Betaling.query
    if type_filter:
        query = query.filter_by(type=type_filter)
    betalingen = query.order_by(Betaling.datum.desc()).all()

    # Enrich with factuur info
    for b in betalingen:
        if b.factuur_type == 'verkoop':
            b.factuur_obj = Verkoopfactuur.query.get(b.factuur_id)
        else:
            b.factuur_obj = Inkoopfactuur.query.get(b.factuur_id)

    return render_template('betalingen/lijst.html', betalingen=betalingen, type_filter=type_filter)


@betalingen_bp.route('/nieuw', methods=['GET', 'POST'])
def nieuw():
    if request.method == 'POST':
        factuur_type = request.form['factuur_type']
        factuur_id = int(request.form['factuur_id'])
        bedrag = float(request.form['bedrag'])
        datum = date.fromisoformat(request.form['datum'])
        betaalmethode = request.form.get('betaalmethode', 'bank')
        referentie = request.form.get('referentie', '')

        type_ = 'inkomend' if factuur_type == 'verkoop' else 'uitgaand'

        betaling = Betaling(
            type=type_,
            factuur_type=factuur_type,
            factuur_id=factuur_id,
            bedrag=bedrag,
            datum=datum,
            betaalmethode=betaalmethode,
            referentie=referentie,
        )
        db.session.add(betaling)
        db.session.flush()

        maak_journaalpost_betaling(betaling)
        update_factuur_status(betaling)
        db.session.commit()

        flash(f'Betaling van \u20ac {bedrag:,.2f} is geregistreerd.', 'success')
        return redirect(url_for('betalingen.lijst'))

    # Get open invoices
    verkoop_facturen = Verkoopfactuur.query.filter(
        Verkoopfactuur.status.in_(['verzonden', 'vervallen'])
    ).order_by(Verkoopfactuur.factuurnummer).all()
    inkoop_facturen = Inkoopfactuur.query.filter(
        Inkoopfactuur.status.in_(['ontvangen', 'goedgekeurd', 'vervallen'])
    ).order_by(Inkoopfactuur.factuurnummer).all()

    # Pre-select from query params
    pre_type = request.args.get('factuur_type', '')
    pre_id = request.args.get('factuur_id', '')

    return render_template('betalingen/form.html',
                           verkoop_facturen=verkoop_facturen,
                           inkoop_facturen=inkoop_facturen,
                           vandaag=date.today(),
                           pre_type=pre_type,
                           pre_id=pre_id)
