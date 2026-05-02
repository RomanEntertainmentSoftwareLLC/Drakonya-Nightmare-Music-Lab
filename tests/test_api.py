from fastapi.testclient import TestClient

from app.api.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["service"] == "drakonya-nightmare-music-lab"


def test_current_provider_defaults_to_manual(monkeypatch):
    monkeypatch.delenv("SUNO_PROVIDER", raising=False)

    response = client.get("/providers/current")
    assert response.status_code == 200
    assert response.json()["provider"] == "manual_suno"


def test_create_generation_manual_provider(monkeypatch):
    monkeypatch.delenv("SUNO_PROVIDER", raising=False)

    response = client.post(
        "/generations",
        json={
            "prompt": "dark gothic techno test",
            "batch_id": "BATCH-TEST",
            "title": "Test Track",
            "genre": "gothic techno",
            "duration_hint": "3 minutes",
            "instrumental": True,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "manual_suno"
    assert data["state"] == "queued"
    assert data["batch_id"] == "BATCH-TEST"
