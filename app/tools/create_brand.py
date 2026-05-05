from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from app.core.paths import brands_dir, project_root
from app.tools.create_batch import safe_slug


def _relative_to_root(path: Path) -> str:
    try:
        return str(path.relative_to(project_root()))
    except ValueError:
        return str(path)


def create_brand(
    name: str,
    lane: str | None = None,
    logo_type: str | None = None,
    notes: str | None = None,
) -> Path:
    brand_slug = safe_slug(name)
    brand_dir = brands_dir() / brand_slug

    folders = [
        brand_dir,
        brand_dir / "logo" / "concepts",
        brand_dir / "logo" / "approved",
        brand_dir / "logo" / "exports",
        brand_dir / "cover_overlays",
        brand_dir / "references",
    ]

    for folder in folders:
        folder.mkdir(parents=True, exist_ok=True)

    profile = {
        "brand_slug": brand_slug,
        "name": name,
        "lane": lane or "",
        "logo_type": logo_type or "",
        "status": "draft",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "notes": notes or "",
        "approved_logo_path": "",
        "approved_logo_variants": {
            "main": "",
            "dark_background": "",
            "light_background": "",
            "icon": "",
            "square_avatar": "",
        },
        "logo_policy": {
            "reuse_across_releases": True,
            "operator_approval_required": True,
            "regenerate_only_on_rebrand": True,
        },
        "folders": {
            "logo_concepts": "logo/concepts/",
            "logo_approved": "logo/approved/",
            "logo_exports": "logo/exports/",
            "cover_overlays": "cover_overlays/",
            "references": "references/",
        },
    }

    (brand_dir / "brand_profile.json").write_text(
        json.dumps(profile, indent=2) + "\n",
        encoding="utf-8",
    )

    (brand_dir / "style_guide.md").write_text(
        "\n".join(
            [
                f"# {name} Style Guide",
                "",
                f"Brand slug: {brand_slug}",
                f"Lane: {lane or ''}",
                f"Logo type: {logo_type or ''}",
                "",
                "## Identity Notes",
                "",
                notes or "Add brand identity notes here.",
                "",
                "## Reuse Rule",
                "",
                "Once an approved logo exists, reuse it across album covers, thumbnails, avatars, and release packages unless the operator requests a rebrand.",
                "",
                "## Cover Placement Notes",
                "",
                "Add notes for logo-on-cover placement here.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    (brand_dir / "logo_prompt.md").write_text(
        "\n".join(
            [
                f"# Logo Prompt — {name}",
                "",
                "Use this file for reusable logo concept prompts.",
                "",
                "## Main Prompt",
                "",
                f"Transparent-background logo for {name}, {logo_type or 'wordmark or emblem'}, {lane or 'selected brand lane'}, clean readable design, scalable, professional music brand identity, no copyrighted logos, no celebrity likenesses, no mockup background.",
                "",
                "## Needed Variants",
                "",
                "- main full-color logo",
                "- dark-background version",
                "- light-background version",
                "- simple icon/emblem",
                "- square avatar version",
                "",
                "## Approved Logo Path",
                "",
                "Add the final approved path to brand_profile.json after operator approval.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(f"Created brand: {_relative_to_root(brand_dir)}")
    return brand_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a reusable artist/project brand folder.")
    parser.add_argument("name", help="Artist, band, or project name")
    parser.add_argument("--lane", default=None, help="Genre/visual lane for this brand")
    parser.add_argument("--logo-type", default=None, help="Logo type, such as wordmark or emblem + wordmark")
    parser.add_argument("--notes", default=None, help="Brand identity notes")
    args = parser.parse_args()

    create_brand(
        args.name,
        lane=args.lane,
        logo_type=args.logo_type,
        notes=args.notes,
    )


if __name__ == "__main__":
    main()
