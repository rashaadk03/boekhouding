from .dashboard import dashboard_bp
from .klanten import klanten_bp
from .leveranciers import leveranciers_bp
from .verkoopfacturen import verkoopfacturen_bp
from .inkoopfacturen import inkoopfacturen_bp
from .betalingen import betalingen_bp
from .grootboek import grootboek_bp
from .rapportages import rapportages_bp

all_blueprints = [
    dashboard_bp,
    klanten_bp,
    leveranciers_bp,
    verkoopfacturen_bp,
    inkoopfacturen_bp,
    betalingen_bp,
    grootboek_bp,
    rapportages_bp,
]
