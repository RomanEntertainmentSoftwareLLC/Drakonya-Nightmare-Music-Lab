from __future__ import annotations

import json
import os
import re
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
from sidecar.browser_controller import browser_status, close_browser, open_suno_page


JobState = Literal[
    "created",
    "submitted",
    "running",
    "completed",
    "downloaded",
    "failed",
]


AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".flac", ".aac", ".ogg"}


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
    prompt_file: str | None = None
    version_a_path: str | None = None
    version_b_path: str | None = None
    notes: str | None = None


class GenerateBody(BaseModel):
    prompt: str = Field(min_length=1)
    batch_id: str = Field(min_length=1)
    title: str | None = None
    genre: str | None = None
    instrumental: bool = False
    copy_to_clipboard: bool = True


class OpenSunoBody(BaseModel):
    url: str | None = None


class DownloadScanBody(BaseModel):
    allow_latest: bool = True
    min_files: int = 2


app = FastAPI(
    title="Drakonya Suno Sidecar",
    version="0.2.0",
    description="Local sidecar for Suno browser assist and download inbox mapping.",
)


_JOBS: dict[str, SunoSidecarJob] = {}
_BROWSER_PROCESS: subprocess.Popen | None = None


BROWSER_CANDIDATES = [
    "google-chrome",
    "chromium",
    "chromium-browser",
    "firefox",
]


CLIPBOARD_COMMANDS = [
    ["wl-copy"],
    ["xclip", "-selection", "clipboard"],
    ["xsel", "--clipboard", "--input"],
    ["clip.exe"],
]


def _new_sidecar_job_id() -> str:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"SUNO-{stamp}-{uuid4().hex[:8]}"


def _safe_slug(value: str | None) -> str:
    raw = (value or "").strip().lower()
    raw = re.sub(r"[^a-z0-9]+", "-", raw)
    return raw.strip("-") or "untitled"


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
    path = _resolve_path(os.getenv("SUNO_BROWSER_DOWNLOAD_DIR"), "data/inbox/suno_downloads")
    path.mkdir(parents=True, exist_ok=True)
    return path


def suno_sidecar_state_dir() -> Path:
    path = _resolve_path(os.getenv("SUNO_SIDECAR_STATE_DIR"), "state/suno_sidecar")
    path.mkdir(parents=True, exist_ok=True)
    return path


def sidecar_jobs_dir() -> Path:
    path = suno_sidecar_state_dir() / "jobs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def sidecar_prompts_dir() -> Path:
    path = suno_sidecar_state_dir() / "prompts"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _job_path(sidecar_job_id: str) -> Path:
    return sidecar_jobs_dir() / f"{sidecar_job_id}.json"


def _save_job(job: SunoSidecarJob) -> SunoSidecarJob:
    _touch(job)
    _job_path(job.sidecar_job_id).write_text(json.dumps(asdict(job), indent=2) + "\n", encoding="utf-8")
    _JOBS[job.sidecar_job_id] = job
    return job


def _load_job(sidecar_job_id: str) -> SunoSidecarJob | None:
    job = _JOBS.get(sidecar_job_id)
    if job:
        return job

    path = _job_path(sidecar_job_id)
    if not path.exists():
        return None

    job = SunoSidecarJob(**json.loads(path.read_text(encoding="utf-8")))
    _JOBS[sidecar_job_id] = job
    return job


def _stage_prompt(job: SunoSidecarJob) -> Path:
    slug = _safe_slug(job.title or job.sidecar_job_id)
    prompt_path = sidecar_prompts_dir() / f"{job.sidecar_job_id}-{slug}.txt"
    prompt_path.write_text(job.prompt.strip() + "\n", encoding="utf-8")
    job.prompt_file = str(prompt_path)
    return prompt_path


def _copy_prompt_to_clipboard(prompt: str) -> str:
    for command in CLIPBOARD_COMMANDS:
        if not shutil.which(command[0]):
            continue
        try:
            subprocess.run(
                command,
                input=prompt.encode("utf-8"),
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
            )
            return f"Copied prompt to clipboard with {command[0]}."
        except (OSError, subprocess.SubprocessError):
            continue

    return "Clipboard copy skipped: no supported clipboard command found."


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


def _audio_candidates(job: SunoSidecarJob, allow_latest: bool) -> list[Path]:
    download_dir = suno_download_dir()
    files = [path for path in download_dir.rglob("*") if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS]

    if not files:
        return []

    tokens = {
        _safe_slug(job.sidecar_job_id),
        _safe_slug(job.title),
        _safe_slug(job.batch_id),
    }
    tokens.discard("untitled")

    matched = [path for path in files if any(token and token in _safe_slug(path.stem) for token in tokens)]
    if matched:
        return sorted(matched, key=lambda path: path.stat().st_mtime)

    if not allow_latest:
        return []

    try:
        created_at = datetime.fromisoformat(job.created_at).timestamp()
        recent = [path for path in files if path.stat().st_mtime >= created_at - 120]
        if recent:
            return sorted(recent, key=lambda path: path.stat().st_mtime)
    except ValueError:
        pass

    return sorted(files, key=lambda path: path.stat().st_mtime)[-2:]


def _map_downloads(job: SunoSidecarJob, allow_latest: bool, min_files: int) -> SunoSidecarJob:
    candidates = _audio_candidates(job, allow_latest=allow_latest)

    if len(candidates) < min_files:
        job.state = "running"
        job.notes = (
            f"Found {len(candidates)} audio file(s) in the Suno download inbox; "
            f"waiting for {min_files}."
        )
        return _save_job(job)

    selected = candidates[:2]
    job.version_a_path = str(selected[0]) if len(selected) >= 1 else None
    job.version_b_path = str(selected[1]) if len(selected) >= 2 else None
    job.state = "downloaded" if job.version_a_path and job.version_b_path else "completed"
    job.notes = "Mapped Suno download inbox files to version A and version B."
    return _save_job(job)


@app.get("/health")
def health() -> dict:
    browser = find_browser_binary()
    return {
        "ok": True,
        "service": "drakonya-suno-sidecar",
        "state": "browser-assist",
        "live_suno_control": False,
        "browser_available": browser is not None and browser.exists(),
        "browser_binary": str(browser) if browser else None,
        "browser_profile_dir": str(suno_browser_profile_dir()),
        "download_dir": str(suno_download_dir()),
        "sidecar_state_dir": str(suno_sidecar_state_dir()),
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
        state="submitted",
    )

    prompt_path = _stage_prompt(job)
    clipboard_note = _copy_prompt_to_clipboard(body.prompt) if body.copy_to_clipboard else "Clipboard copy disabled by request."
    job.notes = (
        "Prompt staged for Suno browser/manual-assist submission. "
        f"Prompt file: {prompt_path}. {clipboard_note}"
    )

    _save_job(job)
    return asdict(job)


@app.get("/suno/jobs/{sidecar_job_id}")
def get_job(sidecar_job_id: str) -> dict:
    job = _load_job(sidecar_job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Sidecar job not found: {sidecar_job_id}")

    return asdict(job)


@app.get("/suno/downloads")
def list_downloads() -> dict:
    files = [
        {
            "path": str(path),
            "name": path.name,
            "size_bytes": path.stat().st_size,
            "mtime": path.stat().st_mtime,
        }
        for path in sorted(suno_download_dir().rglob("*"))
        if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS
    ]
    return {"download_dir": str(suno_download_dir()), "files": files}


@app.post("/suno/jobs/{sidecar_job_id}/download")
def download_job(sidecar_job_id: str, body: DownloadScanBody | None = None) -> dict:
    job = _load_job(sidecar_job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Sidecar job not found: {sidecar_job_id}")

    request = body or DownloadScanBody()
    job = _map_downloads(job, allow_latest=request.allow_latest, min_files=request.min_files)

    if not job.version_a_path and not job.version_b_path:
        raise HTTPException(status_code=404, detail=job.notes)

    return asdict(job)



@app.post("/suno/browser/open")
def browser_open(body: OpenSunoBody | None = None) -> dict:
    url = (body.url if body else None) or os.getenv("SUNO_URL") or "https://suno.com"
    return open_suno_page(url)


@app.get("/suno/browser/status")
def browser_status_endpoint() -> dict:
    return browser_status()


@app.post("/suno/browser/close")
def browser_close() -> dict:
    return close_browser()


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
