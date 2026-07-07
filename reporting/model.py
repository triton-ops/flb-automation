"""Execution result model — the in-memory representation between journal and Allure.

Pure data (no Allure, no I/O). Built by event_reader, enriched by failure_analyzer,
serialized by allure_mapper.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

VALID_STATUSES = {"passed", "failed", "broken", "skipped", "unknown"}


def iso_to_ms(ts: str | None) -> int | None:
    if not ts:
        return None
    try:
        return int(datetime.fromisoformat(ts).timestamp() * 1000)
    except ValueError:
        return None


@dataclass
class Attachment:
    name: str
    mime: str = "text/plain"
    path: str | None = None      # file on disk (relative to run dir or absolute)
    content: bytes | None = None  # or inline content


@dataclass
class StepResult:
    step_id: str
    name: str
    status: str = "passed"
    start: int | None = None   # ms epoch
    stop: int | None = None
    message: str = ""
    trace: str = ""
    parameters: list[dict] = field(default_factory=list)
    steps: list[StepResult] = field(default_factory=list)
    attachments: list[Attachment] = field(default_factory=list)


@dataclass
class TestResult:
    test_id: str
    name: str = ""
    status: str = "unknown"
    start: int | None = None
    stop: int | None = None
    message: str = ""
    trace: str = ""
    steps: list[StepResult] = field(default_factory=list)
    attachments: list[Attachment] = field(default_factory=list)
    labels: list[dict] = field(default_factory=list)
    description: str = ""
    parameters: list[dict] = field(default_factory=list)
    # failure-analysis inputs collected from events
    failed_step: str = ""
    expected: str = ""
    actual: str = ""
    error_type: str = ""

    def normalize(self) -> None:
        if self.status not in VALID_STATUSES:
            self.status = "unknown"
