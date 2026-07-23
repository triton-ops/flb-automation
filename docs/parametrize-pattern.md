# `@pytest.mark.parametrize` in this framework — one TC per file, no exceptions

**Status update (2026-07-23): the cross-TC consolidation this doc originally demonstrated has
been reversed.** `docs/enterprise-gap-analysis.md` flagged zero `parametrize` usage across
`tests/e2e/` as a High finding, and named the 4 Linux "OS Support" TCs (NJM-67806/67807/67808/67809
— 100% identical bodies, differing only in machine name and checksum manifest) as the clearest
case. That group was consolidated into one `test_njm_67806_67809_linux_os_matrix.py` file as a
demonstration — and has since been **split back into one `test_njm_<id>.py` file per TC**
(`test_njm_67806.py`, `test_njm_67807.py`, `test_njm_67808.py`, `test_njm_67809.py`), along with
every other combination test script found anywhere in the project (parametrize matrices and
otherwise), per an explicit, repeated project decision: **every test script maps to exactly one
Jira TC, full stop — no exception for identical bodies.** This doc now explains why that bar wins
even over genuine, byte-for-byte duplication, and where a *different* kind of parametrize (within
one TC, not across TCs) still legitimately applies.

## Why cross-TC parametrize was rejected, not just deprioritized

This project's one-file-per-Jira-TC convention exists for a real reason: `cases/<Suite>/NJM-<id>.md`
runbooks, Jira lookups, and `pytest -k NJM-<id>` all assume a TC maps to something you can find and
reason about independently. A bare `@pytest.mark.parametrize` spanning multiple TCs — even with
careful `marks=pytest.mark.jira(...)`/`id=`/`allure.dynamic.title(...)` handling to preserve
per-case traceability (the demonstrated pattern this doc used to show) — still collapses N
independently-tracked TCs into one Python function and one file. That trade was tried once, live,
on the clearest possible case (truly identical bodies) and reversed anyway: the ease of finding
"the one file for NJM-67807" by filename alone, with zero indirection through a matrix's `id=`
string, was judged worth more than the ~30 duplicated lines per file it costs.

The other real cost, unchanged from the original analysis: most `tests/e2e/*.py` files are **not**
actually identical — they differ in real business logic (different assertions, different wizard
steps, different verification strategy), not just fixture data. That's still true, and still a
reason never to force an artificial common shape onto genuinely different test flows. But even for
the rare case where bodies genuinely are identical, the answer this project landed on is
duplication with a documentation trail, not consolidation — see "Folded-duplicate TCs" below.

## What still uses `@pytest.mark.parametrize` — and why it's a different case

One legitimate use remains, and it's a **different shape entirely**: a single TC's own internal
value matrix, not multiple TCs sharing a body. Example —
`tests/e2e/test_flbv2v3_BackupExecution/test_njm_185036.py` (NJM-185036, "'Limit a concurrent task
to N folders' field governs folder parallelism"):

```python
@pytest.mark.parametrize("limit", [1, 8], ids=["limit-1", "limit-8"])
def test_concurrent_task_limit_accepted(logged_in_page, flb_job_cleanup, limit):
    ...
```

This is fine because there is still exactly **one** `pytest.mark.jira("NJM-185036")` for the whole
file — the parametrize varies a value the TC itself asks to be checked at more than one point
(low and high), not which TC is under test. The tell: does every row still carry the *same* Jira
ID? If yes, it's one TC's own sub-cases (parametrize is fine, or several named functions in the
same file both work — either shape keeps `pytest -k NJM-185036` selecting everything). If rows
carry *different* Jira IDs, it's cross-TC consolidation (never do this, regardless of how similar
the bodies look).

## Folded-duplicate TCs: the pattern that replaces cross-TC parametrize

Occasionally two *different* TCs turn out to require exactly the same steps — one TC's Xray spec
is a strict subset or restatement of another's (e.g. NJM-67687 "Backup to the Onboard Repository"
and NJM-85728 "Repository Integrity and Structure of Backup Data Post-Job" — the second TC's
steps are verbatim the first's own build+run+verify body). Consolidating these into one
parametrized/shared function was the old approach. The current one: **the primary TC keeps its own
single-marker file and real test; the second TC gets nothing — its own coverage is documented in
the primary file's own module docstring**, explaining which real test satisfies it and why a
second live run (rebuilding the same job, re-uploading to the same cloud account, etc.) would add
appliance cost, not coverage. See `test_njm_67687.py`, `test_njm_123122.py`, `test_njm_123133.py`
in `test_flbv2v3_ObjectStorage/` for worked examples, and `test_njm_122643.py`/`test_njm_122656.py`
in `test_flbv2v3_SourceSelection/` for the same pattern applied to two UI-only dialog-navigation
TCs.

## Applying this elsewhere

Before adding any `@pytest.mark.parametrize` to a test file, check which shape it is:

1. **Same Jira ID on every row?** → fine, it's one TC's own sub-case matrix (see NJM-185036 above).
2. **Different Jira ID per row?** → don't. Write one file per TC instead, even if it means
   duplicating a large fraction of the body — see `tests/e2e/_lib/_shared_helpers.py`'s own
   docstring for this project's general "duplication over a forced abstraction" stance, and
   `CLAUDE.md`'s "no half-finished implementations" principle.
3. **One TC's steps are exactly another TC's own body?** → the folded-duplicate pattern above:
   one real file, one skipped-nothing docstring note on the sibling, no parametrize.
