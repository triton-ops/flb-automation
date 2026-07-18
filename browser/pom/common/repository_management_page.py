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
"""
from __future__ import annotations

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

    def open_overflow_menu(self):
        """Open the repo detail page's '...' Management/Maintenance popup (public — check
        scripts that need to read a menu item's state directly, e.g. via
        RepositoryManagementLocators constants, call this before querying)."""
        self.click_visible(L.OVERFLOW_MENU_BUTTON)
        self.wait(700)
        return self

    # kept as an alias for internal call sites below (was private before the public wrapper
    # above was added for check-script use)
    _open_overflow_menu = open_overflow_menu

    def open_backup(self, machine_or_share_name: str):
        """From a repository detail page's own 'Backups' grid, open one backup's detail page
        (Recovery points list) by its machine/share name."""
        self.click_visible(L.backup_row_link(machine_or_share_name))
        self.wait(1800)
        return self

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
