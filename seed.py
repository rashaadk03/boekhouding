"""Database seed script - maakt tabellen, voert migraties uit en laadt standaarddata."""
from app import create_app
from models import db, Grootboekrekening, Valuta, Gebruiker
from sqlalchemy import inspect, text

app = create_app()

REKENINGSCHEMA = [
    # Rubriek 0 - Vaste activa
    ('0100', 'Goodwill', 'activa'),
    ('0110', 'Afschrijving goodwill', 'activa'),
    ('0200', 'Ontwikkelingskosten', 'activa'),
    ('0210', 'Afschrijving ontwikkelingskosten', 'activa'),
    ('0300', 'Concessies en licenties', 'activa'),
    ('0310', 'Afschrijving concessies en licenties', 'activa'),
    ('0400', 'Gebouwen', 'activa'),
    ('0410', 'Afschrijving gebouwen', 'activa'),
    ('0500', 'Machines en installaties', 'activa'),
    ('0510', 'Afschrijving machines en installaties', 'activa'),
    ('0600', 'Inventaris en inrichting', 'activa'),
    ('0610', 'Afschrijving inventaris en inrichting', 'activa'),
    ('0700', 'Vervoermiddelen', 'activa'),
    ('0710', 'Afschrijving vervoermiddelen', 'activa'),
    ('0800', 'Computerapparatuur', 'activa'),
    ('0810', 'Afschrijving computerapparatuur', 'activa'),
    ('0900', 'Deelnemingen', 'activa'),
    ('0950', 'Leningen u/g (langlopend)', 'activa'),

    # Rubriek 1 - Vlottende activa
    ('1000', 'Kas', 'activa'),
    ('1100', 'Bank', 'activa'),
    ('1110', 'Spaarrekening', 'activa'),
    ('1120', 'Kruisposten', 'activa'),
    ('1200', 'Debiteuren', 'activa'),
    ('1210', 'Dubieuze debiteuren', 'activa'),
    ('1220', 'Voorziening dubieuze debiteuren', 'activa'),
    ('1300', 'Voorraad grondstoffen', 'activa'),
    ('1310', 'Voorraad gereed product', 'activa'),
    ('1320', 'Voorraad handelsgoederen', 'activa'),
    ('1330', 'Onderhanden werk', 'activa'),
    ('1400', 'Vooruitbetaalde bedragen', 'activa'),
    ('1410', 'Nog te ontvangen bedragen', 'activa'),
    ('1420', 'Waarborgsommen', 'activa'),
    ('1500', 'Te vorderen vennootschapsbelasting', 'activa'),
    ('1510', 'Te vorderen omzetbelasting', 'activa'),

    # Rubriek 2 - Schulden
    ('2000', 'Crediteuren', 'passiva'),
    ('2100', 'BTW af te dragen', 'passiva'),
    ('2110', 'BTW hoog tarief', 'passiva'),
    ('2120', 'BTW laag tarief', 'passiva'),
    ('2130', 'BTW verlegd', 'passiva'),
    ('2140', 'BTW binnen EU', 'passiva'),
    ('2200', 'BTW te vorderen', 'passiva'),
    ('2210', 'BTW voorbelasting', 'passiva'),
    ('2300', 'Loonheffing', 'passiva'),
    ('2310', 'Pensioenpremies', 'passiva'),
    ('2320', 'Sociale lasten', 'passiva'),
    ('2400', 'Nog te betalen bedragen', 'passiva'),
    ('2410', 'Vooruitontvangen bedragen', 'passiva'),
    ('2500', 'Hypothecaire lening', 'passiva'),
    ('2510', 'Leningen o/g (langlopend)', 'passiva'),
    ('2520', 'Financiële lease', 'passiva'),
    ('2600', 'Te betalen vennootschapsbelasting', 'passiva'),
    ('2700', 'Rekening-courant directie', 'passiva'),
    ('2800', 'Overige kortlopende schulden', 'passiva'),

    # Rubriek 3 - Eigen vermogen en voorzieningen
    ('3000', 'Eigen vermogen', 'passiva'),
    ('3010', 'Aandelenkapitaal', 'passiva'),
    ('3020', 'Agioreserve', 'passiva'),
    ('3100', 'Algemene reserve', 'passiva'),
    ('3200', 'Overige reserves', 'passiva'),
    ('3300', 'Onverdeeld resultaat', 'passiva'),
    ('3400', 'Winst lopend boekjaar', 'passiva'),
    ('3500', 'Privéstortingen', 'passiva'),
    ('3510', 'Privéopnamen', 'passiva'),
    ('3600', 'Voorziening garantie', 'passiva'),
    ('3610', 'Voorziening groot onderhoud', 'passiva'),
    ('3620', 'Voorziening deelnemingen', 'passiva'),

    # Rubriek 4 - Kosten (inkoop en productie)
    ('4000', 'Inkoopkosten', 'kosten'),
    ('4010', 'Inkoopkosten grondstoffen', 'kosten'),
    ('4020', 'Inkoopkosten handelsgoederen', 'kosten'),
    ('4030', 'Inkoopkosten uitbesteed werk', 'kosten'),
    ('4040', 'Inkoopkortingen', 'kosten'),
    ('4100', 'Lonen en salarissen', 'kosten'),
    ('4110', 'Vakantiegeld', 'kosten'),
    ('4120', 'Sociale lasten werkgever', 'kosten'),
    ('4130', 'Pensioenpremies werkgever', 'kosten'),
    ('4140', 'Overige personeelskosten', 'kosten'),
    ('4150', 'Uitzendkrachten', 'kosten'),
    ('4160', 'Reiskosten personeel', 'kosten'),
    ('4170', 'Opleidingskosten', 'kosten'),
    ('4180', 'Arbokosten', 'kosten'),
    ('4200', 'Huisvestingskosten', 'kosten'),
    ('4210', 'Huur bedrijfspand', 'kosten'),
    ('4220', 'Energie en water', 'kosten'),
    ('4230', 'Schoonmaakkosten', 'kosten'),
    ('4240', 'Onderhoud bedrijfspand', 'kosten'),
    ('4250', 'Verzekering bedrijfspand', 'kosten'),
    ('4260', 'Onroerende zaakbelasting', 'kosten'),

    # Rubriek 5 - Overige bedrijfskosten
    ('4300', 'Kantoorkosten', 'kosten'),
    ('4310', 'Kantoorbenodigdheden', 'kosten'),
    ('4320', 'Porti en verzendkosten', 'kosten'),
    ('4330', 'Telefoonkosten', 'kosten'),
    ('4340', 'Internetkosten', 'kosten'),
    ('4350', 'Softwarekosten en licenties', 'kosten'),
    ('4360', 'Drukwerk en kopieën', 'kosten'),
    ('4400', 'Verkoopkosten', 'kosten'),
    ('4410', 'Reclame en advertenties', 'kosten'),
    ('4420', 'Beurzen en evenementen', 'kosten'),
    ('4430', 'Representatiekosten', 'kosten'),
    ('4440', 'Relatiegeschenken', 'kosten'),
    ('4500', 'Autokosten', 'kosten'),
    ('4510', 'Brandstofkosten', 'kosten'),
    ('4520', 'Onderhoud voertuigen', 'kosten'),
    ('4530', 'Motorrijtuigenbelasting', 'kosten'),
    ('4540', 'Verzekering voertuigen', 'kosten'),
    ('4550', 'Leasekosten', 'kosten'),
    ('4600', 'Afschrijvingskosten', 'kosten'),
    ('4610', 'Afschrijving goodwill', 'kosten'),
    ('4620', 'Afschrijving inventaris', 'kosten'),
    ('4630', 'Afschrijving machines', 'kosten'),
    ('4640', 'Afschrijving vervoermiddelen', 'kosten'),
    ('4650', 'Afschrijving computerapparatuur', 'kosten'),

    # Rubriek 6 - Algemene kosten
    ('4700', 'Overige bedrijfskosten', 'kosten'),
    ('4710', 'Accountantskosten', 'kosten'),
    ('4720', 'Administratiekosten', 'kosten'),
    ('4730', 'Advieskosten', 'kosten'),
    ('4740', 'Juridische kosten', 'kosten'),
    ('4750', 'Verzekeringskosten', 'kosten'),
    ('4760', 'Contributies en abonnementen', 'kosten'),
    ('4770', 'KvK-kosten', 'kosten'),
    ('4780', 'Boetes en dwangsommen', 'kosten'),
    ('4790', 'Diverse kosten', 'kosten'),
    ('4800', 'Financiële lasten', 'kosten'),
    ('4810', 'Rentelasten bank', 'kosten'),
    ('4820', 'Rentelasten leningen', 'kosten'),
    ('4830', 'Bankkosten', 'kosten'),
    ('4840', 'Valutaverschillen', 'kosten'),
    ('4850', 'Incassokosten', 'kosten'),
    ('4900', 'Bijzondere lasten', 'kosten'),
    ('4910', 'Boekwaarde verkochte activa', 'kosten'),

    # Rubriek 7 - Kostprijsverrekening
    ('7000', 'Doorbelaste kosten', 'kosten'),
    ('7100', 'Interne leveringen', 'kosten'),
    ('7200', 'Geactiveerde productie', 'kosten'),

    # Rubriek 8 - Opbrengsten
    ('8000', 'Omzet', 'opbrengsten'),
    ('8010', 'Omzet binnenland', 'opbrengsten'),
    ('8020', 'Omzet buitenland EU', 'opbrengsten'),
    ('8030', 'Omzet buitenland niet-EU', 'opbrengsten'),
    ('8100', 'Omzet dienstverlening', 'opbrengsten'),
    ('8200', 'Omzet producten', 'opbrengsten'),
    ('8300', 'Overige opbrengsten', 'opbrengsten'),
    ('8310', 'Verhuur opbrengsten', 'opbrengsten'),
    ('8320', 'Provisie-inkomsten', 'opbrengsten'),
    ('8400', 'Kortingen en bonussen', 'opbrengsten'),
    ('8500', 'Geactiveerde productie', 'opbrengsten'),
    ('8600', 'Subsidies', 'opbrengsten'),

    # Rubriek 9 - Financiële baten en resultaat
    ('9000', 'Financiële baten', 'opbrengsten'),
    ('9010', 'Rentebaten bank', 'opbrengsten'),
    ('9020', 'Rentebaten leningen', 'opbrengsten'),
    ('9030', 'Dividendopbrengsten', 'opbrengsten'),
    ('9100', 'Bijzondere baten', 'opbrengsten'),
    ('9110', 'Boekwinst verkochte activa', 'opbrengsten'),
    ('9200', 'Vennootschapsbelasting', 'kosten'),
    ('9300', 'Resultaat na belasting', 'opbrengsten'),
]


def kolom_bestaat(inspector, tabel, kolom):
    """Controleer of een kolom bestaat in een tabel."""
    kolommen = [c['name'] for c in inspector.get_columns(tabel)]
    return kolom in kolommen


def migraties(inspector):
    """Voer database migraties uit voor ontbrekende kolommen."""
    migratie_lijst = [
        ('klant', 'iban', 'VARCHAR(34)'),
        ('leverancier', 'iban', 'VARCHAR(34)'),
        ('inkoopfactuur', 'pdf_bestand', 'VARCHAR(500)'),
    ]

    for tabel, kolom, kolom_type in migratie_lijst:
        if tabel in inspector.get_table_names() and not kolom_bestaat(inspector, tabel, kolom):
            db.session.execute(text(f'ALTER TABLE {tabel} ADD COLUMN {kolom} {kolom_type}'))
            print(f'  Kolom {tabel}.{kolom} toegevoegd.')

    db.session.commit()


def sync_rekeningschema():
    """Voeg ontbrekende grootboekrekeningen toe (behoudt bestaande)."""
    bestaande_codes = {r.code for r in Grootboekrekening.query.all()}
    toegevoegd = 0

    for code, naam, type_ in REKENINGSCHEMA:
        if code not in bestaande_codes:
            db.session.add(Grootboekrekening(code=code, naam=naam, type=type_))
            toegevoegd += 1

    if toegevoegd > 0:
        db.session.commit()
        print(f'  {toegevoegd} ontbrekende grootboekrekeningen toegevoegd.')
    else:
        print(f'  Alle {len(REKENINGSCHEMA)} grootboekrekeningen aanwezig.')


with app.app_context():
    db.create_all()

    inspector = inspect(db.engine)

    # Migraties uitvoeren
    print('Migraties controleren...')
    migraties(inspector)

    # Rekeningschema synchroniseren
    print('Rekeningschema controleren...')
    sync_rekeningschema()

    # Standaarddata laden (valuta's en admin gebruiker)
    from models import init_standaard_data
    init_standaard_data()

    print(f'Seed voltooid: {Grootboekrekening.query.count()} grootboekrekeningen, '
          f'{Valuta.query.count()} valutas, '
          f'{Gebruiker.query.count()} gebruiker(s).')
