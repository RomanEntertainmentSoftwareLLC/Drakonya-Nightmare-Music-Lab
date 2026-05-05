from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from app.core.paths import project_root
from app.tools.create_cover_request import find_release


REQUIRED_GATES = [
    "audio_ready",
    "cover_ready",
    "metadata_ready",
]


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _relative_to_root(path: Path) -> str:
    try:
        return str(path.relative_to(project_root()))
    except ValueError:
        return str(path)


def _resolve_project_path(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return project_root() / path


def _audio_files(release_dir: Path) -> list[Path]:
    patterns = ["*.mp3", "*.wav", "*.m4a", "*.flac"]
    files: list[Path] = []
    for pattern in patterns:
        files.extend(sorted((release_dir / "audio").glob(pattern)))
    return files


def _manifest_tracks(manifest: dict, audio_files: list[Path]) -> list[dict]:
    tracks = list(manifest.get("tracks") or [])
    if tracks:
        return tracks

    fallback: list[dict] = []
    for index, audio in enumerate(audio_files, start=1):
        fallback.append(
            {
                "track_number": index,
                "title": audio.stem,
                "genre": manifest.get("genre", ""),
                "release_audio_path": _relative_to_root(audio),
            }
        )
    return fallback


def _cover_is_ready(manifest: dict) -> bool:
    cover_art = manifest.get("cover_art", {})
    approved = str(cover_art.get("approved_cover_path", ""))
    if not approved:
        return False
    return _resolve_project_path(approved).exists()


def _tracklist_block(tracks: list[dict]) -> str:
    lines: list[str] = []
    for index, track in enumerate(tracks, start=1):
        number = int(track.get("track_number") or index)
        title = str(track.get("title") or f"Track {number:02d}")
        lines.append(f"{number:02d}. {title}")
    return "\n".join(lines)


def _audio_paths_block(tracks: list[dict]) -> str:
    lines: list[str] = []
    for index, track in enumerate(tracks, start=1):
        number = int(track.get("track_number") or index)
        title = str(track.get("title") or f"Track {number:02d}")
        path = str(track.get("release_audio_path") or "")
        lines.append(f"- {number:02d}. {title} — {path}")
    return "\n".join(lines)


def prepare_release_package(release: str, *, notes: str | None = None) -> Path:
    release_dir = find_release(release)
    manifest_path = release_dir / "release_manifest.json"

    if not manifest_path.exists():
        raise SystemExit(f"Missing release manifest: {manifest_path}")

    manifest = _load_json(manifest_path)
    gates = manifest.setdefault("quality_gates", {})
    audio_files = _audio_files(release_dir)
    tracks = _manifest_tracks(manifest, audio_files)

    audio_ready = bool(audio_files) and bool(tracks)
    cover_ready = _cover_is_ready(manifest)
    metadata_ready = bool(tracks) and (release_dir / "metadata" / "tracklist.md").exists()

    gates["audio_ready"] = audio_ready
    gates["cover_ready"] = cover_ready
    gates["metadata_ready"] = metadata_ready

    package_ready = all(bool(gates.get(gate, False)) for gate in REQUIRED_GATES)
    gates["distrokid_ready"] = package_ready
    gates["youtube_ready"] = package_ready

    manifest["tracks"] = tracks
    manifest["track_count"] = len(tracks)
    manifest["status"] = "packaged" if package_ready else "needs_package_work"
    manifest["package_prepared_at"] = datetime.now(timezone.utc).isoformat()

    if notes:
        manifest["package_notes"] = notes

    cover_art = manifest.get("cover_art", {})
    approved_cover = str(cover_art.get("approved_cover_path", ""))
    approved_logo = str(cover_art.get("approved_logo_path", ""))
    title = str(manifest.get("title", release_dir.name))
    artist = str(manifest.get("artist", ""))
    genre = str(manifest.get("genre", ""))
    tracklist = _tracklist_block(tracks)
    audio_paths = _audio_paths_block(tracks)

    distrokid_dir = release_dir / "distrokid"
    youtube_dir = release_dir / "youtube"
    logs_dir = release_dir / "logs"
    for folder in [distrokid_dir, youtube_dir, logs_dir]:
        folder.mkdir(parents=True, exist_ok=True)

    (distrokid_dir / "upload_sheet.md").write_text(
        "\n".join(
            [
                f"# DistroKid Upload Sheet — {title}",
                "",
                f"Artist/Project: {artist}",
                f"Album/Release Title: {title}",
                f"Genre/Lane: {genre}",
                "Release Type: Album",
                f"Package Status: {'READY' if package_ready else 'NEEDS WORK'}",
                "",
                "## Tracklist",
                "",
                tracklist or "No tracks staged yet.",
                "",
                "## Audio Files",
                "",
                audio_paths or "No audio files staged yet.",
                "",
                "## Cover Art",
                "",
                f"Approved Cover: {approved_cover}",
                f"Approved Logo: {approved_logo}",
                "",
                "## Required Before Upload",
                "",
                f"- Audio ready: {bool(gates.get('audio_ready', False))}",
                f"- Cover ready: {bool(gates.get('cover_ready', False))}",
                f"- Metadata ready: {bool(gates.get('metadata_ready', False))}",
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

    (youtube_dir / "youtube_package.md").write_text(
        "\n".join(
            [
                f"# YouTube Package — {title}",
                "",
                f"Suggested Title: {title} — Full Album / Long Mix",
                "",
                "## Description Draft",
                "",
                f"{title} by {artist}.",
                "",
                f"Genre / lane: {genre}",
                "",
                "Tracklist:",
                tracklist or "No tracks staged yet.",
                "",
                "## Tags / Keywords",
                "",
                f"{genre}, ai music, instrumental music, full album, long mix",
                "",
                "## Thumbnail / Cover",
                "",
                f"Use approved cover: {approved_cover}",
                "",
                f"Package Status: {'READY' if package_ready else 'NEEDS WORK'}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    _write_json(
        logs_dir / "package_prepare_log.json",
        {
            "prepared_at": manifest["package_prepared_at"],
            "release_id": manifest.get("release_id", release_dir.name),
            "package_ready": package_ready,
            "gates": gates,
            "track_count": len(tracks),
            "approved_cover_path": approved_cover,
            "approved_logo_path": approved_logo,
        },
    )

    _write_json(manifest_path, manifest)

    print(f"Prepared release package: {_relative_to_root(release_dir)}")
    print(f"Package status: {'READY' if package_ready else 'NEEDS WORK'}")
    return release_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare DistroKid and YouTube release package files.")
    parser.add_argument("release", help="Release id, folder name, or human title")
    parser.add_argument("--notes", default=None, help="Optional package notes")
    args = parser.parse_args()

    prepare_release_package(args.release, notes=args.notes)


if __name__ == "__main__":
    main()
