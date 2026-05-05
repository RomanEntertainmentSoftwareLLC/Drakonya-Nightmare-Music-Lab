import json

from app.tools.approve_cover import approve_cover
from app.tools.approve_logo import approve_logo
from app.tools.create_brand import create_brand
from app.tools.create_cover_request import create_cover_request
from app.tools.create_release import create_release
from app.tools.release_status import release_status


def test_approve_logo_copies_file_and_updates_brand_profile(tmp_path, monkeypatch):
    monkeypatch.setenv("DRAKONYA_ROOT", str(tmp_path))

    create_brand("Neon Test Project", lane="synthwave", logo_type="wordmark")
    source_logo = tmp_path / "logo_candidate.png"
    source_logo.write_bytes(b"fake logo bytes")

    approved_logo = approve_logo("Neon Test Project", source_logo, notes="operator approved")

    assert approved_logo.exists()
    assert approved_logo.name == "logo_master.png"

    profile_path = tmp_path / "data" / "brands" / "neon-test-project" / "brand_profile.json"
    profile = json.loads(profile_path.read_text(encoding="utf-8"))

    assert profile["status"] == "logo_approved"
    assert profile["approved_logo_path"].endswith("logo_master.png")
    assert profile["approved_logo_variants"]["main"].endswith("logo_master.png")
    assert profile["approval_notes"] == "operator approved"


def test_approve_cover_copies_file_and_marks_release_cover_ready(tmp_path, monkeypatch):
    monkeypatch.setenv("DRAKONYA_ROOT", str(tmp_path))

    release_dir = create_release(
        "Prototype Album 001",
        artist="Drakonya Test Project",
        genre="coding focus",
    )
    create_cover_request(
        "Prototype Album 001",
        concept="clean futuristic coding desk with soft neon and rain ambience",
        lane="coding focus",
        use_logo=False,
    )

    source_cover = tmp_path / "cover_candidate.jpg"
    source_cover.write_bytes(b"fake cover bytes")

    approved_cover = approve_cover("Prototype Album 001", source_cover, notes="operator picked it")

    assert approved_cover.exists()
    assert approved_cover.name == "cover_final.jpg"

    cover_manifest = json.loads(
        (release_dir / "cover_art" / "cover_manifest.json").read_text(encoding="utf-8")
    )
    assert cover_manifest["status"] == "approved"
    assert cover_manifest["approved_cover_path"].endswith("cover_final.jpg")
    assert all(cover_manifest["qa"].values())

    release_manifest = json.loads((release_dir / "release_manifest.json").read_text(encoding="utf-8"))
    assert release_manifest["quality_gates"]["cover_ready"] is True
    assert release_manifest["cover_art"]["status"] == "approved"
    assert release_manifest["cover_art"]["approved_cover_path"].endswith("cover_final.jpg")


def test_release_status_returns_nonzero_until_all_gates_ready(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("DRAKONYA_ROOT", str(tmp_path))

    release_dir = create_release("Prototype Album 001", artist="Drakonya Test Project")

    assert release_status("Prototype Album 001") == 1
    output = capsys.readouterr().out
    assert "Status: NEEDS WORK" in output

    manifest_path = release_dir / "release_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for gate in manifest["quality_gates"]:
        manifest["quality_gates"][gate] = True
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    assert release_status("Prototype Album 001") == 0
    output = capsys.readouterr().out
    assert "Status: READY" in output
