"""AllureMapper — the SINGLE Allure-aware component.

Everything upstream speaks the domain model (TestResult/StepResult/Attachment). If Allure's
result-file schema ever changes, this file is the only one to touch.
Writes Allure 2 JSON: <uuid>-result.json (+ attachments via AttachmentManager).
"""
from __future__ import annotations

import hashlib
import json
import uuid as _uuid
from pathlib import Path

from .attachments import AttachmentManager
from .model import StepResult, TestResult
from .runbook_parser import RunbookMeta


class AllureMapper:
    def __init__(self, allure_results_dir: Path, attachments: AttachmentManager):
        self.dir = Path(allure_results_dir)
        self.att = attachments

    def _map_step(self, step: StepResult) -> dict:
        return {
            "name": step.name,
            "status": step.status,
            "statusDetails": {"message": step.message} if step.message else {},
            "stage": "finished",
            "start": step.start, "stop": step.stop or step.start,
            "parameters": step.parameters,
            "steps": [self._map_step(s) for s in step.steps],
            "attachments": [a for a in (self.att.materialize(x) for x in step.attachments) if a],
        }

    def write_result(self, test: TestResult, meta: RunbookMeta, run_id: str) -> Path:
        result_uuid = str(_uuid.uuid4())
        history_id = hashlib.md5(f"{meta.suite}.{test.test_id}".encode()).hexdigest()
        doc = {
            "uuid": result_uuid,
            "historyId": history_id,                       # stable per TC -> trends/retries work
            "testCaseId": test.test_id,
            "name": f"{test.test_id} — {meta.title}" if meta.title else test.test_id,
            "fullName": f"{meta.suite}.{test.test_id}",
            "description": meta.description or test.description,
            "status": test.status,
            "statusDetails": {"message": test.message, "trace": test.trace},
            "stage": "finished",
            "start": test.start, "stop": test.stop or test.start,
            "labels": meta.as_labels() + [{"name": "package", "value": meta.suite},
                                          {"name": "thread", "value": run_id}],
            "parameters": test.parameters,
            "links": [],
            "steps": [self._map_step(s) for s in test.steps],
            "attachments": [a for a in (self.att.materialize(x) for x in test.attachments) if a],
        }
        self.dir.mkdir(parents=True, exist_ok=True)
        out = self.dir / f"{result_uuid}-result.json"
        # ensure_ascii: some Allure CLI builds mis-decode UTF-8 result files on Windows (cp1252),
        # so non-ASCII (em-dashes etc.) is escaped rather than emitted raw.
        out.write_text(json.dumps(doc, indent=1, ensure_ascii=True, default=str), encoding="utf-8")
        return out
