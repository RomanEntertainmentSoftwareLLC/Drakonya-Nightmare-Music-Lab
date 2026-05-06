from __future__ import annotations

import os
import subprocess
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from app.core.paths import project_root


_DRIVER = None


def _download_dir() -> Path:
    raw = os.getenv("SUNO_BROWSER_DOWNLOAD_DIR")
    if raw:
        path = Path(raw).expanduser()
        return path if path.is_absolute() else project_root() / path
    return project_root() / "data" / "inbox" / "suno_downloads"


def _windows_host_ip() -> str:
    configured = os.getenv("SUNO_WEBDRIVER_HOST")
    if configured:
        return configured

    try:
        return subprocess.check_output(
            "ip route | awk '/default/ {print $3}'",
            shell=True,
            text=True,
        ).strip()
    except Exception:
        return "127.0.0.1"


def webdriver_url() -> str:
    configured = os.getenv("SUNO_WEBDRIVER_URL")
    if configured:
        return configured.rstrip("/")

    host = _windows_host_ip()
    port = os.getenv("SUNO_WEBDRIVER_PORT", "9515")
    return f"http://{host}:{port}"


def _create_driver():
    options = Options()
    options.add_argument("--start-maximized")

    return webdriver.Remote(
        command_executor=webdriver_url(),
        options=options,
    )


def open_suno_page(url: str = "https://suno.com") -> dict:
    global _DRIVER

    _download_dir().mkdir(parents=True, exist_ok=True)

    if _DRIVER is None:
        _DRIVER = _create_driver()

    _DRIVER.get(url)

    return {
        "ok": True,
        "url": _DRIVER.current_url,
        "title": _DRIVER.title,
        "webdriver_url": webdriver_url(),
        "download_dir": str(_download_dir()),
        "notes": "Opened Suno using remote Selenium ChromeDriver.",
    }


def browser_status() -> dict:
    return {
        "driver_active": _DRIVER is not None,
        "webdriver_url": webdriver_url(),
        "current_url": _DRIVER.current_url if _DRIVER else "",
        "download_dir": str(_download_dir()),
    }


def close_browser() -> dict:
    global _DRIVER

    if _DRIVER:
        _DRIVER.quit()

    _DRIVER = None
    return {"ok": True, "notes": "Closed remote Selenium browser session."}
