# Visual regression: the pattern, and why it targets a static fixture, not the live Director UI

`docs/enterprise-gap-analysis.md` flagged visual regression testing as a Medium-severity gap.
`tests/e2e/test_infrastructure/test_visual_regression_example.py` demonstrates the mechanism — verified live: a clean
baseline passes on re-run, and a deliberately changed fixture (badge color swapped) was caught with
a real measured 3.71% pixel-diff against a 1% threshold, then reverted.

## Why the demo targets a static local fixture, not the live ExtJS UI

This project's own recurring, documented pain point is that the Director UI is a live, animating,
timing-sensitive ExtJS app — ripe with hidden duplicate DOM panels, async-rendered content, and
per-load layout differences (see `CLAUDE.md`'s Golden Rule 2 on ExtJS drift, and the POM's
extensive `wait_for`/calibrated-timeout usage throughout `browser/pom/`). Screenshot-diffing that
UI directly would be exactly as flaky as the interaction code already has to work around — a
visual regression suite whose baselines drift out of sync with harmless animation timing produces
noise, not signal, and erodes trust in the whole suite fast.

The fixture used here (`FIXTURE_HTML` in the test file) is fully static and self-contained
(`page.set_content(...)`, no network, no live appliance) specifically so the mechanism itself could
be proven deterministic and reliable before ever being pointed at something that isn't.

## The mechanism

Python Playwright has **no built-in `expect(page).to_have_screenshot()`** — that convenience API is
Playwright Test (JS/TS)-only. `tests/e2e/_lib/_visual_regression.py`'s `assert_matches_snapshot()` is a
small, self-contained replacement built on Pillow:

1. Screenshot the target (a `Page` or, preferably, a scoped `Locator` — see below).
2. If `tests/e2e/__snapshots__/<name>` doesn't exist yet (or `--visual-update-snapshots` was
   passed), write it as the new baseline and pass.
3. Otherwise, pixel-diff against the baseline (`PIL.ImageChops.difference` converted to grayscale,
   `.histogram()` to count differing pixels — chosen because Pillow's type stubs don't model
   `.getdata()`'s iteration correctly for mypy) and assert the differing fraction is
   `<= max_diff_ratio` (default 1%).

**Scope to a Locator, not the whole Page.** The first verification attempt screenshotted the full
viewport and a real, deliberate color change to a small badge element didn't trip the 1% threshold
— diluted by all the unchanged surrounding page. `page.locator(".card").screenshot()` (scoped to
just the element under test) is what actually caught it. Any real usage of this pattern should
screenshot the specific panel/component being tested, not the full page.

## Baselines are committed

`tests/e2e/__snapshots__/*.png` is deliberately **not** gitignored — a baseline with nothing to
compare against isn't a regression test, it's a no-op. Regenerate deliberately with
`--visual-update-snapshots` whenever a fixture's own expected appearance changes on purpose, and
review the diff in the PR like any other change.

## Applying this to the real Director UI (not attempted here)

If this is extended to actual ExtJS pages, do it incrementally and expect to spend real calibration
time on stability, the same way every other POM method here was calibrated live:

- Screenshot a scoped, structurally stable `Locator` (e.g. a static panel header), never the whole
  page — the same lesson as above applies, doubled, against a much less predictable UI.
- Expect to raise `max_diff_ratio` and/or mask genuinely dynamic regions (timestamps, job-status
  badges, counts) — a real Allure precedent for exactly this kind of instability already exists in
  this codebase's calibration comments (e.g. `FileLevelRecoveryPage`'s folder-size async-render
  note).
- Start with ONE low-traffic, visually static area (a wizard step's static header/label region, not
  a live-updating dashboard row) before ever expanding coverage.
