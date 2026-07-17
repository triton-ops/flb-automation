"""Typed, validated, multi-environment configuration — see docs/configuration.md for the full
writeup. Supersedes this module's former load_config()/CONFIG_PATH/CONFIG_PATH_FSB/
load_share_credentials() (moved here from driver.py, which now only holds the browser factory).

Environment switching: the NBR_ENV env var (local/dev/qa/staging/production, case-insensitive,
default "local") selects which named environment's config is loaded. Only "local" has real data
today — this project's only real targets are the nbr-84 (FLB) and nbr-5 (FSB) lab appliances (see
test-data/environment.md), not a deployed app with dev/QA/staging/production tiers. The other
4 names are real, working extension points: selecting one without its .env.<environment> file
raises ConfigError rather than silently reusing "local"'s values or inventing a fake one.

Secrets isolation / .env layering, highest precedence first (every layer is non-destructive, so a
real shell/CI-exported env var always wins over any file):
    1. process env vars already set (shell export, CI secrets)
    2. .env.<environment> (only for non-"local" environments; raises ConfigError if selected but
       missing)
    3. .env (base — today's real lab-appliance values; loaded for every environment)
    4. browser/config/ui_config*.json (gitignored legacy fallback — kept for byte-for-byte
       backward compatibility with any setup that predates .env)
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from dotenv import load_dotenv

_BROWSER_DIR = Path(__file__).resolve().parent.parent.parent
_REPO_ROOT = _BROWSER_DIR.parent

# Legacy JSON fallback paths — lowest-priority layer, unchanged from the former driver.py.
CONFIG_PATH = _BROWSER_DIR / "config" / "ui_config.json"          # nbr-84 (FLB)
CONFIG_PATH_FSB = _BROWSER_DIR / "config" / "ui_config_fsb.json"  # nbr-5 (FSB)

_ENV_VAR = "NBR_ENV"


class Environment(str, Enum):
    LOCAL = "local"
    DEV = "dev"
    QA = "qa"
    STAGING = "staging"
    PRODUCTION = "production"


class ConfigError(Exception):
    """Raised for anything about the resolved configuration that isn't valid or isn't
    provisioned yet — an unknown NBR_ENV value, a selected environment missing its .env file, or
    missing/malformed appliance credentials. Always names the exact problem(s), never a generic
    message, so the fix is obvious from the error alone."""


@dataclass(frozen=True)
class ApplianceCredentials:
    """A Director UI login target (nbr-84/FLB or nbr-5/FSB)."""

    url: str | None
    user: str | None
    password: str | None

    @property
    def is_configured(self) -> bool:
        return bool(self.url and self.user and self.password)

    def validate(self, label: str) -> None:
        """Raise ConfigError listing every problem at once (not just the first) if this
        appliance's credentials are missing or malformed."""
        errors = []
        if not self.url:
            errors.append(f"{label}_URL is not set")
        elif not self.url.startswith(("http://", "https://")):
            errors.append(f"{label}_URL must start with http:// or https:// (got {self.url!r})")
        if not self.user:
            errors.append(f"{label}_USER is not set")
        if not self.password:
            errors.append(f"{label}_PASS is not set")
        if errors:
            raise ConfigError(f"Invalid {label} configuration: " + "; ".join(errors))


@dataclass(frozen=True)
class ShareCredentials:
    """Credentials for a non-NBR fixture host used as an FLR CIFS/NFS export target (e.g.
    win-fs3 — see test-data/environment.md). Distinct from ApplianceCredentials: this
    authenticates a share mount from inside the FLR wizard, not the Director UI itself."""

    user: str | None
    password: str | None

    def validate(self, label: str) -> None:
        errors = []
        if not self.user:
            errors.append(f"{label}_USER is not set")
        if not self.password:
            errors.append(f"{label}_PASS is not set")
        if errors:
            raise ConfigError(f"Invalid {label} share configuration: " + "; ".join(errors))


@dataclass(frozen=True)
class AppConfig:
    environment: Environment
    flb: ApplianceCredentials
    fsb: ApplianceCredentials

    def share(self, host: str) -> ShareCredentials:
        prefix = host.upper()
        return ShareCredentials(
            user=os.environ.get(f"{prefix}_USER"),
            password=os.environ.get(f"{prefix}_PASS"),
        )


def current_environment() -> Environment:
    """The environment named by NBR_ENV (default "local"). Raises ConfigError for any value that
    isn't one of the 5 known environment names."""
    raw = os.environ.get(_ENV_VAR, Environment.LOCAL.value).strip().lower()
    try:
        return Environment(raw)
    except ValueError:
        valid = ", ".join(e.value for e in Environment)
        raise ConfigError(f"Invalid {_ENV_VAR}={raw!r} — must be one of: {valid}") from None


def _load_dotenv_layers(environment: Environment) -> None:
    if environment is not Environment.LOCAL:
        overlay = _REPO_ROOT / f".env.{environment.value}"
        if not overlay.is_file():
            raise ConfigError(
                f"Environment {environment.value!r} was selected via {_ENV_VAR}, but "
                f"{overlay.name} was not found at {overlay}. This environment has not been "
                f"provisioned yet — see .env.example's environment-overlay section for how to "
                f"add it."
            )
        load_dotenv(overlay, override=False)
    # Loaded second (not first) so a value already set by the overlay above wins over this base
    # file — but a real pre-existing shell/CI var (set before either load) still wins over both,
    # since override=False never clobbers an existing os.environ key regardless of source.
    load_dotenv(_REPO_ROOT / ".env", override=False)


def _json_fallback(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def _appliance_from_env(prefix: str, json_fallback: dict, legacy_prefix: str | None = None) -> ApplianceCredentials:
    url = os.environ.get(f"{prefix}URL")
    user = os.environ.get(f"{prefix}USER")
    password = os.environ.get(f"{prefix}PASS")
    if legacy_prefix:
        url = url or os.environ.get(f"{legacy_prefix}URL")
        user = user or os.environ.get(f"{legacy_prefix}USER")
        password = password or os.environ.get(f"{legacy_prefix}PASS")
    return ApplianceCredentials(
        url=url or json_fallback.get("url"),
        user=user or json_fallback.get("user"),
        password=password or json_fallback.get("password"),
    )


def load_app_config(environment: Environment | None = None) -> AppConfig:
    """Resolve the typed config for `environment` (default: current_environment(), i.e. NBR_ENV
    or "local"). See this module's docstring for the full .env layering/precedence order."""
    env = environment or current_environment()
    _load_dotenv_layers(env)
    flb = _appliance_from_env("NBR_FLB_", _json_fallback(CONFIG_PATH), legacy_prefix="NBR_UI_")
    fsb = _appliance_from_env("NBR_FSB_", _json_fallback(CONFIG_PATH_FSB))
    return AppConfig(environment=env, flb=flb, fsb=fsb)
