"""
Locust performance test file for GUDLFT Registration Portal.
Usage: locust -f tests/locustfile.py --host=http://localhost:5000
"""
from locust import HttpUser, task, between


class GUDLFTUser(HttpUser):
    """Simulates a typical user of the GUDLFT portal."""
    wait_time = between(1, 3)

    def on_start(self):
        """Login when the user starts."""
        self.client.post('/showSummary', data={'email': 'john@simplylift.co'})

    @task(3)
    def view_index(self):
        """Consulter la page d'accueil."""
        self.client.get('/')

    @task(5)
    def login(self):
        """Se connecter avec un email valide."""
        self.client.post('/showSummary', data={'email': 'john@simplylift.co'})

    @task(2)
    def view_booking_page(self):
        """Voir la page de réservation pour une compétition."""
        self.client.get('/book/Future Festival/Simply Lift')

    @task(1)
    def purchase_places(self):
        """Réserver des places (happy path)."""
        self.client.post('/purchasePlaces', data={
            'competition': 'Future Festival',
            'club': 'Simply Lift',
            'places': '1'
        })

    @task(2)
    def view_points_board(self):
        """Consulter le tableau des points (public)."""
        self.client.get('/pointsDisplay')

    @task(1)
    def logout(self):
        """Se déconnecter."""
        self.client.get('/logout')


class InvalidEmailUser(HttpUser):
    """Simulates a user with invalid credentials (error cases)."""
    wait_time = between(2, 5)

    @task
    def login_with_invalid_email(self):
        """Tenter de se connecter avec un email inconnu."""
        self.client.post('/showSummary', data={'email': 'hacker@unknown.com'})

    @task
    def book_nonexistent_competition(self):
        """Tenter de réserver une compétition inexistante."""
        self.client.get('/book/FakeCompetition/Simply Lift')
