"""CLI emitter — how the executor (Claude / scripts / CI) writes journal events.

Usage:
  python -m reporting.emit new-run <TEST_ID> [--runbook PATH]      -> prints the new run dir
  python -m reporting.emit <RUN_DIR> <TYPE> --json '<payload>'     -> append one event
  python -m reporting.emit <RUN_DIR> <TYPE> --kv k=v [--kv k=v]    -> append one event (simple)

The executor emits: run_start, test_start, step_start/step_end around each recipe action,
rpc per nbr call (request/response/took_ms), assertion for verify checks, attachment for
screenshots/exports, test_end with the verdict, run_end. See events.py for the schema.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import ReportConfig
from .events import JournalWriter, new_run_dir


def _parse_kv(pairs: list[str]) -> dict:
    out: dict = {}
    for p in pairs or []:
        k, _, v = p.partition("=")
        # best-effort typing: json first, fall back to string
        try:
            out[k] = json.loads(v)
        except (json.JSONDecodeError, ValueError):
            out[k] = v
    return out


def main(argv: list[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    if args and args[0] == "new-run":
        ap = argparse.ArgumentParser(prog="reporting.emit new-run")
        ap.add_argument("test_id")
        ap.add_argument("--runbook", default=None)
        ns = ap.parse_args(args[1:])
        cfg = ReportConfig()
        run_dir = new_run_dir(cfg.runs_dir, ns.test_id)
        w = JournalWriter(run_dir)
        w.emit("run_start", run_id=run_dir.name, test_id=ns.test_id,
               runbook=ns.runbook or "")
        print(run_dir)
        return 0

    ap = argparse.ArgumentParser(prog="reporting.emit")
    ap.add_argument("run_dir")
    ap.add_argument("type")
    ap.add_argument("--json", dest="json_payload", default=None)
    ap.add_argument("--kv", action="append", default=[])
    ns = ap.parse_args(args)
    payload = json.loads(ns.json_payload) if ns.json_payload else {}
    payload.update(_parse_kv(ns.kv))
    JournalWriter(Path(ns.run_dir)).emit(ns.type, **payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
