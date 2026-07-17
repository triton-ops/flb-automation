"""Minimal, self-contained visual-regression helper (Pillow pixel diff — no third-party pytest
plugin, since Python Playwright has no built-in `to_have_screenshot()`; that's a Playwright Test
(JS) only API — see docs/visual-regression-pattern.md for the full writeup of why this exists.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageChops

# parent.parent: this module lives in tests/e2e/_lib/, but baselines are scoped to all of
# tests/e2e/ (not just _lib/), so they live at tests/e2e/__snapshots__/.
SNAPSHOTS_DIR = Path(__file__).resolve().parent.parent / "__snapshots__"


def assert_matches_snapshot(target, name: str, request, max_diff_ratio: float = 0.01) -> None:
    """Screenshot `target` (a Page or Locator — both expose .screenshot()), compare to
    `tests/e2e/__snapshots__/<name>`. Creates the baseline (and passes) if it doesn't exist yet,
    or if run with --visual-update-snapshots. Otherwise asserts the fraction of differing pixels
    is <= max_diff_ratio. Prefer a Locator scoped to the element under test over the whole Page —
    a full-viewport screenshot dilutes a real, localized visual change well below any sane
    max_diff_ratio threshold."""
    SNAPSHOTS_DIR.mkdir(exist_ok=True)
    baseline_path = SNAPSHOTS_DIR / name
    actual_bytes = target.screenshot()

    if not baseline_path.exists() or request.config.getoption("--visual-update-snapshots"):
        baseline_path.write_bytes(actual_bytes)
        return

    import io
    baseline = Image.open(baseline_path).convert("RGB")
    actual = Image.open(io.BytesIO(actual_bytes)).convert("RGB")
    assert actual.size == baseline.size, (
        f"snapshot size mismatch for {name}: baseline={baseline.size}, actual={actual.size}"
    )
    # .histogram() (well-typed: list[int]) avoids .getdata()'s iteration, which Pillow's type
    # stubs don't model correctly (its ImagingCore isn't recognized as Iterable by mypy).
    diff_histogram = ImageChops.difference(baseline, actual).convert("L").histogram()
    total_pixels = baseline.size[0] * baseline.size[1]
    diff_pixels = total_pixels - diff_histogram[0]
    diff_ratio = diff_pixels / total_pixels
    assert diff_ratio <= max_diff_ratio, (
        f"{name}: {diff_ratio:.2%} of pixels differ from the baseline (threshold {max_diff_ratio:.2%}) "
        f"— re-run with --visual-update-snapshots if this change is intentional"
    )
