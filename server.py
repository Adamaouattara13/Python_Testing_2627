import json
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, flash, url_for


def loadClubs():
    with open('clubs.json') as c:
        listOfClubs = json.load(c)['clubs']
        return listOfClubs


def loadCompetitions():
    with open('competitions.json') as comps:
        listOfCompetitions = json.load(comps)['competitions']
        return listOfCompetitions


def saveClubs(clubs_data):
    """Persist clubs data back to JSON file."""
    with open('clubs.json', 'w') as c:
        json.dump({'clubs': clubs_data}, c, indent=4)


def saveCompetitions(competitions_data):
    """Persist competitions data back to JSON file."""
    with open('competitions.json', 'w') as comps:
        json.dump({'competitions': competitions_data}, comps, indent=4)


def is_past_competition(competition):
    """Return True if the competition date is in the past.
    Returns True (safe default) if the date is missing or malformed.
    """
    try:
        comp_date = datetime.strptime(competition['date'], '%Y-%m-%d %H:%M:%S')
        return comp_date < datetime.now()
    except (ValueError, KeyError):
        return True  # Bug-05 fix: treat unparseable dates as past (safe default)


app = Flask(__name__, template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'))
app.secret_key = 'something_special'

competitions = loadCompetitions()
clubs = loadClubs()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/showSummary', methods=['POST'])
def showSummary():
    # Bug-01 fix: handle unknown email gracefully instead of crashing
    email = request.form.get('email', '').strip()
    club = next((c for c in clubs if c['email'] == email), None)
    if not club:
        flash('Email non trouvé. Veuillez vérifier votre adresse email.')
        return redirect(url_for('index'))
    return render_template('welcome.html', club=club, competitions=competitions)


@app.route('/book/<competition>/<club>')
def book(competition, club):
    # Bug-02 fix: handle unknown club/competition gracefully
    foundClub = next((c for c in clubs if c['name'] == club), None)
    foundCompetition = next((c for c in competitions if c['name'] == competition), None)

    if not foundClub:
        flash("Club introuvable - veuillez réessayer.")
        return redirect(url_for('index'))

    if not foundCompetition:
        flash("Compétition introuvable - veuillez réessayer.")
        return redirect(url_for('index'))

    # Bug-05 fix: prevent booking past competitions
    if is_past_competition(foundCompetition):
        flash("Impossible de réserver une compétition passée.")
        return render_template('welcome.html', club=foundClub, competitions=competitions)

    return render_template('booking.html', club=foundClub, competition=foundCompetition)


@app.route('/purchasePlaces', methods=['POST'])
def purchasePlaces():
    # Bug-03 fix: handle unknown club/competition gracefully
    competition_name = request.form.get('competition', '')
    club_name = request.form.get('club', '')

    competition = next((c for c in competitions if c['name'] == competition_name), None)
    club = next((c for c in clubs if c['name'] == club_name), None)

    if not competition or not club:
        flash('Données invalides - veuillez réessayer.')
        return redirect(url_for('index'))

    # Bug-05 fix: prevent purchasing places in past competitions
    if is_past_competition(competition):
        flash("Impossible de réserver une compétition passée.")
        return render_template('welcome.html', club=club, competitions=competitions)

    try:
        placesRequired = int(request.form.get('places', 0))
    except (ValueError, TypeError):
        flash('Nombre de places invalide.')
        return render_template('booking.html', club=club, competition=competition)

    if placesRequired <= 0:
        flash('Le nombre de places doit être supérieur à 0.')
        return render_template('booking.html', club=club, competition=competition)

    availablePlaces = int(competition['numberOfPlaces'])
    clubPoints = int(club['points'])

    # Bug-06 fix: cannot book more places than available
    if placesRequired > availablePlaces:
        flash(f'Seulement {availablePlaces} place(s) disponible(s) pour cette compétition.')
        return render_template('booking.html', club=club, competition=competition)

    # Bug-07 fix: max 12 places per club per competition
    if placesRequired > 12:
        flash('Vous ne pouvez pas réserver plus de 12 places par compétition.')
        return render_template('booking.html', club=club, competition=competition)

    # Bug-08 fix: cannot book more places than club has points
    if placesRequired > clubPoints:
        flash(f'Points insuffisants. Vous avez {clubPoints} point(s) disponible(s).')
        return render_template('booking.html', club=club, competition=competition)

    # Bug-04 fix: deduct points from club AND places from competition
    competition['numberOfPlaces'] = availablePlaces - placesRequired
    club['points'] = clubPoints - placesRequired

    # Bug-09 fix: persist changes to JSON files
    saveCompetitions(competitions)
    saveClubs(clubs)

    flash('Réservation confirmée !')
    return render_template('welcome.html', club=club, competitions=competitions)


# Bug-10 fix: /pointsDisplay is a public board (Phase 2 feature) — no auth needed, clean implementation
@app.route('/pointsDisplay')
def pointsDisplay():
    return render_template('points.html', clubs=clubs)


@app.route('/logout')
def logout():
    return redirect(url_for('index'))