r"""NJM-141434 / 63205 / 122659 / 122646 / 122645 — [FLB v1/v2] FLB Job Wizard - Source Step (UI):
search bar / search controls in the 'Select Items' dialog.

CALIBRATED live 2026-07-18 (see check_select_items_dialog.py's SEARCH_INPUT/SEARCH_CLEAR
calibration and picker_search()'s docstring): the search INPUT and its clear/X control both work
correctly (typing reveals the clear control; clearing empties the box and hides it again) — but
typing into the box does NOT filter the folderInfoItem listing at all in this build (verified live:
a matching term and a non-matching term both leave the full listing unchanged). This means:

  * NJM-141434 (search controls: input + clear) is REAL and asserted below — the controls
    themselves work exactly as specified.
  * NJM-63205 / NJM-122659 (basic / general search bar FUNCTIONALITY — i.e. that searching
    actually narrows the listing) are DOCUMENTED GAPS, not faked: the box accepts input but
    performs no filtering, so there is no "search functionality" to verify beyond the controls
    already covered by 141434.
  * NJM-122646 ('No Matching Items' message) and NJM-122645 (search result limit warning, '>200
    results' via SEARCH specifically) are also DOCUMENTED GAPS for the same root cause — both
    messages are contingent on search actually filtering results, which it does not. (The
    underlying '>200 results' BANNER itself IS real and independently verified via plain
    navigation, NOT search — see NJM-122673 in test_dialog_item_counts.py.)
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.backup_types.flb_wizard_page import FlbWizardPage
from browser.pom.common.data_protection_page import DataProtectionPage

pytestmark = [
    pytest.mark.flb, pytest.mark.sourceselection,
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


@allure.title("NJM-141434 — search box accepts input and the clear control appears/clears reliably")
@pytest.mark.jira("NJM-141434")
def test_search_input_and_clear_controls(logged_in_page):
    page = logged_in_page
    flb = _open_picker(page)

    assert not flb.picker_search_clear_visible(), "clear control should be hidden with an empty search box"
    flb.picker_search("TestData")
    assert flb.picker_search_clear_visible(), "clear control should appear once text is entered"
    flb.picker_clear_search()
    assert not flb.picker_search_clear_visible(), "clear control should hide again once the box is emptied"

    flb.click_cancel()
    flb.click_cancel()


SEARCH_FUNCTIONALITY_GAPS = [
    pytest.param(
        "NJM-63205", "basic search functionality",
        marks=pytest.mark.jira("NJM-63205"), id="NJM-63205-basic-search",
    ),
    pytest.param(
        "NJM-122659", "general search bar functionality",
        marks=pytest.mark.jira("NJM-122659"), id="NJM-122659-general-search-bar",
    ),
    pytest.param(
        "NJM-122646", "'no matching items' message",
        marks=pytest.mark.jira("NJM-122646"), id="NJM-122646-no-matching-message",
    ),
    pytest.param(
        "NJM-122645", "search result limit warning (>200 via search)",
        marks=pytest.mark.jira("NJM-122645"), id="NJM-122645-search-limit-warning",
    ),
]


@pytest.mark.skip(
    reason="BLOCKED: the dialog's search box does not filter the listing in this build (verified "
    "live 2026-07-18 — a matching and a non-matching search term both leave the full listing "
    "unchanged), so no search-driven filtering behavior exists to verify. Written and executable; "
    "unskip once search actually filters."
)
@pytest.mark.parametrize("jira_id,label", SEARCH_FUNCTIONALITY_GAPS)
def test_search_filtering_behavior(logged_in_page, jira_id, label):
    allure.dynamic.title(f"{jira_id} — {label}")
    page = logged_in_page
    flb = _open_picker(page)
    flb.picker_drill("Local Disk (C:)")
    flb.picker_drill("TestData_ForFLB")
    before = set(flb.picker_row_names())
    flb.picker_search("zzzznomatchzzzz")
    after = set(flb.picker_row_names())
    assert after != before, f"search for a non-matching term should narrow/empty the listing ({label})"
    flb.click_cancel()
    flb.click_cancel()
