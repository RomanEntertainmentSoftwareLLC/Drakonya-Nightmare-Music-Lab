from __future__ import annotations

import os

from app.providers.manual import ManualSunoProvider
from app.providers.suno_private import SunoPrivateProvider


def get_music_provider():
    provider = os.getenv("SUNO_PROVIDER", "manual").strip().lower()

    if provider in {"manual", "manual_suno"}:
        return ManualSunoProvider()

    if provider in {"suno_private", "private"}:
        enabled = os.getenv("SUNO_PRIVATE_ENABLED", "false").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        return SunoPrivateProvider(enabled=enabled)

    raise ValueError(f"Unknown SUNO_PROVIDER: {provider}")
