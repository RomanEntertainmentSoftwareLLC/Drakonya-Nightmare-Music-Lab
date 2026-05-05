from __future__ import annotations

import argparse
import os
from pathlib import Path

from app.core.jobs import load_job
from app.tools.add_prompt import add_prompt
from app.tools.create_batch import create_batch, safe_slug
from app.tools.create_jobs_from_prompts import create_jobs_from_prompts
from app.tools.submit_job import submit_job


def _latest_prompt_file() -> Path | None:
    root = Path("state") / "suno_sidecar" / "prompts"
    if not root.exists():
        return None
    files = sorted(root.glob("*.txt"))
    return files[-1] if files else None


def generate_song(
    prompt: str,
    *,
    title: str | None = None,
    genre: str = "TBD",
    batch: str | None = None,
    provider: str = "manual_suno",
    instrumental: bool = False,
    private: bool = False,
) -> str:
    title = title or safe_slug(prompt)[:48].replace("-", " ").title() or "Untitled Track"

    print("[1] Creating/finding batch...")
    if batch:
        batch_name = batch
    else:
        batch_dir = create_batch(f"Single Song - {title}", genre=genre)
        batch_name = batch_dir.name
        print(f"    Created batch: {batch_name}")

    print("[2] Adding prompt...")
    add_prompt(
        batch_name,
        title=title,
        genre=genre,
        prompt=prompt,
        instrumental=instrumental,
    )

    print("[3] Creating generation job...")
    created = create_jobs_from_prompts(
        batch_name,
        provider="suno_private" if private else provider,
        allow_duplicates=False,
    )

    if not created:
        raise SystemExit("No new job created. This prompt may already exist in the batch.")

    job_id = created[-1]
    print(f"    Job: {job_id}")

    print("[4] Submitting job...")
    if private:
        os.environ["SUNO_PROVIDER"] = "suno_private"
        os.environ["SUNO_PRIVATE_ENABLED"] = "true"
        submit_job(job_id, provider_name="suno_private")
    else:
        submit_job(job_id, provider_name=provider)

    job = load_job(job_id)

    print("[5] Generated command summary...")
    print(f"    Batch: {job.batch_id}")
    print(f"    Job: {job.job_id}")
    print(f"    Status: {job.status}")
    print(f"    Provider: {job.provider}")
    print(f"    Provider task: {job.provider_task_id}")
    print(f"    Instrumental: {job.instrumental}")

    staged_prompt = _latest_prompt_file()
    if staged_prompt:
        print(f"    Staged prompt: {staged_prompt}")
        print("")
        print("Paste this into Suno if needed:")
        print(staged_prompt.read_text(encoding="utf-8").strip())

    print("")
    print("After Suno creates/downloads two versions into data/inbox/suno_downloads/, run:")
    print(
        f"python3 -m app.tools.fetch_provider_downloads {job_id} "
        f"--provider {job.provider} "
        + ("--enable-private" if job.provider == "suno_private" else "")
    )

    return job_id


def main() -> None:
    parser = argparse.ArgumentParser(description="Create, queue, and submit one song generation job.")
    parser.add_argument("prompt", help="Manual song generation prompt")
    parser.add_argument("--title", default=None, help="Optional track title")
    parser.add_argument("--genre", default="TBD", help="Genre/release lane")
    parser.add_argument("--batch", default=None, help="Optional existing batch id/name")
    parser.add_argument("--provider", default="manual_suno", help="Provider for non-private mode")
    parser.add_argument("--instrumental", action="store_true", help="Mark this as an instrumental Suno generation")
    parser.add_argument("--private", action="store_true", help="Submit to Suno private sidecar provider")
    args = parser.parse_args()

    generate_song(
        args.prompt,
        title=args.title,
        genre=args.genre,
        batch=args.batch,
        provider=args.provider,
        instrumental=args.instrumental,
        private=args.private,
    )


if __name__ == "__main__":
    main()
