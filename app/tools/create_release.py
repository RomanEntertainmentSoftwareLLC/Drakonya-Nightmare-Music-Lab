from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from app.core.paths import releases_dir
from app.tools.batch_status import find_batch
from app.tools.create_batch import safe_slug


def make_release_id(title: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"RELEASE-{stamp}-{safe_slug(title)}"


def _relative_to_root(path: Path) -> str:
    try:
        from app.core.paths import project_root

        return str(path.relative_to(project_root()))
    except ValueError:
        return str(path)


def create_release(
    title: str,
    artist: str,
    genre: str | None = None,
    source_batch: str | None = None,
    notes: str | None = None,
) -> Path:
    release_id = make_release_id(title)
    release_dir = releases_dir() / release_id

    folders = [
        release_dir,
        release_dir / "audio",
        release_dir / "cover_art",
        release_dir / "metadata",
        release_dir / "distrokid",
        release_dir / "youtube",
        release_dir / "logs",
    ]

    for folder in folders:
        folder.mkdir(parents=True, exist_ok=True)

    batch_dir: Path | None = find_batch(source_batch) if source_batch else None

    manifest = {
        "release_id": release_id,
        "title": title,
        "artist": artist,
        "genre": genre or "",
        "status": "draft",
        "source_batch_id": batch_dir.name if batch_dir else "",
        "source_batch_path": _relative_to_root(batch_dir) if batch_dir else "",
        "notes": notes or "",
        "publishing_cadence": {
            "target": "1-2 albums per week per account maximum",
            "account_scope": "primary account for now",
            "spam_policy": "paced legitimate releases only",
        },
        "quality_gates": {
            "audio_ready": False,
            "cover_ready": False,
            "metadata_ready": False,
            "distrokid_ready": False,
            "youtube_ready": False,
        },
        "tracks": [],
        "cover_art": {
            "approved_cover_path": "",
            "approved_logo_path": "",
            "logo_required": False,
            "logo_reuse_note": "Reuse approved artist/project logo when one exists.",
        },
        "folders": {
            "audio": "audio/",
            "cover_art": "cover_art/",
            "metadata": "metadata/",
            "distrokid": "distrokid/",
            "youtube": "youtube/",
            "logs": "logs/",
        },
    }

    (release_dir / "release_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )

    (release_dir / "README.md").write_text(
        "\n".join(
            [
                f"# {title}",
                "",
                f"Release ID: {release_id}",
                f"Artist/Project: {artist}",
                f"Genre/Lane: {genre or ''}",
                f"Source Batch: {batch_dir.name if batch_dir else ''}",
                "",
                "## Status",
                "",
                "Draft release package created.",
                "",
                "## Folder Map",
                "",
                "- audio/ — final album tracks",
                "- cover_art/ — approved cover and reusable logo assets",
                "- metadata/ — tracklist, credits, descriptions, keywords",
                "- distrokid/ — DistroKid upload sheet and checklist",
                "- youtube/ — YouTube title, description, tags, thumbnail notes",
                "- logs/ — upload and QA notes",
                "",
            ]
        ),
        encoding="utf-8",
    )

    (release_dir / "metadata" / "tracklist.md").write_text(
        f"# Tracklist for {title}\n\nAdd final approved tracks here.\n",
        encoding="utf-8",
    )

    (release_dir / "metadata" / "credits.md").write_text(
        f"# Credits for {title}\n\nArtist/Project: {artist}\n\nAdd production and tool notes here.\n",
        encoding="utf-8",
    )

    (release_dir / "distrokid" / "upload_sheet.md").write_text(
        "\n".join(
            [
                f"# DistroKid Upload Sheet — {title}",
                "",
                f"Artist/Project: {artist}",
                f"Album/Release Title: {title}",
                f"Genre/Lane: {genre or ''}",
                "Release Type: Album",
                "Status: draft",
                "",
                "## Required Before Upload",
                "",
                "- Final audio files in audio/",
                "- Approved cover art in cover_art/",
                "- Track titles and order in metadata/tracklist.md",
                "- Credits completed in metadata/credits.md",
                "- No copyrighted lyrics",
                "- No celebrity voice cloning",
                "- No misleading artist claims",
                "- No artificial streaming or fake engagement",
                "",
                "## Cadence Guardrail",
                "",
                "Target one to two albums per week per account maximum.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    (release_dir / "youtube" / "youtube_package.md").write_text(
        f"# YouTube Package — {title}\n\nTitle:\n\nDescription:\n\nTags:\n\nThumbnail notes:\n",
        encoding="utf-8",
    )

    return release_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a Drakonya album/release package.")
    parser.add_argument("title", help="Album/release title")
    parser.add_argument("--artist", required=True, help="Artist or project name")
    parser.add_argument("--genre", default=None, help="Genre or release lane")
    parser.add_argument("--batch", default=None, help="Optional source batch id/name")
    parser.add_argument("--notes", default=None, help="Optional release notes")
    args = parser.parse_args()

    release_dir = create_release(
        args.title,
        artist=args.artist,
        genre=args.genre,
        source_batch=args.batch,
        notes=args.notes,
    )
    print(f"Created release: {release_dir}")


if __name__ == "__main__":
    main()
