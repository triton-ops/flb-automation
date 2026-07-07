"""EnvironmentReporter — auto-generates environment.properties (self-healing, fail-soft).

Every value is DISCOVERED, never hard-coded: product/build from the run_start event (the
executor knows the live appliance), framework version from the package, host/OS from the
machine, git commit only if a git repo exists. Missing values are simply omitted.
"""
from __future__ import annotations

import platform
import socket
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from . import __version__
from .runbook_parser import RunbookMeta


def _git_commit(repo_root: Path) -> str | None:
    if not (repo_root / ".git").exists():
        return None
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=repo_root,
                             capture_output=True, text=True, timeout=10)
        return out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def build_environment(run_meta: dict, meta: RunbookMeta, repo_root: Path) -> dict[str, str]:
    env: dict[str, str | None] = {
        "Product.Version": run_meta.get("product_version"),
        "Product.Build": run_meta.get("build_number"),
        "Appliance": run_meta.get("appliance") or meta.appliance,
        "Environment": run_meta.get("environment") or meta.environment,
        "Repository.Type": meta.repository_type,
        "Backup.Type": meta.backup_type,
        "Transporter": meta.transporter,
        "Framework.Version": f"flb-automation reporting {__version__}",
        "Executor": run_meta.get("executor", "Claude (nbr MCP / ExtDirect RPC)"),
        "OS": f"{platform.system()} {platform.release()}",
        "Python": platform.python_version(),
        "Execution.Host": socket.gethostname(),
        "Execution.Timestamp": run_meta.get("ts") or datetime.now(UTC).isoformat(),
        "Git.Commit": _git_commit(repo_root),
    }
    return {k: v for k, v in env.items() if v}


def write_environment(allure_results_dir: Path, env: dict[str, str]) -> Path:
    allure_results_dir.mkdir(parents=True, exist_ok=True)
    p = allure_results_dir / "environment.properties"
    p.write_text("".join(f"{k}={v}\n" for k, v in sorted(env.items())), encoding="utf-8")
    return p
