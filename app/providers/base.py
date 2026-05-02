from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol


GenerationState = Literal[
    "queued",
    "submitted",
    "running",
    "completed",
    "failed",
    "cancelled",
]


@dataclass(frozen=True)
class GenerationRequest:
    prompt: str
    batch_id: str
    title: str | None = None
    genre: str | None = None
    duration_hint: str | None = None
    instrumental: bool = False


@dataclass(frozen=True)
class GenerationTask:
    provider: str
    task_id: str
    state: GenerationState
    batch_id: str
    title: str | None = None
    message: str | None = None


@dataclass(frozen=True)
class GeneratedTrack:
    provider: str
    task_id: str
    batch_id: str
    title: str
    audio_path: Path
    duration_seconds: float | None = None
    metadata: dict | None = None


class MusicGenerationProvider(Protocol):
    name: str

    def generate(self, request: GenerationRequest) -> GenerationTask:
        ...

    def status(self, task_id: str) -> GenerationTask:
        ...

    def download(self, task_id: str, output_dir: Path) -> list[GeneratedTrack]:
        ...
