from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta

db = SQLAlchemy()


class Klant(db.Model):
    __tablename__ = 'klant'
    id = db.Column(db.Integer, primary_key=True)
    naam = db.Column(db.String(200), nullable=False)
    adres = db.Column(db.String(200))
    postcode = db.Column(db.String(10))
    plaats = db.Column(db.String(100))
    land = db.Column(db.String(100), default='Nederland')
    kvk_nummer = db.Column(db.String(20))
    btw_nummer = db.Column(db.String(20))
    email = db.Column(db.String(200))
    telefoon = db.Column(db.String(20))
    aangemaakt_op = db.Column(db.DateTime, default=datetime.utcnow)
    facturen = db.relationship('Verkoopfactuur', backref='klant', lazy=True)

    def __repr__(self):
        return f'<Klant {self.naam}>'


class Leverancier(db.Model):
    __tablename__ = 'leverancier'
    id = db.Column(db.Integer, primary_key=True)
    naam = db.Column(db.String(200), nullable=False)
    adres = db.Column(db.String(200))
    postcode = db.Column(db.String(10))
    plaats = db.Column(db.String(100))
    land = db.Column(db.String(100), default='Nederland')
    kvk_nummer = db.Column(db.String(20))
    btw_nummer = db.Column(db.String(20))
    email = db.Column(db.String(200))
    telefoon = db.Column(db.String(20))
    aangemaakt_op = db.Column(db.DateTime, default=datetime.utcnow)
    facturen = db.relationship('Inkoopfactuur', backref='leverancier', lazy=True)

    def __repr__(self):
        return f'<Leverancier {self.naam}>'


class Grootboekrekening(db.Model):
    __tablename__ = 'grootboekrekening'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)
    naam = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # activa, passiva, kosten, opbrengsten

    def __repr__(self):
        return f'<Grootboekrekening {self.code} {self.naam}>'


class Valuta(db.Model):
    __tablename__ = 'valuta'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(3), unique=True, nullable=False)
    naam = db.Column(db.String(50), nullable=False)
    wisselkoers_naar_eur = db.Column(db.Float, nullable=False, default=1.0)

    def __repr__(self):
        return f'<Valuta {self.code}>'


class Verkoopfactuur(db.Model):
    __tablename__ = 'verkoopfactuur'
    id = db.Column(db.Integer, primary_key=True)
    factuurnummer = db.Column(db.String(20), unique=True, nullable=False)
    klant_id = db.Column(db.Integer, db.ForeignKey('klant.id'), nullable=False)
    factuurdatum = db.Column(db.Date, nullable=False, default=date.today)
    vervaldatum = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='concept')  # concept, verzonden, betaald, vervallen
    subtotaal = db.Column(db.Float, default=0.0)
    btw_bedrag = db.Column(db.Float, default=0.0)
    totaal = db.Column(db.Float, default=0.0)
    valuta = db.Column(db.String(3), default='EUR')
    opmerkingen = db.Column(db.Text)
    aangemaakt_op = db.Column(db.DateTime, default=datetime.utcnow)
    regels = db.relationship('VerkoopfactuurRegel', backref='factuur', lazy=True, cascade='all, delete-orphan')
    betalingen = db.relationship('Betaling',
                                 primaryjoin="and_(Betaling.factuur_id==Verkoopfactuur.id, Betaling.factuur_type=='verkoop')",
                                 foreign_keys='Betaling.factuur_id',
                                 lazy=True)

    @property
    def betaald_bedrag(self):
        return sum(b.bedrag for b in Betaling.query.filter_by(factuur_type='verkoop', factuur_id=self.id).all())

    @property
    def openstaand_bedrag(self):
        return self.totaal - self.betaald_bedrag

    @property
    def is_vervallen(self):
        return self.status not in ('betaald', 'concept') and self.vervaldatum < date.today()

    def __repr__(self):
        return f'<Verkoopfactuur {self.factuurnummer}>'


class VerkoopfactuurRegel(db.Model):
    __tablename__ = 'verkoopfactuur_regel'
    id = db.Column(db.Integer, primary_key=True)
    factuur_id = db.Column(db.Integer, db.ForeignKey('verkoopfactuur.id'), nullable=False)
    omschrijving = db.Column(db.String(500), nullable=False)
    aantal = db.Column(db.Float, nullable=False, default=1)
    prijs_per_stuk = db.Column(db.Float, nullable=False, default=0.0)
    btw_percentage = db.Column(db.Float, nullable=False, default=21.0)
    totaal = db.Column(db.Float, default=0.0)
    grootboekrekening_id = db.Column(db.Integer, db.ForeignKey('grootboekrekening.id'))
    grootboekrekening = db.relationship('Grootboekrekening')

    @property
    def netto_bedrag(self):
        return self.aantal * self.prijs_per_stuk

    @property
    def btw_bedrag(self):
        return self.netto_bedrag * (self.btw_percentage / 100)


class Inkoopfactuur(db.Model):
    __tablename__ = 'inkoopfactuur'
    id = db.Column(db.Integer, primary_key=True)
    factuurnummer = db.Column(db.String(20), nullable=False)
    leverancier_id = db.Column(db.Integer, db.ForeignKey('leverancier.id'), nullable=False)
    factuurdatum = db.Column(db.Date, nullable=False, default=date.today)
    vervaldatum = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='ontvangen')  # ontvangen, goedgekeurd, betaald, vervallen
    subtotaal = db.Column(db.Float, default=0.0)
    btw_bedrag = db.Column(db.Float, default=0.0)
    totaal = db.Column(db.Float, default=0.0)
    valuta = db.Column(db.String(3), default='EUR')
    opmerkingen = db.Column(db.Text)
    aangemaakt_op = db.Column(db.DateTime, default=datetime.utcnow)
    regels = db.relationship('InkoopfactuurRegel', backref='factuur', lazy=True, cascade='all, delete-orphan')

    @property
    def betaald_bedrag(self):
        return sum(b.bedrag for b in Betaling.query.filter_by(factuur_type='inkoop', factuur_id=self.id).all())

    @property
    def openstaand_bedrag(self):
        return self.totaal - self.betaald_bedrag

    @property
    def is_vervallen(self):
        return self.status not in ('betaald',) and self.vervaldatum < date.today()

    def __repr__(self):
        return f'<Inkoopfactuur {self.factuurnummer}>'


class InkoopfactuurRegel(db.Model):
    __tablename__ = 'inkoopfactuur_regel'
    id = db.Column(db.Integer, primary_key=True)
    factuur_id = db.Column(db.Integer, db.ForeignKey('inkoopfactuur.id'), nullable=False)
    omschrijving = db.Column(db.String(500), nullable=False)
    aantal = db.Column(db.Float, nullable=False, default=1)
    prijs_per_stuk = db.Column(db.Float, nullable=False, default=0.0)
    btw_percentage = db.Column(db.Float, nullable=False, default=21.0)
    totaal = db.Column(db.Float, default=0.0)
    grootboekrekening_id = db.Column(db.Integer, db.ForeignKey('grootboekrekening.id'))
    grootboekrekening = db.relationship('Grootboekrekening')

    @property
    def netto_bedrag(self):
        return self.aantal * self.prijs_per_stuk

    @property
    def btw_bedrag(self):
        return self.netto_bedrag * (self.btw_percentage / 100)


class Betaling(db.Model):
    __tablename__ = 'betaling'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False)  # inkomend, uitgaand
    factuur_type = db.Column(db.String(20), nullable=False)  # verkoop, inkoop
    factuur_id = db.Column(db.Integer, nullable=False)
    bedrag = db.Column(db.Float, nullable=False)
    datum = db.Column(db.Date, nullable=False, default=date.today)
    betaalmethode = db.Column(db.String(50), default='bank')
    referentie = db.Column(db.String(100))
    aangemaakt_op = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Betaling {self.type} {self.bedrag}>'


class Journaalpost(db.Model):
    __tablename__ = 'journaalpost'
    id = db.Column(db.Integer, primary_key=True)
    datum = db.Column(db.Date, nullable=False, default=date.today)
    omschrijving = db.Column(db.String(500), nullable=False)
    referentie = db.Column(db.String(100))
    aangemaakt_op = db.Column(db.DateTime, default=datetime.utcnow)
    regels = db.relationship('JournaalpostRegel', backref='journaalpost', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Journaalpost {self.id} {self.omschrijving}>'


class JournaalpostRegel(db.Model):
    __tablename__ = 'journaalpost_regel'
    id = db.Column(db.Integer, primary_key=True)
    journaalpost_id = db.Column(db.Integer, db.ForeignKey('journaalpost.id'), nullable=False)
    grootboekrekening_id = db.Column(db.Integer, db.ForeignKey('grootboekrekening.id'), nullable=False)
    debet = db.Column(db.Float, default=0.0)
    credit = db.Column(db.Float, default=0.0)
    grootboekrekening = db.relationship('Grootboekrekening')

    def __repr__(self):
        return f'<JournaalpostRegel {self.grootboekrekening_id} D:{self.debet} C:{self.credit}>'


def init_standaard_data():
    """Initialiseer standaard grootboekrekeningen en valuta's."""
    if Grootboekrekening.query.first() is None:
        rekeningen = [
            # Activa (1xxx)
            ('1000', 'Kas', 'activa'),
            ('1100', 'Bank', 'activa'),
            ('1200', 'Debiteuren', 'activa'),
            ('1300', 'Voorraad', 'activa'),
            ('1400', 'Vooruitbetaalde kosten', 'activa'),
            ('1500', 'Inventaris', 'activa'),
            ('1600', 'Machines', 'activa'),
            ('1700', 'Bedrijfsmiddelen', 'activa'),
            # Passiva (2xxx)
            ('2000', 'Crediteuren', 'passiva'),
            ('2100', 'BTW af te dragen', 'passiva'),
            ('2200', 'BTW te vorderen', 'passiva'),
            ('2300', 'Loonheffing', 'passiva'),
            ('2400', 'Eigen vermogen', 'passiva'),
            ('2500', 'Leningen', 'passiva'),
            ('2600', 'Overige schulden', 'passiva'),
            # Opbrengsten (8xxx)
            ('8000', 'Omzet', 'opbrengsten'),
            ('8100', 'Omzet dienstverlening', 'opbrengsten'),
            ('8200', 'Omzet producten', 'opbrengsten'),
            ('8300', 'Overige opbrengsten', 'opbrengsten'),
            # Kosten (4xxx)
            ('4000', 'Inkoopkosten', 'kosten'),
            ('4100', 'Personeelskosten', 'kosten'),
            ('4200', 'Huisvestingskosten', 'kosten'),
            ('4300', 'Kantoorkosten', 'kosten'),
            ('4400', 'Verkoopkosten', 'kosten'),
            ('4500', 'Autokosten', 'kosten'),
            ('4600', 'Afschrijvingen', 'kosten'),
            ('4700', 'Overige kosten', 'kosten'),
            ('4800', 'Financiele kosten', 'kosten'),
        ]
        for code, naam, type_ in rekeningen:
            db.session.add(Grootboekrekening(code=code, naam=naam, type=type_))

    if Valuta.query.first() is None:
        valutas = [
            ('EUR', 'Euro', 1.0),
            ('USD', 'US Dollar', 0.92),
            ('GBP', 'Brits Pond', 1.16),
            ('CHF', 'Zwitserse Frank', 1.04),
            ('SEK', 'Zweedse Kroon', 0.088),
            ('NOK', 'Noorse Kroon', 0.087),
            ('DKK', 'Deense Kroon', 0.134),
            ('PLN', 'Poolse Zloty', 0.23),
            ('CZK', 'Tsjechische Kroon', 0.041),
            ('JPY', 'Japanse Yen', 0.0062),
        ]
        for code, naam, koers in valutas:
            db.session.add(Valuta(code=code, naam=naam, wisselkoers_naar_eur=koers))

    db.session.commit()
