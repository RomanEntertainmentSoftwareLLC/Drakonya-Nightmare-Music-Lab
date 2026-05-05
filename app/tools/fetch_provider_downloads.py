from __future__ import annotations

import argparse
import os
from pathlib import Path

from app.core.jobs import attach_variant_audio, load_job
from app.core.paths import project_root
from app.providers.factory import get_music_provider
from app.tools.cli_errors import fail, reject_placeholder_job_id


VARIANT_ORDER = ["A", "B"]


def _resolve_output_dir(output_dir: str | None, batch_id: str, job_id: str) -> Path:
    if output_dir:
        path = Path(output_dir).expanduser()
        if path.is_absolute():
            return path
        return project_root() / path
    return project_root() / "data" / "tracks" / batch_id / job_id / "provider_downloads"


def fetch_provider_downloads(
    job_id: str,
    *,
    output_dir: str | None = None,
    provider_name: str | None = None,
    enable_private: bool = False,
) -> list[str]:
    reject_placeholder_job_id(job_id)

    try:
        job = load_job(job_id)
    except FileNotFoundError:
        fail(
            f"Job not found: {job_id}",
            hint="Run: python3 -m app.tools.jobs_status --batch EXACT_BATCH_ID\nThen copy the real JOB-... id.",
        )

    if not job.provider_task_id:
        fail(f"Job has no provider_task_id yet: {job_id}")

    if provider_name:
        os.environ["SUNO_PROVIDER"] = provider_name
    elif job.provider:
        os.environ["SUNO_PROVIDER"] = job.provider

    if enable_private:
        os.environ["SUNO_PRIVATE_ENABLED"] = "true"

    provider = get_music_provider()
    target_dir = _resolve_output_dir(output_dir, job.batch_id, job.job_id)

    try:
        tracks = provider.download(job.provider_task_id, target_dir)
    except RuntimeError as exc:
        message = str(exc)

        if "waiting for 2" in message or "Found 0 audio file" in message:
            fail(
                "Suno downloads are not ready yet.",
                hint=(
                    "Place both downloaded Suno MP3s into:\n"
                    "data/inbox/suno_downloads/\n\n"
                    "Check with:\n"
                    "find data/inbox/suno_downloads -maxdepth 1 -type f | sort\n\n"
                    f"Then rerun:\npython3 -m app.tools.fetch_provider_downloads {job_id} --provider {job.provider} "
                    + ("--enable-private" if job.provider == "suno_private" else "")
                ),
            )

        if "Could not reach Suno sidecar" in message or "Connection refused" in message:
            fail(
                "Suno sidecar is not running.",
                hint="Start it in another terminal:\npython3 -m uvicorn sidecar.suno_sidecar:app --host 127.0.0.1 --port 8766",
            )

        raise

    if not tracks:
        print(f"No provider downloads found for job: {job_id}")
        return []

    attached: list[str] = []
    updated = job

    for variant_id, track in zip(VARIANT_ORDER, tracks[:2]):
        updated = attach_variant_audio(job.job_id, variant_id, Path(track.audio_path))
        attached.append(variant_id)
        print(f"Attached variant {variant_id}: {track.audio_path}")

    print(f"Job: {job_id}")
    print(f"Attached: {', '.join(attached)}")
    print(f"Status: {updated.status}")
    return attached


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch provider downloads and attach A/B audio to a job.")
    parser.add_argument("job_id", help="Generation job id")
    parser.add_argument("--output-dir", default=None, help="Optional provider/manual download folder")
    parser.add_argument("--provider", default=None, help="Provider override, such as manual_suno or suno_private")
    parser.add_argument(
        "--enable-private",
        action="store_true",
        help="Set SUNO_PRIVATE_ENABLED=true for this command",
    )
    args = parser.parse_args()

    fetch_provider_downloads(
        args.job_id,
        output_dir=args.output_dir,
        provider_name=args.provider,
        enable_private=args.enable_private,
    )


if __name__ == "__main__":
    main()
