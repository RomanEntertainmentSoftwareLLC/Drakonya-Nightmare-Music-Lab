from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from app.core.jobs import load_job, select_winner
from app.core.paths import project_root, slop_bin_dir
from app.tools.cli_errors import fail, reject_placeholder_job_id


def _relative_to_root(path: Path) -> str:
    try:
        return str(path.relative_to(project_root()))
    except ValueError:
        return str(path)


def select_job_winner(
    job_id: str,
    winner_variant: str,
    *,
    notes: str | None = None,
    copy_loser_to_slop: bool = True,
):
    reject_placeholder_job_id(job_id)

    winner_variant = winner_variant.upper().strip()
    if winner_variant not in {"A", "B"}:
        fail("Winner variant must be A or B.")

    try:
        job = load_job(job_id)
    except FileNotFoundError:
        fail(
            f"Job not found: {job_id}",
            hint="Run: python3 -m app.tools.jobs_status --batch EXACT_BATCH_ID",
        )

    variants = {variant.variant_id.upper(): variant for variant in job.variants}
    if winner_variant not in variants or not variants[winner_variant].audio_path:
        fail(f"Variant {winner_variant} has no attached audio.")

    loser_variant = "B" if winner_variant == "A" else "A"

    if copy_loser_to_slop and loser_variant in variants and variants[loser_variant].audio_path:
        loser_path = Path(variants[loser_variant].audio_path)
        if loser_path.exists():
            destination_dir = slop_bin_dir() / job.batch_id / job.job_id
            destination_dir.mkdir(parents=True, exist_ok=True)
            destination = destination_dir / loser_path.name
            shutil.copy2(loser_path, destination)
            print(f"Copied loser {loser_variant} to slop: {_relative_to_root(destination)}")

    updated = select_winner(job_id, winner_variant, notes=notes)

    print(f"Selected winner: {winner_variant}")
    print(f"Job: {updated.job_id}")
    print(f"Status: {updated.status}")
    return updated


def main() -> None:
    parser = argparse.ArgumentParser(description="Select A or B as the winning variant for a generation job.")
    parser.add_argument("job_id", help="Generation job id")
    parser.add_argument("winner_variant", help="A or B")
    parser.add_argument("--notes", default=None, help="Optional winner notes")
    parser.add_argument("--no-slop-copy", action="store_true", help="Do not copy loser audio to slop bin")
    args = parser.parse_args()

    select_job_winner(
        args.job_id,
        args.winner_variant,
        notes=args.notes,
        copy_loser_to_slop=not args.no_slop_copy,
    )


if __name__ == "__main__":
    main()
