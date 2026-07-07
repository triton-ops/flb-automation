"""EventReader + ResultCollector — journal.jsonl -> TestResult model.

Tolerant by design (self-healing): malformed lines are skipped with a note, unclosed steps are
auto-closed, missing test_end degrades the status to 'unknown' (or 'failed' if a step failed).
"""
from __future__ import annotations

import json
from pathlib import Path

from .model import Attachment, StepResult, TestResult, iso_to_ms


def read_events(journal: Path) -> tuple[list[dict], list[str]]:
    events, warnings = [], []
    if not journal.exists():
        return events, [f"journal not found: {journal}"]
    for i, line in enumerate(journal.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            warnings.append(f"journal line {i}: malformed, skipped")
    return events, warnings


def _fmt_json(obj) -> bytes:
    return json.dumps(obj, indent=2, ensure_ascii=False, default=str).encode("utf-8")


class ResultCollector:
    """Folds the event stream into a TestResult with nested steps + attachments."""

    def __init__(self, run_dir: Path):
        self.run_dir = run_dir
        self.warnings: list[str] = []

    def collect(self, events: list[dict]) -> tuple[TestResult, dict]:
        run_meta: dict = {}
        test = TestResult(test_id="UNKNOWN")
        open_steps: dict[str, StepResult] = {}
        stack: list[StepResult] = []           # for parentless nesting: last open wins

        def current_container():
            return stack[-1] if stack else None

        def attach_here(att: Attachment, step_id: str | None):
            target = open_steps.get(step_id) if step_id else current_container()
            (target.attachments if target else test.attachments).append(att)

        for evt in events:
            et, ts = evt.get("type"), evt.get("ts")
            if et == "run_start":
                run_meta = evt
                test.test_id = evt.get("test_id", test.test_id)
                test.start = test.start or iso_to_ms(ts)
            elif et == "test_start":
                test.test_id = evt.get("test_id", test.test_id)
                test.name = evt.get("name", "")
                test.start = iso_to_ms(ts) or test.start
            elif et == "step_start":
                step = StepResult(step_id=str(evt.get("step_id") or evt.get("name")),
                                  name=evt.get("name", "step"), start=iso_to_ms(ts))
                parent = open_steps.get(str(evt.get("parent"))) if evt.get("parent") else current_container()
                (parent.steps if parent else test.steps).append(step)
                open_steps[step.step_id] = step
                stack.append(step)
            elif et == "step_end":
                sid = str(evt.get("step_id"))
                step = open_steps.pop(sid, None)
                if step:
                    step.stop = iso_to_ms(ts)
                    step.status = evt.get("status", "passed")
                    step.message = evt.get("message", "")
                    if step in stack:
                        stack.remove(step)
                    if step.status in ("failed", "broken") and not test.failed_step:
                        test.failed_step = step.name
                        test.message = test.message or step.message
                else:
                    self.warnings.append(f"step_end for unknown step_id {sid}")
            elif et == "rpc":
                name = f"RPC {evt.get('service')}.{evt.get('method')}"
                start = iso_to_ms(ts)
                took = evt.get("took_ms") or 0
                sub = StepResult(step_id=f"rpc-{len(open_steps)}-{start}", name=name,
                                 start=start, stop=(start + int(took)) if start else None)
                if evt.get("request") is not None:
                    sub.attachments.append(Attachment(f"{name} — request", "application/json",
                                                      content=_fmt_json(evt["request"])))
                if evt.get("response") is not None:
                    sub.attachments.append(Attachment(f"{name} — response", "application/json",
                                                      content=_fmt_json(evt["response"])))
                if evt.get("error"):
                    sub.status = "broken"
                    sub.message = str(evt["error"])
                    test.error_type = test.error_type or "api"
                    if not test.failed_step:
                        test.failed_step, test.message = name, sub.message
                parent = open_steps.get(str(evt.get("step_id"))) if evt.get("step_id") else current_container()
                (parent.steps if parent else test.steps).append(sub)
            elif et == "assertion":
                ok = bool(evt.get("passed"))
                sub = StepResult(step_id=f"assert-{iso_to_ms(ts)}",
                                 name=f"Assert: {evt.get('name', 'condition')}",
                                 status="passed" if ok else "failed",
                                 start=iso_to_ms(ts), stop=iso_to_ms(ts))
                sub.parameters = [{"name": "expected", "value": str(evt.get("expected"))},
                                  {"name": "actual", "value": str(evt.get("actual"))}]
                if not ok:
                    sub.message = f"expected={evt.get('expected')!r} actual={evt.get('actual')!r}"
                    test.expected = str(evt.get("expected"))
                    test.actual = str(evt.get("actual"))
                    test.error_type = test.error_type or "assertion"
                    if not test.failed_step:
                        test.failed_step, test.message = sub.name, sub.message
                parent = open_steps.get(str(evt.get("step_id"))) if evt.get("step_id") else current_container()
                (parent.steps if parent else test.steps).append(sub)
            elif et == "attachment":
                p = Path(evt.get("path", ""))
                if not p.is_absolute():
                    p = self.run_dir / p
                attach_here(Attachment(evt.get("name", p.name), evt.get("mime", "application/octet-stream"),
                                       path=str(p)), evt.get("step_id"))
            elif et == "test_end":
                test.stop = iso_to_ms(ts)
                test.status = evt.get("status", "unknown")
                if evt.get("message"):
                    test.message = evt["message"]
            elif et == "run_end":
                test.stop = test.stop or iso_to_ms(ts)

        # self-healing: close dangling steps, derive missing status
        for step in list(open_steps.values()):
            step.stop = step.stop or test.stop or step.start
            self.warnings.append(f"step '{step.name}' was never closed; auto-closed")
        if test.status == "unknown":
            def any_failed(steps):
                return any(s.status in ("failed", "broken") or any_failed(s.steps) for s in steps)
            if any_failed(test.steps):
                test.status = "failed"
                self.warnings.append("no test_end event; derived status=failed from steps")
        test.normalize()
        return test, run_meta
