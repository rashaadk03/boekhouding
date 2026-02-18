import csv
import io
from flask import Blueprint, render_template, request, Response, send_file
from models import (db, Grootboekrekening, JournaalpostRegel, Verkoopfactuur,
                     VerkoopfactuurRegel, Inkoopfactuur, InkoopfactuurRegel)
from sqlalchemy import func, extract
from datetime import date
try:
    from weasyprint import HTML
    WEASYPRINT_BESCHIKBAAR = True
except (ImportError, OSError):
    WEASYPRINT_BESCHIKBAAR = False

rapportages_bp = Blueprint('rapportages', __name__, url_prefix='/rapportages')


def get_rekening_saldo(code):
    rek = Grootboekrekening.query.filter_by(code=code).first()
    if not rek:
        return 0
    debet = db.session.query(func.sum(JournaalpostRegel.debet)).filter_by(
        grootboekrekening_id=rek.id
    ).scalar() or 0
    credit = db.session.query(func.sum(JournaalpostRegel.credit)).filter_by(
        grootboekrekening_id=rek.id
    ).scalar() or 0
    return round(debet - credit, 2)


def get_type_saldi(type_):
    rekeningen = Grootboekrekening.query.filter_by(type=type_).order_by(Grootboekrekening.code).all()
    result = []
    totaal = 0
    for rek in rekeningen:
        debet = db.session.query(func.sum(JournaalpostRegel.debet)).filter_by(
            grootboekrekening_id=rek.id
        ).scalar() or 0
        credit = db.session.query(func.sum(JournaalpostRegel.credit)).filter_by(
            grootboekrekening_id=rek.id
        ).scalar() or 0
        saldo = round(debet - credit, 2)
        if saldo != 0:
            result.append({'code': rek.code, 'naam': rek.naam, 'saldo': saldo})
            totaal += saldo
    return result, round(totaal, 2)


@rapportages_bp.route('/')
def index():
    return render_template('rapportages/index.html')


@rapportages_bp.route('/balans')
def balans():
    activa, totaal_activa = get_type_saldi('activa')
    passiva, totaal_passiva = get_type_saldi('passiva')

    # Winst toevoegen aan passiva voor balansevenwicht
    opbrengsten_list, totaal_opbrengsten = get_type_saldi('opbrengsten')
    kosten_list, totaal_kosten = get_type_saldi('kosten')
    # Opbrengsten zijn credit (negatief saldo), kosten zijn debet (positief saldo)
    winst = (-totaal_opbrengsten) - totaal_kosten

    return render_template('rapportages/balans.html',
                           activa=activa, totaal_activa=totaal_activa,
                           passiva=passiva, totaal_passiva=totaal_passiva,
                           winst=winst)


@rapportages_bp.route('/winstverlies')
def winstverlies():
    opbrengsten, totaal_opbrengsten = get_type_saldi('opbrengsten')
    kosten, totaal_kosten = get_type_saldi('kosten')
    # Opbrengsten hebben negatief saldo (credit), neem absoluut
    netto_opbrengsten = -totaal_opbrengsten
    resultaat = netto_opbrengsten - totaal_kosten

    return render_template('rapportages/winstverlies.html',
                           opbrengsten=opbrengsten,
                           totaal_opbrengsten=netto_opbrengsten,
                           kosten=kosten,
                           totaal_kosten=totaal_kosten,
                           resultaat=resultaat)


@rapportages_bp.route('/btw')
def btw_aangifte():
    jaar = int(request.args.get('jaar', date.today().year))
    kwartaal = int(request.args.get('kwartaal', (date.today().month - 1) // 3 + 1))

    maand_start = (kwartaal - 1) * 3 + 1
    maand_eind = kwartaal * 3

    # BTW op verkopen
    verkoop_btw = db.session.query(
        VerkoopfactuurRegel.btw_percentage,
        func.sum(VerkoopfactuurRegel.totaal - (VerkoopfactuurRegel.aantal * VerkoopfactuurRegel.prijs_per_stuk)).label('btw'),
        func.sum(VerkoopfactuurRegel.aantal * VerkoopfactuurRegel.prijs_per_stuk).label('netto')
    ).join(Verkoopfactuur).filter(
        extract('year', Verkoopfactuur.factuurdatum) == jaar,
        extract('month', Verkoopfactuur.factuurdatum) >= maand_start,
        extract('month', Verkoopfactuur.factuurdatum) <= maand_eind,
        Verkoopfactuur.status != 'concept'
    ).group_by(VerkoopfactuurRegel.btw_percentage).all()

    # BTW op inkopen
    inkoop_btw = db.session.query(
        InkoopfactuurRegel.btw_percentage,
        func.sum(InkoopfactuurRegel.totaal - (InkoopfactuurRegel.aantal * InkoopfactuurRegel.prijs_per_stuk)).label('btw'),
        func.sum(InkoopfactuurRegel.aantal * InkoopfactuurRegel.prijs_per_stuk).label('netto')
    ).join(Inkoopfactuur).filter(
        extract('year', Inkoopfactuur.factuurdatum) == jaar,
        extract('month', Inkoopfactuur.factuurdatum) >= maand_start,
        extract('month', Inkoopfactuur.factuurdatum) <= maand_eind,
    ).group_by(InkoopfactuurRegel.btw_percentage).all()

    totaal_verkoop_btw = sum(r.btw or 0 for r in verkoop_btw)
    totaal_inkoop_btw = sum(r.btw or 0 for r in inkoop_btw)
    af_te_dragen = totaal_verkoop_btw - totaal_inkoop_btw

    return render_template('rapportages/btw.html',
                           jaar=jaar, kwartaal=kwartaal,
                           verkoop_btw=verkoop_btw,
                           inkoop_btw=inkoop_btw,
                           totaal_verkoop_btw=round(totaal_verkoop_btw, 2),
                           totaal_inkoop_btw=round(totaal_inkoop_btw, 2),
                           af_te_dragen=round(af_te_dragen, 2))


@rapportages_bp.route('/export/csv/<rapport>')
def export_csv(rapport):
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')

    if rapport == 'balans':
        writer.writerow(['Type', 'Code', 'Naam', 'Saldo'])
        for type_ in ['activa', 'passiva']:
            saldi, _ = get_type_saldi(type_)
            for r in saldi:
                writer.writerow([type_, r['code'], r['naam'], f"{r['saldo']:.2f}"])
    elif rapport == 'winstverlies':
        writer.writerow(['Type', 'Code', 'Naam', 'Saldo'])
        for type_ in ['opbrengsten', 'kosten']:
            saldi, _ = get_type_saldi(type_)
            for r in saldi:
                saldo = -r['saldo'] if type_ == 'opbrengsten' else r['saldo']
                writer.writerow([type_, r['code'], r['naam'], f"{saldo:.2f}"])
    elif rapport == 'debiteuren':
        writer.writerow(['Factuurnummer', 'Klant', 'Factuurdatum', 'Vervaldatum', 'Totaal', 'Openstaand', 'Status'])
        facturen = Verkoopfactuur.query.filter(
            Verkoopfactuur.status.in_(['verzonden', 'vervallen'])
        ).all()
        for f in facturen:
            writer.writerow([f.factuurnummer, f.klant.naam, f.factuurdatum, f.vervaldatum,
                             f"{f.totaal:.2f}", f"{f.openstaand_bedrag:.2f}", f.status])
    elif rapport == 'crediteuren':
        writer.writerow(['Factuurnummer', 'Leverancier', 'Factuurdatum', 'Vervaldatum', 'Totaal', 'Openstaand', 'Status'])
        facturen = Inkoopfactuur.query.filter(
            Inkoopfactuur.status.in_(['ontvangen', 'goedgekeurd', 'vervallen'])
        ).all()
        for f in facturen:
            writer.writerow([f.factuurnummer, f.leverancier.naam, f.factuurdatum, f.vervaldatum,
                             f"{f.totaal:.2f}", f"{f.openstaand_bedrag:.2f}", f.status])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={rapport}_{date.today()}.csv'}
    )


@rapportages_bp.route('/export/pdf/<rapport>')
def export_pdf(rapport):
    if rapport == 'balans':
        activa, totaal_activa = get_type_saldi('activa')
        passiva, totaal_passiva = get_type_saldi('passiva')
        opbrengsten_list, totaal_opbrengsten = get_type_saldi('opbrengsten')
        kosten_list, totaal_kosten = get_type_saldi('kosten')
        winst = (-totaal_opbrengsten) - totaal_kosten
        html = render_template('rapportages/balans_pdf.html',
                               activa=activa, totaal_activa=totaal_activa,
                               passiva=passiva, totaal_passiva=totaal_passiva,
                               winst=winst, datum=date.today())
    elif rapport == 'winstverlies':
        opbrengsten, totaal_opbrengsten = get_type_saldi('opbrengsten')
        kosten, totaal_kosten = get_type_saldi('kosten')
        netto_opbrengsten = -totaal_opbrengsten
        resultaat = netto_opbrengsten - totaal_kosten
        html = render_template('rapportages/winstverlies_pdf.html',
                               opbrengsten=opbrengsten,
                               totaal_opbrengsten=netto_opbrengsten,
                               kosten=kosten,
                               totaal_kosten=totaal_kosten,
                               resultaat=resultaat, datum=date.today())
    else:
        return 'Onbekend rapport', 404

    if WEASYPRINT_BESCHIKBAAR:
        pdf_buffer = io.BytesIO()
        HTML(string=html).write_pdf(pdf_buffer)
        pdf_buffer.seek(0)
        return send_file(pdf_buffer, mimetype='application/pdf',
                         download_name=f'{rapport}_{date.today()}.pdf')
    else:
        html_buffer = io.BytesIO(html.encode('utf-8'))
        return send_file(html_buffer, mimetype='text/html',
                         download_name=f'{rapport}_{date.today()}.html')
