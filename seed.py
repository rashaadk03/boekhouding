"""Database seed script - maakt tabellen en laadt standaarddata."""
from app import create_app
from models import db, Grootboekrekening, Valuta, Gebruiker

app = create_app()

with app.app_context():
    db.create_all()

    # Controleer of seed al is uitgevoerd
    if Grootboekrekening.query.first():
        print(f'Database bevat al {Grootboekrekening.query.count()} grootboekrekeningen. Seed overgeslagen.')
    else:
        from models import init_standaard_data
        init_standaard_data()
        print(f'Seed voltooid: {Grootboekrekening.query.count()} grootboekrekeningen, '
              f'{Valuta.query.count()} valutas, '
              f'{Gebruiker.query.count()} gebruiker(s) aangemaakt.')
