from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path

from app.core.paths import project_root
from app.tools.create_batch import safe_slug
from app.tools.create_cover_request import find_brand


ALLOWED_VARIANTS = {
    "main",
    "dark_background",
    "light_background",
    "icon",
    "square_avatar",
}


def _relative_to_root(path: Path) -> str:
    try:
        return str(path.relative_to(project_root()))
    except ValueError:
        return str(path)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def approve_logo(
    brand: str,
    source_path: str | Path,
    variant: str = "main",
    notes: str | None = None,
) -> Path:
    if variant not in ALLOWED_VARIANTS:
        allowed = ", ".join(sorted(ALLOWED_VARIANTS))
        raise SystemExit(f"Unsupported logo variant: {variant}. Allowed: {allowed}")

    brand_dir = find_brand(brand)
    source = Path(source_path).expanduser().resolve()

    if not source.exists() or not source.is_file():
        raise SystemExit(f"Logo source file not found: {source}")

    profile_path = brand_dir / "brand_profile.json"
    if not profile_path.exists():
        raise SystemExit(f"Missing brand profile: {profile_path}")

    approved_dir = brand_dir / "logo" / "approved"
    approved_dir.mkdir(parents=True, exist_ok=True)

    extension = source.suffix.lower() or ".png"
    destination_name = "logo_master" if variant == "main" else f"logo_{safe_slug(variant)}"
    destination = approved_dir / f"{destination_name}{extension}"

    if source.resolve() != destination.resolve():
        shutil.copy2(source, destination)

    profile = _load_json(profile_path)
    relative_destination = _relative_to_root(destination)

    profile["status"] = "logo_approved"
    profile["approved_logo_path"] = relative_destination
    profile.setdefault("approved_logo_variants", {})[variant] = relative_destination
    profile["logo_approved_at"] = datetime.now().isoformat(timespec="seconds")

    if notes:
        profile["approval_notes"] = notes

    _write_json(profile_path, profile)

    print(f"Approved logo: {relative_destination}")
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description="Approve and lock a reusable artist/project logo.")
    parser.add_argument("brand", help="Brand name or slug")
    parser.add_argument("source_path", help="Path to the selected logo file")
    parser.add_argument(
        "--variant",
        default="main",
        choices=sorted(ALLOWED_VARIANTS),
        help="Logo variant to approve",
    )
    parser.add_argument("--notes", default=None, help="Optional approval notes")
    args = parser.parse_args()

    approve_logo(
        args.brand,
        args.source_path,
        variant=args.variant,
        notes=args.notes,
    )


if __name__ == "__main__":
    main()
