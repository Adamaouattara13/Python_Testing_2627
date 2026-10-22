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
