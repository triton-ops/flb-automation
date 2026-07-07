"""CategoriesReporter — automatic failure classification buckets for the Allure dashboard.

Regexes intentionally mirror failure_analyzer's message format `[Category] — ...` so the
analyzer's classification and the dashboard buckets can never drift apart.
"""
from __future__ import annotations

import json
from pathlib import Path

DEFAULT_CATEGORIES = [
    {"name": "Environment Issue (BLOCKED)", "matchedStatuses": ["skipped"],
     "messageRegex": ".*(BLOCKED|Environment Issue|requires ).*"},
    {"name": "Assertion Failure", "matchedStatuses": ["failed"],
     "messageRegex": r".*(Assertion Failure|expected=).*"},
    {"name": "Timeout", "matchedStatuses": ["failed", "broken"],
     "messageRegex": ".*([Tt]imeout|timed out).*"},
    {"name": "API Error", "matchedStatuses": ["broken"],
     "messageRegex": ".*(API Error|RPC|Exception|HTTP).*"},
    {"name": "Configuration Error", "matchedStatuses": ["failed", "broken"],
     "messageRegex": ".*(Configuration Error|placeholder|missing required).*"},
    {"name": "Product Bug (suspected)", "matchedStatuses": ["failed"],
     "messageRegex": ".*(Product Bug|lrState|ict45|error135|error346|error374).*"},
    {"name": "Infrastructure / Network", "matchedStatuses": ["broken"],
     "messageRegex": ".*(unreachable|connection|network|TLS|certificate).*"},
    {"name": "Automation Bug", "matchedStatuses": ["broken"],
     "messageRegex": ".*(journal|auto-closed|never closed|malformed).*"},
]


def write_categories(allure_results_dir: Path) -> Path:
    allure_results_dir.mkdir(parents=True, exist_ok=True)
    p = allure_results_dir / "categories.json"
    p.write_text(json.dumps(DEFAULT_CATEGORIES, indent=2), encoding="utf-8")
    return p
