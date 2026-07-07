"""BasePage — the SINGLE place for all Playwright interaction methods.

Every page object inherits this and calls these wrappers only (never `self.page.<api>`
directly). Centralizing the Playwright API here means UI-driver changes, logging, retries,
or waits are maintained in ONE file. Selectors live in locators.py; data in config/ui_values.json.
"""
from __future__ import annotations

import re
from pathlib import Path

from .driver import SHOTS_DIR


class BasePage:
    def __init__(self, page):
        self.page = page

    # --- navigation ---
    def goto(self, url: str, wait_until: str = "domcontentloaded"):
        self.page.goto(url, wait_until=wait_until)
        return self

    # --- waits ---
    def wait(self, ms: int = 2000):
        self.page.wait_for_timeout(ms)
        return self

    def wait_idle(self):
        self.page.wait_for_load_state("networkidle")
        return self

    def wait_for(self, selector: str, timeout: int = 20000):
        self.page.locator(selector).first.wait_for(timeout=timeout)
        return self

    def wait_masks_gone(self, timeout: int = 15000):
        """Poll until no VISIBLE ExtJS loading mask (div.x-mask) remains — masks intercept
        pointer events (e.g. after drilling into a folder in the Select Items dialog)."""
        deadline = timeout
        step = 300
        waited = 0
        while waited < deadline:
            try:
                vis = self.page.locator("//div[contains(@class,'x-mask')]").locator("visible=true").count()
            except Exception:
                vis = 0
            if vis == 0:
                return self
            self.page.wait_for_timeout(step)
            waited += step
        return self

    # --- actions ---
    def fill(self, selector: str, value: str):
        self.page.locator(selector).first.fill(value)
        return self

    def click(self, selector: str, timeout: int = 15000):
        self.page.locator(selector).first.click(timeout=timeout)
        return self

    def click_text(self, text: str, exact: bool = False, timeout: int = 15000):
        self.page.get_by_text(text, exact=exact).first.click(timeout=timeout)
        return self

    def click_text_cs(self, text: str, timeout: int = 15000):
        """Case-SENSITIVE substring text click — picks 'Backup copy' (menu item), not the
        all-caps 'BACKUP COPY JOB' section header. Use for create-menu items."""
        self.page.get_by_text(re.compile(re.escape(text))).first.click(timeout=timeout)
        return self

    def click_xy(self, x: int, y: int):
        self.page.mouse.click(x, y)
        return self

    # --- ExtJS-friendly variants ---
    def click_force(self, selector: str, timeout: int = 10000):
        """Click bypassing visibility/actionability — needed for ExtJS inputs that are
        styled/covered (e.g. x-tree-checkbox, hover-revealed icons)."""
        self.page.locator(selector).first.click(timeout=timeout, force=True)
        return self

    def hover(self, selector: str, timeout: int = 10000):
        self.page.locator(selector).first.hover(timeout=timeout)
        return self

    def dispatch_click(self, selector: str):
        """Last-resort click via DOM event (for elements ExtJS shows only on hover)."""
        self.page.locator(selector).first.dispatch_event("click")
        return self

    def click_visible(self, selector: str, timeout: int = 10000):
        """Click the first VISIBLE match. ExtJS renders every wizard step in the DOM at once,
        so a plain .first often resolves a hidden duplicate — filter to visible first."""
        loc = self.page.locator(selector).locator("visible=true")
        loc.first.click(timeout=timeout)
        return self

    def reveal_and_click(self, hover_selector: str, click_selector: str):
        """Hover a container to reveal an icon, then click it (force, then dispatch fallback)."""
        try:
            self.hover(hover_selector, timeout=5000)
            self.wait(400)
        except Exception:
            pass
        try:
            self.click_force(click_selector, timeout=4000)
        except Exception:
            self.dispatch_click(click_selector)
        return self

    def type_into(self, selector: str, value: str):
        loc = self.page.locator(selector).first
        loc.click()
        loc.fill("")
        loc.type(value)
        return self

    # --- queries ---
    def exists(self, selector: str) -> bool:
        return self.page.locator(selector).count() > 0

    def is_visible(self, selector: str) -> bool:
        loc = self.page.locator(selector).first
        return bool(loc.count()) and loc.is_visible()

    def is_disabled(self, selector: str) -> bool | None:
        loc = self.page.locator(selector).first
        return loc.is_disabled() if loc.count() else None

    def text_present(self, text: str) -> bool:
        return self.page.get_by_text(text, exact=False).count() > 0

    def get_text(self, selector: str) -> str:
        loc = self.page.locator(selector).first
        return loc.inner_text() if loc.count() else ""

    # --- evidence ---
    def screenshot(self, name: str, subdir: str | None = None) -> Path:
        out_dir = SHOTS_DIR / subdir if subdir else SHOTS_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        p = out_dir / name
        self.page.screenshot(path=str(p), full_page=False)
        return p
