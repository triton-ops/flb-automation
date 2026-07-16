"""Browser/driver factory + config loading for the UI POM."""
from __future__ import annotations

import json
import os
from contextlib import contextmanager
from pathlib import Path

from dotenv import load_dotenv

_BROWSER_DIR = Path(__file__).resolve().parent.parent.parent
_REPO_ROOT = _BROWSER_DIR.parent
CONFIG_PATH = _BROWSER_DIR / "config" / "ui_config.json"       # nbr-84 (FLB): url, user, password
CONFIG_PATH_FSB = _BROWSER_DIR / "config" / "ui_config_fsb.json"  # nbr-5 (FSB)
VALUES_PATH = _BROWSER_DIR / "config" / "ui_values.json"       # reusable UI-check data
SHOTS_DIR = _BROWSER_DIR.parent / "results" / "screenshots"
TRACES_DIR = _BROWSER_DIR.parent / "results" / "traces"

# Auto-load a repo-root .env file (see .env.example for the expected keys) into os.environ.
# Non-destructive: load_dotenv() never overrides a variable the shell/CI already set.
load_dotenv(_REPO_ROOT / ".env")


def load_config(path: Path | None = None) -> dict:
    """Load UI secrets. Default = nbr-84 (FLB); pass CONFIG_PATH_FSB for nbr-5 (FSB).

    Resolution order: env vars first (so CI can inject GitHub Secrets directly, or a local
    .env file — auto-loaded above — without writing them to a JSON file on disk), then the
    gitignored JSON config file. Env vars only override whichever keys they set — a
    partially-set config file plus env vars for the rest still resolves correctly.

    Env var names are keyed per-appliance (NBR_FLB_*/NBR_FSB_*) so setting one doesn't bleed
    into the other's config when both are loaded in the same process — NBR_UI_URL/USER/PASS
    (no FLB/FSB distinction) are kept as a legacy alias for NBR_FLB_* only, for scripts that
    predate this split (browser/nbr_ui.py, browser/checks/cleanup_auto_flb_jobs.py)."""
    is_fsb = path == CONFIG_PATH_FSB
    prefix = "NBR_FSB_" if is_fsb else "NBR_FLB_"
    cfg = json.loads((path or CONFIG_PATH).read_text(encoding="utf-8")) if (path or CONFIG_PATH).is_file() else {}
    url = os.environ.get(f"{prefix}URL")
    user = os.environ.get(f"{prefix}USER")
    pwd = os.environ.get(f"{prefix}PASS")
    if not is_fsb:
        url = url or os.environ.get("NBR_UI_URL")
        user = user or os.environ.get("NBR_UI_USER")
        pwd = pwd or os.environ.get("NBR_UI_PASS")
    cfg["url"] = url or cfg.get("url")
    cfg["user"] = user or cfg.get("user")
    cfg["password"] = pwd or cfg.get("password")
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
