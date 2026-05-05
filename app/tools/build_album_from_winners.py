from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path

from app.core.jobs import JOB_STATUS_SELECTED, GenerationJob, list_jobs
from app.core.paths import project_root
from app.tools.batch_status import find_batch
from app.tools.create_batch import safe_slug
from app.tools.create_cover_request import find_release


def _relative_to_root(path: Path) -> str:
    try:
        return str(path.relative_to(project_root()))
    except ValueError:
        return str(path)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _safe_track_filename(index: int, title: str, extension: str) -> str:
    slug = safe_slug(title)[:80] or f"track-{index:02d}"
    return f"{index:02d}-{slug}{extension.lower() or '.mp3'}"


def _winner_audio_for_job(job: GenerationJob) -> tuple[Path, str] | None:
    if job.status != JOB_STATUS_SELECTED or not job.winner_variant_id:
        return None

    for variant in job.variants:
        if variant.variant_id == job.winner_variant_id and variant.audio_path:
            source = Path(variant.audio_path)
            if source.exists() and source.is_file():
                return source, variant.variant_id

    return None


def _selected_jobs_for_batch(batch_id: str) -> list[GenerationJob]:
    jobs = [job for job in list_jobs() if job.batch_id == batch_id]
    selected = [job for job in jobs if _winner_audio_for_job(job)]
    selected.sort(key=lambda job: job.created_at)
    return selected


def build_album_from_winners(
    release: str,
    batch: str,
    *,
    limit: int | None = None,
    overwrite: bool = False,
) -> Path:
    release_dir = find_release(release)
    batch_dir = find_batch(batch)
    batch_id = batch_dir.name

    manifest_path = release_dir / "release_manifest.json"
    if not manifest_path.exists():
        raise SystemExit(f"Missing release manifest: {manifest_path}")

    audio_dir = release_dir / "audio"
    metadata_dir = release_dir / "metadata"
    distrokid_dir = release_dir / "distrokid"
    youtube_dir = release_dir / "youtube"
    logs_dir = release_dir / "logs"

    for folder in [audio_dir, metadata_dir, distrokid_dir, youtube_dir, logs_dir]:
        folder.mkdir(parents=True, exist_ok=True)

    selected_jobs = _selected_jobs_for_batch(batch_id)
    if limit is not None:
        selected_jobs = selected_jobs[:limit]

    if not selected_jobs:
        raise SystemExit(f"No selected winner jobs with audio found for batch: {batch_id}")

    manifest = _load_json(manifest_path)
    tracks: list[dict] = []

    for index, job in enumerate(selected_jobs, start=1):
        winner = _winner_audio_for_job(job)
        if winner is None:
            continue

        source, variant_id = winner
        title = job.title or f"Track {index:02d}"
        destination = audio_dir / _safe_track_filename(index, title, source.suffix)

        if destination.exists() and not overwrite:
            raise SystemExit(
                f"Destination exists: {destination}. Re-run with --overwrite to replace it."
            )

        shutil.copy2(source, destination)

        tracks.append(
            {
                "track_number": index,
                "title": title,
                "genre": job.genre or manifest.get("genre", ""),
                "job_id": job.job_id,
                "winner_variant_id": variant_id,
                "source_audio_path": _relative_to_root(source),
                "release_audio_path": _relative_to_root(destination),
            }
        )

    manifest["source_batch_id"] = batch_id
    manifest["source_batch_path"] = _relative_to_root(batch_dir)
    manifest["tracks"] = tracks
    manifest["track_count"] = len(tracks)
    manifest["status"] = "album_built"
    manifest["album_built_at"] = datetime.now().isoformat(timespec="seconds")
    manifest.setdefault("quality_gates", {})["audio_ready"] = bool(tracks)
    manifest.setdefault("quality_gates", {})["metadata_ready"] = bool(tracks)

    _write_json(manifest_path, manifest)

    tracklist_lines = [f"# Tracklist for {manifest.get('title', release_dir.name)}", ""]
    for track in tracks:
        tracklist_lines.append(f"{track['track_number']:02d}. {track['title']}")
    tracklist_lines.append("")
    (metadata_dir / "tracklist.md").write_text("\n".join(tracklist_lines), encoding="utf-8")

    credits_lines = [
        f"# Credits for {manifest.get('title', release_dir.name)}",
        "",
        f"Artist/Project: {manifest.get('artist', '')}",
        "",
        "## Production Notes",
        "",
        "AI-assisted music production workflow managed by Drakonya Nightmare Music Lab.",
        "Final operator review required before distribution.",
        "",
        "## Source Jobs",
        "",
    ]

    for track in tracks:
        credits_lines.append(
            f"- {track['track_number']:02d}. {track['title']} — {track['job_id']} winner {track['winner_variant_id']}"
        )

    credits_lines.append("")
    (metadata_dir / "credits.md").write_text("\n".join(credits_lines), encoding="utf-8")

    upload_sheet = distrokid_dir / "upload_sheet.md"
    existing_sheet = upload_sheet.read_text(encoding="utf-8") if upload_sheet.exists() else ""
    track_block = "\n".join([f"- {track['track_number']:02d}. {track['title']}" for track in tracks])

    upload_sheet.write_text(
        existing_sheet.rstrip()
        + "\n\n## Album Tracks\n\n"
        + track_block
        + "\n\nAudio files are staged in release/audio/.\n",
        encoding="utf-8",
    )

    youtube_package = youtube_dir / "youtube_package.md"
    existing_youtube = youtube_package.read_text(encoding="utf-8") if youtube_package.exists() else ""

    youtube_package.write_text(
        existing_youtube.rstrip()
        + "\n\n## Long Mix / Album Tracklist\n\n"
        + track_block
        + "\n",
        encoding="utf-8",
    )

    log_path = logs_dir / "album_build_log.json"
    _write_json(
        log_path,
        {
            "built_at": manifest["album_built_at"],
            "source_batch_id": batch_id,
            "release_id": manifest.get("release_id", release_dir.name),
            "track_count": len(tracks),
            "tracks": tracks,
        },
    )

    print(f"Built album package: {_relative_to_root(release_dir)}")
    print(f"Tracks copied: {len(tracks)}")
    return release_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a release album package from selected winner jobs.")
    parser.add_argument("release", help="Release id, folder name, or human title")
    parser.add_argument("--batch", required=True, help="Source batch id, folder name, or human title")
    parser.add_argument("--limit", type=int, default=None, help="Optional max number of winner tracks to copy")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing release audio files")
    args = parser.parse_args()

    build_album_from_winners(
        args.release,
        args.batch,
        limit=args.limit,
        overwrite=args.overwrite,
    )


if __name__ == "__main__":
    main()
