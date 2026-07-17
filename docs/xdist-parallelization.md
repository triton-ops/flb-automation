# Parallelization: why not `-n auto`, and the safe alternative

`docs/enterprise-gap-analysis.md` explicitly rejected *full* `pytest-xdist` adoption as a "not a
gap" — this project's own established finding is that concurrent jobs against the **same source
VID** lock/stall rather than queue (see `[[no-concurrent-jobs-same-source]]` in memory, and
`tests/e2e/test_flbv2v3_Inventory/_helpers.py`'s own module docstring). Blindly running
`pytest -n auto` would schedule tests onto workers with no awareness of which physical
machine/source each test targets, and two tests hitting the same source at once produce a false
failure that has nothing to do with the product under test.

The Medium-severity finding this doc addresses is narrower: a **safe, partial** parallelization
strategy exists via `pytest-xdist`'s `--dist loadgroup` mode, which guarantees every test carrying
the same `@pytest.mark.xdist_group(name=...)` value lands on the same worker (and therefore never
runs concurrently with its group-mates), while tests in *different* groups (different, independent
sources) can run in parallel across workers.

## Status: opt-in, not enabled by default

- `pytest-xdist` is **not** in `requirements-dev.txt`'s default set and **not** wired into
  `pyproject.toml`'s `addopts` — plain `pytest tests/e2e/...` behaves exactly as it does today,
  fully sequential.
- Two real, already-documented shared-source pairs have been tagged as a concrete demonstration:
  `NJM-67807` and `NJM-68933` (both target `Linux_16.84`/PM-2) now carry
  `pytest.mark.xdist_group(name="Linux_16.84")` in
  `tests/e2e/test_flbv2v3_Inventory/test_njm_67807.py` /
  `tests/e2e/test_flbv2v3_Inventory/test_njm_68933.py` (and the equivalent parametrized case in
  `test_njm_67806_67809_linux_os_matrix.py`, since it also runs against `Linux_16.84`). The marker
  is inert unless xdist is actually invoked with `--dist loadgroup` — it changes nothing about a
  normal sequential run.
- This has **not** been live-verified running actual parallel workers against the appliance (that
  would mean deliberately exercising the exact concurrent-access scenario this project's own
  findings warn against, just to prove the safeguard works) — the marker's *correctness* was
  confirmed via `--collect-only` and normal sequential execution only.

## How to use it, if/when parallel execution is wanted

1. `pip install pytest-xdist` (add to `requirements-dev.txt` if adopted permanently).
2. Tag every test that shares a source machine/VID with the same
   `@pytest.mark.xdist_group(name="<machine-name>")` value. A test with no shared source doesn't
   need the marker — it'll be scheduled freely.
3. Run with: `pytest tests/e2e -n auto --dist loadgroup`

## Before adopting this beyond the two demonstrated cases

Every suite's `_helpers.py` should be checked for its own "shared source" notes (grep for
"concurrently" across `tests/e2e/`) and each pair/group tagged the same way — this doc intentionally
tags only the one pair already known and documented, not a blanket audit of every suite.
