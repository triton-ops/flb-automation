"""Browser/driver factory for the UI POM. Config loading lives in config.py (Environment,
AppConfig, load_app_config()) — see that module's docstring for the full typed/validated,
multi-environment configuration system."""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

_BROWSER_DIR = Path(__file__).resolve().parent.parent.parent
SHOTS_DIR = _BROWSER_DIR.parent / "results" / "screenshots"
TRACES_DIR = _BROWSER_DIR.parent / "results" / "traces"


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
