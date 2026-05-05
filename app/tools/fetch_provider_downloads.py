from __future__ import annotations

import argparse
import os
from pathlib import Path

from app.core.jobs import attach_variant_audio, load_job
from app.core.paths import project_root
from app.providers.factory import get_music_provider


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
    job = load_job(job_id)

    if not job.provider_task_id:
        raise SystemExit(f"Job has no provider_task_id yet: {job_id}")

    if provider_name:
        os.environ["SUNO_PROVIDER"] = provider_name
    elif job.provider:
        os.environ["SUNO_PROVIDER"] = job.provider

    if enable_private:
        os.environ["SUNO_PRIVATE_ENABLED"] = "true"

    provider = get_music_provider()
    target_dir = _resolve_output_dir(output_dir, job.batch_id, job.job_id)
    tracks = provider.download(job.provider_task_id, target_dir)

    if not tracks:
        print(f"No provider downloads found for job: {job_id}")
        return []

    attached: list[str] = []
    for variant_id, track in zip(VARIANT_ORDER, tracks[:2]):
        updated = attach_variant_audio(job.job_id, variant_id, Path(track.audio_path))
        attached.append(variant_id)
        print(f"Attached variant {variant_id}: {track.audio_path}")

    print(f"Job: {job_id}")
    print(f"Attached: {', '.join(attached)}")
    print(f"Status: {updated.status if attached else job.status}")
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
