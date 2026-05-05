from __future__ import annotations

import argparse
from pathlib import Path

from app.core.jobs import JOB_STATUS_SELECTED, load_job
from app.tools.approve_cover import approve_cover
from app.tools.build_album_from_winners import build_album_from_winners
from app.tools.cli_errors import fail, reject_placeholder_job_id
from app.tools.create_cover_request import create_cover_request
from app.tools.create_release import create_release
from app.tools.prepare_release_package import prepare_release_package
from app.tools.release_status import release_status


def package_song_release(
    job_id: str,
    *,
    title: str,
    artist: str,
    genre: str | None = None,
    cover_path: str | None = None,
    cover_concept: str | None = None,
    notes: str | None = None,
) -> Path:
    reject_placeholder_job_id(job_id)

    try:
        job = load_job(job_id)
    except FileNotFoundError:
        fail(
            f"Job not found: {job_id}",
            hint="Run: python3 -m app.tools.jobs_status --batch EXACT_BATCH_ID",
        )

    if job.status != JOB_STATUS_SELECTED or not job.winner_variant_id:
        fail(
            f"Job is not selected yet: {job.job_id} status={job.status}",
            hint=f"Select a winner first:\npython3 -m app.tools.select_job_winner {job.job_id} A",
        )

    release_dir = create_release(
        title,
        artist=artist,
        genre=genre or job.genre or "",
        source_batch=job.batch_id,
        notes=notes or f"Packaged from selected job {job.job_id}.",
    )

    build_album_from_winners(
        title,
        batch=job.batch_id,
        limit=1,
        overwrite=True,
    )

    if cover_concept or cover_path:
        create_cover_request(
            title,
            concept=cover_concept or f"Cover art for {title} by {artist}.",
            lane=genre or job.genre or "",
            use_logo=False,
        )

    if cover_path:
        approve_cover(
            title,
            cover_path,
            notes="Cover approved during song release packaging.",
        )
        prepare_release_package(title, notes="Prepared by package_song_release.")
    else:
        print("")
        print("Cover not approved yet.")
        print("To continue later:")
        print(
            f'python3 -m app.tools.create_cover_request "{title}" '
            f'--concept "YOUR COVER CONCEPT" --lane "{genre or job.genre or ""}" --no-use-logo'
        )
        print(f'python3 -m app.tools.approve_cover "{title}" PATH_TO_COVER')
        print(f'python3 -m app.tools.prepare_release_package "{title}"')

    print("")
    release_status(title)
    return release_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Package one selected song job into a release folder.")
    parser.add_argument("job_id", help="Selected generation job id")
    parser.add_argument("--title", required=True, help="Release title")
    parser.add_argument("--artist", required=True, help="Artist/project name")
    parser.add_argument("--genre", default=None, help="Release genre/lane")
    parser.add_argument("--cover-path", default=None, help="Optional approved cover image path")
    parser.add_argument("--cover-concept", default=None, help="Optional cover concept")
    parser.add_argument("--notes", default=None, help="Optional release notes")
    args = parser.parse_args()

    package_song_release(
        args.job_id,
        title=args.title,
        artist=args.artist,
        genre=args.genre,
        cover_path=args.cover_path,
        cover_concept=args.cover_concept,
        notes=args.notes,
    )


if __name__ == "__main__":
    main()
