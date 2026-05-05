import json

from app.core.jobs import attach_variant_audio, create_generation_job
from app.tools.create_batch import create_batch
from app.tools.package_song_release import package_song_release
from app.tools.select_job_winner import select_job_winner


def test_package_song_release_builds_release_from_selected_job(tmp_path, monkeypatch):
    monkeypatch.setenv("DRAKONYA_ROOT", str(tmp_path))

    batch_dir = create_batch("Package Test Batch", genre="dubstep")

    a = tmp_path / "a.mp3"
    b = tmp_path / "b.mp3"
    a.write_bytes(b"A")
    b.write_bytes(b"B")

    job = create_generation_job(
        prompt="brutal dubstep with a cyberpunk vibe",
        batch_id=batch_dir.name,
        title="Cyberbreaker",
        genre="dubstep",
    )
    attach_variant_audio(job.job_id, "A", a)
    attach_variant_audio(job.job_id, "B", b)
    select_job_winner(job.job_id, "A")

    release_dir = package_song_release(
        job.job_id,
        title="Cyberbreaker Prototype Single",
        artist="Drakonya Test Project",
        genre="dubstep",
    )

    assert release_dir.exists()
    assert (release_dir / "release_manifest.json").exists()

    manifest = json.loads((release_dir / "release_manifest.json").read_text(encoding="utf-8"))
    assert manifest["title"] == "Cyberbreaker Prototype Single"
    assert manifest["artist"] == "Drakonya Test Project"
    assert manifest["genre"] == "dubstep"
    assert manifest["quality_gates"]["audio_ready"] is True
    assert manifest["quality_gates"]["metadata_ready"] is True
    assert manifest["track_count"] == 1

    audio_files = list((release_dir / "audio").glob("*.mp3"))
    assert len(audio_files) == 1
    assert audio_files[0].read_bytes() == b"A"


def test_package_song_release_requires_selected_job(tmp_path, monkeypatch):
    monkeypatch.setenv("DRAKONYA_ROOT", str(tmp_path))

    batch_dir = create_batch("Package Test Batch", genre="TBD")
    job = create_generation_job(
        prompt="test prompt",
        batch_id=batch_dir.name,
        title="Unselected",
    )

    try:
        package_song_release(
            job.job_id,
            title="Bad Release",
            artist="Drakonya Test Project",
        )
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("Expected SystemExit")
