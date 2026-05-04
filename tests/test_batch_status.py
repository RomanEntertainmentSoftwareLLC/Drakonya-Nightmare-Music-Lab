from pathlib import Path

from app.tools.create_batch import create_batch
from app.tools.batch_status import find_batch, has_audio_files, has_video_files


def test_find_batch_by_partial_name(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("DRAKONYA_ROOT", str(tmp_path))

    batch_dir = create_batch("Night Drive Test", genre="synthwave")

    found = find_batch("night-drive-test")

    assert found == batch_dir


def test_media_file_detection(tmp_path: Path):
    audio_dir = tmp_path / "audio"
    video_dir = tmp_path / "video"
    audio_dir.mkdir()
    video_dir.mkdir()

    assert has_audio_files(audio_dir) is False
    assert has_video_files(video_dir) is False

    (audio_dir / "track.mp3").write_bytes(b"fake audio")
    (video_dir / "loop.mp4").write_bytes(b"fake video")

    assert has_audio_files(audio_dir) is True
    assert has_video_files(video_dir) is True
