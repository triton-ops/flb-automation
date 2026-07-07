# Execution rules — FLB automation (read before running any case)

These are binding rules for Claude when generating or executing a file-level backup test case.

## Golden rules

1. **Single source of truth.** All fixtures come from `test-data/environment.md` and
   `test-data/test-data.md`. Never hardcode addresses, VIDs, paths, or credentials in a case.
2. **Introspect before you mutate.** Before the first *write* RPC of a kind in a session, run
   `mcp__nbr__describe_method` to confirm the parameter shape against the live spec. Spec can
   drift across builds.
3. **Safety fence.** Only ever create/modify/delete entities whose name starts with
   `AUTO_FLB_`. The discovered machines, repositories, and transporters are **read-only
   references** — never delete or edit them. Never touch a job you didn't create.
4. **Evidence always.** Every executed step records its RPC request + raw response (+ `took_ms`)
   into the result report. Screenshots (R8) at the verify step and at any failure.
5. **Honest reporting.** If a step fails, mark it FAIL with the exact response — never
   paper over it. If a step is skipped, say so and why. Don't claim PASS without the
   verification (R7) actually succeeding.
6. **Stop on hard failure.** If a step's precondition fails (e.g. source not OK, repo
   inaccessible), stop and report BLOCKED rather than pushing ahead.

## Standard lifecycle of a case

1. **Resolve** — read the TC (Jira `get_issue`) + `test-data.md`; pick source(s), repo, paths.
2. **Preconditions** — R1 (source OK), R3 (repo OK), test data seeded (manifest filled).
3. **Act** — R4 create job → R5 run → R6 poll to terminal state.
4. **Verify** — R7 savepoint/backup-object/FLR vs the manifest; R8 screenshot.
5. **Report** — write `results/reports/<JIRA-ID>__<stamp>.md` with per-step evidence + verdict.
6. **Cleanup** — R9 only if PASS. On FAIL, leave artifacts and record the job name/id.

## Polling guidance

- Backup runs are async. Poll `getJob` on a sane interval (e.g. 15–30s); don't busy-loop.
- Set a max wait appropriate to the data size (the seeded fileset is small — a few minutes).
- On timeout, capture the last state, screenshot, and report FAIL (timeout).

## Verdict definitions

- **PASS** — job reached `SUCCEEDED`, ≥1 savepoint created, and FLR-restored files match the
  manifest checksums (when the TC requires content verification).
- **FAIL** — any expected step did not meet its expectation; evidence captured.
- **BLOCKED** — a precondition was not met (environment issue), not a product defect.

## Secrets

Never print credentials. The nbr MCP handles auth; the browser helper reads the UI password
from local config. Use `echo_args=False` (default) on `call`.
