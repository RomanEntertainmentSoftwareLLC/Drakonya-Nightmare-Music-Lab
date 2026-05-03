from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse

from pydantic import BaseModel, Field

from app.providers.base import GenerationRequest
from app.providers.factory import get_music_provider
from app.core.paths import project_root

app = FastAPI(
    title="Drakonya Nightmare Music Lab API",
    version="0.1.0",
    description="Internal API for Drakonya Nightmare Music Lab.",
    docs_url=None,
)

@app.get("/docs", include_in_schema=False)
def custom_swagger_ui_html() -> HTMLResponse:
    html = get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title="Drakonya Nightmare Music Lab API",
        swagger_favicon_url="",
    )

    dark_css = """
    <style>
      body {
        background: #08080c !important;
        color: #e8e8ee !important;
      }

      .swagger-ui {
        background: #08080c !important;
        color: #e8e8ee !important;
      }

      .swagger-ui .topbar {
        display: none !important;
      }

      .swagger-ui .info .title,
      .swagger-ui .info p,
      .swagger-ui .info li,
      .swagger-ui .opblock-tag,
      .swagger-ui .opblock .opblock-summary-description,
      .swagger-ui .opblock .opblock-summary-path,
      .swagger-ui .opblock .opblock-summary-method,
      .swagger-ui table thead tr td,
      .swagger-ui table thead tr th,
      .swagger-ui .parameter__name,
      .swagger-ui .parameter__type,
      .swagger-ui .response-col_status,
      .swagger-ui .response-col_description,
      .swagger-ui label,
      .swagger-ui .tab li,
      .swagger-ui .model-title,
      .swagger-ui .model,
      .swagger-ui .model-box,
      .swagger-ui .prop-type,
      .swagger-ui .prop-format,
      .swagger-ui .servers-title {
        color: #e8e8ee !important;
      }

      .swagger-ui .scheme-container,
      .swagger-ui .opblock,
      .swagger-ui .opblock-section-header,
      .swagger-ui .responses-wrapper,
      .swagger-ui .parameters-container,
      .swagger-ui .model-box,
      .swagger-ui section.models,
      .swagger-ui textarea,
      .swagger-ui input,
      .swagger-ui select {
        background: #11111a !important;
        color: #e8e8ee !important;
        border-color: #35354a !important;
      }

      .swagger-ui .opblock.opblock-get {
        background: rgba(61, 105, 180, 0.16) !important;
        border-color: #3d69b4 !important;
      }

      .swagger-ui .opblock.opblock-post {
        background: rgba(64, 170, 120, 0.16) !important;
        border-color: #40aa78 !important;
      }

      .swagger-ui .opblock.opblock-delete {
        background: rgba(190, 70, 70, 0.16) !important;
        border-color: #be4646 !important;
      }

      .swagger-ui .opblock.opblock-put,
      .swagger-ui .opblock.opblock-patch {
        background: rgba(200, 150, 60, 0.16) !important;
        border-color: #c8963c !important;
      }

      .swagger-ui .btn,
      .swagger-ui button {
        background: #1d1d2b !important;
        color: #f5f5ff !important;
        border-color: #55556d !important;
      }

      .swagger-ui .btn.execute {
        background: #8b1e3f !important;
        border-color: #d33663 !important;
        color: #fff !important;
      }

      .swagger-ui .highlight-code,
      .swagger-ui .microlight,
      .swagger-ui pre {
        background: #050508 !important;
        color: #e8e8ee !important;
      }
    </style>
    """

    return HTMLResponse(
        html.body.decode("utf-8").replace("</head>", f"{dark_css}</head>")
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


class AttachVariantBody(BaseModel):
    source_audio_path: str = Field(min_length=1)


@app.post("/jobs/{job_id}/variants/{variant_id}/attach")
def attach_variant(job_id: str, variant_id: str, body: AttachVariantBody) -> dict:
    from pathlib import Path
    from app.core.jobs import attach_variant_audio

    try:
        job = attach_variant_audio(job_id, variant_id.upper(), Path(body.source_audio_path))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "job_id": job.job_id,
        "batch_id": job.batch_id,
        "status": job.status,
        "variants": [variant.__dict__ for variant in job.variants],
    }


@app.post("/jobs/{job_id}/submit")
def submit_job_to_provider(job_id: str) -> dict:
    from app.core.jobs import load_job, mark_job_submitted
    from app.providers.base import GenerationRequest
    from app.providers.factory import get_music_provider

    try:
        job = load_job(job_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    provider = get_music_provider()

    try:
        task = provider.generate(
            GenerationRequest(
                prompt=job.prompt,
                batch_id=job.batch_id,
                title=job.title,
                genre=job.genre,
            )
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    updated = mark_job_submitted(
        job_id=job.job_id,
        provider_task_id=task.task_id,
        provider=task.provider,
        notes=task.message,
    )

    return {
        "job_id": updated.job_id,
        "batch_id": updated.batch_id,
        "status": updated.status,
        "provider": updated.provider,
        "provider_task_id": updated.provider_task_id,
        "notes": updated.notes,
    }
