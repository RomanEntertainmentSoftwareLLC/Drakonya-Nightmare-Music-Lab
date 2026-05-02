from __future__ import annotations

from pathlib import Path

from app.providers.base import GenerationRequest, GenerationTask, GeneratedTrack


class ManualSunoProvider:
    name = "manual_suno"

    def generate(self, request: GenerationRequest) -> GenerationTask:
        return GenerationTask(
            provider=self.name,
            task_id=f"manual-{request.batch_id}",
            state="queued",
            batch_id=request.batch_id,
            title=request.title,
            message="Manual provider: paste prompt into Suno, then place downloaded audio in the batch folder.",
        )

    def status(self, task_id: str) -> GenerationTask:
        return GenerationTask(
            provider=self.name,
            task_id=task_id,
            state="queued",
            batch_id="manual",
            message="Manual provider has no remote status.",
        )

    def download(self, task_id: str, output_dir: Path) -> list[GeneratedTrack]:
        output_dir.mkdir(parents=True, exist_ok=True)

        audio_files = []
        for pattern in ("*.mp3", "*.wav", "*.m4a", "*.flac"):
            audio_files.extend(output_dir.glob(pattern))

        tracks: list[GeneratedTrack] = []
        for audio_file in sorted(audio_files):
            tracks.append(
                GeneratedTrack(
                    provider=self.name,
                    task_id=task_id,
                    batch_id=output_dir.name,
                    title=audio_file.stem,
                    audio_path=audio_file,
                    metadata={"source": "manual_import"},
                )
            )

        return tracks
