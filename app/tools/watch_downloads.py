from __future__ import annotations

import argparse
import time
from pathlib import Path

from app.core.jobs import load_job
from app.tools.cli_errors import fail, reject_placeholder_job_id
from app.tools.fetch_provider_downloads import fetch_provider_downloads


AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".flac", ".aac", ".ogg"}


def count_audio_files(path: Path) -> int:
    return len(
        [
            f
            for f in path.glob("*")
            if f.is_file() and f.suffix.lower() in AUDIO_EXTS
        ]
    )


def watch_downloads(
    job_id: str,
    *,
    poll_seconds: float = 2.0,
    timeout_seconds: float = 300.0,
):
    reject_placeholder_job_id(job_id)

    try:
        job = load_job(job_id)
    except FileNotFoundError:
        fail(
            f"Job not found: {job_id}",
            hint="Run jobs_status to find the correct JOB-...",
        )

    inbox = Path("data/inbox/suno_downloads")

    print("")
    print(f"Watching downloads for job: {job_id}")
    print(f"Inbox: {inbox}")
    print("Waiting for 2 audio files...")
    print("")

    start = time.time()

    while True:
        count = count_audio_files(inbox)

        elapsed = int(time.time() - start)
        print(f"[{elapsed:>3}s] Found {count}/2 files", end="\r")

        if count >= 2:
            print("")
            print("Detected 2 files. Attaching...")
            break

        if time.time() - start > timeout_seconds:
            fail(
                "Timed out waiting for downloads.",
                hint=f"Check folder: {inbox}",
            )

        time.sleep(poll_seconds)

    print("")
    fetch_provider_downloads(
        job_id,
        provider_name=job.provider,
        enable_private=(job.provider == "suno_private"),
    )

    print("")
    print("Done.")
