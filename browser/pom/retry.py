"""retry_on_transient — small, reusable retry-with-backoff helper for genuinely transient
failures (browser startup, temporary network blips). Single responsibility, used by driver.py
and available to any page-object action that needs it.

Deliberately NOT used to paper over product defects or flaky selectors — those need fixing at
the source (calibration), not masking with retries. See CLAUDE.md rule 5 (honest reporting).
"""
from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def retry_on_transient(
    fn: Callable[[], T],
    attempts: int = 3,
    base_delay_s: float = 1.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> T:
    """Call fn() up to `attempts` times with exponential backoff, re-raising the last error.

    Example: retry_on_transient(lambda: pw.chromium.launch(headless=True), attempts=3)
    """
    last_exc: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except exceptions as exc:  # noqa: PERF203 — retry loops inherently re-try in the loop
            last_exc = exc
            if attempt == attempts:
                break
            time.sleep(base_delay_s * (2 ** (attempt - 1)))
    assert last_exc is not None
    raise last_exc
