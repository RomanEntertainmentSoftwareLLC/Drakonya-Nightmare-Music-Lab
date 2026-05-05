import json

from app.tools.create_batch import create_batch
from app.tools.create_release import create_release


def test_create_release_creates_album_package(tmp_path, monkeypatch):
    monkeypatch.setenv("DRAKONYA_ROOT", str(tmp_path))

    release_dir = create_release(
        "Prototype Album 001",
        artist="Drakonya Test Project",
        genre="coding focus",
        notes="test release",
    )

    assert release_dir.exists()
    assert (release_dir / "release_manifest.json").exists()
    assert (release_dir / "README.md").exists()

    for folder in [
        "audio",
        "cover_art",
        "metadata",
        "distrokid",
        "youtube",
        "logs",
    ]:
        assert (release_dir / folder).exists()

    manifest = json.loads((release_dir / "release_manifest.json").read_text(encoding="utf-8"))
    assert manifest["title"] == "Prototype Album 001"
    assert manifest["artist"] == "Drakonya Test Project"
    assert manifest["genre"] == "coding focus"
    assert manifest["status"] == "draft"
    assert manifest["quality_gates"]["distrokid_ready"] is False
    assert "1-2 albums per week" in manifest["publishing_cadence"]["target"]


def test_create_release_can_link_source_batch(tmp_path, monkeypatch):
    monkeypatch.setenv("DRAKONYA_ROOT", str(tmp_path))

    batch_dir = create_batch("Prototype Music Batch 001", genre="TBD")
    release_dir = create_release(
        "Prototype Album 001",
        artist="Drakonya Test Project",
        source_batch="Prototype Music Batch 001",
    )

    manifest = json.loads((release_dir / "release_manifest.json").read_text(encoding="utf-8"))
    assert manifest["source_batch_id"] == batch_dir.name
    assert manifest["source_batch_path"].endswith(batch_dir.name)
