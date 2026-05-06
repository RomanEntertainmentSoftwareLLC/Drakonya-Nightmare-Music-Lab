from __future__ import annotations

import argparse
from collections import Counter

from app.core.jobs import (
    JOB_STATUS_CREATED,
    JOB_STATUS_DOWNLOADED,
    JOB_STATUS_GENERATED,
    JOB_STATUS_SELECTED,
    list_jobs,
)
from app.tools.batch_status import find_batch
from app.tools.cli_errors import fail


def _next_action_for_status(status: str, job_id: str) -> str:
    if status == JOB_STATUS_CREATED:
        return f"Submit job: python3 -m app.tools.drakonya generate-song ... or submit existing job {job_id}"
    if status == JOB_STATUS_GENERATED:
        return f"Download two Suno versions, then: python3 -m app.tools.drakonya watch-downloads {job_id}"
    if status == JOB_STATUS_DOWNLOADED:
        return f"Listen to A/B, then: python3 -m app.tools.drakonya select-winner {job_id} A"
    if status == JOB_STATUS_SELECTED:
        return f"Package release: python3 -m app.tools.drakonya package-song {job_id} --title TITLE --artist ARTIST"
    return "Review job state manually."


def pipeline_status(batch: str | None = None) -> int:
    batch_id = None
    if batch:
        batch_id = find_batch(batch).name

    jobs = list_jobs()
    if batch_id:
        jobs = [job for job in jobs if job.batch_id == batch_id]

    if not jobs:
        fail(
            "No jobs found.",
            hint="Create one with: python3 -m app.tools.drakonya generate-song \"your prompt\" --instrumental --private",
        )

    jobs.sort(key=lambda job: job.created_at)
    latest = jobs[-1]
    counts = Counter(job.status for job in jobs)

    print("")
    print("Drakonya Pipeline Status")
    print("========================")
    if batch_id:
        print(f"Batch: {batch_id}")
    print(f"Jobs:  {len(jobs)}")
    print("")

    for status, count in sorted(counts.items()):
        print(f"- {status}: {count}")

    print("")
    print("Latest Job")
    print("----------")
    print(f"Job:      {latest.job_id}")
    print(f"Title:    {latest.title or ''}")
    print(f"Genre:    {latest.genre or ''}")
    print(f"Status:   {latest.status}")
    print(f"Provider: {latest.provider}")
    print(f"Task:     {latest.provider_task_id or ''}")
    print(f"Winner:   {latest.winner_variant_id or '-'}")
    print("")

    print("Next Action")
    print("-----------")
    print(_next_action_for_status(latest.status, latest.job_id))
    print("")

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Show Drakonya pipeline status and next action.")
    parser.add_argument("--batch", default=None, help="Optional exact batch id/name")
    args = parser.parse_args()

    raise SystemExit(pipeline_status(args.batch))


if __name__ == "__main__":
    main()
