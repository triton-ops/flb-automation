r"""NJM-182442 — [FLB v2] FLB Job Wizard - Source Step (UI): "Selected Items Expanded + Millions of
Folders/Files View" — a DOCUMENTED, impractical-to-reproduce gap.

Seeding millions of files is out of this framework's small-seeded-fileset convention (same
reasoning as NJM-68975) and would flood the repository; skipped, not faked. Written and executable
against a hypothetical millions-scale fixture.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.backup_types.flb_wizard_page import FlbWizardPage
from browser.pom.common.data_protection_page import DataProtectionPage
from browser.pom.common.locators import SelectItemsLocators as SI

pytestmark = [
    pytest.mark.flb, pytest.mark.sourceselection, pytest.mark.jira("NJM-182442"),
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


@pytest.mark.skip(
    reason="Impractical to reproduce: seeding millions of files is out of this framework's "
    "small-seeded-fileset convention (same reasoning as NJM-68975) and would flood the repository. "
    "Written and executable against a hypothetical millions-scale fixture; not run by default."
)
@allure.title("NJM-182442 — Selected Items panel remains usable with millions of folders/files")
def test_selected_items_expanded_with_millions_of_items(logged_in_page):
    page = logged_in_page
    flb = _open_picker(page)
    flb.picker_drill("Local Disk (C:)")
    flb.picker_drill("MillionsScale_ForFLB")  # hypothetical fixture — does not exist
    flb.wait(2000)
    names = [n for n in flb.picker_row_names() if n != "[..]"][:2]
    for n in names:
        flb.click_force(SI.checkbox(n))
    flb.picker_toggle_selected_items()
    assert flb.picker_selected_items_panel_expanded()
    flb.click_cancel()
    flb.click_cancel()
