from __future__ import annotations

import argparse

from app.tools.fetch_provider_downloads import fetch_provider_downloads
from app.tools.generate_song import generate_song
from app.tools.jobs_status import jobs_status
from app.tools.package_song_release import package_song_release
from app.tools.select_job_winner import select_job_winner
from app.tools.watch_downloads import watch_downloads


def main() -> None:
    parser = argparse.ArgumentParser(description="Drakonya Nightmare Music Lab unified CLI.")
    sub = parser.add_subparsers(dest="command", required=True)

    generate = sub.add_parser("generate-song")
    generate.add_argument("prompt")
    generate.add_argument("--title", default=None)
    generate.add_argument("--genre", default="TBD")
    generate.add_argument("--batch", default=None)
    generate.add_argument("--provider", default="manual_suno")
    generate.add_argument("--instrumental", action="store_true")
    generate.add_argument("--private", action="store_true")

    status = sub.add_parser("jobs-status")
    status.add_argument("--batch", default=None)

    fetch = sub.add_parser("fetch-downloads")
    fetch.add_argument("job_id")
    fetch.add_argument("--provider", default=None)
    fetch.add_argument("--output-dir", default=None)
    fetch.add_argument("--enable-private", action="store_true")

    winner = sub.add_parser("select-winner")
    winner.add_argument("job_id")
    winner.add_argument("winner_variant")
    winner.add_argument("--notes", default=None)
    winner.add_argument("--no-slop-copy", action="store_true")

    
    watch = sub.add_parser("watch-downloads")
    watch.add_argument("job_id")
    watch.add_argument("--poll", type=float, default=2.0)
    watch.add_argument("--timeout", type=float, default=300.0)

    package = sub.add_parser("package-song")
    package.add_argument("job_id")
    package.add_argument("--title", required=True)
    package.add_argument("--artist", required=True)
    package.add_argument("--genre", default=None)
    package.add_argument("--cover-path", default=None)
    package.add_argument("--cover-concept", default=None)
    package.add_argument("--notes", default=None)

    args = parser.parse_args()

    if args.command == "generate-song":
        generate_song(
            args.prompt,
            title=args.title,
            genre=args.genre,
            batch=args.batch,
            provider=args.provider,
            instrumental=args.instrumental,
            private=args.private,
        )
    elif args.command == "jobs-status":
        raise SystemExit(jobs_status(args.batch))
    elif args.command == "fetch-downloads":
        fetch_provider_downloads(
            args.job_id,
            output_dir=args.output_dir,
            provider_name=args.provider,
            enable_private=args.enable_private,
        )
    elif args.command == "select-winner":
        select_job_winner(
            args.job_id,
            args.winner_variant,
            notes=args.notes,
            copy_loser_to_slop=not args.no_slop_copy,
        )

    elif args.command == "watch-downloads":
        watch_downloads(
            args.job_id,
            poll_seconds=args.poll,
            timeout_seconds=args.timeout,
        )

    elif args.command == "package-song":
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
