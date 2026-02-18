from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Leverancier

leveranciers_bp = Blueprint('leveranciers', __name__, url_prefix='/leveranciers')


@leveranciers_bp.route('/')
def lijst():
    zoek = request.args.get('zoek', '')
    if zoek:
        leveranciers = Leverancier.query.filter(
            Leverancier.naam.ilike(f'%{zoek}%') |
            Leverancier.email.ilike(f'%{zoek}%') |
            Leverancier.plaats.ilike(f'%{zoek}%')
        ).order_by(Leverancier.naam).all()
    else:
        leveranciers = Leverancier.query.order_by(Leverancier.naam).all()
    return render_template('leveranciers/lijst.html', leveranciers=leveranciers, zoek=zoek)


@leveranciers_bp.route('/nieuw', methods=['GET', 'POST'])
def nieuw():
    if request.method == 'POST':
        leverancier = Leverancier(
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
        db.session.add(leverancier)
        db.session.commit()
        flash(f'Leverancier "{leverancier.naam}" is aangemaakt.', 'success')
        return redirect(url_for('leveranciers.lijst'))
    return render_template('leveranciers/form.html', leverancier=None)


@leveranciers_bp.route('/<int:id>/bewerk', methods=['GET', 'POST'])
def bewerk(id):
    leverancier = Leverancier.query.get_or_404(id)
    if request.method == 'POST':
        leverancier.naam = request.form['naam']
        leverancier.adres = request.form.get('adres', '')
        leverancier.postcode = request.form.get('postcode', '')
        leverancier.plaats = request.form.get('plaats', '')
        leverancier.land = request.form.get('land', 'Nederland')
        leverancier.kvk_nummer = request.form.get('kvk_nummer', '')
        leverancier.btw_nummer = request.form.get('btw_nummer', '')
        leverancier.email = request.form.get('email', '')
        leverancier.telefoon = request.form.get('telefoon', '')
        db.session.commit()
        flash(f'Leverancier "{leverancier.naam}" is bijgewerkt.', 'success')
        return redirect(url_for('leveranciers.lijst'))
    return render_template('leveranciers/form.html', leverancier=leverancier)


@leveranciers_bp.route('/<int:id>/verwijder', methods=['POST'])
def verwijder(id):
    leverancier = Leverancier.query.get_or_404(id)
    if leverancier.facturen:
        flash('Kan leverancier niet verwijderen: er zijn facturen gekoppeld.', 'danger')
        return redirect(url_for('leveranciers.lijst'))
    naam = leverancier.naam
    db.session.delete(leverancier)
    db.session.commit()
    flash(f'Leverancier "{naam}" is verwijderd.', 'success')
    return redirect(url_for('leveranciers.lijst'))
