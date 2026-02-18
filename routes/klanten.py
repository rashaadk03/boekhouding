from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Klant

klanten_bp = Blueprint('klanten', __name__, url_prefix='/klanten')


@klanten_bp.route('/')
def lijst():
    zoek = request.args.get('zoek', '')
    if zoek:
        klanten = Klant.query.filter(
            Klant.naam.ilike(f'%{zoek}%') |
            Klant.email.ilike(f'%{zoek}%') |
            Klant.plaats.ilike(f'%{zoek}%')
        ).order_by(Klant.naam).all()
    else:
        klanten = Klant.query.order_by(Klant.naam).all()
    return render_template('klanten/lijst.html', klanten=klanten, zoek=zoek)


@klanten_bp.route('/nieuw', methods=['GET', 'POST'])
def nieuw():
    if request.method == 'POST':
        klant = Klant(
            naam=request.form['naam'],
            adres=request.form.get('adres', ''),
            postcode=request.form.get('postcode', ''),
            plaats=request.form.get('plaats', ''),
            land=request.form.get('land', 'Nederland'),
            kvk_nummer=request.form.get('kvk_nummer', ''),
            btw_nummer=request.form.get('btw_nummer', ''),
            email=request.form.get('email', ''),
            telefoon=request.form.get('telefoon', ''),
        )
        db.session.add(klant)
        db.session.commit()
        flash(f'Klant "{klant.naam}" is aangemaakt.', 'success')
        return redirect(url_for('klanten.lijst'))
    return render_template('klanten/form.html', klant=None)


@klanten_bp.route('/<int:id>/bewerk', methods=['GET', 'POST'])
def bewerk(id):
    klant = Klant.query.get_or_404(id)
    if request.method == 'POST':
        klant.naam = request.form['naam']
        klant.adres = request.form.get('adres', '')
        klant.postcode = request.form.get('postcode', '')
        klant.plaats = request.form.get('plaats', '')
        klant.land = request.form.get('land', 'Nederland')
        klant.kvk_nummer = request.form.get('kvk_nummer', '')
        klant.btw_nummer = request.form.get('btw_nummer', '')
        klant.email = request.form.get('email', '')
        klant.telefoon = request.form.get('telefoon', '')
        db.session.commit()
        flash(f'Klant "{klant.naam}" is bijgewerkt.', 'success')
        return redirect(url_for('klanten.lijst'))
    return render_template('klanten/form.html', klant=klant)


@klanten_bp.route('/<int:id>/verwijder', methods=['POST'])
def verwijder(id):
    klant = Klant.query.get_or_404(id)
    if klant.facturen:
        flash('Kan klant niet verwijderen: er zijn facturen gekoppeld.', 'danger')
        return redirect(url_for('klanten.lijst'))
    naam = klant.naam
    db.session.delete(klant)
    db.session.commit()
    flash(f'Klant "{naam}" is verwijderd.', 'success')
    return redirect(url_for('klanten.lijst'))
