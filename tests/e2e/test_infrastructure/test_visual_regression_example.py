"""Visual regression pattern EXAMPLE (see docs/enterprise-gap-analysis.md's Medium finding). Not
appliance-verification — see docs/visual-regression-pattern.md for why the live Director UI is
deliberately NOT the target here.

Demonstrates Playwright's `expect(page).to_have_screenshot()` pixel-diff mechanism against a
static, self-contained local HTML fixture (no network, no live appliance) so the pattern is
100% reproducible: no ExtJS animation/async-render timing to fight, no ephemeral job/job-status
data to make each screenshot different run-to-run.

First run creates the baseline under tests/e2e/__snapshots__/; every later run pixel-diffs against
it (via tests/e2e/_lib/_visual_regression.py's Pillow-based helper — Python Playwright has no built-in
`to_have_screenshot()`, that's a Playwright Test (JS)-only API) and fails on an unexpected visual
change. Run with `--visual-update-snapshots` once, deliberately, whenever the fixture's own HTML
changes on purpose.
"""
from __future__ import annotations

import pytest

from tests.e2e._lib._visual_regression import assert_matches_snapshot

pytestmark = pytest.mark.visual_regression_example

FIXTURE_HTML = """<!doctype html>
<html><head><style>
  body { margin: 0; font-family: Arial, sans-serif; background: #f4f4f4; }
  .card { margin: 40px; padding: 24px; background: white; border: 1px solid #ccc; width: 300px; }
  h1 { color: #2c3e50; font-size: 20px; }
  .badge { display: inline-block; padding: 4px 10px; background: #27ae60; color: white; border-radius: 4px; }
</style></head>
<body>
  <div class="card">
    <h1>Visual regression fixture</h1>
    <span class="badge">Stable</span>
  </div>
</body></html>"""


def test_static_fixture_visual_regression(page, request):
    page.set_content(FIXTURE_HTML)
    page.wait_for_timeout(100)  # let the (trivial, static) layout settle
    # Scoped to the .card element, not the whole page — see assert_matches_snapshot()'s docstring
    # on why a full-viewport screenshot would dilute this fixture's small badge-color change.
    assert_matches_snapshot(page.locator(".card"), "fixture-card.png", request)
