"""flb-automation reporting layer.

Execution emits structured events (journal.jsonl per run) — see `events.py` / `emit.py`.
This package consumes those events and produces Allure results/reports — see `generate.py`.
Execution code NEVER touches the Allure API; `allure_mapper.py` is the single Allure-aware seam.
"""
__version__ = "1.0.0"
