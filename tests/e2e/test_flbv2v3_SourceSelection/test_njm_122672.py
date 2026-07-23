r"""NJM-122672 — [FLB v1/v2] FLB Job Wizard - Source Step (UI): a folder with fewer than 200 items
lists them all in the 'Select Items' dialog, with no '>200' banner.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.backup_types.flb_wizard_page import FlbWizardPage
from browser.pom.common.data_protection_page import DataProtectionPage

pytestmark = [
    pytest.mark.flb, pytest.mark.sourceselection, pytest.mark.jira("NJM-122672"),
    pytest.mark.xdist_group(name="Window11"),
]

MACHINE = "Window11"


def _open_picker(page) -> FlbWizardPage:
    DataProtectionPage(page).open().open_create_menu().start_file_level_backup()
    flb = FlbWizardPage(page).on_sources_step()
    flb.expand_windows()
    flb.select_machine(MACHINE)
    flb.open_item_picker()
    flb.wait(1500)
    return flb


@allure.title("NJM-122672 — folder with fewer than 200 items lists them all, no banner")
def test_item_display_fewer_than_200(logged_in_page):
    page = logged_in_page
    flb = _open_picker(page)
    flb.picker_drill("Local Disk (C:)")
    flb.picker_drill("SpecialFiles_ForFLB")  # this suite's own fixture: 13 items, well under 200
    flb.wait(800)
    names = [n for n in flb.picker_row_names() if n != "[..]"]
    assert 0 < len(names) < 200, f"expected a small item count, got {len(names)}: {names}"
    assert not flb.picker_over_200_message_shown(), "the >200 banner should NOT show for a small folder"
    flb.click_cancel()
    flb.click_cancel()
