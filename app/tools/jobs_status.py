from __future__ import annotations

import argparse
from collections import Counter

from app.core.jobs import list_jobs
from app.tools.batch_status import find_batch


def jobs_status(batch: str | None = None) -> int:
    batch_id = None
    if batch:
        batch_id = find_batch(batch).name

    jobs = list_jobs()
    if batch_id:
        jobs = [job for job in jobs if job.batch_id == batch_id]

    print(f"Jobs: {len(jobs)}")
    if batch_id:
        print(f"Batch: {batch_id}")
    print("")

    if not jobs:
        print("No jobs found.")
        return 1

    counts = Counter(job.status for job in jobs)
    for status, count in sorted(counts.items()):
        print(f"{status}: {count}")

    print("")
    for job in sorted(jobs, key=lambda item: item.created_at):
        winner = job.winner_variant_id or "-"
        title = job.title or job.job_id
        print(f"{job.job_id} | {job.status} | winner={winner} | {title}")

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Show generation job status.")
    parser.add_argument("--batch", default=None, help="Optional batch id, folder name, or human title")
    args = parser.parse_args()

    raise SystemExit(jobs_status(args.batch))


if __name__ == "__main__":
    main()
