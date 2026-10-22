import json
from flask import Flask,render_template,request,redirect,flash,url_for


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
    placesRequired = int(request.form['places'])
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