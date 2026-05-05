from __future__ import annotations

import argparse
import os

from app.core.jobs import JOB_STATUS_CREATED, load_job, mark_job_submitted
from app.providers.base import GenerationRequest
from app.providers.factory import get_music_provider


def submit_job(job_id: str, *, provider_name: str | None = None, force: bool = False):
    job = load_job(job_id)

    if job.status != JOB_STATUS_CREATED and not force:
        raise SystemExit(
            f"Job is not in created status: {job.job_id} status={job.status}. "
            "Use --force to resubmit intentionally."
        )

    if provider_name:
        os.environ["SUNO_PROVIDER"] = provider_name

    provider = get_music_provider()
    task = provider.generate(
        GenerationRequest(
            prompt=job.prompt,
            batch_id=job.batch_id,
            title=job.title,
            genre=job.genre,
            instrumental=job.instrumental,
        )
    )

    updated = mark_job_submitted(
        job_id=job.job_id,
        provider_task_id=task.task_id,
        provider=task.provider,
        notes=task.message,
    )

    print(f"Submitted job: {updated.job_id}")
    print(f"Provider: {updated.provider}")
    print(f"Provider task: {updated.provider_task_id}")
    print(f"Status: {updated.status}")
    if updated.notes:
        print(f"Notes: {updated.notes}")

    return updated


def main() -> None:
    parser = argparse.ArgumentParser(description="Submit a generation job to the configured music provider.")
    parser.add_argument("job_id", help="Generation job id")
    parser.add_argument("--provider", default=None, help="Provider override, such as manual_suno or suno_private")
    parser.add_argument("--force", action="store_true", help="Resubmit even if the job is not in created status")
    args = parser.parse_args()

    submit_job(args.job_id, provider_name=args.provider, force=args.force)


if __name__ == "__main__":
    main()
