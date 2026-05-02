from __future__ import annotations

from pathlib import Path

from app.providers.base import GenerationRequest, GenerationTask, GeneratedTrack


class SunoPrivateProvider:
    name = "suno_private"

    def __init__(self, enabled: bool = False) -> None:
        self.enabled = enabled

    def _guard(self) -> None:
        if not self.enabled:
            raise RuntimeError(
                "Suno private provider is disabled. "
                "Enable only after the sidecar/browser automation layer is intentionally implemented."
            )

    def generate(self, request: GenerationRequest) -> GenerationTask:
        self._guard()
        raise NotImplementedError("Suno private generation is not implemented yet.")

    def status(self, task_id: str) -> GenerationTask:
        self._guard()
        raise NotImplementedError("Suno private status is not implemented yet.")

    def download(self, task_id: str, output_dir: Path) -> list[GeneratedTrack]:
        self._guard()
        raise NotImplementedError("Suno private download is not implemented yet.")
