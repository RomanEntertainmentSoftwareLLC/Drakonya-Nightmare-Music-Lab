from pathlib import Path

from fastapi.testclient import TestClient

from sidecar import suno_sidecar
from sidecar.suno_sidecar import app


client = TestClient(app)


def test_sidecar_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["service"] == "drakonya-suno-sidecar"
    assert data["live_suno_control"] is False
    assert "browser_available" in data
    assert "browser_profile_dir" in data
    assert "download_dir" in data


def test_sidecar_open_returns_501_without_browser(monkeypatch):
    monkeypatch.delenv("SUNO_BROWSER_BIN", raising=False)
    monkeypatch.setattr(suno_sidecar.shutil, "which", lambda _name: None)

    response = client.post("/suno/open")

    assert response.status_code == 501
    assert "no supported browser" in response.json()["detail"].lower()


def test_sidecar_open_launches_configured_browser(tmp_path: Path, monkeypatch):
    fake_browser = tmp_path / "fake-browser"
    fake_browser.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    fake_browser.chmod(0o755)

    launched: dict[str, list[str] | int] = {}

    class FakeProcess:
        pid = 12345

    def fake_popen(command):
        launched["command"] = command
        return FakeProcess()

    monkeypatch.setenv("DRAKONYA_ROOT", str(tmp_path))
    monkeypatch.setenv("SUNO_BROWSER_BIN", str(fake_browser))
    monkeypatch.setattr(suno_sidecar.subprocess, "Popen", fake_popen)

    response = client.post("/suno/open", json={"url": "https://suno.com"})

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["pid"] == 12345
    assert str(fake_browser) == data["browser_binary"]
    assert launched["command"][0] == str(fake_browser)
    assert "https://suno.com" in launched["command"]
    assert (tmp_path / "state" / "suno_browser_profile").exists()
    assert (tmp_path / "data" / "inbox" / "suno_downloads").exists()


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
