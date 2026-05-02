from fastapi.testclient import TestClient

from sidecar.suno_sidecar import app


client = TestClient(app)


def test_sidecar_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["service"] == "drakonya-suno-sidecar"
    assert data["live_suno_control"] is False


def test_sidecar_create_and_read_job():
    create = client.post(
        "/suno/generate",
        json={
            "prompt": "melodic vampire dubstep",
            "batch_id": "BATCH-TEST",
            "title": "Blood Drop Test",
            "genre": "gothic bass",
        },
    )

    assert create.status_code == 200
    data = create.json()
    sidecar_job_id = data["sidecar_job_id"]

    assert data["state"] == "created"
    assert data["batch_id"] == "BATCH-TEST"

    read = client.get(f"/suno/jobs/{sidecar_job_id}")
    assert read.status_code == 200
    assert read.json()["sidecar_job_id"] == sidecar_job_id


def test_sidecar_download_not_implemented():
    create = client.post(
        "/suno/generate",
        json={
            "prompt": "melodic vampire dubstep",
            "batch_id": "BATCH-TEST",
        },
    )
    sidecar_job_id = create.json()["sidecar_job_id"]

    download = client.post(f"/suno/jobs/{sidecar_job_id}/download")

    assert download.status_code == 501
    assert "not implemented" in download.json()["detail"].lower()
