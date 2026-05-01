from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        # Do not overwrite real environment variables.
        os.environ.setdefault(key, value)


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _as_float(value: str | None, default: float) -> float:
    if value is None:
        return default

    try:
        return float(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class DrakonyaConfig:
    root: Path
    env: str
    hermes_enabled: bool
    openai_enabled: bool
    openai_model: str
    openai_api_key_present: bool
    agent_automation_enabled: bool
    max_daily_llm_usd: float
    max_run_llm_usd: float


def load_config() -> DrakonyaConfig:
    # Locate project root from this file:
    # app/core/config.py -> app/core -> app -> project root
    root = Path(os.getenv("DRAKONYA_ROOT", Path(__file__).resolve().parents[2])).resolve()

    # Load local .env if present. This file must never be committed.
    _load_env_file(root / ".env")

    return DrakonyaConfig(
        root=root,
        env=os.getenv("DRAKONYA_ENV", "local"),
        hermes_enabled=_as_bool(os.getenv("HERMES_ENABLED"), default=False),
        openai_enabled=_as_bool(os.getenv("OPENAI_ENABLED"), default=False),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-5.5-mini"),
        openai_api_key_present=bool(os.getenv("OPENAI_API_KEY")),
        agent_automation_enabled=_as_bool(os.getenv("DRAKONYA_AGENT_AUTOMATION"), default=False),
        max_daily_llm_usd=_as_float(os.getenv("DRAKONYA_MAX_DAILY_LLM_USD"), 1.00),
        max_run_llm_usd=_as_float(os.getenv("DRAKONYA_MAX_RUN_LLM_USD"), 0.10),
    )


def assert_llm_allowed() -> None:
    config = load_config()

    if not config.openai_enabled:
        raise RuntimeError("OpenAI is wired but disabled. Set OPENAI_ENABLED=true only when ready.")

    if not config.agent_automation_enabled:
        raise RuntimeError("Agent automation is disabled. Set DRAKONYA_AGENT_AUTOMATION=true only when ready.")

    if not config.openai_api_key_present:
        raise RuntimeError("OPENAI_API_KEY is missing.")

    if config.max_run_llm_usd <= 0:
        raise RuntimeError("DRAKONYA_MAX_RUN_LLM_USD must be greater than zero.")
