from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, Gebruiker

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        gebruikersnaam = request.form.get('gebruikersnaam', '').strip()
        wachtwoord = request.form.get('wachtwoord', '')

        gebruiker = Gebruiker.query.filter_by(gebruikersnaam=gebruikersnaam).first()

        if gebruiker and gebruiker.check_wachtwoord(wachtwoord):
            login_user(gebruiker)
            volgende = request.args.get('next')
            return redirect(volgende or url_for('dashboard.index'))

        flash('Ongeldige gebruikersnaam of wachtwoord.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('U bent uitgelogd.', 'success')
    return redirect(url_for('auth.login'))
