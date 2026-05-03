from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.core.paths import project_root


JOB_STATUS_CREATED = "created"
JOB_STATUS_GENERATED = "generated"
JOB_STATUS_DOWNLOADED = "downloaded"
JOB_STATUS_SELECTED = "selected"
JOB_STATUS_FAILED = "failed"


@dataclass
class TrackVariant:
    variant_id: str
    status: str = "pending"
    audio_path: str | None = None
    title: str | None = None
    score: float | None = None
    notes: str | None = None


@dataclass
class GenerationJob:
    job_id: str
    batch_id: str
    prompt: str
    title: str | None = None
    genre: str | None = None
    status: str = JOB_STATUS_CREATED
    provider: str = "manual_suno"
    provider_task_id: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    variants: list[TrackVariant] = field(default_factory=list)
    winner_variant_id: str | None = None
    notes: str | None = None


def jobs_dir() -> Path:
    path = project_root() / "data" / "jobs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def job_path(job_id: str) -> Path:
    return jobs_dir() / f"{job_id}.json"


def new_job_id() -> str:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"JOB-{stamp}-{uuid4().hex[:8]}"


def save_job(job: GenerationJob) -> GenerationJob:
    job.updated_at = datetime.now(timezone.utc).isoformat()
    job_path(job.job_id).write_text(json.dumps(asdict(job), indent=2), encoding="utf-8")
    return job


def load_job(job_id: str) -> GenerationJob:
    path = job_path(job_id)
    if not path.exists():
        raise FileNotFoundError(f"Job not found: {job_id}")

    data = json.loads(path.read_text(encoding="utf-8"))
    variants = [TrackVariant(**item) for item in data.pop("variants", [])]
    return GenerationJob(**data, variants=variants)


def list_jobs() -> list[GenerationJob]:
    jobs: list[GenerationJob] = []
    for path in sorted(jobs_dir().glob("*.json"), reverse=True):
        data = json.loads(path.read_text(encoding="utf-8"))
        variants = [TrackVariant(**item) for item in data.pop("variants", [])]
        jobs.append(GenerationJob(**data, variants=variants))
    return jobs


def create_generation_job(
    *,
    prompt: str,
    batch_id: str,
    title: str | None = None,
    genre: str | None = None,
    provider: str = "manual_suno",
) -> GenerationJob:
    job = GenerationJob(
        job_id=new_job_id(),
        batch_id=batch_id,
        prompt=prompt,
        title=title,
        genre=genre,
        provider=provider,
        variants=[
            TrackVariant(variant_id="A"),
            TrackVariant(variant_id="B"),
        ],
    )
    return save_job(job)


def job_track_dir(job: GenerationJob) -> Path:
    path = project_root() / "data" / "tracks" / job.batch_id / job.job_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def attach_variant_audio(job_id: str, variant_id: str, source_audio: Path) -> GenerationJob:
    job = load_job(job_id)
    output_dir = job_track_dir(job)

    if variant_id not in {"A", "B"}:
        raise ValueError("variant_id must be A or B")

    if not source_audio.exists():
        raise FileNotFoundError(str(source_audio))

    dest = output_dir / f"{job.job_id}_{variant_id}{source_audio.suffix.lower()}"
    shutil.copy2(source_audio, dest)

    found = False
    for variant in job.variants:
        if variant.variant_id == variant_id:
            variant.status = "downloaded"
            variant.audio_path = str(dest)
            variant.title = f"{job.title or job.job_id} version {variant_id}"
            found = True

    if not found:
        job.variants.append(
            TrackVariant(
                variant_id=variant_id,
                status="downloaded",
                audio_path=str(dest),
                title=f"{job.title or job.job_id} version {variant_id}",
            )
        )

    if all(v.status == "downloaded" for v in job.variants):
        job.status = JOB_STATUS_DOWNLOADED

    return save_job(job)


def select_winner(job_id: str, winner_variant_id: str, notes: str | None = None) -> GenerationJob:
    job = load_job(job_id)

    if winner_variant_id not in {"A", "B"}:
        raise ValueError("winner_variant_id must be A or B")

    loser_ids = {"A", "B"} - {winner_variant_id}
    slop_dir = project_root() / "data" / "slop_bin" / job.batch_id / job.job_id
    slop_dir.mkdir(parents=True, exist_ok=True)

    for variant in job.variants:
        if variant.variant_id in loser_ids and variant.audio_path:
            source = Path(variant.audio_path)
            if source.exists():
                dest = slop_dir / source.name
                shutil.move(str(source), str(dest))
                variant.audio_path = str(dest)
                variant.status = "SLOP_BIN"

        if variant.variant_id == winner_variant_id:
            variant.status = "APPROVED"

    job.winner_variant_id = winner_variant_id
    job.status = JOB_STATUS_SELECTED
    job.notes = notes
    return save_job(job)


def mark_job_submitted(job_id: str, provider_task_id: str, provider: str, notes: str | None = None) -> GenerationJob:
    job = load_job(job_id)
    job.provider_task_id = provider_task_id
    job.provider = provider
    job.status = JOB_STATUS_GENERATED
    job.notes = notes
    return save_job(job)
