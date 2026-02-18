"""BTW-tarieven en berekeningen voor Nederlandse boekhouding."""

BTW_TARIEVEN = {
    21.0: 'Hoog tarief (21%)',
    9.0: 'Laag tarief (9%)',
    0.0: 'Vrijgesteld (0%)',
}


def bereken_btw(bedrag, percentage):
    """Bereken BTW-bedrag over een nettobedrag."""
    return round(bedrag * (percentage / 100), 2)


def bereken_netto(bruto, percentage):
    """Bereken nettobedrag vanuit brutobedrag."""
    return round(bruto / (1 + percentage / 100), 2)


def bereken_factuur_totalen(regels):
    """Bereken subtotaal, BTW en totaal voor een lijst factuurregels.

    regels: lijst van dicts met 'aantal', 'prijs_per_stuk', 'btw_percentage'
    """
    subtotaal = 0.0
    btw_bedrag = 0.0
    for regel in regels:
        netto = regel['aantal'] * regel['prijs_per_stuk']
        btw = bereken_btw(netto, regel['btw_percentage'])
        subtotaal += netto
        btw_bedrag += btw
    return {
        'subtotaal': round(subtotaal, 2),
        'btw_bedrag': round(btw_bedrag, 2),
        'totaal': round(subtotaal + btw_bedrag, 2),
    }
