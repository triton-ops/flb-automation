"""Foundational layer: BasePage (all Playwright actions), the browser/config driver, and the
transient-failure retry helper. No locators live here — these are primitives every page object
and locator-owning module builds on, not page objects themselves.
"""
