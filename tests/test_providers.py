from pathlib import Path

from app.providers.base import GenerationRequest
from app.providers.factory import get_music_provider
from app.providers.manual import ManualSunoProvider
from app.providers.suno_private import SunoPrivateProvider


def test_default_provider_is_manual(monkeypatch):
    monkeypatch.delenv("SUNO_PROVIDER", raising=False)
    provider = get_music_provider()
    assert isinstance(provider, ManualSunoProvider)


def test_manual_provider_returns_queued_task():
    provider = ManualSunoProvider()
    task = provider.generate(
        GenerationRequest(
            prompt="test prompt",
            batch_id="BATCH-TEST",
            title="Test Track",
        )
    )

    assert task.provider == "manual_suno"
    assert task.state == "queued"
    assert task.batch_id == "BATCH-TEST"


def test_suno_private_blocks_when_disabled():
    provider = SunoPrivateProvider(enabled=False)

    try:
        provider.generate(GenerationRequest(prompt="x", batch_id="BATCH-TEST"))
    except RuntimeError as exc:
        assert "disabled" in str(exc).lower()
    else:
        raise AssertionError("Suno private provider should block when disabled")


def test_manual_download_imports_existing_audio(tmp_path: Path):
    audio = tmp_path / "fake_track.mp3"
    audio.write_bytes(b"not real audio, just a placeholder")

    provider = ManualSunoProvider()
    tracks = provider.download("manual-BATCH-TEST", tmp_path)

    assert len(tracks) == 1
    assert tracks[0].title == "fake_track"
    assert tracks[0].audio_path == audio


def test_suno_private_generate_uses_sidecar(monkeypatch):
    provider = SunoPrivateProvider(enabled=True, sidecar_url="http://sidecar-test")

    def fake_request_json(method, path, payload=None):
        assert method == "POST"
        assert path == "/suno/generate"
        assert payload["prompt"] == "melodic vampire dubstep"
        return {
            "sidecar_job_id": "SUNO-TEST",
            "batch_id": "BATCH-TEST",
            "title": "Blood Drop Test",
            "state": "created",
            "notes": "fake sidecar response",
        }

    monkeypatch.setattr(provider, "_request_json", fake_request_json)

    task = provider.generate(
        GenerationRequest(
            prompt="melodic vampire dubstep",
            batch_id="BATCH-TEST",
            title="Blood Drop Test",
        )
    )

    assert task.provider == "suno_private"
    assert task.task_id == "SUNO-TEST"
    assert task.state == "submitted"
    assert task.batch_id == "BATCH-TEST"


def test_suno_private_status_uses_sidecar(monkeypatch):
    provider = SunoPrivateProvider(enabled=True, sidecar_url="http://sidecar-test")

    def fake_request_json(method, path, payload=None):
        assert method == "GET"
        assert path == "/suno/jobs/SUNO-TEST"
        return {
            "sidecar_job_id": "SUNO-TEST",
            "batch_id": "BATCH-TEST",
            "title": "Blood Drop Test",
            "state": "running",
            "notes": "fake running job",
        }

    monkeypatch.setattr(provider, "_request_json", fake_request_json)

    task = provider.status("SUNO-TEST")

    assert task.provider == "suno_private"
    assert task.task_id == "SUNO-TEST"
    assert task.state == "running"
    assert task.batch_id == "BATCH-TEST"
