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
