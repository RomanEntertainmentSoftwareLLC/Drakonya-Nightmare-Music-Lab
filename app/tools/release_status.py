from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.tools.create_cover_request import find_release


READY_GATES = [
    "audio_ready",
    "cover_ready",
    "metadata_ready",
    "distrokid_ready",
    "youtube_ready",
]


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _mark(value: bool) -> str:
    return "OK" if value else "TODO"


def release_status(release: str) -> int:
    release_dir = find_release(release)
    manifest_path = release_dir / "release_manifest.json"

    if not manifest_path.exists():
        raise SystemExit(f"Missing release manifest: {manifest_path}")

    manifest = _load_json(manifest_path)
    gates = manifest.get("quality_gates", {})
    cover_art = manifest.get("cover_art", {})

    print(f"Release: {manifest.get('title', release_dir.name)}")
    print(f"ID:      {manifest.get('release_id', release_dir.name)}")
    print(f"Artist:  {manifest.get('artist', '')}")
    print(f"Genre:   {manifest.get('genre', '')}")
    print(f"Path:    {release_dir}")
    print("")

    failures = 0
    for gate in READY_GATES:
        ok = bool(gates.get(gate, False))
        print(f"{_mark(ok):8} {gate}")
        if not ok:
            failures += 1

    print("")
    print(f"Cover status: {cover_art.get('status', 'not_requested')}")
    print(f"Approved cover: {cover_art.get('approved_cover_path', '')}")
    print(f"Approved logo:  {cover_art.get('approved_logo_path', '')}")
    print("")

    if failures:
        print(f"Status: NEEDS WORK ({failures} readiness gates open)")
        return 1

    print("Status: READY")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Show Drakonya release readiness status.")
    parser.add_argument("release", help="Release id, folder name, or human title")
    args = parser.parse_args()

    raise SystemExit(release_status(args.release))


if __name__ == "__main__":
    main()
