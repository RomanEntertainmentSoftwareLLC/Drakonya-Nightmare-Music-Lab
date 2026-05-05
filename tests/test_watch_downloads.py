from pathlib import Path

from app.core.jobs import create_generation_job
from app.tools.watch_downloads import count_audio_files


def test_count_audio_files(tmp_path):
    (tmp_path / "a.mp3").write_bytes(b"x")
    (tmp_path / "b.wav").write_bytes(b"x")
    (tmp_path / "c.txt").write_text("nope")

    assert count_audio_files(tmp_path) == 2
