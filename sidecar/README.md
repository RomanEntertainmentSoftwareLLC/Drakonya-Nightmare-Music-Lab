# Drakonya Suno Sidecar

This sidecar is the future local bridge between Drakonya Nightmare Music Lab and the user's own Suno account/browser session.

It is intentionally a skeleton right now.

## Purpose

The sidecar will eventually:

1. Use a dedicated browser profile logged into Suno.
2. Submit a prompt to Suno.
3. Wait for Suno to generate two versions.
4. Download both audio files.
5. Return local file paths to the main Drakonya API.

## Current State

No live Suno control exists yet.

Available endpoints:

- GET /health
- POST /suno/generate
- GET /suno/jobs/{sidecar_job_id}
- POST /suno/jobs/{sidecar_job_id}/download

## Run

From the project root:

    python3 -m uvicorn sidecar.suno_sidecar:app --host 127.0.0.1 --port 8766 --reload

Open:

    http://127.0.0.1:8766/docs
