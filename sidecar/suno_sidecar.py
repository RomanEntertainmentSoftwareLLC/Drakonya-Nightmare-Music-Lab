from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


JobState = Literal[
    "created",
    "submitted",
    "running",
    "completed",
    "downloaded",
    "failed",
]


@dataclass
class SunoSidecarJob:
    sidecar_job_id: str
    prompt: str
    batch_id: str
    title: str | None = None
    genre: str | None = None
    state: JobState = "created"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    version_a_path: str | None = None
    version_b_path: str | None = None
    notes: str | None = None


class GenerateBody(BaseModel):
    prompt: str = Field(min_length=1)
    batch_id: str = Field(min_length=1)
    title: str | None = None
    genre: str | None = None


app = FastAPI(
    title="Drakonya Suno Sidecar",
    version="0.1.0",
    description="Local sidecar for future Suno account/browser control.",
)


_JOBS: dict[str, SunoSidecarJob] = {}


def _new_sidecar_job_id() -> str:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"SUNO-{stamp}-{uuid4().hex[:8]}"


def _touch(job: SunoSidecarJob) -> SunoSidecarJob:
    job.updated_at = datetime.now(timezone.utc).isoformat()
    return job


@app.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "service": "drakonya-suno-sidecar",
        "state": "skeleton",
        "live_suno_control": False,
    }


@app.post("/suno/generate")
def generate(body: GenerateBody) -> dict:
    sidecar_job_id = _new_sidecar_job_id()

    job = SunoSidecarJob(
        sidecar_job_id=sidecar_job_id,
        prompt=body.prompt,
        batch_id=body.batch_id,
        title=body.title,
        genre=body.genre,
        state="created",
        notes=(
            "Skeleton only. Future implementation will submit this prompt "
            "to Suno and produce two generated audio versions."
        ),
    )

    _JOBS[sidecar_job_id] = job

    return asdict(job)


@app.get("/suno/jobs/{sidecar_job_id}")
def get_job(sidecar_job_id: str) -> dict:
    job = _JOBS.get(sidecar_job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Sidecar job not found: {sidecar_job_id}")

    return asdict(job)


@app.post("/suno/jobs/{sidecar_job_id}/download")
def download_job(sidecar_job_id: str) -> dict:
    job = _JOBS.get(sidecar_job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Sidecar job not found: {sidecar_job_id}")

    job.state = "failed"
    job.notes = (
        "Download is not implemented yet. Future implementation will download "
        "Suno version A and version B, then return both local file paths."
    )
    _touch(job)

    raise HTTPException(status_code=501, detail=job.notes)


@app.get("/")
def root() -> dict:
    return {
        "service": "drakonya-suno-sidecar",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/favicon.ico")
def favicon() -> dict:
    return {}
