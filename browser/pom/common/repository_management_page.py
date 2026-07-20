"""RepositoryManagementPage — Settings -> Inventory -> Repositories area: open a repository's
own detail page and drive its Management/Maintenance actions (Self-Healing, Reclaim unused
space, Verify all backups, Repair). CALIBRATED live 2026-07-18 against nbr-84 — first POM
coverage for this area (backs NJM-85730 / NJM-85733). See RepositoryManagementLocators'
docstring in locators.py for the full DOM-shape writeup and the repo-type/state gating found
live (self-healing is LOCAL-repo-only; reclaim is hidden until something is reclaimable).

⚠ SAFETY: this class only ever acts on a REPOSITORY (a shared, pre-existing infrastructure
object per CLAUDE.md — self-healing/reclaim/verify/repair are maintenance actions, not deletes,
so they're allowed against Onboard repository/Local-Immutable etc.). It never deletes a
repository and never touches a JOB — job deletion stays JobManagementPage's job, with its own
AUTO_FLB_/AUTO_FSB_ safety fence.

ADDED 2026-07-20 (NJM-68621): open_backup_by_job()/recovery_point_count()/
delete_all_recovery_points() add read/delete access to a single BACKUP's own recovery points,
identified unambiguously by its owning job's name (never by position/index). This still never
touches the JOB entity itself (job deletion stays JobManagementPage's job) — only that job's own
backup/recovery-point data on the repository, and only when the caller passes an
AUTO_FLB_*/AUTO_FSB_* job name. delete_all_recovery_points() deliberately does NOT use the
repository-wide 'Delete backups in bulk' action (confirmed live to have no per-job scoping — see
RepositoryManagementLocators' docstring) precisely to avoid the blast-radius-beyond-your-own-job
risk CLAUDE.md's safety fence warns about.
"""
from __future__ import annotations

import re

from ..base.base_page import BasePage
from .locators import RepositoryManagementLocators as L


class RepositoryManagementPage(BasePage):
    # ---------- navigation ----------
    def open(self):
        """Settings -> Repositories. Lands on the Repositories grid (Repository Name/Details
        columns)."""
        self.click_visible(L.SETTINGS_NAV)
        self.wait(1200)
        self.click_visible(L.REPOSITORIES_SUBNAV)
        self.wait(1800)
        return self

    def open_repository(self, repo_name: str):
        """Click a repository row to open its own detail page."""
        self.click_visible(L.repo_row(repo_name))
        self.wait(1800)
        return self

    def go_back(self):
        """Click the drilldown page's own '<' back button to go up one level (e.g. a backup
        detail page -> its repo's own detail page, or a repo detail page -> the Repositories
        list). ADDED 2026-07-20 (NJM-68621): a drilldown page replaces the Repositories subnav
        tabs with a breadcrumb, so re-calling open()/SETTINGS_NAV+REPOSITORIES_SUBNAV from two
        levels deep does nothing useful (CALIBRATED live: that click sequence timed out
        entirely) — this is the correct way back."""
        self.click_visible(L.BACK_BUTTON)
        self.wait(1200)
        return self

    def open_overflow_menu(self):
        """Open the repo detail page's '...' Management/Maintenance popup (public — check
        scripts that need to read a menu item's state directly, e.g. via
        RepositoryManagementLocators constants, call this before querying).

        Also works, unmodified, on a BACKUP's own detail page (same OVERFLOW_MENU_BUTTON
        locator/class — `.locator("visible=true").first` correctly resolves to that page's
        top-right '...' there too, confirmed live 2026-07-20) which opens a DIFFERENT menu
        (Verify/Repair/Delete, scoped to that one backup) — see delete_all_recovery_points()."""
        self.click_visible(L.OVERFLOW_MENU_BUTTON)
        self.wait(700)
        return self

    # kept as an alias for internal call sites below (was private before the public wrapper
    # above was added for check-script use)
    _open_overflow_menu = open_overflow_menu

    def open_backup(self, machine_or_share_name: str):
        """From a repository detail page's own 'Backups' grid, open one backup's detail page
        (Recovery points list) by its machine/share name.

        ⚠ AMBIGUOUS on a repo with multiple jobs sharing the same source machine — see
        open_backup_by_job()'s docstring (the safe alternative) for the live-confirmed finding
        that prompted it."""
        self.click_visible(L.backup_row_link(machine_or_share_name))
        self.wait(1800)
        return self

    def open_backup_by_job(self, job_name: str):
        """Open a backup's own detail page (Recovery points list) by its Job-column value
        instead of its displayed machine/share Name — ADDED 2026-07-20 (NJM-68621).

        CALIBRATED live: open_backup(name) alone is ambiguous whenever a repository has more
        than one backup sharing the same machine/share display name (e.g. Onboard repository's
        ~7 'Window11'-named backups, one per job that has ever targeted it) — see
        RepositoryManagementLocators.backup_row_link_by_job()'s docstring for the full finding.
        This scopes the click to the grid row whose Job column matches `job_name` exactly."""
        self.click_visible(L.backup_row_link_by_job(job_name))
        self.wait(1800)
        return self

    def recovery_point_count(self, job_name: str | None = None) -> int:
        """Read the 'Points: N' field from a backup's own detail page. Pass `job_name` to
        navigate there first (via open_backup_by_job()); pass nothing to read whichever backup
        detail page is already open. Returns 0 if the field can't be parsed (e.g. wrong page).

        ADDED 2026-07-20 (NJM-68621) — same pragmatic raw-page-text-scan approach as
        immutability_marker_text() (no fixed grid-column locator needed for this simple
        label/value pair); a regex tolerates whatever whitespace/newline ExtJS renders between
        the 'Points:' label and its numeric value."""
        if job_name:
            self.open_backup_by_job(job_name)
        text = self.page.locator("body").inner_text()
        m = re.search(r"Points:\s*(\d+)", text)
        return int(m.group(1)) if m else 0

    def delete_all_recovery_points(self, job_name: str):
        """From an already-open repository detail page (open_repository()), open the backup
        identified by `job_name`, select every recovery point, and attempt to delete them via
        the backup detail page's own top-right '...' -> Delete. ADDED 2026-07-20 (NJM-68621).

        ⚠ Must be called with the repo detail page's own 'Backups' grid as the current page
        (same precondition as open_backup_by_job()/open_backup()) — NOT from an already-open
        backup detail page (e.g. right after a recovery_point_count(job_name) call), since it
        re-navigates via open_backup_by_job() internally, which needs that grid to be present.

        ⚠ CALIBRATED FINDING, live 2026-07-20: this 'Delete' action operates on the WHOLE
        backup object, not on whichever recovery points are checked in the grid — selecting
        only some vs. all of them produced the IDENTICAL result. NBR blocks the action outright
        while ANY job still references the backup:
            'Cannot delete the backup. This backup is used by the following item(s): <job name>'
        This method still drives the full click sequence (open backup -> select-all -> overflow
        -> Delete) and, if that 'Cannot delete the backup' dialog appears, dismisses it via its
        own OK button so it doesn't linger over the page — but it does NOT raise or assert on
        the outcome (this project's convention: no asserts inside a POM method, see CLAUDE.md).
        Callers MUST check recovery_point_count() afterward to learn whether the delete actually
        took effect.

        A repository-wide 'Delete backups in bulk' action exists but was confirmed live to have
        no per-backup/per-job picker at all (see RepositoryManagementLocators' docstring on this
        area) — deliberately NOT used here, since it cannot be scoped to a single job's backup
        without risking every other backup in the repository."""
        self.open_backup_by_job(job_name)
        self.page.locator(L.RECOVERY_POINTS_SELECT_ALL_CHECKBOX).click(force=True)
        self.wait(600)
        self._open_overflow_menu()
        self.click_visible(L.DELETE_THIS_BACKUP)
        self.wait(1000)
        blocked_dialog_ok = self.page.locator(L.CANNOT_DELETE_BACKUP_OK_BUTTON).locator("visible=true")
        if blocked_dialog_ok.count():
            blocked_dialog_ok.first.click()
            self.wait(500)
        return self

    def immutability_marker_text(self) -> str:
        """On an already-open backup detail page (open_backup()), return the 'Immutable until'
        text if present, else ''. ADDED 2026-07-19 (backs NJM-70517/70017/123118/123120/123122/
        123124/123133): the recovery-points grid has an 'Immutable until' column not visible
        without horizontal scroll — CALIBRATED live 2026-07-18 by check_immutability_calibration.py
        via a raw page-text scan; this wraps that same pragmatic approach (no fixed grid-column
        locator needed) as a reusable reader rather than every caller re-scanning inline. No
        assertion here — callers decide what a non-empty/empty result means."""
        text = self.page.locator("body").inner_text()
        idx = text.find("Immutable until")
        return text[idx:idx + 60].strip() if idx >= 0 else ""

    # ---------- readers (no asserts — callers decide) ----------
    def menu_item_visible(self, item_locator: str) -> bool:
        """True if `item_locator` (one of the RepositoryManagementLocators menu-item constants)
        resolves to a VISIBLE node — some items render a second, permanently hidden/disabled
        copy (see locators.py docstring), so this is the reliable enabled/offered signal, not a
        bare .count() on the unscoped locator."""
        return self.page.locator(item_locator).locator("visible=true").count() > 0

    def menu_item_disabled_reason(self, item_locator: str) -> str:
        """The @title tooltip on the (possibly hidden) disabled copy of a menu item — e.g.
        'No space can be reclaimed' for Reclaim unused space, 'The action is not enabled.' for
        the disabled Repair variant. Reads whichever copy exists (visible or not), since the
        reason tooltip only ever lives on the disabled copy."""
        loc = self.page.locator(item_locator)
        return loc.first.get_attribute("title") or "" if loc.count() else ""

    def self_healing_available(self) -> bool:
        """Open the overflow menu and report whether 'Run repository self-healing' is offered
        (rendered+enabled) for the currently-open repository. CALIBRATED finding: this is
        LOCAL-repo-type-only (absent entirely for S3/Azure repos, not just disabled)."""
        self._open_overflow_menu()
        return self.menu_item_visible(L.RUN_SELF_HEALING)

    def reclaim_available(self) -> bool:
        """Open the overflow menu and report whether 'Reclaim unused space' is currently
        enabled (visible) for the open repository — it renders hidden+disabled with the tooltip
        'No space can be reclaimed' whenever there is nothing to reclaim (verified live: this is
        the default/common state, not a bug)."""
        self._open_overflow_menu()
        return self.menu_item_visible(L.RECLAIM_UNUSED_SPACE)

    # ---------- actions ----------
    def run_self_healing(self):
        """Open the overflow menu, click 'Run repository self-healing', confirm the
        'Repository self-healing' dialog's Start button. Caller should then poll the global
        Activities panel (RepositoryManagementLocators.ACTIVITIES_NAV /
        activity_row_text('self-healing')) for a 0%->Completed transition — the repo detail
        page itself shows no in-page progress indicator (see locators.py docstring)."""
        self._open_overflow_menu()
        self.click_visible(L.RUN_SELF_HEALING)
        self.wait(700)
        self.click_visible(L.SELF_HEALING_START_BUTTON)
        self.wait(1500)
        return self

    def reclaim_unused_space(self):
        """Open the overflow menu and click 'Reclaim unused space'. Caller MUST confirm via
        reclaim_available() first — clicking a hidden/disabled copy is a no-op that silently
        times out (same duplicate-node caveat as everywhere else in this app)."""
        self._open_overflow_menu()
        self.click_visible(L.RECLAIM_UNUSED_SPACE)
        self.wait(1500)
        return self

    def verify_all_backups(self):
        self._open_overflow_menu()
        self.click_visible(L.VERIFY_ALL_BACKUPS)
        self.wait(1500)
        return self

    def close_overflow_menu(self):
        """Best-effort dismiss of the overflow popup without acting on it — the popup does not
        appear to respond to Escape (observed live). Clicks a fixed point inside the repo
        detail page's top info panel (Free/Used/etc. — plain text, never a clickable row) to
        avoid the CALIBRATED-live gotcha of accidentally landing on a Backups-grid row further
        down the page (a repo with >=1 backup extends that grid into viewport space a
        lower/blinder click point could hit, silently navigating to the backup's own detail
        page instead of closing the popup — caught live 2026-07-18 via
        check_repository_reclaim_and_selfheal.py's first run)."""
        try:
            self.page.mouse.click(900, 175)
            self.wait(400)
        except Exception:
            pass
        return self

    # ---------- Activities panel (progress/completion for the actions above) ----------
    def open_activities(self):
        self.click_visible(L.ACTIVITIES_NAV)
        self.wait(1500)
        return self

    def activities_text(self) -> str:
        """Flat text dump of the Activities panel (Running + Past Activities) — callers search
        it for a repo/action name and 'Completed'/percentage, matching the pragmatic
        no-fixed-row-structure approach documented on RepositoryManagementLocators."""
        return self.page.locator("body").inner_text()
