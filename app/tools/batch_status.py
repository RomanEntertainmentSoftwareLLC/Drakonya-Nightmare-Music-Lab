from __future__ import annotations

import argparse
from pathlib import Path

from app.core.paths import project_root
from app.tools.create_batch import safe_slug


CHECKS = [
    ("README", "README.md"),
    ("Suno prompts", "prompts/suno_prompts.md"),
    ("Jobs folder", "jobs"),
    ("Tracks folder", "tracks"),
    ("Winners folder", "winners"),
    ("Slop folder", "slop"),
    ("Covers folder", "covers"),
    ("Videos folder", "videos"),
    ("Release package folder", "release_package"),
]


def find_batch(batch_id: str) -> Path:
    batches_dir = project_root() / "data" / "batches"
    direct = batches_dir / batch_id

    if direct.exists():
        return direct

    normalized = safe_slug(batch_id)
    search_terms = [batch_id]
    if normalized and normalized != batch_id:
        search_terms.append(normalized)

    matches: list[Path] = []
    if batches_dir.exists():
        seen: set[Path] = set()
        for term in search_terms:
            for match in sorted(batches_dir.glob(f"*{term}*")):
                if match not in seen:
                    matches.append(match)
                    seen.add(match)
    if len(matches) == 1:
        return matches[0]

    if not matches:
        raise SystemExit(f"Batch not found: {batch_id}")

    raise SystemExit(
        "Multiple batches matched. Use the exact batch folder name:\n"
        + "\n".join(f"  {match.name}" for match in matches)
        + "\n\nExample:\n"
        + f"  python3 -m app.tools.jobs_status --batch \"{matches[-1].name}\""
    )


def has_audio_files(path: Path) -> bool:
    patterns = ["*.mp3", "*.wav", "*.m4a", "*.flac"]
    return any(file.exists() for pattern in patterns for file in path.glob(pattern))


def has_video_files(path: Path) -> bool:
    patterns = ["*.mp4", "*.mov", "*.webm", "*.mkv"]
    return any(file.exists() for pattern in patterns for file in path.glob(pattern))


def batch_status(batch_id: str) -> int:
    batch_dir = find_batch(batch_id)

    print(f"Batch: {batch_dir.name}")
    print(f"Path:  {batch_dir}")
    print("")

    failures = 0

    for label, relative in CHECKS:
        path = batch_dir / relative
        ok = path.exists()
        mark = "OK" if ok else "MISSING"
        print(f"{mark:8} {label}: {relative}")
        if not ok:
            failures += 1

    print("")

    tracks_ok = has_audio_files(batch_dir / "tracks")
    winners_ok = has_audio_files(batch_dir / "winners")
    videos_ok = has_video_files(batch_dir / "videos")
    release_files_ok = any((batch_dir / "release_package").glob("*")) if (batch_dir / "release_package").exists() else False

    extra_checks = [
        ("Audio in tracks/", tracks_ok),
        ("Approved audio in winners/", winners_ok),
        ("Video assets in videos/", videos_ok),
        ("Release package files", release_files_ok),
    ]

    for label, ok in extra_checks:
        mark = "OK" if ok else "TODO"
        print(f"{mark:8} {label}")
        if not ok:
            failures += 1

    print("")
    if failures:
        print(f"Status: NEEDS WORK ({failures} missing/TODO items)")
        return 1

    print("Status: READY")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Show Drakonya batch readiness status.")
    parser.add_argument("batch_id", help="Full or partial batch id/name")
    args = parser.parse_args()

    raise SystemExit(batch_status(args.batch_id))


if __name__ == "__main__":
    main()
