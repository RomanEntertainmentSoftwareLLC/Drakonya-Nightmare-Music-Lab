from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from app.core.paths import brands_dir, project_root, releases_dir
from app.tools.create_batch import safe_slug


def _relative_to_root(path: Path) -> str:
    try:
        return str(path.relative_to(project_root()))
    except ValueError:
        return str(path)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def find_release(release_id_or_title: str) -> Path:
    root = releases_dir()
    direct = root / release_id_or_title
    if direct.exists():
        return direct

    normalized = safe_slug(release_id_or_title)
    matches: list[Path] = []

    if root.exists():
        for candidate in sorted(path for path in root.iterdir() if path.is_dir()):
            candidate_slug_match = normalized and normalized in candidate.name
            manifest_path = candidate / "release_manifest.json"
            title_slug_match = False

            if manifest_path.exists():
                try:
                    manifest = _load_json(manifest_path)
                    title_slug_match = normalized == safe_slug(str(manifest.get("title", "")))
                except json.JSONDecodeError:
                    title_slug_match = False

            if candidate_slug_match or title_slug_match:
                matches.append(candidate)

    if len(matches) == 1:
        return matches[0]

    if not matches:
        raise SystemExit(f"Release not found: {release_id_or_title}")

    raise SystemExit(
        "Multiple releases matched:\n" + "\n".join(str(match) for match in matches)
    )


def find_brand(brand_name_or_slug: str) -> Path:
    root = brands_dir()
    direct = root / brand_name_or_slug
    if direct.exists():
        return direct

    normalized = safe_slug(brand_name_or_slug)
    direct_slug = root / normalized
    if direct_slug.exists():
        return direct_slug

    matches: list[Path] = []

    if root.exists():
        for candidate in sorted(path for path in root.iterdir() if path.is_dir()):
            if normalized and normalized in candidate.name:
                matches.append(candidate)
                continue

            profile_path = candidate / "brand_profile.json"
            if profile_path.exists():
                try:
                    profile = _load_json(profile_path)
                    if normalized == safe_slug(str(profile.get("name", ""))):
                        matches.append(candidate)
                except json.JSONDecodeError:
                    pass

    if len(matches) == 1:
        return matches[0]

    if not matches:
        raise SystemExit(f"Brand not found: {brand_name_or_slug}")

    raise SystemExit(
        "Multiple brands matched:\n" + "\n".join(str(match) for match in matches)
    )


def _cover_prompt_text(
    *,
    title: str,
    artist: str,
    lane: str,
    concept: str,
    use_logo: bool,
    approved_logo_path: str,
) -> str:
    logo_line = "No approved logo selected. Create cover art without inventing a fake logo."

    if use_logo and approved_logo_path:
        logo_line = f"Use the approved reusable artist/project logo from: {approved_logo_path}"
    elif use_logo:
        logo_line = "Logo requested, but no approved logo path exists yet. Leave logo placement space and do not invent a fake logo."

    return "\n".join(
        [
            f"# Cover Prompt — {title}",
            "",
            f"Artist/Project: {artist}",
            f"Release Lane: {lane}",
            "",
            "## Concept",
            "",
            concept,
            "",
            "## Logo Rule",
            "",
            logo_line,
            "",
            "## Prompt",
            "",
            f"Square album cover for {title} by {artist}. Visual concept: {concept}. Release lane: {lane}. Professional streaming-platform album artwork, strong focal point, genre-appropriate colors and mood, polished composition, readable at thumbnail size, no copyrighted logos, no copyrighted characters, no celebrity likenesses, no fake artist impersonation, no text unless explicitly requested.",
            "",
            "## Negative / Avoid",
            "",
            "Avoid unreadable fake text, copyrighted logos, real celebrity likenesses, distorted faces or hands, blurry details, QR codes, URLs, platform logos, explicit pricing, and forced gothic/horror imagery unless the selected lane calls for it.",
            "",
        ]
    )


def create_cover_request(
    release: str,
    concept: str,
    lane: str | None = None,
    brand: str | None = None,
    use_logo: bool = True,
    notes: str | None = None,
) -> Path:
    release_dir = find_release(release)
    manifest_path = release_dir / "release_manifest.json"

    if not manifest_path.exists():
        raise SystemExit(f"Missing release manifest: {manifest_path}")

    manifest = _load_json(manifest_path)
    release_title = str(manifest.get("title", release_dir.name))
    artist = str(manifest.get("artist", ""))
    selected_lane = lane or str(manifest.get("genre", "")) or "operator-selected lane"

    brand_slug = ""
    brand_path = ""
    approved_logo_path = ""

    if brand:
        brand_dir = find_brand(brand)
        brand_path = _relative_to_root(brand_dir)
        brand_profile_path = brand_dir / "brand_profile.json"

        if brand_profile_path.exists():
            brand_profile = _load_json(brand_profile_path)
            brand_slug = str(brand_profile.get("brand_slug", brand_dir.name))
            approved_logo_path = str(brand_profile.get("approved_logo_path", ""))
        else:
            brand_slug = brand_dir.name

    cover_dir = release_dir / "cover_art"
    prompts_dir = cover_dir / "prompts"
    variants_dir = cover_dir / "variants"
    approved_dir = cover_dir / "approved"
    logo_dir = cover_dir / "logo"

    for folder in [cover_dir, prompts_dir, variants_dir, approved_dir, logo_dir]:
        folder.mkdir(parents=True, exist_ok=True)

    request_id = f"COVER-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    prompt_path = prompts_dir / "cover_prompt.md"
    cover_manifest_path = cover_dir / "cover_manifest.json"

    prompt_path.write_text(
        _cover_prompt_text(
            title=release_title,
            artist=artist,
            lane=selected_lane,
            concept=concept,
            use_logo=use_logo,
            approved_logo_path=approved_logo_path,
        ),
        encoding="utf-8",
    )

    cover_manifest = {
        "cover_request_id": request_id,
        "release_id": manifest.get("release_id", release_dir.name),
        "release_title": release_title,
        "artist": artist,
        "lane": selected_lane,
        "concept": concept,
        "status": "draft",
        "provider": "manual_cover",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "notes": notes or "",
        "brand": {
            "brand_slug": brand_slug,
            "brand_path": brand_path,
            "use_logo": use_logo,
            "approved_logo_path": approved_logo_path,
            "logo_reuse_rule": "Reuse approved logo when it exists; do not invent a new logo per album.",
        },
        "paths": {
            "prompt": _relative_to_root(prompt_path),
            "variants_dir": _relative_to_root(variants_dir),
            "approved_dir": _relative_to_root(approved_dir),
            "logo_dir": _relative_to_root(logo_dir),
        },
        "variants": [],
        "approved_cover_path": "",
        "qa": {
            "square_format": False,
            "thumbnail_readable": False,
            "genre_fit": False,
            "no_copyrighted_logos": False,
            "no_celebrity_likeness": False,
            "safe_for_distribution": False,
        },
    }

    _write_json(cover_manifest_path, cover_manifest)

    manifest.setdefault("quality_gates", {})["cover_ready"] = False
    manifest["cover_art"] = {
        **manifest.get("cover_art", {}),
        "status": "cover_requested",
        "cover_manifest_path": _relative_to_root(cover_manifest_path),
        "cover_prompt_path": _relative_to_root(prompt_path),
        "approved_cover_path": manifest.get("cover_art", {}).get("approved_cover_path", ""),
        "brand_slug": brand_slug,
        "brand_path": brand_path,
        "approved_logo_path": approved_logo_path,
        "logo_required": bool(use_logo and brand),
        "logo_reuse_note": "Reuse approved artist/project logo when one exists.",
    }

    _write_json(manifest_path, manifest)

    print(f"Created cover request: {_relative_to_root(cover_manifest_path)}")
    return cover_manifest_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a cover-art request for a release package.")
    parser.add_argument("release", help="Release id, folder name, or human title")
    parser.add_argument("--concept", required=True, help="Cover concept or visual brief")
    parser.add_argument("--lane", default=None, help="Optional visual/release lane override")
    parser.add_argument("--brand", default=None, help="Optional reusable artist/project brand")
    parser.add_argument("--use-logo", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--notes", default=None, help="Optional cover notes")
    args = parser.parse_args()

    create_cover_request(
        release=args.release,
        concept=args.concept,
        lane=args.lane,
        brand=args.brand,
        use_logo=args.use_logo,
        notes=args.notes,
    )


if __name__ == "__main__":
    main()
