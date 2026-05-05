from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path

from app.core.paths import project_root
from app.tools.create_cover_request import find_release


QA_FIELDS = [
    "square_format",
    "thumbnail_readable",
    "genre_fit",
    "no_copyrighted_logos",
    "no_celebrity_likeness",
    "safe_for_distribution",
]


def _relative_to_root(path: Path) -> str:
    try:
        return str(path.relative_to(project_root()))
    except ValueError:
        return str(path)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def approve_cover(
    release: str,
    source_path: str | Path,
    notes: str | None = None,
    mark_ready: bool = True,
) -> Path:
    release_dir = find_release(release)
    source = Path(source_path).expanduser().resolve()

    if not source.exists() or not source.is_file():
        raise SystemExit(f"Cover source file not found: {source}")

    manifest_path = release_dir / "release_manifest.json"
    cover_manifest_path = release_dir / "cover_art" / "cover_manifest.json"

    if not manifest_path.exists():
        raise SystemExit(f"Missing release manifest: {manifest_path}")

    if not cover_manifest_path.exists():
        raise SystemExit(
            "Missing cover manifest. Create a cover request before approving a cover."
        )

    approved_dir = release_dir / "cover_art" / "approved"
    approved_dir.mkdir(parents=True, exist_ok=True)

    extension = source.suffix.lower() or ".png"
    destination = approved_dir / f"cover_final{extension}"

    if source.resolve() != destination.resolve():
        shutil.copy2(source, destination)

    relative_destination = _relative_to_root(destination)

    cover_manifest = _load_json(cover_manifest_path)
    cover_manifest["status"] = "approved" if mark_ready else "selected"
    cover_manifest["approved_cover_path"] = relative_destination
    cover_manifest["approved_at"] = datetime.now().isoformat(timespec="seconds")

    if notes:
        cover_manifest["approval_notes"] = notes

    if mark_ready:
        qa = cover_manifest.setdefault("qa", {})
        for field in QA_FIELDS:
            qa[field] = True

    _write_json(cover_manifest_path, cover_manifest)

    release_manifest = _load_json(manifest_path)
    release_manifest.setdefault("quality_gates", {})["cover_ready"] = bool(mark_ready)
    release_manifest["cover_art"] = {
        **release_manifest.get("cover_art", {}),
        "status": "approved" if mark_ready else "selected",
        "approved_cover_path": relative_destination,
        "cover_manifest_path": _relative_to_root(cover_manifest_path),
        "approved_at": cover_manifest["approved_at"],
    }

    _write_json(manifest_path, release_manifest)

    print(f"Approved cover: {relative_destination}")
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description="Approve a selected cover for a release.")
    parser.add_argument("release", help="Release id, folder name, or human title")
    parser.add_argument("source_path", help="Path to selected cover image")
    parser.add_argument("--notes", default=None, help="Optional approval notes")
    parser.add_argument(
        "--no-mark-ready",
        action="store_true",
        help="Copy/select cover without flipping cover_ready to true",
    )
    args = parser.parse_args()

    approve_cover(
        args.release,
        args.source_path,
        notes=args.notes,
        mark_ready=not args.no_mark_ready,
    )


if __name__ == "__main__":
    main()
