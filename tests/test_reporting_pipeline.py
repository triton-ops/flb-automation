"""Unit tests for the event-journal -> Allure-result reporting pipeline.

These exercise reporting/ end-to-end with SYNTHETIC journals in tmp_path — fully offline,
deterministic, no dependency on any live appliance or the real results/runs/ history.
"""
from __future__ import annotations

import json

from reporting.allure_mapper import AllureMapper
from reporting.attachments import AttachmentManager
from reporting.config import ReportConfig
from reporting.event_reader import ResultCollector, read_events
from reporting.events import JournalWriter, new_run_dir
from reporting.failure_analyzer import analyze, classify
from reporting.generate import process_run
from reporting.model import TestResult


def _write_passed_run(run_dir):
    w = JournalWriter(run_dir)
    w.emit("run_start", run_id=run_dir.name, test_id="TEST-1", appliance="nbr-84")
    w.emit("test_start", test_id="TEST-1", name="Synthetic passing case")
    w.emit("step_start", step_id="s1", name="Preconditions")
    w.emit("rpc", step_id="s1", service="Svc", method="check", request=[1], response={"ok": True}, took_ms=12)
    w.emit("assertion", step_id="s1", name="precondition met", expected="OK", actual="OK", passed=True)
    w.emit("step_end", step_id="s1", status="passed")
    w.emit("test_end", test_id="TEST-1", status="passed", message="all good")
    w.emit("run_end")


def test_new_run_dir_is_unique_and_never_collides(tmp_path):
    d1 = new_run_dir(tmp_path, "TEST-1")
    d2 = new_run_dir(tmp_path, "TEST-1")
    assert d1 != d2
    assert d1.is_dir() and d2.is_dir()


def test_passed_run_collects_into_expected_model(tmp_path):
    run_dir = tmp_path / "run1"
    _write_passed_run(run_dir)

    events, warnings = read_events(run_dir / "journal.jsonl")
    assert warnings == []
    collector = ResultCollector(run_dir)
    test, run_meta = collector.collect(events)

    assert test.status == "passed"
    assert test.test_id == "TEST-1"
    assert run_meta["appliance"] == "nbr-84"
    assert len(test.steps) == 1
    step = test.steps[0]
    assert step.name == "Preconditions"
    assert step.status == "passed"
    # the rpc + assertion each land as a nested sub-step under the enclosing step
    assert len(step.steps) == 2
    assert collector.warnings == []


def test_missing_test_end_derives_failed_status_from_steps(tmp_path):
    run_dir = tmp_path / "run2"
    w = JournalWriter(run_dir)
    w.emit("test_start", test_id="TEST-2")
    w.emit("step_start", step_id="s1", name="Run")
    w.emit("step_end", step_id="s1", status="failed", message="boom")
    # no test_end / run_end — the collector must self-heal, not crash

    events, _ = read_events(run_dir / "journal.jsonl")
    collector = ResultCollector(run_dir)
    test, _ = collector.collect(events)

    assert test.status == "failed"
    assert any("no test_end event" in w for w in collector.warnings)


def test_malformed_journal_line_is_skipped_not_fatal(tmp_path):
    run_dir = tmp_path / "run3"
    run_dir.mkdir()
    (run_dir / "journal.jsonl").write_text(
        '{"type": "test_start", "test_id": "TEST-3", "ts": "2026-01-01T00:00:00+00:00"}\n'
        "not-json-at-all\n"
        '{"type": "test_end", "test_id": "TEST-3", "status": "passed", '
        '"ts": "2026-01-01T00:00:01+00:00"}\n',
        encoding="utf-8",
    )
    events, warnings = read_events(run_dir / "journal.jsonl")
    assert len(events) == 2
    assert any("malformed" in w for w in warnings)


def test_dangling_step_is_auto_closed(tmp_path):
    run_dir = tmp_path / "run4"
    w = JournalWriter(run_dir)
    w.emit("test_start", test_id="TEST-4")
    w.emit("step_start", step_id="s1", name="Never closed")
    w.emit("test_end", test_id="TEST-4", status="passed")

    events, _ = read_events(run_dir / "journal.jsonl")
    collector = ResultCollector(run_dir)
    test, _ = collector.collect(events)

    assert test.steps[0].stop is not None
    assert any("never closed" in w for w in collector.warnings)


def test_blocked_precondition_classifies_as_environment_issue():
    test = TestResult(test_id="X", status="skipped",
                      message="BLOCKED(env): requires an Amazon S3 repository on nbr-84")
    assert classify(test) == "Environment Issue"
    analyze(test)
    assert any(a.name == "failure-analysis.md" for a in test.attachments)


def test_assertion_failure_classifies_correctly():
    test = TestResult(test_id="X", status="failed", error_type="assertion",
                      message="expected=OK actual=FAILED")
    assert classify(test) == "Assertion Failure"


def test_process_run_writes_a_valid_allure_result(tmp_path):
    cfg = ReportConfig(repo_root=tmp_path)
    run_dir = new_run_dir(cfg.runs_dir, "TEST-5")  # creates the run directory only
    w = JournalWriter(run_dir)
    w.emit("run_start", run_id=run_dir.name, test_id="TEST-5")
    w.emit("test_start", test_id="TEST-5", name="Synthetic")
    w.emit("test_end", test_id="TEST-5", status="passed")

    att = AttachmentManager(cfg.allure_results_dir)
    mapper = AllureMapper(cfg.allure_results_dir, att)
    test_id, status, ctx = process_run(run_dir, cfg, mapper, att)

    assert test_id == "TEST-5"
    assert status == "passed"
    results = list(cfg.allure_results_dir.glob("*-result.json"))
    assert len(results) == 1
    doc = json.loads(results[0].read_text(encoding="utf-8"))
    assert doc["status"] == "passed"
    assert doc["historyId"]
    label_names = {label["name"] for label in doc["labels"]}
    assert {"epic", "feature", "suite", "owner", "severity", "framework"} <= label_names
    # the journal itself is always auto-attached, with zero attach-code in the runbook
    attachment_names = {a["name"] for a in doc["attachments"]}
    assert "execution-journal.jsonl" in attachment_names


def test_process_run_is_fail_soft_when_runbook_is_missing(tmp_path):
    """No matching runbook under cases/ -> defaults, never a crash."""
    cfg = ReportConfig(repo_root=tmp_path)
    run_dir = new_run_dir(cfg.runs_dir, "NO-SUCH-RUNBOOK")
    w = JournalWriter(run_dir)
    w.emit("test_start", test_id="NO-SUCH-RUNBOOK")
    w.emit("test_end", test_id="NO-SUCH-RUNBOOK", status="passed")

    att = AttachmentManager(cfg.allure_results_dir)
    mapper = AllureMapper(cfg.allure_results_dir, att)
    test_id, status, _ = process_run(run_dir, cfg, mapper, att)
    assert test_id == "NO-SUCH-RUNBOOK"
    assert status == "passed"
