"""PDF generatie voor facturen en rapportages."""

from flask import render_template_string, current_app
import io

try:
    from weasyprint import HTML
    WEASYPRINT_BESCHIKBAAR = True
except (ImportError, OSError):
    WEASYPRINT_BESCHIKBAAR = False


FACTUUR_PDF_TEMPLATE = """
<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="utf-8">
<style>
    body { font-family: Arial, sans-serif; font-size: 12px; color: #333; margin: 40px; }
    .header { display: flex; justify-content: space-between; margin-bottom: 30px; }
    .bedrijf { font-size: 11px; }
    .bedrijf h2 { margin: 0 0 5px 0; font-size: 16px; color: #2c3e50; }
    .factuur-titel { font-size: 24px; color: #2c3e50; margin-bottom: 20px; font-weight: bold; }
    .factuur-info { display: flex; justify-content: space-between; margin-bottom: 30px; }
    .klant-info, .factuur-meta { width: 45%; }
    .klant-info h3, .factuur-meta h3 { font-size: 13px; color: #7f8c8d; margin-bottom: 5px; text-transform: uppercase; }
    table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
    th { background-color: #2c3e50; color: white; padding: 10px 8px; text-align: left; font-size: 11px; }
    td { padding: 8px; border-bottom: 1px solid #eee; }
    .rechts { text-align: right; }
    .totalen { width: 300px; margin-left: auto; }
    .totalen td { padding: 5px 8px; }
    .totalen .totaal-rij { font-weight: bold; font-size: 14px; border-top: 2px solid #2c3e50; }
    .footer { margin-top: 40px; padding-top: 15px; border-top: 1px solid #ddd; font-size: 10px; color: #999; }
    .status { display: inline-block; padding: 3px 10px; border-radius: 3px; font-weight: bold; font-size: 11px; }
    .status-concept { background: #f0f0f0; color: #666; }
    .status-verzonden { background: #3498db; color: white; }
    .status-betaald { background: #27ae60; color: white; }
    .status-vervallen { background: #e74c3c; color: white; }
    .opmerkingen { margin-top: 20px; padding: 10px; background: #f9f9f9; border-left: 3px solid #2c3e50; font-size: 11px; }
</style>
</head>
<body>
    <div class="header">
        <div class="bedrijf">
            <h2>{{ bedrijf.naam }}</h2>
            <p>{{ bedrijf.adres }}<br>{{ bedrijf.postcode }} {{ bedrijf.plaats }}<br>{{ bedrijf.land }}</p>
            <p>KvK: {{ bedrijf.kvk }}<br>BTW: {{ bedrijf.btw }}<br>IBAN: {{ bedrijf.iban }}</p>
        </div>
        <div>
            <span class="status status-{{ factuur.status }}">{{ factuur.status|upper }}</span>
        </div>
    </div>

    <div class="factuur-titel">FACTUUR</div>

    <div class="factuur-info">
        <div class="klant-info">
            <h3>Factuur aan</h3>
            <strong>{{ klant.naam }}</strong><br>
            {% if klant.adres %}{{ klant.adres }}<br>{% endif %}
            {% if klant.postcode %}{{ klant.postcode }} {{ klant.plaats }}<br>{% endif %}
            {% if klant.btw_nummer %}BTW: {{ klant.btw_nummer }}{% endif %}
        </div>
        <div class="factuur-meta">
            <h3>Factuurgegevens</h3>
            <table style="width:100%">
                <tr><td>Factuurnummer:</td><td class="rechts"><strong>{{ factuur.factuurnummer }}</strong></td></tr>
                <tr><td>Factuurdatum:</td><td class="rechts">{{ factuur.factuurdatum.strftime('%d-%m-%Y') }}</td></tr>
                <tr><td>Vervaldatum:</td><td class="rechts">{{ factuur.vervaldatum.strftime('%d-%m-%Y') }}</td></tr>
                <tr><td>Valuta:</td><td class="rechts">{{ factuur.valuta }}</td></tr>
            </table>
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th>Omschrijving</th>
                <th class="rechts">Aantal</th>
                <th class="rechts">Prijs</th>
                <th class="rechts">BTW %</th>
                <th class="rechts">Totaal</th>
            </tr>
        </thead>
        <tbody>
            {% for regel in factuur.regels %}
            <tr>
                <td>{{ regel.omschrijving }}</td>
                <td class="rechts">{{ regel.aantal }}</td>
                <td class="rechts">{{ "€ {:,.2f}".format(regel.prijs_per_stuk) }}</td>
                <td class="rechts">{{ regel.btw_percentage }}%</td>
                <td class="rechts">{{ "€ {:,.2f}".format(regel.totaal) }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <table class="totalen">
        <tr><td>Subtotaal:</td><td class="rechts">{{ "€ {:,.2f}".format(factuur.subtotaal) }}</td></tr>
        <tr><td>BTW:</td><td class="rechts">{{ "€ {:,.2f}".format(factuur.btw_bedrag) }}</td></tr>
        <tr class="totaal-rij"><td>Totaal:</td><td class="rechts">{{ "€ {:,.2f}".format(factuur.totaal) }}</td></tr>
    </table>

    {% if factuur.opmerkingen %}
    <div class="opmerkingen">
        <strong>Opmerkingen:</strong><br>
        {{ factuur.opmerkingen }}
    </div>
    {% endif %}

    <div class="footer">
        <p>Betaling binnen 30 dagen na factuurdatum op IBAN {{ bedrijf.iban }} o.v.v. factuurnummer {{ factuur.factuurnummer }}.</p>
        <p>{{ bedrijf.naam }} | KvK {{ bedrijf.kvk }} | BTW {{ bedrijf.btw }}</p>
    </div>
</body>
</html>
"""


def genereer_factuur_html(factuur, klant):
    """Genereer HTML content voor een verkoopfactuur."""
    bedrijf = {
        'naam': current_app.config.get('BEDRIJFSNAAM', 'Mijn Bedrijf B.V.'),
        'adres': current_app.config.get('BEDRIJFSADRES', ''),
        'postcode': current_app.config.get('BEDRIJFSPOSTCODE', ''),
        'plaats': current_app.config.get('BEDRIJFSPLAATS', ''),
        'land': current_app.config.get('BEDRIJFSLAND', 'Nederland'),
        'kvk': current_app.config.get('BEDRIJFSKVK', ''),
        'btw': current_app.config.get('BEDRIJFSBTW', ''),
        'iban': current_app.config.get('BEDRIJFSIBAN', ''),
    }

    return render_template_string(
        FACTUUR_PDF_TEMPLATE,
        factuur=factuur,
        klant=klant,
        bedrijf=bedrijf
    )


def genereer_factuur_pdf(factuur, klant):
    """Genereer een PDF voor een verkoopfactuur. Valt terug op HTML als WeasyPrint niet beschikbaar is."""
    html_content = genereer_factuur_html(factuur, klant)

    if WEASYPRINT_BESCHIKBAAR:
        pdf_buffer = io.BytesIO()
        HTML(string=html_content).write_pdf(pdf_buffer)
        pdf_buffer.seek(0)
        return pdf_buffer, 'application/pdf'
    else:
        # Fallback: return HTML
        html_buffer = io.BytesIO(html_content.encode('utf-8'))
        return html_buffer, 'text/html'
