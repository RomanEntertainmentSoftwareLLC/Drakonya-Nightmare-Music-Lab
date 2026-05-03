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


def test_attach_variant_audio_and_select_winner_api(tmp_path):
    create_response = client.post(
        "/jobs/generate",
        json={
            "prompt": "dark gothic techno test",
            "batch_id": "BATCH-API-TEST",
            "title": "API Test Track",
            "genre": "gothic techno",
            "provider": "manual_suno",
        },
    )

    assert create_response.status_code == 200
    job_id = create_response.json()["job_id"]

    a = tmp_path / "version_a.mp3"
    b = tmp_path / "version_b.mp3"
    a.write_bytes(b"fake audio a")
    b.write_bytes(b"fake audio b")

    attach_a = client.post(
        f"/jobs/{job_id}/variants/A/attach",
        json={"source_audio_path": str(a)},
    )
    assert attach_a.status_code == 200

    attach_b = client.post(
        f"/jobs/{job_id}/variants/B/attach",
        json={"source_audio_path": str(b)},
    )
    assert attach_b.status_code == 200
    assert attach_b.json()["status"] == "downloaded"

    winner = client.post(
        f"/jobs/{job_id}/select-winner",
        json={
            "winner_variant_id": "A",
            "notes": "Version A has better energy.",
        },
    )

    assert winner.status_code == 200
    data = winner.json()

    assert data["status"] == "selected"
    assert data["winner_variant_id"] == "A"

    statuses = {variant["variant_id"]: variant["status"] for variant in data["variants"]}
    assert statuses["A"] == "APPROVED"
    assert statuses["B"] == "SLOP_BIN"


def test_create_job_and_submit_to_manual_provider(monkeypatch):
    monkeypatch.delenv("SUNO_PROVIDER", raising=False)

    create_response = client.post(
        "/jobs/generate",
        json={
            "prompt": "dark gothic techno test",
            "batch_id": "BATCH-SUBMIT-TEST",
            "title": "Submit Test Track",
            "genre": "gothic techno",
            "provider": "manual_suno",
        },
    )

    assert create_response.status_code == 200
    job_id = create_response.json()["job_id"]

    submit_response = client.post(f"/jobs/{job_id}/submit")

    assert submit_response.status_code == 200
    data = submit_response.json()

    assert data["job_id"] == job_id
    assert data["provider"] == "manual_suno"
    assert data["provider_task_id"].startswith("manual-")
    assert data["status"] == "generated"
