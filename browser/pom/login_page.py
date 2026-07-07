"""LoginPage — Director sign-in. XPath selectors in locators.LoginLocators."""
from __future__ import annotations

from .base_page import BasePage
from .locators import LoginLocators as L


class LoginPage(BasePage):
    def open(self, url: str):
        self.goto(url)
        return self

    def login(self, user: str, password: str):
        self.fill(L.USERNAME, user)
        self.fill(L.PASSWORD, password)
        self.click(L.SUBMIT)
        self.wait_idle()
        self.wait(3000)
        return self
