import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
for path in (HERE, os.path.dirname(HERE)):
    if path not in sys.path:
        sys.path.insert(0, path)

import server  # noqa: E402


def test_save_clubs_writes_json(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    clubs = [{"name": "X", "email": "x@test.com", "points": "5"}]
    server.saveClubs(clubs)
    data = json.loads((tmp_path / "clubs.json").read_text())
    assert data == {"clubs": clubs}


def test_save_competitions_writes_json(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    comps = [{"name": "Cup", "date": "2030-01-01 10:00:00",
              "numberOfPlaces": "10"}]
    server.saveCompetitions(comps)
    data = json.loads((tmp_path / "competitions.json").read_text())
    assert data == {"competitions": comps}
