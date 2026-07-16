"""Phase-1 skeleton smoke test.

Proves the fixture chain (browser context, login, config) works end-to-end BEFORE any POM gaps
are filled or real Jira TCs are ported. Not itself a Jira test case — infra-only.
"""
from __future__ import annotations

from browser.pom.backup_types.flb_wizard_page import FlbWizardPage
from browser.pom.common.data_protection_page import DataProtectionPage


def test_flb_wizard_opens(logged_in_page):
    """Login succeeds and the New File Level Backup Job wizard opens on its Source step."""
    DataProtectionPage(logged_in_page).open().open_create_menu().start_file_level_backup()
    flb = FlbWizardPage(logged_in_page).on_sources_step()

    title = flb.current_step_title()
    assert title.strip().startswith("1"), f"expected wizard to land on step 1 (Source), got {title!r}"

    flb.click_cancel()
