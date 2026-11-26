import os
import sys
import threading

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from werkzeug.serving import make_server

HERE = os.path.dirname(os.path.abspath(__file__))
for path in (HERE, os.path.dirname(HERE)):
    if path not in sys.path:
        sys.path.insert(0, path)

import server  # noqa: E402


@pytest.fixture
def live_server(monkeypatch):
    """Lance l'application Flask dans un thread, avec des donnees de test."""
    monkeypatch.setattr(server, "clubs", [
        {"name": "Club A", "email": "a@test.com", "points": "13"},
        {"name": "Club B", "email": "b@test.com", "points": "4"},
    ])
    monkeypatch.setattr(server, "competitions", [
        {"name": "Future Cup", "date": "2030-03-27 10:00:00",
         "numberOfPlaces": "25"},
    ])
    # Evite d'ecraser les vrais fichiers clubs.json / competitions.json
    monkeypatch.setattr(server, "saveClubs", lambda data: None)
    monkeypatch.setattr(server, "saveCompetitions", lambda data: None)
    server.app.config["TESTING"] = True

    srv = make_server("127.0.0.1", 5001, server.app)
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    yield "http://127.0.0.1:5001"
    srv.shutdown()
    thread.join()


@pytest.fixture
def driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1280,900")
    drv = webdriver.Chrome(options=options)
    drv.implicitly_wait(3)
    yield drv
    drv.quit()


def click_and_wait(driver, selector="form button, form input[type=submit]"):
    button = driver.find_element(By.CSS_SELECTOR, selector)
    button.click()
    # Attend que la page soit remplacée (le bouton devient obsolète)
    WebDriverWait(driver, 10).until(EC.staleness_of(button))


def login(driver, live_server, email):
    driver.get(live_server)
    field = driver.find_element(By.NAME, "email")
    field.clear()
    field.send_keys(email)
    click_and_wait(driver)


def submit_places(driver, places):
    field = driver.find_element(By.NAME, "places")
    # Neutralise les contraintes HTML (min/max) pour tester la validation serveur
    driver.execute_script(
        "arguments[0].removeAttribute('max'); arguments[0].removeAttribute('min');",
        field,
    )
    field.clear()
    field.send_keys(str(places))
    click_and_wait(driver)


def test_login_with_valid_email(driver, live_server):
    login(driver, live_server, "a@test.com")
    assert "Club A" in driver.page_source


def test_login_with_unknown_email_stays_on_index(driver, live_server):
    login(driver, live_server, "inconnu@test.com")
    assert driver.current_url.rstrip("/") == live_server
    assert "Email non trouvé" in driver.page_source


def test_book_and_purchase_places(driver, live_server):
    login(driver, live_server, "a@test.com")
    driver.get(f"{live_server}/book/Future Cup/Club A")
    submit_places(driver, 2)
    assert "Réservation confirmée" in driver.page_source
    assert "11" in driver.page_source  # 13 - 2 points restants


def test_purchase_more_than_12_places_refused(driver, live_server):
    login(driver, live_server, "a@test.com")
    driver.get(f"{live_server}/book/Future Cup/Club A")
    submit_places(driver, 13)
    assert "Réservation confirmée" not in driver.page_source
    assert "Vous ne pouvez pas réserver plus de 12 places" in driver.page_source
