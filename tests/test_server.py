import copy
import os
import sys
from datetime import datetime, timedelta

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import server  # noqa: E402
from server import app  # noqa: E402

CLUBS_DATA = {
    "clubs": [
        {"name": "Simply Lift", "email": "john@simplylift.co", "points": "13"},
        {"name": "Iron Temple", "email": "admin@irontemple.com", "points": "4"},
        {"name": "She Lifts", "email": "kate@shelifts.co.uk", "points": "12"}
    ]
}

COMPETITIONS_DATA = {
    "competitions": [
        {
            "name": "Future Festival",
            "date": (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S'),
            "numberOfPlaces": "25"
        },
        {
            "name": "Past Competition",
            "date": "2020-03-27 10:00:00",
            "numberOfPlaces": "10"
        }
    ]
}

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def client(monkeypatch):
    """Create a test client with in-memory test data."""
    test_clubs = copy.deepcopy(CLUBS_DATA['clubs'])
    test_competitions = copy.deepcopy(COMPETITIONS_DATA['competitions'])

    monkeypatch.setattr(server, 'clubs', test_clubs)
    monkeypatch.setattr(server, 'competitions', test_competitions)
    if hasattr(server, 'saveClubs'):
        monkeypatch.setattr(server, 'saveClubs', lambda data: None)
    if hasattr(server, 'saveCompetitions'):
        monkeypatch.setattr(server, 'saveCompetitions', lambda data: None)

    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    with app.test_client() as client:
        yield client


class TestIndex:
    def test_index_returns_200(self, client):
        """Happy path: page d'accueil accessible."""
        response = client.get('/')
        assert response.status_code == 200

    def test_index_contains_form(self, client):
        """La page d'accueil contient un formulaire email."""
        response = client.get('/')
        assert b'email' in response.data


class TestShowSummary:
    def test_valid_email_returns_welcome(self, client):
        """Happy path: email valide -> page welcome avec les points du club."""
        response = client.post('/showSummary', data={'email': 'john@simplylift.co'})
        assert response.status_code == 200
        assert b'john@simplylift.co' in response.data

    def test_valid_email_shows_points(self, client):
        """Happy path: les points du club sont affiches."""
        response = client.post('/showSummary', data={'email': 'john@simplylift.co'})
        assert b'13' in response.data

    def test_invalid_email_redirects_to_index(self, client):
        """Bug-01 fix: email inconnu -> redirection vers index, pas de crash."""
        response = client.post('/showSummary', data={'email': 'unknown@email.com'})
        assert response.status_code == 302

    def test_invalid_email_shows_flash_message(self, client):
        """Bug-01 fix: email inconnu -> message flash d'erreur visible."""
        response = client.post('/showSummary', data={'email': 'unknown@email.com'}, follow_redirects=True)
        assert response.status_code == 200
        assert 'non trouv'.encode('utf-8') in response.data or b'Email' in response.data or b'found' in response.data

    def test_empty_email_redirects(self, client):
        """Sad path: email vide -> redirection."""
        response = client.post('/showSummary', data={'email': ''})
        assert response.status_code == 302


class TestBook:
    def test_valid_club_and_competition(self, client):
        """Happy path: club et competition valides -> page booking."""
        response = client.get('/book/Future Festival/Simply Lift')
        assert response.status_code == 200
        assert b'Future Festival' in response.data

    def test_unknown_club_redirects(self, client):
        """Bug-02 fix: club inconnu -> redirection, pas de crash."""
        response = client.get('/book/Future Festival/Unknown Club')
        assert response.status_code == 302

    def test_unknown_competition_redirects(self, client):
        """Bug-02 fix: competition inconnue -> redirection, pas de crash."""
        response = client.get('/book/Unknown Competition/Simply Lift')
        assert response.status_code == 302


class TestPurchasePlaces:
    def test_valid_purchase(self, client):
        """Happy path: achat valide -> confirmation."""
        response = client.post('/purchasePlaces', data={
            'competition': 'Future Festival',
            'club': 'Simply Lift',
            'places': '2'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_cannot_book_more_than_available_places(self, client):
        """Bug-03 fix: ne peut pas reserver plus que le nombre de places disponibles."""
        response = client.post('/purchasePlaces', data={
            'competition': 'Future Festival',
            'club': 'Simply Lift',
            'places': '999'
        }, follow_redirects=True)
        assert b'disponible' in response.data or b'available' in response.data

    def test_places_deducted_from_competition(self, client):
        """Bug-04 fix: les places sont bien deduites de la competition."""
        initial_places = int(server.competitions[0]['numberOfPlaces'])
        client.post('/purchasePlaces', data={
            'competition': 'Future Festival',
            'club': 'Simply Lift',
            'places': '3'
        })
        assert int(server.competitions[0]['numberOfPlaces']) == initial_places - 3

    def test_points_deducted_from_club(self, client):
        """Bug-04 fix: les points sont bien deduits du club."""
        initial_points = int(server.clubs[0]['points'])
        client.post('/purchasePlaces', data={
            'competition': 'Future Festival',
            'club': 'Simply Lift',
            'places': '3'
        })
        assert int(server.clubs[0]['points']) == initial_points - 3

    def test_cannot_book_more_than_12_places(self, client):
        """Bug-05 fix: ne peut pas reserver plus de 12 places par competition."""
        response = client.post('/purchasePlaces', data={
            'competition': 'Future Festival',
            'club': 'Simply Lift',
            'places': '13'
        }, follow_redirects=True)
        assert b'12' in response.data

    def test_zero_places_rejected(self, client):
        """Bug-06 fix: 0 places -> message d'erreur."""
        response = client.post('/purchasePlaces', data={
            'competition': 'Future Festival',
            'club': 'Simply Lift',
            'places': '0'
        }, follow_redirects=True)
        assert b'sup' in response.data or b'0' in response.data

    def test_cannot_book_past_competition(self, client):
        """Bug-07 fix: impossible de reserver une competition passee."""
        response = client.post('/purchasePlaces', data={
            'competition': 'Past Competition',
            'club': 'Simply Lift',
            'places': '1'
        }, follow_redirects=True)
        assert b'pass' in response.data


class TestHelpers:
    def test_is_past_competition_past_date(self):
        """Competition passee -> True."""
        comp = {'date': '2020-01-01 00:00:00', 'name': 'Old'}
        assert server.is_past_competition(comp) is True

    def test_is_past_competition_future_date(self):
        """Competition future -> False."""
        future = (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d %H:%M:%S')
        comp = {'date': future, 'name': 'Future'}
        assert server.is_past_competition(comp) is False

    def test_is_past_competition_invalid_date(self):
        """Date invalide -> True."""
        comp = {'date': 'invalid-date', 'name': 'Bad'}
        assert server.is_past_competition(comp) is True

    def test_cannot_book_more_than_club_points(self, client):
        """Bug-08 fix: ne peut pas reserver plus de places que de points disponibles."""
        response = client.post('/purchasePlaces', data={
            'competition': 'Future Festival',
            'club': 'Iron Temple',
            'places': '5'
        }, follow_redirects=True)
        assert b'insuffisant' in response.data or b'point' in response.data
