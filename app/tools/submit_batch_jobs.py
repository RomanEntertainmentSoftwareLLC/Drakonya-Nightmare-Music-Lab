from __future__ import annotations

import argparse

from app.core.jobs import JOB_STATUS_CREATED, list_jobs
from app.tools.batch_status import find_batch
from app.tools.submit_job import submit_job


def submit_batch_jobs(
    batch: str,
    *,
    provider_name: str | None = None,
    limit: int | None = None,
    force: bool = False,
) -> list[str]:
    batch_dir = find_batch(batch)
    batch_id = batch_dir.name

    jobs = [job for job in list_jobs() if job.batch_id == batch_id]
    jobs.sort(key=lambda job: job.created_at)

    if not force:
        jobs = [job for job in jobs if job.status == JOB_STATUS_CREATED]

    if limit is not None:
        jobs = jobs[:limit]

    if not jobs:
        print(f"No jobs to submit for batch: {batch_id}")
        return []

    submitted: list[str] = []
    print(f"Submitting jobs for batch: {batch_id}")
    print(f"Count: {len(jobs)}")
    print("")

    for job in jobs:
        updated = submit_job(job.job_id, provider_name=provider_name, force=force)
        submitted.append(updated.job_id)
        print("")

    print(f"Submitted: {len(submitted)}")
    return submitted


def main() -> None:
    parser = argparse.ArgumentParser(description="Submit created generation jobs for a batch.")
    parser.add_argument("batch", help="Batch id, folder name, or human title")
    parser.add_argument("--provider", default=None, help="Provider override, such as manual_suno or suno_private")
    parser.add_argument("--limit", type=int, default=None, help="Optional max jobs to submit")
    parser.add_argument("--force", action="store_true", help="Resubmit jobs even if they are not in created status")
    args = parser.parse_args()

    submit_batch_jobs(
        args.batch,
        provider_name=args.provider,
        limit=args.limit,
        force=args.force,
    )


if __name__ == "__main__":
    main()
