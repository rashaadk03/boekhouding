from flask import Blueprint, render_template, request
from models import db, Grootboekrekening, Journaalpost, JournaalpostRegel
from sqlalchemy import func

grootboek_bp = Blueprint('grootboek', __name__, url_prefix='/grootboek')


@grootboek_bp.route('/')
def rekeningen():
    type_filter = request.args.get('type', '')
    query = Grootboekrekening.query
    if type_filter:
        query = query.filter_by(type=type_filter)
    rekeningen = query.order_by(Grootboekrekening.code).all()

    # Bereken saldi
    for rek in rekeningen:
        debet = db.session.query(func.sum(JournaalpostRegel.debet)).filter_by(
            grootboekrekening_id=rek.id
        ).scalar() or 0
        credit = db.session.query(func.sum(JournaalpostRegel.credit)).filter_by(
            grootboekrekening_id=rek.id
        ).scalar() or 0
        rek.totaal_debet = round(debet, 2)
        rek.totaal_credit = round(credit, 2)
        rek.saldo = round(debet - credit, 2)

    return render_template('grootboek/rekeningen.html', rekeningen=rekeningen, type_filter=type_filter)


@grootboek_bp.route('/rekening/<int:id>')
def rekening_detail(id):
    rekening = Grootboekrekening.query.get_or_404(id)
    regels = JournaalpostRegel.query.filter_by(
        grootboekrekening_id=id
    ).order_by(JournaalpostRegel.id).all()

    # Bereken lopend saldo
    saldo = 0
    for regel in regels:
        saldo += regel.debet - regel.credit
        regel.lopend_saldo = round(saldo, 2)

    return render_template('grootboek/rekening_detail.html', rekening=rekening, regels=regels)


@grootboek_bp.route('/journaal')
def journaal():
    posten = Journaalpost.query.order_by(Journaalpost.datum.desc(), Journaalpost.id.desc()).all()
    return render_template('grootboek/journaal.html', posten=posten)


@grootboek_bp.route('/proefbalans')
def proefbalans():
    rekeningen = Grootboekrekening.query.order_by(Grootboekrekening.code).all()
    totaal_debet = 0
    totaal_credit = 0

    for rek in rekeningen:
        debet = db.session.query(func.sum(JournaalpostRegel.debet)).filter_by(
            grootboekrekening_id=rek.id
        ).scalar() or 0
        credit = db.session.query(func.sum(JournaalpostRegel.credit)).filter_by(
            grootboekrekening_id=rek.id
        ).scalar() or 0
        rek.totaal_debet = round(debet, 2)
        rek.totaal_credit = round(credit, 2)
        rek.saldo = round(debet - credit, 2)
        totaal_debet += debet
        totaal_credit += credit

    # Filter out zero-balance accounts
    rekeningen = [r for r in rekeningen if r.totaal_debet != 0 or r.totaal_credit != 0]

    return render_template('grootboek/proefbalans.html',
                           rekeningen=rekeningen,
                           totaal_debet=round(totaal_debet, 2),
                           totaal_credit=round(totaal_credit, 2))
