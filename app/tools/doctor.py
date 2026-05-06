from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from app.core.paths import project_root


AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".flac", ".aac", ".ogg"}


def _audio_count(path: Path) -> int:
    if not path.exists():
        return 0
    return len([p for p in path.glob("*") if p.is_file() and p.suffix.lower() in AUDIO_EXTS])


def _check_sidecar(url: str) -> tuple[bool, str]:
    try:
        with urlopen(f"{url.rstrip('/')}/health", timeout=3) as response:
            data = json.loads(response.read().decode("utf-8"))
        return True, f"OK sidecar reachable: {data.get('service', 'unknown')}"
    except (OSError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        return False, f"TODO sidecar not reachable at {url}: {exc}"


def doctor(sidecar_url: str = "http://127.0.0.1:8766") -> int:
    root = project_root()
    inbox = root / "data" / "inbox" / "suno_downloads"

    checks: list[tuple[bool, str]] = []

    checks.append((root.exists(), f"Project root: {root}"))
    checks.append(((root / "app").exists(), "App folder exists"))
    checks.append(((root / "sidecar" / "suno_sidecar.py").exists(), "Suno sidecar file exists"))
    checks.append((inbox.exists(), f"Suno download inbox exists: {inbox}"))

    sidecar_ok, sidecar_msg = _check_sidecar(sidecar_url)
    checks.append((sidecar_ok, sidecar_msg))

    audio_count = _audio_count(inbox)
    checks.append((True, f"Suno inbox audio files: {audio_count}"))

    print("")
    print("Drakonya Doctor")
    print("===============")

    failures = 0
    for ok, message in checks:
        label = "OK" if ok else "TODO"
        print(f"{label:5} {message}")
        if not ok:
            failures += 1

    print("")
    if failures:
        print("Next action:")
        print("Start sidecar with:")
        print("python3 -m app.tools.drakonya sidecar")
        print("")
        return 1

    print("Status: READY")
    print("")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Drakonya local preflight checks.")
    parser.add_argument("--sidecar-url", default="http://127.0.0.1:8766")
    args = parser.parse_args()

    raise SystemExit(doctor(args.sidecar_url))


if __name__ == "__main__":
    main()
