"""Browser/driver factory + config loading for the UI POM."""
from __future__ import annotations

import json
import os
from contextlib import contextmanager
from pathlib import Path

_BROWSER_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = _BROWSER_DIR / "config" / "ui_config.json"       # nbr-84 (FLB): url, user, password
CONFIG_PATH_FSB = _BROWSER_DIR / "config" / "ui_config_fsb.json"  # nbr-5 (FSB)
VALUES_PATH = _BROWSER_DIR / "config" / "ui_values.json"       # reusable UI-check data
SHOTS_DIR = _BROWSER_DIR.parent / "results" / "screenshots"
TRACES_DIR = _BROWSER_DIR.parent / "results" / "traces"


def load_config(path: Path | None = None) -> dict:
    """Load UI secrets. Default = nbr-84 (FLB); pass CONFIG_PATH_FSB for nbr-5 (FSB).

    Resolution order: NBR_UI_URL/NBR_UI_USER/NBR_UI_PASS env vars first (so CI can inject
    GitHub Secrets directly, without writing them to a file on disk), then the gitignored
    JSON config file. Env vars only override whichever keys they set — a partially-set config
    file plus env vars for the rest still resolves correctly.
    """
    cfg = json.loads((path or CONFIG_PATH).read_text(encoding="utf-8")) if (path or CONFIG_PATH).is_file() else {}
    cfg["url"] = os.environ.get("NBR_UI_URL") or cfg.get("url")
    cfg["user"] = os.environ.get("NBR_UI_USER") or cfg.get("user")
    cfg["password"] = os.environ.get("NBR_UI_PASS") or cfg.get("password")
    return cfg


def load_values() -> dict:
    return json.loads(VALUES_PATH.read_text(encoding="utf-8"))


@contextmanager
def browser_page(headless: bool = True, viewport=(1600, 900), trace_name: str | None = None):
    """Yield a ready Playwright page (Chromium, self-signed-cert tolerant).

    trace_name: when given, records a Playwright trace for the whole session and saves it to
    results/traces/<trace_name>.zip on exit (always — pass, fail, or exception) so a failure
    can be replayed with `playwright show-trace`. Opt-in and additive: omitting it preserves
    the exact prior behavior (no tracing overhead for routine runs).
    """
    from playwright.sync_api import sync_playwright

    from .retry import retry_on_transient
    with sync_playwright() as pw:
        # browser startup is the one step here that's genuinely transient (resource contention,
        # a flaky first-run browser download) — retry it; everything after is deterministic
        # page-object logic that should fail loudly, not be silently retried.
        b = retry_on_transient(lambda: pw.chromium.launch(headless=headless), attempts=3)
        ctx = b.new_context(ignore_https_errors=True,
                            viewport={"width": viewport[0], "height": viewport[1]})
        if trace_name:
            ctx.tracing.start(screenshots=True, snapshots=True, sources=True)
        page = ctx.new_page()
        page.set_default_timeout(20000)
        try:
            yield page
        finally:
            if trace_name:
                TRACES_DIR.mkdir(parents=True, exist_ok=True)
                ctx.tracing.stop(path=str(TRACES_DIR / f"{trace_name}.zip"))
            ctx.close()
            b.close()
