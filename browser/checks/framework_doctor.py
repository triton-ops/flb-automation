"""Framework Doctor — diagnoses WHY the framework might fail, across 8 root-cause categories,
before spending real TC time (3-4 min per job build) finding out the hard way.

Complements health_check.py rather than duplicating it: health_check.py is a pass/warning/fail
GATE over 8 concrete UI workflow steps (does the wizard open, does Recover work); this tool is a
DIAGNOSIS across 8 root-cause CATEGORIES (why would something fail, if it did) — Playwright/
package-level, environment-level, and locator-level checks that don't map to a single workflow
step. Run this first when something is behaving strangely, or before a long session, to get a
"what's actually wrong" read rather than a binary go/no-go.

Categories, in the order checked (cheapest/most-foundational first, so later checks can be
skipped cleanly if an earlier one rules them out):
    1. Playwright version mismatch  — installed package/driver/plugin versions vs. pinned
    2. Environment issue            — .env / config files / network reachability
    3. Browser issue                — can Chromium actually launch at all
    4. Broken locator               — every XPath constant in locators.py is syntactically valid
    5. Test data issue              — manifests/docs present, non-empty, parseable
    6. Authentication issue         — a real login attempt, classifying WHY it failed if it did
    7. Wrong selector               — live canary locators actually resolve against the real UI
    8. Timeout                      — are today's response times already eating into this
                                       project's own calibrated timeout budgets (early warning
                                       for appliance-load-induced flakiness)

Verdicts: HEALTHY (no issue) / AT RISK (non-blocking, worth knowing) / SICK (real, blocking
problem — a suggested fix is always included). Exit code 0 unless any category is SICK.

Usage:
    python browser/checks/framework_doctor.py            # full diagnosis
    python browser/checks/framework_doctor.py --headed   # watch it live
"""
from __future__ import annotations

import argparse
import importlib.metadata as metadata
import re
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pom.base.config import ConfigError, load_app_config  # noqa: E402
from pom.base.driver import browser_page  # noqa: E402
from pom.common import locators as locators_module  # noqa: E402
from pom.common.checksum import load_manifest  # noqa: E402
from pom.common.data_protection_page import DataProtectionPage  # noqa: E402
from pom.common.locators import DataProtectionLocators as DP  # noqa: E402
from pom.common.login_page import LoginPage  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class Diagnosis:
    def __init__(self, category: str):
        self.category = category
        self.verdict = "SICK"
        self.detail = ""
        self.fix = ""
        self.elapsed = 0.0


def diagnose(category: str, results: list[Diagnosis], fn):
    d = Diagnosis(category)
    t0 = time.time()
    try:
        d.verdict, d.detail, d.fix = fn()
    except Exception as exc:  # noqa: BLE001 — the exception IS the diagnosis
        d.verdict, d.detail, d.fix = "SICK", f"{type(exc).__name__}: {exc}", "investigate the traceback above"
    d.elapsed = time.time() - t0
    results.append(d)
    return d


def _pinned_version(requirements_text: str, package: str) -> str | None:
    m = re.search(rf"^{re.escape(package)}==([\d.]+)", requirements_text, re.MULTILINE)
    return m.group(1) if m else None


# ---------------------------------------------------------------------------
# 1. Playwright version mismatch
# ---------------------------------------------------------------------------
def check_playwright_version():
    installed_pkg = metadata.version("playwright")
    installed_plugin = metadata.version("pytest-playwright")
    req_txt = (REPO_ROOT / "requirements.txt").read_text()
    dev_txt = (REPO_ROOT / "requirements-dev.txt").read_text()
    pinned_pkg = _pinned_version(req_txt, "playwright")
    pinned_plugin = _pinned_version(dev_txt, "pytest-playwright")

    driver_out = subprocess.run(
        [sys.executable, "-m", "playwright", "--version"],
        capture_output=True, text=True, timeout=10,
    ).stdout.strip()

    issues = []
    if pinned_pkg and installed_pkg != pinned_pkg:
        issues.append(f"installed playwright {installed_pkg} != requirements.txt pin {pinned_pkg}")
    if pinned_plugin and installed_plugin != pinned_plugin:
        issues.append(f"installed pytest-playwright {installed_plugin} != requirements-dev.txt pin {pinned_plugin}")
    if installed_pkg not in driver_out:
        issues.append(f"browser driver reports {driver_out!r}, doesn't match installed package {installed_pkg}")

    if not issues:
        return ("HEALTHY",
                f"playwright {installed_pkg}, pytest-playwright {installed_plugin}, driver {driver_out!r} — consistent",
                "")
    return ("SICK", "; ".join(issues),
            "run `pip install -r requirements.txt -r requirements-dev.txt && playwright install chromium` "
            "to realign package, plugin, and browser binary versions")


# ---------------------------------------------------------------------------
# 2. Environment issue
# ---------------------------------------------------------------------------
def check_environment():
    env_path = REPO_ROOT / ".env"
    if not env_path.is_file():
        return ("SICK", ".env file not found",
                "copy .env.example to .env and fill in NBR_FLB_URL/USER/PASS (see .env.example)")

    cfg = load_app_config().flb
    try:
        cfg.validate("NBR_FLB")
    except ConfigError as exc:
        return ("SICK", str(exc),
                "set the missing NBR_FLB_* values in .env or browser/config/ui_config.json")

    parsed = urlparse(cfg.url)
    host, port = parsed.hostname, parsed.port or 443
    try:
        with socket.create_connection((host, port), timeout=5):
            pass
    except OSError as exc:
        return ("SICK", f"cannot reach {host}:{port} — {exc}",
                "check VPN/network connectivity to the appliance, or whether its address changed")

    return ("HEALTHY", f".env present, NBR_FLB_* configured, {host}:{port} reachable", "")


# ---------------------------------------------------------------------------
# 3. Browser issue
# ---------------------------------------------------------------------------
def check_browser(page):
    try:
        page.goto("about:blank", timeout=8000)
        _ = page.title()
        return "HEALTHY", "Chromium launched and responded", ""
    except Exception as exc:  # noqa: BLE001
        msg = str(exc)
        if "Executable doesn't exist" in msg:
            return ("SICK", f"browser binaries not installed ({exc})",
                    "run `playwright install chromium`")
        return "SICK", f"{type(exc).__name__}: {exc}", "investigate the traceback above"


# ---------------------------------------------------------------------------
# 4. Broken locator (static XPath syntax check — no lxml needed, Playwright IS the validator)
# ---------------------------------------------------------------------------
def check_broken_locators(page):
    bad: list[tuple[str, str]] = []
    checked = 0
    for cls_name in dir(locators_module):
        cls = getattr(locators_module, cls_name)
        if not isinstance(cls, type):
            continue
        for attr_name in dir(cls):
            if attr_name.startswith("_"):
                continue
            try:
                val = getattr(cls, attr_name)
            except Exception:
                continue
            if isinstance(val, str) and val.strip().startswith(("//", "(//")):
                checked += 1
                try:
                    page.locator(val).count()
                except Exception as exc:  # noqa: BLE001 — a genuine XPath syntax error
                    bad.append((f"{cls_name}.{attr_name}", str(exc).splitlines()[0]))
    if bad:
        detail = f"{len(bad)}/{checked} locator constant(s) have invalid XPath syntax: {bad[:5]}"
        return "SICK", detail, "fix the malformed XPath string(s) listed above in locators.py"
    return "HEALTHY", f"all {checked} static XPath locator constants are syntactically valid", ""


# ---------------------------------------------------------------------------
# 5. Test data issue
# ---------------------------------------------------------------------------
def check_test_data():
    issues = []
    manifests_dir = REPO_ROOT / "test-data" / "manifests"
    if not manifests_dir.is_dir():
        return "SICK", "test-data/manifests/ directory missing", "restore it from git or re-seed manifests"

    files = list(manifests_dir.glob("*.sha256")) + list(manifests_dir.glob("*.md5"))
    if not files:
        return "SICK", "test-data/manifests/ has no .sha256/.md5 files", "restore manifests from git"

    empty = [f.name for f in files if f.stat().st_size == 0]
    if empty:
        issues.append(f"{len(empty)} empty manifest file(s): {empty}")

    try:
        parsed = load_manifest(files[0])
        if not parsed:
            issues.append(f"{files[0].name} parsed to zero entries")
    except Exception as exc:  # noqa: BLE001
        issues.append(f"{files[0].name} failed to parse: {exc}")

    for doc in ("test-data/environment.md", "test-data/test-data.md"):
        p = REPO_ROOT / doc
        if not p.is_file() or p.stat().st_size == 0:
            issues.append(f"{doc} missing or empty")

    if issues:
        return "SICK", "; ".join(issues), "restore the missing/empty file(s) from git"
    return ("HEALTHY",
            f"{len(files)} manifest file(s) present and parseable; environment.md/test-data.md present",
            "")


# ---------------------------------------------------------------------------
# 6. Authentication issue
# ---------------------------------------------------------------------------
def check_auth(page, cfg, timings: dict):
    t0 = time.time()
    LoginPage(page).open(cfg.url).login(cfg.user, cfg.password)
    bad_creds = page.get_by_text("Invalid", exact=False).locator("visible=true")
    if bad_creds.count() > 0:
        text = bad_creds.first.inner_text()
        return ("SICK", f"appliance rejected login: {text!r}",
                "check NBR_FLB_USER/NBR_FLB_PASS in .env — credentials are likely wrong or expired")

    waited = 0
    while waited < 8000:
        if page.locator("//input[@name='username']").locator("visible=true").count() == 0:
            break
        page.wait_for_timeout(500)
        waited += 500
    timings["login"] = time.time() - t0
    if page.locator("//input[@name='username']").locator("visible=true").count() > 0:
        return ("SICK", "login form still showing, no explicit error message appeared",
                "possible UI drift in the login flow — inspect LoginLocators against the live page")
    return "HEALTHY", f"logged in, landed on {page.url}", ""


# ---------------------------------------------------------------------------
# 7. Wrong selector (live canary locators — only meaningful after a successful login)
# ---------------------------------------------------------------------------
def check_wrong_selector(page, auth_ok: bool, timings: dict):
    if not auth_ok:
        return "AT RISK", "skipped — requires a successful login first", "resolve the authentication issue above first"

    t0 = time.time()
    DataProtectionPage(page).open()
    page.wait_for_timeout(1500)
    results = [
        ("Jobs sidebar container",
         page.locator("//div[contains(@class,'jobDashboardNavigator')]").locator("visible=true").count() > 0),
        ("Left-nav menu icons",
         page.locator("//div[contains(@class,'itemMenuSidebar')]").locator("visible=true").count() > 0),
    ]
    timings["jobs_page"] = time.time() - t0

    t0 = time.time()
    DataProtectionPage(page).open_create_menu()
    # Poll for the menu items rather than a fixed sleep-then-check-once — open_create_menu()
    # already retries the '+' click itself for slow-appliance tolerance (see its own docstring),
    # but the ITEMS rendering afterward can still lag past a short fixed wait under load. A
    # single-shot check here would misreport genuine appliance slowness as "selector broken".
    menu_locators = {
        "Create menu: File level backup": DP.MENU_FLB,
        "Create menu: Backup copy": DP.MENU_BACKUP_COPY,
        "Create menu: Backup for file share": DP.MENU_FILE_SHARE,
    }
    waited = 0
    menu_found: dict[str, bool] = {label: False for label in menu_locators}
    while waited < 8000:
        menu_found = {label: page.locator(loc).locator("visible=true").count() > 0
                      for label, loc in menu_locators.items()}
        if any(menu_found.values()):
            break
        page.wait_for_timeout(400)
        waited += 400
    # CALIBRATED live 2026-07-17: capture the canary results HERE, BEFORE dismissing the popup —
    # an earlier version of this check read them AFTER the click-away dismiss below, so every
    # item correctly reported "not visible" simply because the menu had already been closed by
    # this check's own cleanup action, not because anything was actually broken.
    results += list(menu_found.items())
    page.mouse.click(5, 5)  # click-away dismiss (Escape doesn't close this ExtJS popup)
    page.wait_for_timeout(400)
    timings["create_menu"] = time.time() - t0

    missing = [label for label, ok in results if not ok]
    if not missing:
        return "HEALTHY", f"all {len(results)} live canary locators resolved", ""
    detail = f"{len(missing)}/{len(results)} canary locator(s) didn't resolve: {missing}"
    fix = "the Director build likely changed — recalibrate the listed locator(s) against the live DOM"
    if len(missing) == 1:
        return "AT RISK", detail, fix
    return "SICK", detail, fix


# ---------------------------------------------------------------------------
# 8. Timeout (rolls up latency already measured above — no extra navigation needed)
# ---------------------------------------------------------------------------
def check_timeout(timings: dict):
    # Budgets drawn from this project's OWN calibrated timeouts (see data_protection_page.py's
    # run_job()/click_visible defaults) — 70% of budget is the "getting risky" line.
    budgets = {"login": 8, "jobs_page": 6, "create_menu": 5}
    if not timings:
        return (
            "AT RISK",
            "no timing data collected (earlier checks may have failed first)",
            "resolve earlier issues first",
        )
    slow = []
    for label, elapsed in timings.items():
        budget = budgets.get(label, 10)
        if elapsed > budget * 0.7:
            slow.append(f"{label}={elapsed:.1f}s (>{budget * 0.7:.1f}s of its {budget}s budget)")
    summary = ", ".join(f"{k}={v:.1f}s" for k, v in timings.items())
    if not slow:
        return "HEALTHY", f"all timed operations comfortably under budget ({summary})", ""
    fix = (
        "the appliance is likely under sustained load — expect real TCs to be slower/flakier "
        "than usual; consider spacing out job builds"
    )
    if len(slow) < len(timings):
        return "AT RISK", f"some operations running slow: {slow}", fix
    return "SICK", f"most operations running slow: {slow}", fix


def report(results: list[Diagnosis]) -> int:
    width = max(len(r.category) for r in results)
    print(f"\n{'FRAMEWORK DOCTOR — DIAGNOSIS':^{width + 40}}")
    print("=" * (width + 40))
    for r in results:
        print(f"  [{r.verdict:^8}] {r.category:<{width}}  ({r.elapsed:.1f}s)")
        print(f"             {r.detail}")
        if r.fix:
            print(f"             -> {r.fix}")
    print("=" * (width + 40))
    n_sick = sum(1 for r in results if r.verdict == "SICK")
    n_risk = sum(1 for r in results if r.verdict == "AT RISK")
    n_healthy = len(results) - n_sick - n_risk
    overall = "SICK" if n_sick else ("AT RISK" if n_risk else "HEALTHY")
    print(f"  Overall: {overall} — {n_healthy} healthy, {n_risk} at risk, {n_sick} sick")
    return 1 if n_sick else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()

    results: list[Diagnosis] = []
    timings: dict[str, float] = {}

    diagnose("Playwright version mismatch", results, check_playwright_version)
    env_check = diagnose("Environment issue", results, check_environment)
    if env_check.verdict == "SICK":
        # Every remaining check needs either a browser or a reachable appliance — no point
        # pretending otherwise, and each would just restate the same root cause.
        for cat in ["Browser issue", "Broken locator", "Test data issue",
                    "Authentication issue", "Wrong selector", "Timeout"]:
            d = Diagnosis(cat)
            d.verdict, d.detail, d.fix = "SICK", "skipped — environment issue above must be fixed first", ""
            results.append(d)
        return report(results)

    cfg = load_app_config().flb

    with browser_page(headless=not args.headed) as page:
        browser_check = diagnose("Browser issue", results, lambda: check_browser(page))
        if browser_check.verdict == "SICK":
            for cat in ["Broken locator", "Test data issue", "Authentication issue",
                        "Wrong selector", "Timeout"]:
                d = Diagnosis(cat)
                d.verdict, d.detail, d.fix = "SICK", "skipped — browser issue above must be fixed first", ""
                results.append(d)
            return report(results)

        diagnose("Broken locator", results, lambda: check_broken_locators(page))
        diagnose("Test data issue", results, check_test_data)
        auth_check = diagnose("Authentication issue", results, lambda: check_auth(page, cfg, timings))
        diagnose(
            "Wrong selector", results,
            lambda: check_wrong_selector(page, auth_check.verdict == "HEALTHY", timings),
        )
        diagnose("Timeout", results, lambda: check_timeout(timings))

    return report(results)


if __name__ == "__main__":
    raise SystemExit(main())
