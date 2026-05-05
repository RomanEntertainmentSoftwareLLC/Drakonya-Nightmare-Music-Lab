import json

from app.core.jobs import attach_variant_audio, create_generation_job, select_winner
from app.tools.approve_cover import approve_cover
from app.tools.build_album_from_winners import build_album_from_winners
from app.tools.create_batch import create_batch
from app.tools.create_cover_request import create_cover_request
from app.tools.create_release import create_release
from app.tools.prepare_release_package import prepare_release_package


def test_prepare_release_package_marks_distrokid_and_youtube_ready(tmp_path, monkeypatch):
    monkeypatch.setenv("DRAKONYA_ROOT", str(tmp_path))

    batch_dir = create_batch("Prototype Music Batch 001", genre="coding focus")
    release_dir = create_release(
        "Prototype Album 001",
        artist="Drakonya Test Project",
        genre="coding focus",
        source_batch="Prototype Music Batch 001",
    )

    source_audio = tmp_path / "candidate_a.mp3"
    source_audio.write_bytes(b"fake audio")

    job = create_generation_job(
        prompt="coding focus rain synth track",
        batch_id=batch_dir.name,
        title="Code Rain Drive",
        genre="coding focus",
    )
    attach_variant_audio(job.job_id, "A", source_audio)
    select_winner(job.job_id, "A")

    build_album_from_winners("Prototype Album 001", batch="Prototype Music Batch 001")

    create_cover_request(
        "Prototype Album 001",
        concept="clean futuristic coding desk with soft neon and rain ambience",
        lane="coding focus",
        use_logo=False,
    )
    source_cover = tmp_path / "cover_candidate.jpg"
    source_cover.write_bytes(b"fake cover")
    approve_cover("Prototype Album 001", source_cover)

    prepare_release_package("Prototype Album 001", notes="ready for upload prep")

    manifest = json.loads((release_dir / "release_manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "packaged"
    assert manifest["quality_gates"]["audio_ready"] is True
    assert manifest["quality_gates"]["cover_ready"] is True
    assert manifest["quality_gates"]["metadata_ready"] is True
    assert manifest["quality_gates"]["distrokid_ready"] is True
    assert manifest["quality_gates"]["youtube_ready"] is True

    upload_sheet = (release_dir / "distrokid" / "upload_sheet.md").read_text(encoding="utf-8")
    assert "Package Status: READY" in upload_sheet
    assert "01. Code Rain Drive" in upload_sheet
    assert "Approved Cover:" in upload_sheet

    youtube_package = (release_dir / "youtube" / "youtube_package.md").read_text(encoding="utf-8")
    assert "Suggested Title: Prototype Album 001" in youtube_package
    assert "Tracklist:" in youtube_package

    log = json.loads((release_dir / "logs" / "package_prepare_log.json").read_text(encoding="utf-8"))
    assert log["package_ready"] is True
    assert log["track_count"] == 1


def test_prepare_release_package_stays_not_ready_without_cover(tmp_path, monkeypatch):
    monkeypatch.setenv("DRAKONYA_ROOT", str(tmp_path))

    release_dir = create_release("Draft Album", artist="Drakonya Test Project", genre="TBD")
    audio_dir = release_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    (audio_dir / "01-test.mp3").write_bytes(b"fake audio")

    manifest_path = release_dir / "release_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["tracks"] = [
        {
            "track_number": 1,
            "title": "Test Track",
            "genre": "TBD",
            "release_audio_path": "data/releases/example/audio/01-test.mp3",
        }
    ]
    manifest["quality_gates"]["audio_ready"] = True
    manifest["quality_gates"]["metadata_ready"] = True
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    prepare_release_package("Draft Album")

    updated = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert updated["status"] == "needs_package_work"
    assert updated["quality_gates"]["cover_ready"] is False
    assert updated["quality_gates"]["distrokid_ready"] is False
    assert updated["quality_gates"]["youtube_ready"] is False
