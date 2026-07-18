r"""NJM-67569 / 67570 / 67571 — [FLB v1] FLB Job Wizard - Destination Step - Verify Wasabi / Amazon
S3 / Azure Blob Repository is a Supported Target.

Lightweight wizard-navigation checks, NOT full backup runs: reach the Destination step, select
each cloud repository, and confirm it's selectable without error. No job is ever Finished (Cancel
out after confirming selection succeeded) — this only proves the repository TYPE is offered/
selectable as a destination, which is exactly what these TCs ask for; the "does a real backup to
it actually succeed" question is covered separately by test_repo_backup_matrix.py.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.backup_types.flb_wizard_page import FlbWizardPage
from browser.pom.common.data_protection_page import DataProtectionPage
from browser.pom.common.locators import SelectItemsLocators as SI

pytestmark = [
    pytest.mark.flb, pytest.mark.objectstorage,
    pytest.mark.xdist_group(name="Window11"),
]

MACHINE = "Window11"

SUPPORTED_TARGET_TCS = [
    pytest.param("NJM-67569", "Wasabi_Repo", marks=pytest.mark.jira("NJM-67569"), id="NJM-67569-wasabi"),
    pytest.param("NJM-67570", "Amazon_Repo", marks=pytest.mark.jira("NJM-67570"), id="NJM-67570-s3"),
    pytest.param("NJM-67571", "Azure_Repo", marks=pytest.mark.jira("NJM-67571"), id="NJM-67571-azure"),
]


@pytest.mark.parametrize("jira_id,repo_name", SUPPORTED_TARGET_TCS)
def test_repository_is_supported_target(logged_in_page, jira_id, repo_name):
    allure.dynamic.title(f"{jira_id} — {repo_name} is a selectable Destination-step target")
    page = logged_in_page
    DataProtectionPage(page).open().open_create_menu().start_file_level_backup()
    flb = FlbWizardPage(page).on_sources_step()
    flb.expand_windows()
    flb.select_machine(MACHINE)
    flb.open_item_picker()
    flb.wait(1500)
    flb.picker_drill("Local Disk (C:)")
    flb.picker_drill("SpecialFiles_ForFLB")
    flb.click_force(SI.checkbox("Makefile"))
    flb.wait(500)
    flb.picker_apply()
    flb.click_next()  # Inclusion
    flb.click_next()  # Exclusion
    flb.click_next()  # -> Destination

    # select_repository() already asserts nothing itself — if the repo weren't selectable this
    # would raise a Playwright timeout, which is the real failure signal for this TC.
    flb.select_repository(repo_name)
    flb.click_cancel()
