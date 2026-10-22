import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, flash, url_for


def is_past_competition(competition):
    """Vérifie si la date d'une compétition est passée."""
    try:
        comp_date = datetime.strptime(competition['date'], '%Y-%m-%d %H:%M:%S')
        return comp_date < datetime.now()
    except (ValueError, KeyError, TypeError):
        return True



def loadClubs():
    with open('clubs.json') as c:
         listOfClubs = json.load(c)['clubs']
         return listOfClubs


def loadCompetitions():
    with open('competitions.json') as comps:
         listOfCompetitions = json.load(comps)['competitions']
         return listOfCompetitions


app = Flask(__name__)
app.secret_key = 'something_special'

competitions = loadCompetitions()
clubs = loadClubs()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/showSummary', methods=['POST'])
def showSummary():
    email = request.form.get('email', '').strip()
    matching_clubs = [club for club in clubs if club['email'] == email]
    if not matching_clubs:
        flash("Désolé, cette adresse email n'a pas été trouvée.", 'error')
        return redirect(url_for('index'))
    club = matching_clubs[0]
    return render_template('welcome.html', club=club, competitions=competitions)


@app.route('/book/<competition>/<club>')
def book(competition, club):
    found_clubs = [c for c in clubs if c['name'] == club]
    found_comps = [c for c in competitions if c['name'] == competition]
    if not found_clubs or not found_comps:
        flash("Club ou compétition introuvable.", 'error')
        return redirect(url_for('index'))
    foundClub = found_clubs[0]
    foundCompetition = found_comps[0]
    if is_past_competition(foundCompetition):
        flash("Cette compétition est déjà terminée.", 'error')
        return redirect(url_for('index'))
    return render_template('booking.html', club=foundClub, competition=foundCompetition)


@app.route('/purchasePlaces', methods=['POST'])
def purchasePlaces():
    comp_matches = [c for c in competitions if c['name'] == request.form.get('competition')]
    club_matches = [c for c in clubs if c['name'] == request.form.get('club')]
    if not comp_matches or not club_matches:
        flash("Données de réservation invalides.", 'error')
        return redirect(url_for('index'))
    competition = comp_matches[0]
    club = club_matches[0]
    if is_past_competition(competition):
        flash("Impossible de réserver pour une compétition passée.", 'error')
        return render_template('welcome.html', club=club, competitions=competitions)
    try:
        placesRequired = int(request.form.get('places', 0))
    except (ValueError, TypeError):
        flash("Veuillez saisir un nombre entier valide.", 'error')
        return render_template('booking.html', club=club, competition=competition)
    if placesRequired <= 0:
        flash("Le nombre de places doit être supérieur à zéro.", 'error')
        return render_template('booking.html', club=club, competition=competition)
    if placesRequired > 12:
        flash("Impossible de réserver plus de 12 places en une seule fois.", 'error')
        return render_template('booking.html', club=club, competition=competition)
    if placesRequired > int(club['points']):
        flash("Vous n'avez pas assez de points pour réserver ce nombre de places.", 'error')
        return render_template('booking.html', club=club, competition=competition)
    if placesRequired > int(competition['numberOfPlaces']):
        flash(f"Impossible de réserver : seulement {competition['numberOfPlaces']} places disponibles.", 'error')
        return render_template('booking.html', club=club, competition=competition)
    competition['numberOfPlaces'] = int(competition['numberOfPlaces']) - placesRequired
    club['points'] = int(club['points']) - placesRequired
    flash('Great-booking complete!')
    return render_template('welcome.html', club=club, competitions=competitions)


# TODO: Add route for points display


@app.route('/logout')
def logout():
    return redirect(url_for('index'))