"""NBR Director UI screenshot helper (Playwright, Chromium).

Companion to the flb-automation RPC framework: the nbr MCP is headless RPC and
cannot screenshot, so this drives the Director web UI to capture PNG evidence at
the verify step and at any failed step.

Usage:
    python nbr_ui.py --out shot.png                 # login + dashboard, screenshot
    python nbr_ui.py --view jobs --out jobs.png     # login + open Jobs view, screenshot
    python nbr_ui.py --calibrate --out login.png    # dump login-page inputs (selector tuning)

Credentials (same test1 account as RPC) resolution order:
    1. --user / --password CLI flags
    2. env NBR_UI_USER / NBR_UI_PASS
    3. browser/config/ui_config.json  ->  {"url": "...", "user": "...", "password": "..."}

The appliance uses a self-signed cert -> Chromium launched with ignore_https_errors.

NOTE: NBR Director is an ExtDirect single-page app; the login selectors below are
best-effort with fallbacks. If login does not land, run --calibrate once to see the
actual field names, then adjust LOGIN_SELECTORS.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

DEFAULT_URL = "https://10.10.15.149:4443"
CONFIG_PATH = Path(__file__).resolve().parent / "config" / "ui_config.json"

# Best-effort login selectors, tried in order. Tune via --calibrate.
USER_SELECTORS = [
    "input[name='username']",
    "input[name='login']",
    "input[type='text']",
    "input[placeholder*='ser' i]",
]
PASS_SELECTORS = [
    "input[name='password']",
    "input[type='password']",
    "input[placeholder*='ass' i]",
]
SUBMIT_SELECTORS = [
    "button[type='submit']",
    "button:has-text('Log In')",
    "button:has-text('Login')",
    "input[type='submit']",
]

# View navigation: appliance route fragments (calibrate against the live build).
VIEW_FRAGMENTS = {
    "dashboard": "",
    "jobs": "#jobs",
    "repositories": "#repositories",
    "activities": "#activities",
}


def load_config() -> dict:
    if CONFIG_PATH.is_file():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    return {}


def resolve_creds(args) -> tuple[str, str, str]:
    cfg = load_config()
    url = args.url or os.environ.get("NBR_UI_URL") or cfg.get("url") or DEFAULT_URL
    user = args.user or os.environ.get("NBR_UI_USER") or cfg.get("user")
    pwd = args.password or os.environ.get("NBR_UI_PASS") or cfg.get("password")
    return url, user, pwd


def _first(page, selectors):
    for sel in selectors:
        loc = page.locator(sel)
        try:
            if loc.count() > 0:
                return loc.first
        except Exception:
            continue
    return None


def calibrate(page, out: Path) -> int:
    inputs = page.eval_on_selector_all(
        "input",
        "els => els.map(e => ({name:e.name, type:e.type, id:e.id, placeholder:e.placeholder}))",
    )
    buttons = page.eval_on_selector_all(
        "button, input[type=submit]",
        "els => els.map(e => ({text:(e.innerText||e.value||'').trim(), type:e.type}))",
    )
    print(json.dumps({"inputs": inputs, "buttons": buttons}, indent=2))
    page.screenshot(path=str(out), full_page=True)
    print(f"calibration screenshot -> {out}")
    return 0


def login(page, user: str, pwd: str) -> None:
    u = _first(page, USER_SELECTORS)
    p = _first(page, PASS_SELECTORS)
    if u is None or p is None:
        raise RuntimeError(
            "login fields not found; run --calibrate to inspect the page and tune selectors"
        )
    u.fill(user)
    p.fill(pwd)
    btn = _first(page, SUBMIT_SELECTORS)
    if btn is not None:
        btn.click()
    else:
        p.press("Enter")
    page.wait_for_load_state("networkidle")


def main() -> int:
    ap = argparse.ArgumentParser(description="NBR Director UI screenshot helper")
    ap.add_argument("--out", required=True, help="output PNG path")
    ap.add_argument("--view", default="dashboard", choices=sorted(VIEW_FRAGMENTS),
                    help="view to open before screenshot")
    ap.add_argument("--url", default=None, help="UI base URL (default %s)" % DEFAULT_URL)
    ap.add_argument("--user", default=None)
    ap.add_argument("--password", default=None)
    ap.add_argument("--calibrate", action="store_true",
                    help="dump login-page inputs/buttons and screenshot, then exit")
    ap.add_argument("--timeout", type=int, default=30000, help="ms")
    ap.add_argument("--headed", action="store_true", help="show the browser window")
    args = ap.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    url, user, pwd = resolve_creds(args)

    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=not args.headed)
        ctx = browser.new_context(ignore_https_errors=True,
                                   viewport={"width": 1600, "height": 900})
        page = ctx.new_page()
        page.set_default_timeout(args.timeout)
        try:
            page.goto(url, wait_until="domcontentloaded")
            if args.calibrate:
                return calibrate(page, out)
            if not user or not pwd:
                print("ERROR: no UI credentials (set --user/--password, env "
                      "NBR_UI_USER/NBR_UI_PASS, or config/ui_config.json)", file=sys.stderr)
                return 2
            login(page, user, pwd)
            frag = VIEW_FRAGMENTS.get(args.view, "")
            if frag:
                page.goto(url.rstrip("/") + "/" + frag, wait_until="networkidle")
            page.screenshot(path=str(out), full_page=True)
            print(f"screenshot -> {out}")
            return 0
        finally:
            ctx.close()
            browser.close()


if __name__ == "__main__":
    sys.exit(main())
