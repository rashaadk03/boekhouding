import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'boekhouding-geheim-sleutel-2024')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'boekhouding.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BEDRIJFSNAAM = 'Mijn Bedrijf B.V.'
    BEDRIJFSADRES = 'Voorbeeldstraat 1'
    BEDRIJFSPOSTCODE = '1234 AB'
    BEDRIJFSPLAATS = 'Amsterdam'
    BEDRIJFSLAND = 'Nederland'
    BEDRIJFSKVK = '12345678'
    BEDRIJFSBTW = 'NL123456789B01'
    BEDRIJFSIBAN = 'NL00BANK0123456789'
