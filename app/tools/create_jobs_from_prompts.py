from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.core.jobs import create_generation_job, list_jobs
from app.core.paths import project_root
from app.tools.batch_status import find_batch
from app.tools.create_batch import safe_slug


PROMPT_RELATIVE_PATH = Path("prompts") / "suno_prompts.md"


def _relative_to_root(path: Path) -> str:
    try:
        return str(path.relative_to(project_root()))
    except ValueError:
        return str(path)


def _parse_prompt_entry(title: str, body_lines: list[str]) -> dict | None:
    genre = ""
    prompt_lines: list[str] = []
    instrumental = False
    in_prompt = False

    for raw_line in body_lines:
        line = raw_line.rstrip()
        stripped = line.strip()

        if stripped.lower().startswith("genre:") and not in_prompt:
            genre = stripped.split(":", 1)[1].strip()
            continue

        if stripped.lower().startswith("instrumental:") and not in_prompt:
            value = stripped.split(":", 1)[1].strip().lower()
            instrumental = value in {"1", "true", "yes", "on"}
            continue

        if stripped.lower() == "prompt:" and not in_prompt:
            in_prompt = True
            continue

        if in_prompt:
            prompt_lines.append(line)

    prompt = "\n".join(prompt_lines).strip()

    if not title.strip() or not prompt:
        return None

    return {
        "title": title.strip(),
        "genre": genre,
        "instrumental": instrumental,
        "prompt": prompt,
    }


def parse_prompt_pack(prompt_file: Path) -> list[dict]:
    if not prompt_file.exists():
        raise SystemExit(f"Prompt pack not found: {prompt_file}")

    entries: list[dict] = []
    current_title: str | None = None
    current_body: list[str] = []

    for raw_line in prompt_file.read_text(encoding="utf-8").splitlines():
        if raw_line.startswith("## "):
            if current_title is not None:
                parsed = _parse_prompt_entry(current_title, current_body)
                if parsed:
                    entries.append(parsed)

            current_title = raw_line[3:].strip()
            current_body = []
        else:
            if current_title is not None:
                current_body.append(raw_line)

    if current_title is not None:
        parsed = _parse_prompt_entry(current_title, current_body)
        if parsed:
            entries.append(parsed)

    return entries


def _existing_job_keys(batch_id: str) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for job in list_jobs():
        if job.batch_id == batch_id:
            keys.add((safe_slug(job.title or ""), safe_slug(job.prompt or "")))
    return keys


def create_jobs_from_prompts(
    batch: str,
    *,
    provider: str = "manual_suno",
    allow_duplicates: bool = False,
) -> list[str]:
    batch_dir = find_batch(batch)
    prompt_file = batch_dir / PROMPT_RELATIVE_PATH
    prompts = parse_prompt_pack(prompt_file)

    if not prompts:
        raise SystemExit(f"No usable prompt entries found in: {prompt_file}")

    batch_id = batch_dir.name
    existing_keys = _existing_job_keys(batch_id)
    created_job_ids: list[str] = []
    skipped: list[str] = []

    for entry in prompts:
        key = (safe_slug(entry["title"]), safe_slug(entry["prompt"]))
        if key in existing_keys and not allow_duplicates:
            skipped.append(entry["title"])
            continue

        job = create_generation_job(
            prompt=entry["prompt"],
            batch_id=batch_id,
            title=entry["title"],
            genre=entry["genre"],
            provider=provider,
            instrumental=bool(entry.get("instrumental", False)),
        )
        created_job_ids.append(job.job_id)
        existing_keys.add(key)

    index_path = batch_dir / "jobs" / "generation_jobs.json"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_data = {
        "batch_id": batch_id,
        "prompt_file": _relative_to_root(prompt_file),
        "provider": provider,
        "created_job_ids": created_job_ids,
        "skipped_titles": skipped,
        "total_prompt_entries": len(prompts),
    }
    index_path.write_text(json.dumps(index_data, indent=2) + "\n", encoding="utf-8")

    print(f"Batch: {batch_id}")
    print(f"Prompt entries: {len(prompts)}")
    print(f"Created jobs: {len(created_job_ids)}")
    print(f"Skipped duplicates: {len(skipped)}")
    print(f"Index: {_relative_to_root(index_path)}")

    for job_id in created_job_ids:
        print(f"JOB {job_id}")

    return created_job_ids


def main() -> None:
    parser = argparse.ArgumentParser(description="Create generation jobs from a batch Suno prompt pack.")
    parser.add_argument("batch", help="Batch id, folder name, or human title")
    parser.add_argument("--provider", default="manual_suno", help="Provider name to stamp on created jobs")
    parser.add_argument("--allow-duplicates", action="store_true", help="Create jobs even if matching batch/title/prompt jobs already exist")
    args = parser.parse_args()

    create_jobs_from_prompts(
        args.batch,
        provider=args.provider,
        allow_duplicates=args.allow_duplicates,
    )


if __name__ == "__main__":
    main()
