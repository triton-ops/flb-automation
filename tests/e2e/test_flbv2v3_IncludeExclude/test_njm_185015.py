"""NJM-185015 — [FLB v3] FLB Job Wizard - Step 2/3 - Parameter box limits: 5000 chars total,
255 (Win) / 4095 (Linux) per path (FLB-11/FLB-12). Original status: PENDING.
UI-behavior/validation check — needs BOTH a Windows and a Linux source.

Per the NAS Backup Confluence spec (https://confluence.nakivo.com/display/tst/NAS+Backup, which
File Level Backup's own spec explicitly reuses for Inclusion/Exclusion): "Maximum length 5000
characters per the whole text box" and "Path length shall be limited by: 255 characters for
Windows, 4095 characters for Linux."

CALIBRATED live 2026-07-15/16: confirmed live that this build does NOT enforce the 5000-character
total cap — content well beyond 5000 chars is accepted in full (185015a). The per-path limits are
enforced ASYMMETRICALLY: Windows' 255-char limit IS enforced (185015b correctly rejects a 257-char
path), but Linux's 4095-char limit is NOT — a 4097-char path reaches the textarea untouched (ruled
out silent truncation by reading back the raw textarea value) and still advances the wizard
(185015c). Both gaps are reported as explicit FAILs (not silently passed or reworded to match
observed behavior), same honest-reporting approach used elsewhere in this suite for spec gaps.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.backup_types.flb_wizard_page import FlbWizardPage
from browser.pom.common.data_protection_page import DataProtectionPage
from browser.pom.common.locators import InclusionExclusionLocators as IE

from ._helpers import LINUX_MACHINE, open_to_inclusion

pytestmark = [pytest.mark.flb, pytest.mark.include_exclude, pytest.mark.jira("NJM-185015")]


@allure.title("NJM-185015a — parameter box total-length cap (5000 chars) — NOT enforced")
def test_parameter_total_char_limit(logged_in_page):
    page = logged_in_page
    flb = open_to_inclusion(page)

    # 60 lines * 99 chars (each well under the 255-char per-path limit) joined by 59 newlines is
    # 5999, not 6000 (the (N-1) newline count is one short of the naive N*100 estimate) — pad the
    # last line by one char to land on exactly 6000.
    total_6000 = "\n".join(["a" * 99] * 60)
    total_6000 += "a" * (6000 - len(total_6000))
    assert len(total_6000) == 6000
    flb.enable_inclusion([total_6000])
    textarea = flb.page.locator(IE.INCLUDE_TEXTAREA).locator("visible=true").first
    accepted_len = len(textarea.input_value())
    assert accepted_len <= 5000, (
        f"spec expects the textarea to cap total input at 5000 chars; this build accepted "
        f"{accepted_len} chars (no cap enforced)"
    )
    flb.click_cancel()


@allure.title("NJM-185015b — Windows per-path limit (255 chars)")
def test_parameter_windows_path_limit(logged_in_page):
    page = logged_in_page
    win_path_257 = "C:\\" + ("a" * 254)  # "C:\" is 3 chars + 254 = 257 total
    assert len(win_path_257) == 257
    flb = open_to_inclusion(page)
    flb.enable_inclusion([win_path_257])
    assert not flb.inclusion_advances_wizard(), "a 257-char Windows path should exceed the 255-char limit"
    flb.click_cancel()


@allure.title("NJM-185015c — Linux per-path limit (4095 chars) — NOT enforced (spec deviation)")
def test_parameter_linux_path_limit(logged_in_page):
    page = logged_in_page
    linux_path_4097 = "/" + ("a" * 4096)
    assert len(linux_path_4097) == 4097
    DataProtectionPage(page).open().open_create_menu().start_file_level_backup()
    flbl = FlbWizardPage(page).on_sources_step()
    flbl.expand_linux()
    flbl.select_machine(LINUX_MACHINE)
    flbl.open_item_picker()
    flbl.select_items([], ["TestData_ForFLB"])
    flbl.picker_apply()
    flbl.click_next()
    flbl.enable_inclusion([linux_path_4097])
    # Corroborate with the raw textarea content (same technique as 185015a) so a "silently
    # truncated to the compliant 4095-char length" explanation is ruled out, not assumed, before
    # concluding the limit isn't enforced at all.
    textarea = flbl.page.locator(IE.INCLUDE_TEXTAREA).locator("visible=true").first
    accepted_len = len(textarea.input_value())
    advanced = flbl.inclusion_advances_wizard()
    assert accepted_len == 4097, (
        f"expected the full 4097-char path to reach the textarea untouched, got {accepted_len} "
        f"chars — if this is exactly 4095, the build truncates rather than rejects outright"
    )
    assert not advanced, "a 4097-char Linux path should exceed the 4095-char limit"
    flbl.click_cancel()
