from __future__ import annotations

from pathlib import Path


PLACEHOLDER_JOB_IDS = {"JOB-ID", "JOB_ID", "<JOB-ID>", "<JOB_ID>", "job-id", "job_id"}


def fail(message: str, *, hint: str | None = None, code: int = 2) -> None:
    print("")
    print(f"ERROR: {message}")
    if hint:
        print("")
        print("Hint:")
        print(hint)
    print("")
    raise SystemExit(code)


def reject_placeholder_job_id(job_id: str) -> None:
    if job_id.strip() in PLACEHOLDER_JOB_IDS:
        fail(
            "JOB-ID is a placeholder, not a real job id.",
            hint="Run: python3 -m app.tools.jobs_status --batch EXACT_BATCH_ID\nThen copy the real JOB-... id.",
        )


def require_audio_downloads(download_dir: Path, minimum: int = 2) -> None:
    audio_exts = {".mp3", ".wav", ".m4a", ".flac", ".aac", ".ogg"}
    files = [
        path
        for path in download_dir.glob("*")
        if path.is_file() and path.suffix.lower() in audio_exts
    ]

    if len(files) < minimum:
        fail(
            f"Found {len(files)} audio file(s) in {download_dir}; need {minimum}.",
            hint=(
                "Download both Suno versions, then place them here:\n"
                f"{download_dir}\n\n"
                "Then rerun fetch_provider_downloads."
            ),
        )
