"""Shared build/run/verify helpers for the FLBv2v3_UiReporting suite (NJM-182729, "UI/UX / l10n /
reporting").

`build_flb_job()` is cloned (not imported) from the sibling suites deliberately, per this
project's documented per-suite `_helpers.py` convention.

Skipped-item fixture: CALIBRATED live 2026-07-21. A dangling/broken symlink (Windows: `mklink`
to a non-existent target; Linux: `ln -s` to a non-existent target) placed inside an FLB source
folder reliably produces exactly one skipped item — the job still completes with status
`Successful` (not `Completed with warnings`), and its Job Info panel shows `Skipped items: N
item(s)` plus a `View details` link. Two other candidate mechanisms were tried and do NOT work:
an NTFS deny-ACL on a file (the agent's backup semantics bypass discretionary ACL checks), and a
file held open with FILE_SHARE_NONE for the whole run (the agent tolerates the sharing
violation and backs it up anyway — 0 skipped items both times, confirmed live via
AUTO_FLB_SKIPCHECK). Fixtures seeded once, reused by every test in this suite:
  - Windows (win11 / `Window11`): `C:\\SkipTest_ForFLB\\{normal1.txt, normal2.txt, broken_link.txt}`
  - Linux (flb-linux / `Linux_16.84`): `/SkipTest_ForFLB/{normal1.txt, normal2.txt, broken_link.txt}`

⚠ A single job with BOTH a Windows AND a Linux source hit a reproducible item-picker bug: adding
a SECOND source machine's item via `open_item_picker()`/`select_items()` times out finding a
folder that is demonstrably present at that machine's own picker root when it's the ONLY source
(confirmed both ways live) — a real POM/product finding, not yet root-caused. Tests needing both
OSes build TWO separate single-source jobs instead of one dual-source job.

⚠ GENUINE PRODUCT DEFECT found live 2026-07-21 while building this suite: the Job Info panel's
per-object skipped-items report link (anchor with `data-action="report"`,
`data-event-code="error346"`, `data-vid="JOB-<id>"`, `data-event-id="<id>"`, rendered as the text
"View details" both in the Job Info summary and in the matching Events-log row) does not open any
report. Confirmed via SIX independent click strategies against a real job with exactly 1 skipped
item (AUTO_FLB_SKIPCHECK, since cleaned up): plain `.click()`, `.click(force=True)`,
`.dblclick()`, a native `dispatchEvent` mousedown/mouseup/click sequence at the element's real
bounding-box coordinates, clicking the parent grid row first then the link, and — critically —
launching Chromium with `--disable-popup-blocking` (which revealed the underlying behavior:
`window.open()` IS being called, but with no real report URL — it just opens a blank duplicate
of the whole Director app at `/c/main`, confirmed by polling the new window's URL for 10s). No
console error, no modal, no iframe with real content. See `test_njm_182573.py` for the test that
captures this as a real, reproducible FAIL (not a POM bug — the correct link with the correct
data attributes IS present; clicking it just doesn't work).
"""
from __future__ import annotations

from browser.pom.backup_types.flb_wizard_page import FlbWizardPage
from browser.pom.common.alarms_page import AlarmsPage
from browser.pom.common.data_protection_page import DataProtectionPage
from tests.e2e._lib._shared_helpers import attach_test_data, run_and_wait_flb_job

__all__ = [
    "attach_test_data", "build_flb_job", "run_and_wait_flb_job", "skipped_items_count",
    "report_link_attrs", "read_job_alarm_text",
]


def build_flb_job(
    page,
    job_name: str,
    machine: str,
    drill_path: list[str],
    checks: list[str],
    *,
    is_linux: bool = False,
    repository: str = "Onboard repository",
) -> FlbWizardPage:
    """Build (but do not run) an FLB job via the wizard through Finish. Same shape as every
    sibling suite's build_flb_job()."""
    attach_test_data(
        job_name=job_name, machine=machine, drill_path=drill_path, checks=checks,
        is_linux=is_linux, repository=repository,
    )
    dp = DataProtectionPage(page)
    dp.open().open_create_menu().start_file_level_backup()
    flb = FlbWizardPage(page).on_sources_step()
    if is_linux:
        flb.expand_linux()
    else:
        flb.expand_windows()
    flb.select_machine(machine)
    flb.open_item_picker()
    flb.select_items(drill_path, checks)
    flb.picker_apply()
    flb.click_next()  # Inclusion
    flb.click_next()  # Exclusion
    flb.click_next()  # Destination
    flb.select_repository(repository)
    flb.click_next()  # Schedule
    flb.set_run_on_demand()
    flb.click_next()  # Options
    flb.set_job_name(job_name)
    flb.finish()
    page.wait_for_timeout(2000)
    return flb


def skipped_items_count(page, job_name: str) -> int:
    """Select `job_name`'s dashboard and parse the 'Skipped items: N item(s)' line from its Job
    Info panel. Returns 0 if the line isn't found (job has no skips, or hasn't run yet)."""
    dp = DataProtectionPage(page)
    dp.select_job_row(job_name)
    page.wait_for_timeout(1500)
    text = page.locator("body").inner_text()
    idx = text.find("Skipped items:")
    if idx == -1:
        return 0
    tail = text[idx:idx + 40]
    digits = "".join(ch for ch in tail.split(":", 1)[1] if ch.isdigit())
    return int(digits) if digits else 0


def report_link_attrs(page, job_name: str) -> dict[str, str | None]:
    """Select `job_name`'s dashboard and return the real DOM attributes of its per-object
    skipped-items 'View details' link (data-action/data-vid/data-event-code/data-event-id), or
    an empty dict if no such link is present. Does NOT click it — see this module's docstring
    for why clicking is a separate, already-documented product defect."""
    dp = DataProtectionPage(page)
    dp.select_job_row(job_name)
    page.wait_for_timeout(1500)
    return page.evaluate("""
    () => {
        const el = document.evaluate(
            "//a[@data-action='report']", document, null,
            XPathResult.FIRST_ORDERED_NODE_TYPE, null
        ).singleNodeValue;
        if (!el) return {};
        return {
            action: el.getAttribute('data-action'),
            vid: el.getAttribute('data-vid'),
            eventCode: el.getAttribute('data-event-code'),
            eventId: el.getAttribute('data-event-id'),
            text: el.textContent.trim(),
        };
    }
    """)


def read_job_alarm_text(page, job_name: str) -> str:
    """Select `job_name`'s dashboard, open its Issues panel, and return the full panel text.
    Cloned from test_flbv2v3_Alarms/_helpers.py per this project's per-suite _helpers.py
    convention (see AlarmsPage's own docstring for the panel's real behavior/safety notes)."""
    dp = DataProtectionPage(page)
    dp.select_job_row(job_name)
    page.wait_for_timeout(1500)
    alarms = AlarmsPage(page)
    alarms.open_issues_panel()
    text = alarms.issues_panel_text()
    alarms.close_issues_panel()
    return text
