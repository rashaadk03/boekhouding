from flask import Blueprint, render_template, jsonify
from models import db, Verkoopfactuur, Inkoopfactuur, Betaling, Klant, Leverancier
from datetime import date, timedelta
from sqlalchemy import func, extract

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
def index():
    vandaag = date.today()
    begin_jaar = date(vandaag.year, 1, 1)

    # Openstaande debiteuren
    openstaande_verkoop = Verkoopfactuur.query.filter(
        Verkoopfactuur.status.in_(['verzonden', 'vervallen'])
    ).all()
    totaal_debiteuren = sum(f.openstaand_bedrag for f in openstaande_verkoop)

    # Openstaande crediteuren
    openstaande_inkoop = Inkoopfactuur.query.filter(
        Inkoopfactuur.status.in_(['ontvangen', 'goedgekeurd', 'vervallen'])
    ).all()
    totaal_crediteuren = sum(f.openstaand_bedrag for f in openstaande_inkoop)

    # Vervallen facturen
    vervallen_verkoop = [f for f in openstaande_verkoop if f.is_vervallen]
    vervallen_inkoop = [f for f in openstaande_inkoop if f.is_vervallen]

    # Omzet dit jaar
    omzet_jaar = db.session.query(func.sum(Verkoopfactuur.totaal)).filter(
        Verkoopfactuur.factuurdatum >= begin_jaar,
        Verkoopfactuur.status != 'concept'
    ).scalar() or 0

    # Kosten dit jaar
    kosten_jaar = db.session.query(func.sum(Inkoopfactuur.totaal)).filter(
        Inkoopfactuur.factuurdatum >= begin_jaar
    ).scalar() or 0

    # Inkomende betalingen dit jaar
    inkomend_jaar = db.session.query(func.sum(Betaling.bedrag)).filter(
        Betaling.type == 'inkomend',
        Betaling.datum >= begin_jaar
    ).scalar() or 0

    # Uitgaande betalingen dit jaar
    uitgaand_jaar = db.session.query(func.sum(Betaling.bedrag)).filter(
        Betaling.type == 'uitgaand',
        Betaling.datum >= begin_jaar
    ).scalar() or 0

    # Aantal klanten en leveranciers
    aantal_klanten = Klant.query.count()
    aantal_leveranciers = Leverancier.query.count()

    return render_template('dashboard.html',
                           totaal_debiteuren=totaal_debiteuren,
                           totaal_crediteuren=totaal_crediteuren,
                           vervallen_verkoop=vervallen_verkoop,
                           vervallen_inkoop=vervallen_inkoop,
                           omzet_jaar=omzet_jaar,
                           kosten_jaar=kosten_jaar,
                           winst_jaar=omzet_jaar - kosten_jaar,
                           inkomend_jaar=inkomend_jaar,
                           uitgaand_jaar=uitgaand_jaar,
                           cashflow_jaar=inkomend_jaar - uitgaand_jaar,
                           aantal_klanten=aantal_klanten,
                           aantal_leveranciers=aantal_leveranciers)


@dashboard_bp.route('/api/omzet-per-maand')
def omzet_per_maand():
    jaar = date.today().year
    data = []
    for maand in range(1, 13):
        omzet = db.session.query(func.sum(Verkoopfactuur.totaal)).filter(
            extract('year', Verkoopfactuur.factuurdatum) == jaar,
            extract('month', Verkoopfactuur.factuurdatum) == maand,
            Verkoopfactuur.status != 'concept'
        ).scalar() or 0
        kosten = db.session.query(func.sum(Inkoopfactuur.totaal)).filter(
            extract('year', Inkoopfactuur.factuurdatum) == jaar,
            extract('month', Inkoopfactuur.factuurdatum) == maand
        ).scalar() or 0
        data.append({'maand': maand, 'omzet': round(omzet, 2), 'kosten': round(kosten, 2)})
    return jsonify(data)


@dashboard_bp.route('/api/cashflow-per-maand')
def cashflow_per_maand():
    jaar = date.today().year
    data = []
    for maand in range(1, 13):
        inkomend = db.session.query(func.sum(Betaling.bedrag)).filter(
            Betaling.type == 'inkomend',
            extract('year', Betaling.datum) == jaar,
            extract('month', Betaling.datum) == maand
        ).scalar() or 0
        uitgaand = db.session.query(func.sum(Betaling.bedrag)).filter(
            Betaling.type == 'uitgaand',
            extract('year', Betaling.datum) == jaar,
            extract('month', Betaling.datum) == maand
        ).scalar() or 0
        data.append({'maand': maand, 'inkomend': round(inkomend, 2), 'uitgaand': round(uitgaand, 2)})
    return jsonify(data)
