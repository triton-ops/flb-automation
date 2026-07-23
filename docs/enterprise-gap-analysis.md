# Enterprise Framework Gap Analysis — flb-automation

Prepared 2026-07-17 as analysis only. **Status update (2026-07-23): nearly every item below has
since been implemented** — this document is kept as-is below (a point-in-time snapshot, not
rewritten) with a resolution summary here at the top instead, so the original reasoning for each
item stays intact as context for *why* each thing was built.

| # | Item | Status |
|---:|---|---|
| 1 | No CI/CD pipeline | **Resolved** — `.github/workflows/ci.yml` (two-tier: `lint-and-collect` on every push/PR, `e2e-appliance` manual/opt-in) |
| 2 | No automated flaky-test retry | **Resolved** — `pytest-rerunfailures`, `--reruns=1 --reruns-delay=10` in `pyproject.toml` |
| 3 | Zero `@pytest.mark.parametrize` usage | **Evaluated, then reversed** — one consolidation was built and live-verified (the Linux OS-support matrix), then deliberately split back into one-file-per-TC project-wide. See `docs/parametrize-pattern.md` for the full reasoning; parametrize is still used, just never across different Jira TCs. |
| 4 | Trace Viewer not enabled | **Resolved** — `--tracing=retain-on-failure` in `pyproject.toml` |
| 5 | Ruff configured but unenforced | **Resolved** — `.pre-commit-config.yaml` runs `ruff check` on commit |
| 6 | Incomplete marker registration | **Resolved** — `flrfunctional` (and every other suite's) marker registered in `pyproject.toml`, applied across all suite files |
| 7 | No pre-commit hooks | **Resolved** — same `.pre-commit-config.yaml` as item 5 |
| 8 | No static type checking | **Resolved** — `mypy` added with a lenient baseline config |
| 9 | No partial parallelization strategy | **Documented, opt-in** — `docs/xdist-parallelization.md` (`xdist_group` marker pattern demonstrated on 2 TCs); `pytest-xdist` itself still not installed/wired by default |
| 10 | No flaky-test trend/historical analytics | **Resolved** — Allure history/trend graphs enabled (`allurerc.json`'s `historyPath`) |
| 11 | No visual regression testing | **Resolved** — `docs/visual-regression-pattern.md` + `tests/e2e/test_infrastructure/test_visual_regression_example.py` |
| 12 | No dependency lockfile | **Resolved** — `requirements-lock.txt` (`pip freeze` snapshot) |
| 13 | No container/devcontainer | **Resolved, unverified** — `Dockerfile`/`.dockerignore` added; no Docker daemon was available to build-test it |
| 14 | No secrets-manager integration | **Documented** — `docs/ci-secrets.md` (GitHub Secrets pattern for CI credentials) |
| 15 | No accessibility (axe-core) scanning | **Resolved** — `axe-playwright-python` example script added |
| 16 | `conftest.py` is a single flat file | **Still open** — unchanged; still low urgency (only 6 fixtures, none suite-specific yet) |
| 17 | Documentation currency drift | **Actively maintained** — this pass (2026-07-23) is itself an instance of keeping docs current after the project-wide test-file reorganization; see `CALIBRATION_LOG.md`'s 2026-07-22/23 section |

Only item 16 remains genuinely open, and it's still correctly assessed as low-urgency below. The
rest of this document is preserved unmodified as the original analysis and reasoning.

---

Analysis only, as originally written — **nothing in this document has been implemented [as of
2026-07-17]**. Every claim about the current codebase's state was verified against the actual
files (`pyproject.toml`, `requirements*.txt`, `.github/`, `.pre-commit-config.yaml` presence)
before being written down, not assumed.

## Methodology and an important caveat

This framework is compared against four reference points:

- **Microsoft's own Playwright examples/docs** — canonical Page Object Model structure, GitHub
  Actions CI templates, Trace Viewer, sharding, projects/config patterns.
- **BrowserStack** — cloud grid execution, test observability/flaky-test analytics, CI
  integration guides, visual testing add-ons.
- **Sauce Labs** — similar to BrowserStack (cloud grid, Sauce Connect for local/internal
  targets, analytics, visual testing), plus their emphasis on test orchestration at scale.
- **General pytest best practices** — fixture scoping/hierarchy, parametrization, markers,
  plugins for retries/parallelism/coverage, pre-commit/lint/type-check gates.

**The caveat that matters most**: BrowserStack's and Sauce Labs' *core* value proposition is
running the *same* test across a large matrix of real browsers/devices/OSes. That doesn't map
onto this project's actual domain — this framework always drives one browser (Chromium) against
one specific, internal admin console (NAKIVO Director), and the "cross-platform" coverage this
project already has (Windows/Linux/RHEL/SLES/Ubuntu source machines) is about the **backed-up**
machine's OS, not the browser running the test. Recommending "add a BrowserStack/Sauce Labs grid"
would be cargo-culting a capability this project doesn't need. Each gap below is evaluated on its
actual merit for *this* project, not by mechanically checking whether a reference source mentions
it — and several items below are flagged as **already evaluated and deliberately rejected**, not
as oversights.

---

## Not gaps — already deliberately evaluated and rejected

Listed first so they aren't miscounted as findings below:

- **`pytest-xdist` / full parallel execution** — explicitly rejected. Several TCs in
  `test_flbv2v3_Inventory` deliberately target the same physical source machine, and this
  project's own documented finding is that concurrent jobs against the same source VID lock/stall
  rather than queue. This is a real environment constraint, not an oversight.
- **Cross-browser testing (Firefox/WebKit)** — not applicable. This tests one internal admin
  console's UI, not a multi-browser-support product; NAKIVO Director isn't validated against
  WebKit in this environment either.
- **Network mocking/interception (`page.route()`)** — deliberately out of scope. `CLAUDE.md`'s
  core architectural principle is "no backend RPC in the test path" — this project values real
  end-to-end fidelity over mocked speed. Introducing request mocking would contradict the
  project's own stated philosophy, not fill a gap in it.
- **Structured `logging` module usage** — already addressed head-on in
  `docs/framework-guidelines.md` §9: Allure's video/screenshot capture plus pytest's own
  assertion output serve the same underlying need (debuggability) via a different, arguably
  better-suited mechanism for UI testing specifically. Not a gap, a different solution to the
  same problem.
- **Test-data factory pattern (`factory_boy` etc.)** — low applicability. This project's test
  data is static, pre-seeded real fixtures on real physical/virtual machines (see
  `test-data/test-data.md`), not synthetic data generated per test run.

---

## Critical

### 1. No CI/CD pipeline at all
Verified: no `.github/` directory, no `.pre-commit-config.yaml`, no CI config of any kind exists
in this repo. Every test run today is a human or agent manually invoking `pytest` locally. This
is Microsoft's and both cloud providers' single most consistent recommendation — a CI gate that
runs independently of any one person remembering to run tests. **Caveat**: a naive
GitHub-hosted-runner workflow won't work here — the appliance (`10.10.16.84`) is only reachable
from this project's own network, so real CI needs either a self-hosted runner with network
access or a scheduled job, not a public Actions runner. The earlier architecture review already
scoped this as a Large-effort roadmap item (one canary TC per suite, not full regression, given
the live-appliance constraint) — still unimplemented.

### 2. No automated flaky-test retry mechanism
Verified: no `pytest-rerunfailures` (or equivalent) in `requirements-dev.txt`, no `--reruns` flag
in `pyproject.toml`'s `addopts`. This project has **extensively documented, real, recurring
appliance-load-induced flakiness** — the "Run this job?" dialog timeout (3 consecutive real
failures before being root-caused), NJM-67692's transient picker timeout, NJM-70313's identical
retry pattern — every one of these required a *human-or-agent-judgment* decision to retry
manually. There is no automated, reported "this test passed on retry 2" signal anywhere in this
framework today. Given how well-characterized this project's flakiness patterns already are (see
`browser/checks/framework_doctor.py`'s own load-detection logic), wiring `pytest-rerunfailures`
with a small, deliberate rerun count (1-2, matching this project's own "retry once, then treat a
repeat as a real signal" rule already stated in `CLAUDE.md`) would convert a manual, invisible
practice into an automated, visible one.

---

## High

### 3. Zero use of `@pytest.mark.parametrize`
Verified: no `parametrize` decorator appears anywhere in `tests/e2e/`. Every TC is its own
hand-written file, including cases that are structurally identical and differ only in fixture
data. The clearest example: tasks queued in this project's own backlog right now — NJM-83226,
-83229, -83231, -83234, -83235, -83244, -83246, -83252, -83255 (9 "OS Support via FLR" TCs) will
almost certainly produce 9 near-identical test bodies differing only in machine name and manifest
file. This is the textbook case both Microsoft's examples and general pytest guidance parametrize
rather than copy-paste. **This is the single most concretely actionable finding in this entire
analysis** — it applies directly to already-planned, not-yet-written work.

### 4. Playwright Trace Viewer not enabled
Verified: `pyproject.toml`'s `addopts` configures `--video=on` but no `--tracing=` flag, despite
`requirements-dev.txt`'s own comment on `pytest-playwright` explicitly listing `--tracing` as one
of the flags this plugin provides. Trace Viewer captures a full step-by-step timeline (DOM
snapshots, network, console, actionability waiting) that video alone cannot provide — you can't
inspect DOM state at a specific step from a `.webm` file. `--tracing=retain-on-failure` (traces
only kept for failed tests) is near-zero marginal cost given `--video=on` is already accepted as
worth the overhead, and is one of Microsoft's most consistently recommended Playwright practices.

### 5. Existing lint configuration isn't enforced anywhere
Verified: `pyproject.toml` has a complete `[tool.ruff]`/`[tool.ruff.lint]` configuration
(target-version, line-length, selected rule sets, one deliberately-documented ignore). But there
is no `.pre-commit-config.yaml` and no CI to run it — the configuration exists but nothing
actually invokes `ruff check` before or during a commit. This is a "config without enforcement"
gap: the hard part (deciding the ruleset) is already done; wiring it to run automatically is the
missing, comparatively cheap remainder.

### 6. Incomplete pytest marker registration
Verified: `pyproject.toml`'s `markers` list has `flb`, `fsb`, `include_exclude`, `inventory`,
`beta_smoke`, and `jira(id)` — but no marker for `test_flbv2v3_FLRFunctional`, the newest and
currently most actively-growing suite (5 TCs today, 28 planned). Every test file in that suite
uses only `pytest.mark.flb`, so `pytest -m flrfunctional` (the filtering pattern every other
suite supports) doesn't work for it. Already flagged in `docs/framework-guidelines.md` §3;
repeated here because it's directly relevant to the "pytest best practices" comparison axis.

---

## Medium

### 7. No pre-commit hooks at all
Verified: no `.pre-commit-config.yaml` anywhere in the repo. Item 5 above (ruff enforcement) is
one instance of this broader gap — a pre-commit framework would also be the natural place to run
`py_compile`/import-sanity checks (the kind this session did manually via Bash before trusting
any refactor) automatically, rather than as an ad hoc verification step.

### 8. No static type checking
Verified: no `mypy`/`pyright` dependency anywhere, despite the codebase using type hints
consistently (`-> bool`, `-> list[dict]`, `job_name: str`, etc., across essentially every POM
method). The hints exist; nothing currently validates them stay correct as the codebase evolves.

### 9. No partial/safe parallelization strategy
The full-parallelization rejection (see "Not gaps" above) is correct and well-justified, but
nothing has explored *safe* partial parallelization — e.g., an FSB suite job against nbr-5 and an
FLB suite job against nbr-84 touch entirely different appliances and could safely run
concurrently; even within FLB, TCs targeting genuinely different source machines (not already
identified as contended) could too. As the `FLRFunctional` suite grows toward its planned 28 TCs
at roughly 3-4 minutes each, purely sequential execution is a real, growing wall-clock cost that a
smarter (not blanket) parallelization strategy could partially address.

### 10. No flaky-test trend/historical analytics
Allure gives excellent *per-run* detail (this project uses it well), but there's no cross-run
trend view — no way to see "this TC has flaked 3 times in the last 2 weeks" without manually
recalling or searching. Both BrowserStack and Sauce Labs center their observability pitch on
exactly this kind of longitudinal view.

### 11. No visual regression testing
No screenshot-diffing against a stored baseline (Playwright's own `expect(page).to_have_screenshot()`
equivalent, or a Percy/Applitools-style integration). Screenshots are already captured on
failure, but never compared. Moderate priority for this project specifically — the existing
functional/content assertions (FLR-browse listing match, checksum match, dashboard status) already
provide strong correctness signal for a data/wizard-driven admin console, where visual diffing
would mostly catch cosmetic drift rather than functional regressions.

### 12. No dependency lockfile for transitive dependencies
`requirements.txt`/`requirements-dev.txt` pin direct dependencies exactly (a good practice already
followed, with an explicit comment about *why* pinning matters for CI determinism), but neither
locks the full transitive dependency tree the way Poetry/PDM/`uv`'s lockfiles do. Two installs
six months apart could still resolve different transitive versions.

### 13. No container/devcontainer for standardized execution
No `Dockerfile`/`.devcontainer/`. Every test run today depends on a correctly-configured local
Windows venv. This becomes more pressing the moment CI (item 1) is introduced — a container
would remove "works on my machine" as a variable for both CI and any additional human
contributors.

### 14. No secrets-manager integration beyond `.env`
Fine for the current single-machine, single-operator setup, but a real blocker the moment CI is
introduced: there's no established pattern yet for injecting `NBR_FLB_PASS`/`WINFS3_PASS`/etc.
into a CI runner without copying `.env` insecurely. Worth planning alongside item 1, not before
it's needed.

---

## Low

### 15. No accessibility (axe-core) scanning
No `axe-playwright-python` or equivalent. Genuinely low priority for this specific project — an
internal admin console without the legal/public-facing accessibility obligations that make this
a near-mandatory practice for customer-facing products (which is where BrowserStack/Sauce Labs
push it hardest).

### 16. `conftest.py` is a single flat file
No per-suite `conftest.py` hierarchy. Low urgency today — only 5 fixtures exist, and none are
suite-specific yet. Worth revisiting if suite-specific fixtures start accumulating (e.g., an
FSB-only fixture that doesn't belong in the shared file).

### 17. Documentation currency drift
Already identified in this project's own earlier architecture review (README's coverage table
missing the FLRFunctional suite; `browser/README.md` describing a superseded verdict model). Not
re-analyzed in depth here — cross-referenced because "keep onboarding docs current" is a
consistent theme across all four comparison sources, and this is the concrete instance of it in
this repo today.

---

## Summary

| Priority | Count | Items |
|---|---:|---|
| Critical | 2 | No CI/CD pipeline; no automated flaky-test retry mechanism |
| High | 4 | No `parametrize` usage; Trace Viewer not enabled; ruff configured but unenforced; incomplete marker registration |
| Medium | 8 | No pre-commit hooks; no type checking; no partial parallelization strategy; no flaky-test analytics; no visual regression testing; no dependency lockfile; no container/devcontainer; no secrets-manager integration |
| Low | 3 | No accessibility scanning; flat conftest.py; documentation currency drift |
| **Not gaps (deliberately rejected/inapplicable)** | 5 | Full `pytest-xdist`; cross-browser testing; network mocking; structured `logging`; test-data factories |

Nothing above has been implemented — this is the analysis only, per your instruction.
