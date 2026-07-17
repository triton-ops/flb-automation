"""Accessibility scan (axe-core, via the axe-playwright-python wrapper) — read-only, ad-hoc audit
of the Director UI. See docs/enterprise-gap-analysis.md's Low-severity "no accessibility scanning"
finding.

Unlike the visual-regression example (which deliberately avoids the live appliance because
screenshot-diffing is timing-sensitive), an axe-core scan is safe to point at the real Director UI:
it injects JS, queries the rendered DOM/ARIA tree at a point in time, and reports violations — no
clicks, no mutations, nothing that could interact with a job or trip the safety fence in
CLAUDE.md. This script only opens pages and logs in (an action every test in this suite already
performs) — it never creates, runs, or deletes anything.

This is an audit tool, not a pass/fail gate: real accessibility issues in third-party ExtJS
markup are expected and are not this project's bug to fix — it prints a findings report for
awareness, and exits non-zero only on a script error (unreachable appliance, axe injection
failure), never on found violations.

Usage:
    python browser/checks/accessibility_scan.py                 # nbr-84, login page + Jobs dashboard
    python browser/checks/accessibility_scan.py --headed         # watch it live
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from axe_playwright_python.sync_playwright import Axe  # noqa: E402
from pom.base.config import ConfigError, load_app_config  # noqa: E402
from pom.base.driver import browser_page  # noqa: E402
from pom.common.data_protection_page import DataProtectionPage  # noqa: E402
from pom.common.login_page import LoginPage  # noqa: E402

# WCAG 2.x A/AA — the standard baseline most accessibility audits start from.
AXE_OPTIONS = {"runOnly": {"type": "tag", "values": ["wcag2a", "wcag2aa"]}}


def scan_page(axe: Axe, page, label: str) -> None:
    results = axe.run(page, options=AXE_OPTIONS)
    violations = results.response.get("violations", [])
    print(f"\n=== {label}: {len(violations)} violation type(s) ===")
    for v in violations:
        nodes = len(v.get("nodes", []))
        print(f"  [{v['impact'] or 'unknown':<8}] {v['id']} — {v['help']} ({nodes} element(s))")
        print(f"             {v['helpUrl']}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()

    cfg = load_app_config().flb
    try:
        cfg.validate("NBR_FLB")
    except ConfigError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    axe = Axe()
    with browser_page(headless=not args.headed) as page:
        page.goto(cfg.url)
        page.wait_for_timeout(1500)
        scan_page(axe, page, "Login page")

        LoginPage(page).open(cfg.url).login(cfg.user, cfg.password)
        DataProtectionPage(page).open()
        page.wait_for_timeout(1500)
        scan_page(axe, page, "Jobs dashboard (post-login)")

    print("\nDone. This is an awareness report, not a pass/fail gate (see this script's docstring).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
