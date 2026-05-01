from __future__ import annotations

import os
from pathlib import Path


def project_root() -> Path:
    env_root = os.getenv("DRAKONYA_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()

    # app/core/paths.py -> app/core -> app -> project root
    return Path(__file__).resolve().parents[2]


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def state_dir() -> Path:
    return ensure_dir(project_root() / "state")


def logs_dir() -> Path:
    return ensure_dir(project_root() / "logs")


def data_dir() -> Path:
    return ensure_dir(project_root() / "data")


def tracks_dir() -> Path:
    return ensure_dir(data_dir() / "tracks")


def covers_dir() -> Path:
    return ensure_dir(data_dir() / "covers")


def videos_dir() -> Path:
    return ensure_dir(data_dir() / "videos")


def releases_dir() -> Path:
    return ensure_dir(data_dir() / "releases")


def analytics_dir() -> Path:
    return ensure_dir(data_dir() / "analytics")


def slop_bin_dir() -> Path:
    return ensure_dir(data_dir() / "slop_bin")


def agents_dir() -> Path:
    return ensure_dir(project_root() / "agents")


def docs_dir() -> Path:
    return ensure_dir(project_root() / "docs")
