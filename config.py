import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'boekhouding-geheim-sleutel-2024')
    _db_url = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'boekhouding.db'))
    # Railway geeft postgres:// maar SQLAlchemy vereist postgresql://
    if _db_url.startswith('postgres://'):
        _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BEDRIJFSNAAM = 'Mijn Bedrijf B.V.'
    BEDRIJFSADRES = 'Voorbeeldstraat 1'
    BEDRIJFSPOSTCODE = '1234 AB'
    BEDRIJFSPLAATS = 'Amsterdam'
    BEDRIJFSLAND = 'Nederland'
    BEDRIJFSKVK = '12345678'
    BEDRIJFSBTW = 'NL123456789B01'
    BEDRIJFSIBAN = 'NL00BANK0123456789'
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max
