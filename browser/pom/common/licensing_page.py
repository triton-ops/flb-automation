"""LicensingPage — Settings -> Licensing area, READ-ONLY. CALIBRATED live 2026-07-21 against
nbr-84 (NJM-182729 suite L, "UI/UX / l10n / reporting" — first POM coverage for this area).

⚠ SAFETY: this class deliberately has no Change-License caller. Changing the appliance's license
edition is an APPLIANCE-WIDE action affecting every job on nbr-84, not just this session's own
AUTO_FLB_* entities — see CLAUDE.md Golden Rule 3 and this suite's test_njm_70027/70024/70022
skip-stubs for the full reasoning. Only ever read this page's text.

nbr-84's license, confirmed live 2026-07-21: Trial / Enterprise Plus edition, EXPIRED (10-day
grace period active). Workload counts under "Per-workload subscription licensing" read as
"Workloads — N out of unlimited used" — there is no finite cap on this license (see
test_njm_70026.py for the TC this rules out).
"""
from __future__ import annotations

import re

from ..base.base_page import BasePage
from .locators import ci_exact


class LicensingLocators:
    SETTINGS_NAV = ci_exact("Settings")
    LICENSING_SUBNAV = ci_exact("Licensing")


class LicensingPage(BasePage):
    def open(self):
        """Settings -> Licensing. Lands on the License Details page."""
        self.click_visible(LicensingLocators.SETTINGS_NAV)
        self.wait(1200)
        self.click_visible(LicensingLocators.LICENSING_SUBNAV)
        self.wait(1500)
        return self

    def workloads_used(self) -> int | None:
        """Parse 'Workloads — N out of ... used' from the page text. Returns None if the line
        isn't found (e.g. this license edition doesn't expose per-workload subscription
        licensing at all)."""
        text = self.page.locator("body").inner_text()
        match = re.search(r"Workloads\s*\n?\s*(\d+)\s*out of", text)
        return int(match.group(1)) if match else None
