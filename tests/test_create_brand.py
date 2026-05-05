import json

from app.tools.create_brand import create_brand


def test_create_brand_creates_reusable_logo_structure(tmp_path, monkeypatch):
    monkeypatch.setenv("DRAKONYA_ROOT", str(tmp_path))

    brand_dir = create_brand(
        "Neon Test Project",
        lane="synthwave",
        logo_type="wordmark",
        notes="test brand",
    )

    assert brand_dir.exists()
    assert brand_dir.name == "neon-test-project"
    assert (brand_dir / "brand_profile.json").exists()
    assert (brand_dir / "style_guide.md").exists()
    assert (brand_dir / "logo_prompt.md").exists()

    for folder in [
        "logo/concepts",
        "logo/approved",
        "logo/exports",
        "cover_overlays",
        "references",
    ]:
        assert (brand_dir / folder).exists()

    profile = json.loads((brand_dir / "brand_profile.json").read_text(encoding="utf-8"))
    assert profile["name"] == "Neon Test Project"
    assert profile["lane"] == "synthwave"
    assert profile["logo_type"] == "wordmark"
    assert profile["approved_logo_path"] == ""
    assert profile["logo_policy"]["reuse_across_releases"] is True
    assert profile["logo_policy"]["operator_approval_required"] is True
    assert profile["logo_policy"]["regenerate_only_on_rebrand"] is True
