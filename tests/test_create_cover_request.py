import json

from app.tools.create_brand import create_brand
from app.tools.create_cover_request import create_cover_request
from app.tools.create_release import create_release


def test_create_cover_request_updates_release_manifest(tmp_path, monkeypatch):
    monkeypatch.setenv("DRAKONYA_ROOT", str(tmp_path))

    create_release(
        "Prototype Album 001",
        artist="Drakonya Test Project",
        genre="coding focus",
    )

    cover_manifest_path = create_cover_request(
        "Prototype Album 001",
        concept="clean futuristic coding desk with soft neon and rain ambience",
        lane="coding focus",
        use_logo=False,
    )

    assert cover_manifest_path.exists()

    cover_dir = cover_manifest_path.parent
    assert (cover_dir / "prompts" / "cover_prompt.md").exists()
    assert (cover_dir / "variants").exists()
    assert (cover_dir / "approved").exists()
    assert (cover_dir / "logo").exists()

    cover_manifest = json.loads(cover_manifest_path.read_text(encoding="utf-8"))
    assert cover_manifest["release_title"] == "Prototype Album 001"
    assert cover_manifest["lane"] == "coding focus"
    assert cover_manifest["provider"] == "manual_cover"
    assert cover_manifest["brand"]["use_logo"] is False

    release_manifest = json.loads(
        (cover_manifest_path.parents[1] / "release_manifest.json").read_text(encoding="utf-8")
    )
    assert release_manifest["quality_gates"]["cover_ready"] is False
    assert release_manifest["cover_art"]["status"] == "cover_requested"
    assert release_manifest["cover_art"]["cover_prompt_path"].endswith("cover_prompt.md")


def test_create_cover_request_can_link_brand_logo_policy(tmp_path, monkeypatch):
    monkeypatch.setenv("DRAKONYA_ROOT", str(tmp_path))

    brand_dir = create_brand(
        "Neon Test Project",
        lane="synthwave",
        logo_type="wordmark",
    )

    profile_path = brand_dir / "brand_profile.json"
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    profile["approved_logo_path"] = "data/brands/neon-test-project/logo/approved/logo_master.png"
    profile_path.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")

    create_release(
        "Neon Test Album",
        artist="Neon Test Project",
        genre="synthwave",
    )

    cover_manifest_path = create_cover_request(
        "Neon Test Album",
        concept="retro night drive with glowing horizon and clean premium composition",
        brand="Neon Test Project",
    )

    cover_manifest = json.loads(cover_manifest_path.read_text(encoding="utf-8"))
    assert cover_manifest["brand"]["brand_slug"] == "neon-test-project"
    assert cover_manifest["brand"]["use_logo"] is True
    assert cover_manifest["brand"]["approved_logo_path"].endswith("logo_master.png")

    release_manifest = json.loads(
        (cover_manifest_path.parents[1] / "release_manifest.json").read_text(encoding="utf-8")
    )
    assert release_manifest["cover_art"]["brand_slug"] == "neon-test-project"
    assert release_manifest["cover_art"]["logo_required"] is True
