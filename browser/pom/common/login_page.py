"""LoginPage — Director sign-in. XPath selectors in locators.LoginLocators."""
from __future__ import annotations

from ..base.base_page import BasePage
from .locators import LoginLocators as L


class LoginPage(BasePage):
    def open(self, url: str):
        self.goto(url)
        return self

    def login(self, user: str, password: str):
        """CALIBRATED live 2026-07-22: post-submit used to wait via BasePage.wait_idle()
        (page.wait_for_load_state("networkidle")), which reliably timed out (20s) as this
        appliance's own Activities/Issues load has grown (53 Issues, 17 Jobs at time of
        finding) — the post-login Overview dashboard has enough ongoing background polling
        that it may never go fully network-idle. Confirmed via direct screenshot: login itself
        succeeds and lands on /c/overview well within a few seconds every time; only the
        strict networkidle wait afterward was the failure. Replaced with a wait for the URL to
        actually leave the login page — deterministic and doesn't depend on background network
        activity settling."""
        self.fill(L.USERNAME, user)
        self.fill(L.PASSWORD, password)
        self.click(L.SUBMIT)
        self.page.wait_for_url(lambda url: "/c/" in url, timeout=20000)
        self.wait(3000)
        return self
