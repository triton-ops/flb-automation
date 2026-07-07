"""FailureAnalyzer — turns a failed/broken/skipped result into a meaningful analysis.

Never a bare "Test Failed": statusDetails carries expected/actual/failed step/category, and a
'failure-analysis.md' attachment gives investigation guidance.
"""
from __future__ import annotations

from .model import Attachment, TestResult

# (category, matched statuses, message-substring heuristics) — mirrored in categories.py regexes
_RULES = [
    ("Environment Issue",   ("skipped",), ("blocked", "requires ", "not present", "inaccessible")),
    ("Timeout",             ("failed", "broken"), ("timeout", "timed out", "max wait")),
    ("API Error",           ("broken",), ("exception", "rpc", "http", "login")),
    ("Assertion Failure",   ("failed",), ("expected=",)),
    ("Configuration Error", ("failed", "broken"), ("placeholder", "missing required", "validation")),
    ("Product Bug (suspected)", ("failed",), ("lrstate", "error135", "ict45", "error346", "error374")),
]


def classify(test: TestResult) -> str:
    msg = (test.message or "").lower()
    for cat, statuses, needles in _RULES:
        if test.status in statuses and any(n in msg for n in needles):
            return cat
    if test.error_type == "assertion":
        return "Assertion Failure"
    if test.error_type == "api":
        return "API Error"
    return "Unknown"


def analyze(test: TestResult) -> None:
    """Enrich statusDetails + attach a failure-analysis document. No-op on pass."""
    if test.status == "passed":
        return
    category = classify(test)
    parts = [f"[{category}]"]
    if test.failed_step:
        parts.append(f"failed step: {test.failed_step}")
    if test.expected or test.actual:
        parts.append(f"expected: {test.expected} | actual: {test.actual}")
    if test.message and test.message not in " ".join(parts):
        parts.append(test.message)
    test.message = " — ".join(parts) if parts else (test.message or f"{test.status} without detail")

    suggestion = {
        "Environment Issue": "Provision the missing fixture named in the message, then re-run. "
                             "This is not a product defect (verdict BLOCKED by design).",
        "Timeout": "Check job progress in Activities; verify transporter/repo throughput; "
                   "raise the poll budget for large/cloud targets.",
        "API Error": "Inspect the attached RPC request/response; re-introspect the method with "
                     "describe_method (spec drift); check appliance reachability/session.",
        "Assertion Failure": "Compare expected vs actual in the assertion step parameters; check the "
                             "FLR browse/export evidence attachments.",
        "Configuration Error": "Fix the runbook/template payload named in the message (ValidationBuilder output).",
        "Product Bug (suspected)": "Reproduce manually once; capture appliance logs; file a defect "
                                   "linking this report and the RPC evidence.",
        "Unknown": "Read the execution journal attachment; the failure did not match known patterns.",
    }[category]

    body = "\n".join([
        "# Failure analysis",
        f"- **Status:** {test.status}",
        f"- **Category:** {category}",
        f"- **Failed step:** {test.failed_step or 'n/a'}",
        f"- **Expected:** {test.expected or 'n/a'}",
        f"- **Actual:** {test.actual or 'n/a'}",
        f"- **Message:** {test.message}",
        "",
        "## Suggested investigation",
        suggestion,
    ])
    test.attachments.append(Attachment("failure-analysis.md", "text/markdown",
                                       content=body.encode("utf-8")))
