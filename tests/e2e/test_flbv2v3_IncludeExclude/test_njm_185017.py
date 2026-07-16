"""NJM-185017 — [FLB v3] FLB Job Wizard - Step 2/3 - Entry rules: one item per line, empty line
ignored, duplicate lines treated as one (FLB-11/FLB-12). Original status: PENDING. UI-behavior
check.

Per the NAS Backup Confluence spec (https://confluence.nakivo.com/display/tst/NAS+Backup, which
File Level Backup's own spec explicitly reuses for Inclusion/Exclusion): "Only one parameter
shall be allowed in a line", "If a line is left empty, shall be considered as no value to check",
and "If the same parameter(s) are added to the text box in different lines, the product shall
treat them as one parameter."
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import open_to_inclusion

pytestmark = [pytest.mark.flb, pytest.mark.include_exclude, pytest.mark.jira("NJM-185017")]


@allure.title("NJM-185017a — a blank line between entries does not block Next")
def test_blank_line_between_entries(logged_in_page):
    flb = open_to_inclusion(logged_in_page)
    flb.enable_inclusion(["*.docx", "", "*.pdf"])
    assert flb.inclusion_advances_wizard(), "a blank line between entries should not block Next"


@allure.title("NJM-185017b — duplicate lines collapse to one parameter, not an error")
def test_duplicate_lines_collapse(logged_in_page):
    flb = open_to_inclusion(logged_in_page)
    flb.enable_inclusion(["*.pdf", "*.pdf", "*.pdf"])
    assert flb.inclusion_advances_wizard(), "duplicate lines should collapse to one parameter, not error"
