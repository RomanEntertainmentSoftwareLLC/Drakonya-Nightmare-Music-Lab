from pathlib import Path

from app.core.jobs import JOB_STATUS_DOWNLOADED, create_generation_job, load_job, mark_job_submitted
from app.providers.base import GeneratedTrack
from app.tools.fetch_provider_downloads import fetch_provider_downloads
from fastapi.testclient import TestClient
from sidecar import suno_sidecar
from sidecar.suno_sidecar import app


client = TestClient(app)


def test_sidecar_generate_stages_prompt_file(tmp_path, monkeypatch):
    monkeypatch.setenv("DRAKONYA_ROOT", str(tmp_path))
    monkeypatch.setattr(suno_sidecar.shutil, "which", lambda _name: None)

    response = client.post(
        "/suno/generate",
        json={
            "prompt": "Instrumental coding focus track with rain and soft synths.",
            "batch_id": "BATCH-TEST",
            "title": "Code Rain Drive",
            "genre": "coding focus",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["state"] == "submitted"
    assert data["sidecar_job_id"].startswith("SUNO-")
    assert data["prompt_file"]
    assert Path(data["prompt_file"]).exists()
    assert "coding focus" in data["genre"]


def test_sidecar_download_maps_two_inbox_files(tmp_path, monkeypatch):
    monkeypatch.setenv("DRAKONYA_ROOT", str(tmp_path))
    monkeypatch.setattr(suno_sidecar.shutil, "which", lambda _name: None)

    create = client.post(
        "/suno/generate",
        json={
            "prompt": "Peaceful sleep ambient track with soft pads.",
            "batch_id": "BATCH-TEST",
            "title": "Sleep Cloud",
            "genre": "sleep ambient",
        },
    )
    sidecar_job_id = create.json()["sidecar_job_id"]

    download_dir = tmp_path / "data" / "inbox" / "suno_downloads"
    download_dir.mkdir(parents=True, exist_ok=True)
    first = download_dir / "sleep-cloud-version-a.mp3"
    second = download_dir / "sleep-cloud-version-b.mp3"
    first.write_bytes(b"version A")
    second.write_bytes(b"version B")

    response = client.post(f"/suno/jobs/{sidecar_job_id}/download")

    assert response.status_code == 200
    data = response.json()
    assert data["state"] == "downloaded"
    assert data["version_a_path"].endswith("sleep-cloud-version-a.mp3")
    assert data["version_b_path"].endswith("sleep-cloud-version-b.mp3")


class FakeProvider:
    name = "fake_provider"

    def download(self, task_id, output_dir):
        source_a = output_dir / "fake-a.mp3"
        source_b = output_dir / "fake-b.mp3"
        source_a.parent.mkdir(parents=True, exist_ok=True)
        source_a.write_bytes(b"A")
        source_b.write_bytes(b"B")
        return [
            GeneratedTrack(
                provider="fake_provider",
                task_id=task_id,
                batch_id="BATCH-TEST",
                title="Version A",
                audio_path=source_a,
            ),
            GeneratedTrack(
                provider="fake_provider",
                task_id=task_id,
                batch_id="BATCH-TEST",
                title="Version B",
                audio_path=source_b,
            ),
        ]


def test_fetch_provider_downloads_attaches_a_and_b(tmp_path, monkeypatch):
    monkeypatch.setenv("DRAKONYA_ROOT", str(tmp_path))
    monkeypatch.setattr("app.tools.fetch_provider_downloads.get_music_provider", lambda: FakeProvider())

    job = create_generation_job(
        prompt="test prompt",
        batch_id="BATCH-TEST",
        title="Test Track",
        provider="fake_provider",
    )
    mark_job_submitted(job.job_id, provider_task_id="TASK-1", provider="fake_provider")

    attached = fetch_provider_downloads(job.job_id, output_dir="tmp/provider-output")

    assert attached == ["A", "B"]
    updated = load_job(job.job_id)
    assert updated.status == JOB_STATUS_DOWNLOADED
    assert updated.variants[0].audio_path
    assert updated.variants[1].audio_path
