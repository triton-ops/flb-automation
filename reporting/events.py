"""Execution-event journal — the contract between execution and reporting.

Execution (Claude following EXECUTION_PROMPT.md, or any future runner) emits these events into
`results/runs/<run-id>/journal.jsonl`, one JSON object per line, append-only. Execution knows
ONLY this schema — never Allure.

Event types (all carry `ts` ISO-8601 UTC):
  run_start   {run_id, runbook, test_id, appliance?, product_version?, build_number?, environment?}
  test_start  {test_id, name?}
  step_start  {step_id, name, parent?}          # parent = enclosing step_id for nesting
  step_end    {step_id, status, message?}       # status: passed|failed|broken|skipped
  rpc         {step_id?, service, method, request?, response?, took_ms?, error?}
  assertion   {step_id?, name, expected, actual, passed}
  attachment  {step_id?, name, path, mime?}     # path relative to run dir or absolute
  test_end    {test_id, status, message?}       # status: passed|failed|broken|skipped|unknown
  run_end     {run_id}
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

EVENT_TYPES = {
    "run_start", "test_start", "step_start", "step_end",
    "rpc", "assertion", "attachment", "test_end", "run_end",
}


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


class JournalWriter:
    """Append-only journal emitter. Safe to call from anywhere; creates the run dir on demand."""

    def __init__(self, run_dir: Path):
        self.run_dir = Path(run_dir)
        self.path = self.run_dir / "journal.jsonl"

    def emit(self, event_type: str, **payload) -> dict:
        if event_type not in EVENT_TYPES:
            raise ValueError(f"unknown event type {event_type!r}; expected one of {sorted(EVENT_TYPES)}")
        self.run_dir.mkdir(parents=True, exist_ok=True)
        evt = {"type": event_type, "ts": payload.pop("ts", None) or utc_now_iso(), **payload}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(evt, ensure_ascii=False, default=str) + "\n")
        return evt


def new_run_dir(runs_dir: Path, test_id: str) -> Path:
    """Create a unique per-run directory: <UTCstamp>__<test_id>. Never reuses/overwrites."""
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    d = runs_dir / f"{stamp}__{test_id}"
    n = 1
    while d.exists():
        n += 1
        d = runs_dir / f"{stamp}__{test_id}_{n}"
    d.mkdir(parents=True)
    return d
