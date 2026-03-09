from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta

db = SQLAlchemy()


class Gebruiker(UserMixin, db.Model):
    __tablename__ = 'gebruiker'
    id = db.Column(db.Integer, primary_key=True)
    gebruikersnaam = db.Column(db.String(80), unique=True, nullable=False)
    wachtwoord_hash = db.Column(db.String(256), nullable=False)
    naam = db.Column(db.String(200))
    is_admin = db.Column(db.Boolean, default=False)
    aangemaakt_op = db.Column(db.DateTime, default=datetime.utcnow)

    def set_wachtwoord(self, wachtwoord):
        self.wachtwoord_hash = generate_password_hash(wachtwoord, method='pbkdf2:sha256')

    def check_wachtwoord(self, wachtwoord):
        return check_password_hash(self.wachtwoord_hash, wachtwoord)

    def __repr__(self):
        return f'<Gebruiker {self.gebruikersnaam}>'


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
    iban = db.Column(db.String(34))
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
    iban = db.Column(db.String(34))
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
    pdf_bestand = db.Column(db.String(500))
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

            # Rubriek 2 - Schulden (kortlopend en langlopend)
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

            # Rubriek 7 - Kostprijsverrekening (niet altijd gebruikt)
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
        for code, naam, type_ in rekeningen:
            db.session.add(Grootboekrekening(code=code, naam=naam, type=type_))

    if Gebruiker.query.first() is None:
        import os
        admin = Gebruiker(
            gebruikersnaam=os.environ.get('ADMIN_USER', 'admin'),
            naam='Administrator',
            is_admin=True
        )
        admin.set_wachtwoord(os.environ.get('ADMIN_PASSWORD', 'changeme'))
        db.session.add(admin)

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
