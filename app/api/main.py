from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.providers.base import GenerationRequest
from app.providers.factory import get_music_provider
from app.core.paths import project_root


app = FastAPI(
    title="Drakonya Nightmare Music Lab API",
    version="0.1.0",
    description="Internal API for Drakonya Nightmare Music Lab.",
)


class GenerateRequestBody(BaseModel):
    prompt: str = Field(min_length=1)
    batch_id: str = Field(min_length=1)
    title: str | None = None
    genre: str | None = None
    duration_hint: str | None = None
    instrumental: bool = False


@app.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "service": "drakonya-nightmare-music-lab",
        "root": str(project_root()),
    }


@app.get("/providers/current")
def current_provider() -> dict:
    provider = get_music_provider()
    return {
        "provider": provider.name,
    }


@app.post("/generations")
def create_generation(body: GenerateRequestBody) -> dict:
    provider = get_music_provider()

    request = GenerationRequest(
        prompt=body.prompt,
        batch_id=body.batch_id,
        title=body.title,
        genre=body.genre,
        duration_hint=body.duration_hint,
        instrumental=body.instrumental,
    )

    try:
        task = provider.generate(request)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "provider": task.provider,
        "task_id": task.task_id,
        "state": task.state,
        "batch_id": task.batch_id,
        "title": task.title,
        "message": task.message,
    }


@app.get("/generations/{task_id}")
def get_generation_status(task_id: str) -> dict:
    provider = get_music_provider()

    try:
        task = provider.status(task_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "provider": task.provider,
        "task_id": task.task_id,
        "state": task.state,
        "batch_id": task.batch_id,
        "title": task.title,
        "message": task.message,
    }


@app.post("/generations/{task_id}/download")
def download_generation(task_id: str, batch_id: str = "inbox") -> dict:
    provider = get_music_provider()
    output_dir = project_root() / "data" / "tracks" / batch_id

    try:
        tracks = provider.download(task_id, output_dir)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "provider": provider.name,
        "task_id": task_id,
        "batch_id": batch_id,
        "output_dir": str(output_dir),
        "tracks": [
            {
                "title": track.title,
                "audio_path": str(track.audio_path),
                "duration_seconds": track.duration_seconds,
                "metadata": track.metadata,
            }
            for track in tracks
        ],
    }


class CreateJobBody(BaseModel):
    prompt: str = Field(min_length=1)
    batch_id: str = Field(min_length=1)
    title: str | None = None
    genre: str | None = None
    provider: str = "manual_suno"


class SelectWinnerBody(BaseModel):
    winner_variant_id: str = Field(pattern="^[AB]$")
    notes: str | None = None


@app.post("/jobs/generate")
def create_job(body: CreateJobBody) -> dict:
    from app.core.jobs import create_generation_job

    job = create_generation_job(
        prompt=body.prompt,
        batch_id=body.batch_id,
        title=body.title,
        genre=body.genre,
        provider=body.provider,
    )

    return {
        "job_id": job.job_id,
        "batch_id": job.batch_id,
        "status": job.status,
        "provider": job.provider,
        "variants": [variant.__dict__ for variant in job.variants],
    }


@app.get("/jobs")
def get_jobs() -> dict:
    from app.core.jobs import list_jobs

    jobs = list_jobs()
    return {
        "jobs": [
            {
                "job_id": job.job_id,
                "batch_id": job.batch_id,
                "title": job.title,
                "genre": job.genre,
                "status": job.status,
                "provider": job.provider,
                "winner_variant_id": job.winner_variant_id,
                "created_at": job.created_at,
            }
            for job in jobs
        ]
    }


@app.get("/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    from app.core.jobs import load_job

    try:
        job = load_job(job_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "job_id": job.job_id,
        "batch_id": job.batch_id,
        "prompt": job.prompt,
        "title": job.title,
        "genre": job.genre,
        "status": job.status,
        "provider": job.provider,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "winner_variant_id": job.winner_variant_id,
        "notes": job.notes,
        "variants": [variant.__dict__ for variant in job.variants],
    }


@app.post("/jobs/{job_id}/select-winner")
def choose_winner(job_id: str, body: SelectWinnerBody) -> dict:
    from app.core.jobs import select_winner

    try:
        job = select_winner(job_id, body.winner_variant_id, body.notes)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "job_id": job.job_id,
        "status": job.status,
        "winner_variant_id": job.winner_variant_id,
        "variants": [variant.__dict__ for variant in job.variants],
    }
