# When (and how) to use `@pytest.mark.parametrize` in this framework

`docs/enterprise-gap-analysis.md` flagged zero `parametrize` usage across `tests/e2e/` as a High
finding, and named `tests/e2e/test_flbv2v3_Inventory/test_njm_67806.py` through `test_njm_67809.py`
(OS-support end-to-end workflow on Debian 12 / Ubuntu 24.04 / RHEL 9 / SLES 15 — 100% identical
bodies, differing only in machine name and checksum manifest) as the clearest case. That group has
since been consolidated into
`tests/e2e/test_flbv2v3_Inventory/test_njm_67806_67809_linux_os_matrix.py` as the one demonstrated
example — re-verified live against all four real sources post-consolidation. The other ~90 TC files
in `tests/e2e/` were deliberately left as-is. This doc explains both halves of that decision.

## Why this isn't a blanket migration

This project's one-file-per-Jira-TC convention exists for a real reason: `cases/<Suite>/NJM-<id>.md`
runbooks, Jira lookups, and `pytest -k NJM-<id>` all assume a TC maps to something you can find and
reason about independently. Naively parametrizing collapses that — a bare
`@pytest.mark.parametrize` with no `marks=`/`id=` handling produces one generically-named test with
N sub-results, which:

- loses the per-TC `pytest.mark.jira(...)` tag `-k`/`-m` filtering and reporting rely on,
- produces an Allure entry titled after the function, not the TC, unless corrected per-case,
- and, more importantly, most `tests/e2e/*.py` files are **not** actually identical — they differ
  in real business logic (different assertions, different wizard steps, different verification
  strategy), not just in fixture data. Parametrizing those would force an artificial common shape
  onto genuinely different test flows, which is a worse trade than the duplication it removes.

So the bar for parametrizing a group is: **the bodies must be byte-for-byte identical except for
data values** (machine name, path, manifest, expected fileset) — the same bar this project already
applies to `tests/e2e/_lib/_shared_helpers.py` extraction (see that module's docstring). Don't parametrize
tests that merely look similar at a glance.

## The pattern, when it does apply

```python
import allure
import pytest

MATRIX = [
    pytest.param(
        "NJM-67806", "Debian_12", "manifest-debian12-mixed.sha256", "Debian 12",
        marks=pytest.mark.jira("NJM-67806"), id="NJM-67806-debian12",
    ),
    # ... one row per TC
]

@pytest.mark.parametrize("jira_id,machine,manifest,os_label", MATRIX)
def test_linux_os_support_e2e(logged_in_page, flb_job_cleanup, jira_id, machine, manifest, os_label):
    allure.dynamic.title(f"{jira_id} — End-to-end workflow on {os_label}")
    job_name = flb_job_cleanup(f"AUTO_FLB_{jira_id}")
    ...
```

Three things preserve per-TC traceability that a naive parametrize loses:

1. **`marks=pytest.mark.jira(id)` per `pytest.param`** — `-m jira` filtering and Allure's Jira
   integration still resolve to the right TC per case, not just per function.
2. **`id=` per `pytest.param`** — gives each case a stable, readable node ID
   (`test_linux_os_support_e2e[NJM-67806-debian12]`) instead of pytest's default positional-index ID,
   which would silently renumber if the matrix is reordered.
3. **`allure.dynamic.title(...)` inside the test body** — sets the Allure report's displayed title
   per invocation, so the report still reads as 4 distinctly-named results, not one title with 4
   parameter blobs.

## Applying this elsewhere

Before parametrizing another group, diff the candidate files (the way `_shared_helpers.py`'s own
extraction was justified — see its module docstring) to confirm they're truly identical apart from
data. If they diverge in logic, leave them as separate files; duplication is the safer default in
this codebase over a forced abstraction (see `CLAUDE.md`'s "no half-finished implementations"
principle and this project's general anti-over-engineering stance).
