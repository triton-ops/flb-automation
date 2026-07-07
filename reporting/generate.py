"""ReportGenerator — the one CLI entry point: journal(s) -> allure-results -> Allure report.

Usage:
  python -m reporting.generate --latest            # newest run under results/runs/
  python -m reporting.generate --run <RUN_DIR>     # a specific run (repeatable)
  python -m reporting.generate --all               # every run (full rebuild)
  ... [--no-report]                                # emit allure-results only, skip `allure generate`

Self-healing: missing runbook -> defaults; missing attachments -> skipped with warning;
missing Allure CLI -> results still emitted + instructions printed. History is carried over
before each generation so trends/retries accumulate.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from .allure_mapper import AllureMapper
from .attachments import AttachmentManager
from .categories import write_categories
from .config import ReportConfig
from .environment import build_environment, write_environment
from .event_reader import ResultCollector, read_events
from .failure_analyzer import analyze
from .history import carry_history
from .model import Attachment
from .runbook_parser import RunbookMeta, find_runbook, parse_runbook


def process_run(run_dir: Path, cfg: ReportConfig, mapper: AllureMapper,
                att: AttachmentManager) -> tuple[str, str, dict]:
    events, warnings = read_events(run_dir / "journal.jsonl")
    collector = ResultCollector(run_dir)
    test, run_meta = collector.collect(events)
    warnings += collector.warnings

    # metadata from the runbook (single source of truth); fail-soft to defaults
    runbook_path = None
    if run_meta.get("runbook"):
        p = Path(run_meta["runbook"])
        runbook_path = p if p.is_absolute() else cfg.repo_root / p
        if not runbook_path.exists():
            runbook_path = None
    runbook_path = runbook_path or find_runbook(cfg.cases_dir, test.test_id)
    meta = parse_runbook(runbook_path) if runbook_path else RunbookMeta(test_id=test.test_id)
    if meta.test_id == "UNKNOWN":
        meta.test_id = test.test_id

    # automatic artifacts: journal + runbook copy + any files dropped into the run dir
    test.attachments.append(Attachment("execution-journal.jsonl", "text/plain",
                                       path=str(run_dir / "journal.jsonl")))
    if runbook_path:
        test.attachments.append(Attachment(f"runbook {meta.test_id}.md", "text/markdown",
                                           path=str(runbook_path)))
    for extra in sorted(run_dir.glob("*")):
        if extra.name != "journal.jsonl" and extra.is_file():
            test.attachments.append(Attachment(extra.name, "application/octet-stream",
                                               path=str(extra)))
    if warnings:
        test.attachments.append(Attachment("reporting-warnings.txt", "text/plain",
                                           content="\n".join(warnings).encode()))

    analyze(test)  # failure analysis + category tagging (no-op on pass)
    mapper.write_result(test, meta, run_id=run_dir.name)
    return test.test_id, test.status, {"run_meta": run_meta, "meta": meta}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="reporting.generate")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--latest", action="store_true")
    g.add_argument("--run", action="append", default=None)
    g.add_argument("--all", action="store_true")
    ap.add_argument("--no-report", action="store_true", help="emit allure-results only")
    ap.add_argument("--clean-results", action="store_true",
                    help="wipe allure-results first (history is re-carried from the report)")
    ns = ap.parse_args(argv)

    cfg = ReportConfig()
    runs: list[Path] = []
    if ns.latest:
        latest = cfg.latest_run_dir()
        if not latest:
            print("no runs found under", cfg.runs_dir, file=sys.stderr)
            return 2
        runs = [latest]
    elif ns.run:
        runs = [Path(r) if Path(r).is_absolute() else cfg.runs_dir / r for r in ns.run]
    elif ns.all:
        runs = sorted(d for d in cfg.runs_dir.iterdir()
                      if (d / "journal.jsonl").exists()) if cfg.runs_dir.is_dir() else []

    if ns.clean_results and cfg.allure_results_dir.exists():
        shutil.rmtree(cfg.allure_results_dir)
    cfg.allure_results_dir.mkdir(parents=True, exist_ok=True)

    att = AttachmentManager(cfg.allure_results_dir)
    mapper = AllureMapper(cfg.allure_results_dir, att)

    last_env: dict = {}
    for run_dir in runs:
        test_id, status, ctx = process_run(run_dir, cfg, mapper, att)
        print(f"[reporting] {run_dir.name}: {test_id} -> {status}")
        last_env = build_environment(ctx["run_meta"], ctx["meta"], cfg.repo_root) or last_env

    write_environment(cfg.allure_results_dir, last_env)
    write_categories(cfg.allure_results_dir)
    if att.warnings:
        print("[reporting] warnings:", *att.warnings, sep="\n  ")

    executor_meta = cfg.allure_results_dir / "executor.json"
    executor_meta.write_text(json.dumps({
        "name": "flb-automation", "type": "claude-mcp",
        "reportName": "FLB Automation — Allure Report"}), encoding="utf-8")

    carry_history(cfg.allure_report_dir, cfg.allure_results_dir)

    if ns.no_report:
        print(f"[reporting] allure-results ready: {cfg.allure_results_dir}")
        return 0

    allure = shutil.which("allure")
    if not allure:
        print(f"[reporting] Allure CLI not found — results emitted to {cfg.allure_results_dir}.\n"
              f"  Generate manually: allure generate \"{cfg.allure_results_dir}\" "
              f"-o \"{cfg.allure_report_dir}\"")
        return 0
    # version-agnostic: Allure 2 needs --clean for a non-empty output dir, Allure 3 dropped the
    # flag — so we clear the output ourselves (history was already carried into results above).
    if cfg.allure_report_dir.exists():
        shutil.rmtree(cfg.allure_report_dir, ignore_errors=True)
    proc = subprocess.run([allure, "generate", str(cfg.allure_results_dir),
                           "-o", str(cfg.allure_report_dir)],
                          capture_output=True, text=True)
    tail = (proc.stdout + proc.stderr).strip().splitlines()
    print(*(f"[allure] {line}" for line in tail[-5:]), sep="\n")
    if proc.returncode != 0:
        print("[reporting] allure generate failed; results remain valid in",
              cfg.allure_results_dir, file=sys.stderr)
        return proc.returncode
    print(f"[reporting] report: {cfg.allure_report_dir / 'index.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
