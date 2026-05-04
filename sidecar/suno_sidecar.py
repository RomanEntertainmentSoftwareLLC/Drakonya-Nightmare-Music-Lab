from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.core.paths import project_root


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


class OpenSunoBody(BaseModel):
    url: str | None = None


app = FastAPI(
    title="Drakonya Suno Sidecar",
    version="0.1.0",
    description="Local sidecar for future Suno account/browser control.",
)


_JOBS: dict[str, SunoSidecarJob] = {}
_BROWSER_PROCESS: subprocess.Popen | None = None


BROWSER_CANDIDATES = [
    "google-chrome",
    "chromium",
    "chromium-browser",
    "firefox",
]


def _new_sidecar_job_id() -> str:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"SUNO-{stamp}-{uuid4().hex[:8]}"


def _touch(job: SunoSidecarJob) -> SunoSidecarJob:
    job.updated_at = datetime.now(timezone.utc).isoformat()
    return job


def _resolve_path(value: str | None, default_relative: str) -> Path:
    if value:
        path = Path(value).expanduser()
        if path.is_absolute():
            return path
        return project_root() / path
    return project_root() / default_relative


def suno_browser_profile_dir() -> Path:
    return _resolve_path(os.getenv("SUNO_BROWSER_PROFILE_DIR"), "state/suno_browser_profile")


def suno_download_dir() -> Path:
    return _resolve_path(os.getenv("SUNO_BROWSER_DOWNLOAD_DIR"), "data/inbox/suno_downloads")


def find_browser_binary() -> Path | None:
    configured = os.getenv("SUNO_BROWSER_BIN")
    if configured:
        path = Path(configured).expanduser()
        if path.exists():
            return path
        found = shutil.which(configured)
        if found:
            return Path(found)
        return path

    for candidate in BROWSER_CANDIDATES:
        found = shutil.which(candidate)
        if found:
            return Path(found)

    return None


def build_browser_command(browser: Path, url: str) -> list[str]:
    profile_dir = suno_browser_profile_dir()
    profile_dir.mkdir(parents=True, exist_ok=True)
    suno_download_dir().mkdir(parents=True, exist_ok=True)

    name = browser.name.lower()
    if "firefox" in name:
        return [str(browser), "-profile", str(profile_dir), "-new-window", url]

    return [
        str(browser),
        f"--user-data-dir={profile_dir}",
        "--no-first-run",
        "--new-window",
        url,
    ]


@app.get("/health")
def health() -> dict:
    browser = find_browser_binary()
    return {
        "ok": True,
        "service": "drakonya-suno-sidecar",
        "state": "skeleton",
        "live_suno_control": False,
        "browser_available": browser is not None and browser.exists(),
        "browser_binary": str(browser) if browser else None,
        "browser_profile_dir": str(suno_browser_profile_dir()),
        "download_dir": str(suno_download_dir()),
    }


@app.post("/suno/open")
def open_suno(body: OpenSunoBody | None = None) -> dict:
    global _BROWSER_PROCESS

    browser = find_browser_binary()
    if not browser or not browser.exists():
        raise HTTPException(
            status_code=501,
            detail=(
                "No supported browser found. Install google-chrome, chromium, "
                "chromium-browser, or firefox; or set SUNO_BROWSER_BIN."
            ),
        )

    url = (body.url if body else None) or os.getenv("SUNO_URL") or "https://suno.com"
    command = build_browser_command(browser, url)
    _BROWSER_PROCESS = subprocess.Popen(command)

    return {
        "ok": True,
        "url": url,
        "browser_binary": str(browser),
        "browser_profile_dir": str(suno_browser_profile_dir()),
        "download_dir": str(suno_download_dir()),
        "pid": _BROWSER_PROCESS.pid,
        "notes": "Opened Suno in a dedicated local browser profile. Login manually if needed.",
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
