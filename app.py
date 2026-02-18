from flask import Flask
from config import Config
from models import db, init_standaard_data
from routes import all_blueprints


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    for bp in all_blueprints:
        app.register_blueprint(bp)

    with app.app_context():
        db.create_all()
        init_standaard_data()

    # Jinja2 filters
    @app.template_filter('euro')
    def euro_filter(value):
        try:
            return f"\u20ac {value:,.2f}"
        except (ValueError, TypeError):
            return f"\u20ac 0,00"

    @app.template_filter('datum')
    def datum_filter(value):
        if value:
            return value.strftime('%d-%m-%Y')
        return ''

    return app


app = create_app()

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
