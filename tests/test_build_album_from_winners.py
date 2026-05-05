import json

from app.core.jobs import attach_variant_audio, create_generation_job, select_winner
from app.tools.build_album_from_winners import build_album_from_winners
from app.tools.create_batch import create_batch
from app.tools.create_release import create_release


def test_build_album_from_winners_copies_selected_tracks_and_updates_release(tmp_path, monkeypatch):
    monkeypatch.setenv("DRAKONYA_ROOT", str(tmp_path))

    batch_dir = create_batch("Prototype Music Batch 001", genre="coding focus")
    release_dir = create_release(
        "Prototype Album 001",
        artist="Drakonya Test Project",
        genre="coding focus",
        source_batch="Prototype Music Batch 001",
    )

    source_a = tmp_path / "candidate_a.mp3"
    source_b = tmp_path / "candidate_b.mp3"
    source_a.write_bytes(b"fake audio A")
    source_b.write_bytes(b"fake audio B")

    job = create_generation_job(
        prompt="coding focus rain synth track",
        batch_id=batch_dir.name,
        title="Code Rain Drive",
        genre="coding focus",
    )

    attach_variant_audio(job.job_id, "A", source_a)
    attach_variant_audio(job.job_id, "B", source_b)
    select_winner(job.job_id, "A", notes="best version")

    build_album_from_winners("Prototype Album 001", batch="Prototype Music Batch 001")

    audio_files = sorted((release_dir / "audio").glob("*.mp3"))
    assert len(audio_files) == 1
    assert audio_files[0].name == "01-code-rain-drive.mp3"
    assert audio_files[0].read_bytes() == b"fake audio A"

    manifest = json.loads((release_dir / "release_manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "album_built"
    assert manifest["track_count"] == 1
    assert manifest["quality_gates"]["audio_ready"] is True
    assert manifest["quality_gates"]["metadata_ready"] is True
    assert manifest["tracks"][0]["title"] == "Code Rain Drive"
    assert manifest["tracks"][0]["winner_variant_id"] == "A"

    tracklist = (release_dir / "metadata" / "tracklist.md").read_text(encoding="utf-8")
    assert "01. Code Rain Drive" in tracklist

    upload_sheet = (release_dir / "distrokid" / "upload_sheet.md").read_text(encoding="utf-8")
    assert "## Album Tracks" in upload_sheet
    assert "01. Code Rain Drive" in upload_sheet


def test_build_album_from_winners_errors_without_selected_tracks(tmp_path, monkeypatch):
    monkeypatch.setenv("DRAKONYA_ROOT", str(tmp_path))

    create_batch("Empty Batch", genre="TBD")
    create_release("Empty Album", artist="Drakonya Test Project", genre="TBD")

    try:
        build_album_from_winners("Empty Album", batch="Empty Batch")
    except SystemExit as exc:
        assert "No selected winner jobs" in str(exc)
    else:
        raise AssertionError("Expected SystemExit")
