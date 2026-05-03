from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.providers.base import GenerationRequest, GenerationTask, GeneratedTrack


class SunoPrivateProvider:
    name = "suno_private"

    def __init__(self, enabled: bool = False, sidecar_url: str | None = None) -> None:
        self.enabled = enabled
        self.sidecar_url = (sidecar_url or os.getenv("SUNO_SIDECAR_URL", "http://127.0.0.1:8766")).rstrip("/")

    def _guard(self) -> None:
        if not self.enabled:
            raise RuntimeError(
                "Suno private provider is disabled. "
                "Enable only after the sidecar/browser automation layer is intentionally implemented."
            )

    def _request_json(self, method: str, path: str, payload: dict | None = None) -> dict:
        self._guard()

        url = f"{self.sidecar_url}{path}"
        body = None
        headers = {"Content-Type": "application/json"}

        if payload is not None:
            body = json.dumps(payload).encode("utf-8")

        request = Request(url=url, data=body, headers=headers, method=method)

        try:
            with urlopen(request, timeout=30) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Suno sidecar HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise RuntimeError(f"Could not reach Suno sidecar at {self.sidecar_url}: {exc}") from exc

    def generate(self, request: GenerationRequest) -> GenerationTask:
        data = self._request_json(
            "POST",
            "/suno/generate",
            {
                "prompt": request.prompt,
                "batch_id": request.batch_id,
                "title": request.title,
                "genre": request.genre,
            },
        )

        return GenerationTask(
            provider=self.name,
            task_id=data["sidecar_job_id"],
            state="submitted" if data.get("state") == "created" else data.get("state", "submitted"),
            batch_id=data["batch_id"],
            title=data.get("title"),
            message=data.get("notes"),
        )

    def status(self, task_id: str) -> GenerationTask:
        data = self._request_json("GET", f"/suno/jobs/{task_id}")

        return GenerationTask(
            provider=self.name,
            task_id=data["sidecar_job_id"],
            state=data.get("state", "running"),
            batch_id=data["batch_id"],
            title=data.get("title"),
            message=data.get("notes"),
        )

    def download(self, task_id: str, output_dir: Path) -> list[GeneratedTrack]:
        data = self._request_json("POST", f"/suno/jobs/{task_id}/download")

        tracks: list[GeneratedTrack] = []
        for variant_id, key in (("A", "version_a_path"), ("B", "version_b_path")):
            audio_path = data.get(key)
            if not audio_path:
                continue

            path = Path(audio_path)
            tracks.append(
                GeneratedTrack(
                    provider=self.name,
                    task_id=task_id,
                    batch_id=data.get("batch_id", output_dir.name),
                    title=f"{data.get('title') or task_id} version {variant_id}",
                    audio_path=path,
                    metadata={
                        "variant_id": variant_id,
                        "sidecar_job_id": task_id,
                    },
                )
            )

        return tracks
