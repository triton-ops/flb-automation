"""Browser/driver factory + config loading for the UI POM."""
from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path

_BROWSER_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = _BROWSER_DIR / "config" / "ui_config.json"       # nbr-84 (FLB): url, user, password
CONFIG_PATH_FSB = _BROWSER_DIR / "config" / "ui_config_fsb.json"  # nbr-5 (File Share Backup)
VALUES_PATH = _BROWSER_DIR / "config" / "ui_values.json"       # reusable UI-check data
SHOTS_DIR = _BROWSER_DIR.parent / "results" / "screenshots"


def load_config(path: Path | None = None) -> dict:
    """Load a secrets config. Default = nbr-84 (FLB). Pass CONFIG_PATH_FSB for nbr-5 (FSB)."""
    return json.loads((path or CONFIG_PATH).read_text(encoding="utf-8"))


def load_values() -> dict:
    return json.loads(VALUES_PATH.read_text(encoding="utf-8"))


@contextmanager
def browser_page(headless: bool = True, viewport=(1600, 900)):
    """Yield a ready Playwright page (Chromium, self-signed-cert tolerant)."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=headless)
        ctx = b.new_context(ignore_https_errors=True,
                            viewport={"width": viewport[0], "height": viewport[1]})
        page = ctx.new_page()
        page.set_default_timeout(20000)
        try:
            yield page
        finally:
            ctx.close()
            b.close()
