# reporting/ — Allure reporting layer

Execution and reporting are decoupled by an **event journal**:

```
Runbook (cases/**/<ID>.md — metadata source of truth)
  → executor emits events → results/runs/<run-id>/journal.jsonl  (+ raw artifacts in the run dir)
  → python -m reporting.generate --latest
      RunbookParser/MetadataExtractor → labels (epic/feature/story/owner/severity/tags/repoType…)
      EventReader/ResultCollector     → TestResult → nested StepResults (RPCs, assertions)
      FailureAnalyzer + categories    → meaningful statusDetails + dashboard buckets
      EnvironmentReporter             → environment.properties (auto-discovered, fail-soft)
      AttachmentManager               → journal, runbook, API req/resp, screenshots, any run-dir file
      AllureMapper  ← the ONLY Allure-aware module
      HistoryManager                  → carries history/ → trends & retries accumulate
  → results/allure-results/ → allure generate → results/allure-report/index.html
```

## Run it
```
python -m reporting.emit new-run NJM-1234 --runbook cases/<area>/NJM-1234.md
python -m reporting.emit <RUN_DIR> step_start --json '{"step_id":"s1","name":"Preconditions"}'
python -m reporting.emit <RUN_DIR> rpc --json '{"step_id":"s1","service":"...","method":"...","request":...,"response":...,"took_ms":42}'
python -m reporting.emit <RUN_DIR> assertion --json '{"step_id":"s1","name":"...","expected":"...","actual":"...","passed":true}'
python -m reporting.emit <RUN_DIR> step_end --json '{"step_id":"s1","status":"passed"}'
python -m reporting.emit <RUN_DIR> test_end --json '{"test_id":"NJM-1234","status":"passed","message":"..."}'
python -m reporting.generate --latest        # or --all (full rebuild) / --run <dir> / --no-report
```
Event schema: `events.py`. Statuses: passed|failed|broken|skipped|unknown (BLOCKED = skipped +
message naming the missing prerequisite → lands in the "Environment Issue" category).

## Design rules (keep these invariants)
- **Execution never imports/knows Allure.** Only `allure_mapper.py` does. Allure upgrade → touch
  that one file (see the version-agnostic `generate` invocation in `generate.py`).
- **No hard-coded paths.** Everything derives from `config.ReportConfig` (repo root discovered by
  markers). Components take config/paths via constructors (DI) — no globals.
- **Fail-soft everywhere.** Missing runbook → default labels; missing attachment → skipped with a
  warning attachment; missing Allure CLI → results still emitted; malformed journal lines → skipped.
- **History is never overwritten.** Per-run dirs under `results/runs/` are permanent;
  `historyId` is stable per test case so Allure trends/retries work across runs.

## How to extend
- **New metadata/label:** add a field + regex in `runbook_parser.py` and include it in
  `RunbookMeta.as_labels()`. Nothing else changes.
- **New attachment kind:** drop the file into the run dir (auto-attached), or emit an
  `attachment` event; MIME/extension mapping lives only in `attachments.py`.
- **New failure category:** add a rule in `failure_analyzer._RULES` **and** the matching regex in
  `categories.DEFAULT_CATEGORIES` (they are deliberately mirrored).
- **New runbook format:** add a parse strategy in `runbook_parser.py` (keep `RunbookMeta` stable).
- **New backup/repository type:** no code change — it's just a new label value from the runbook.
- **New reporting tool (non-Allure):** write a sibling of `allure_mapper.py` consuming the same
  `model.TestResult`; the journal and model are tool-agnostic.
- **Future ideal:** an MCP-level tap that auto-journals every `nbr.call` (needs a change in the
  nbr MCP server) would remove the executor's per-call `rpc` emission entirely.

## CI usage
Run tests (journals accumulate under `results/runs/`), then `python -m reporting.generate --all`
and publish `results/allure-report/` (or feed `results/allure-results/` to an Allure service).
Requires Java + Allure CLI on the agent; without them the pipeline still emits valid results.
