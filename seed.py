"""Database seed script - maakt tabellen, voert migraties uit en laadt standaarddata."""
from app import create_app
from models import db, Grootboekrekening, Valuta, Gebruiker
from sqlalchemy import inspect, text

app = create_app()


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


with app.app_context():
    db.create_all()

    inspector = inspect(db.engine)

    # Migraties uitvoeren
    print('Migraties controleren...')
    migraties(inspector)

    # Standaarddata laden
    if Grootboekrekening.query.first():
        print(f'Database bevat al {Grootboekrekening.query.count()} grootboekrekeningen. Seed overgeslagen.')
    else:
        from models import init_standaard_data
        init_standaard_data()
        print(f'Seed voltooid: {Grootboekrekening.query.count()} grootboekrekeningen, '
              f'{Valuta.query.count()} valutas, '
              f'{Gebruiker.query.count()} gebruiker(s) aangemaakt.')
