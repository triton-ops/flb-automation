"""Unit tests for browser/pom/base/config.py — the typed, multi-environment configuration system
(see docs/configuration.md). Pure logic, no browser/appliance access: fast and deterministic.

Every test isolates itself from the real repo .env/.env.* and JSON fallback files (by
monkeypatching config's _REPO_ROOT/CONFIG_PATH/CONFIG_PATH_FSB to a throwaway tmp_path) and from
the real process environment, so nothing here ever reads or could leak a real secret, and results
never depend on whatever happens to be configured in the real .env right now.
"""
from __future__ import annotations

import os

import pytest

from browser.pom.base import config as config_module
from browser.pom.base.config import (
    ApplianceCredentials,
    ConfigError,
    Environment,
    ShareCredentials,
    current_environment,
    load_app_config,
)

pytestmark = pytest.mark.config_unit

_NBR_ENV_KEYS = [
    "NBR_FLB_URL", "NBR_FLB_USER", "NBR_FLB_PASS",
    "NBR_FSB_URL", "NBR_FSB_USER", "NBR_FSB_PASS",
    "NBR_UI_URL", "NBR_UI_USER", "NBR_UI_PASS",
    "WINFS3_USER", "WINFS3_PASS",
]


@pytest.fixture(autouse=True)
def _isolated_config(tmp_path, monkeypatch):
    monkeypatch.setattr(config_module, "_REPO_ROOT", tmp_path)
    monkeypatch.setattr(config_module, "CONFIG_PATH", tmp_path / "ui_config.json")
    monkeypatch.setattr(config_module, "CONFIG_PATH_FSB", tmp_path / "ui_config_fsb.json")
    monkeypatch.delenv("NBR_ENV", raising=False)
    for key in _NBR_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    yield tmp_path
    # load_dotenv() writes directly into os.environ, bypassing monkeypatch's own tracking/revert
    # — clean up explicitly so a fake value this test's .env/.env.<env> injected can never leak
    # into a real appliance-touching test running later in the same pytest session.
    for key in _NBR_ENV_KEYS:
        os.environ.pop(key, None)


def test_default_environment_is_local():
    assert current_environment() is Environment.LOCAL


def test_current_environment_reads_nbr_env_case_insensitively(monkeypatch):
    monkeypatch.setenv("NBR_ENV", "QA")
    assert current_environment() is Environment.QA


def test_unknown_nbr_env_value_raises_config_error(monkeypatch):
    monkeypatch.setenv("NBR_ENV", "bogus")
    with pytest.raises(ConfigError, match="bogus"):
        current_environment()


def test_selecting_unprovisioned_environment_raises_and_names_the_file(monkeypatch):
    monkeypatch.setenv("NBR_ENV", "staging")
    with pytest.raises(ConfigError, match=r"\.env\.staging"):
        load_app_config()


def test_local_environment_needs_no_overlay_file():
    # no .env, no .env.local written in this test's tmp_path — local must still resolve cleanly
    # (to an unconfigured-but-valid AppConfig), never raise.
    cfg = load_app_config()
    assert cfg.environment is Environment.LOCAL
    assert cfg.flb.is_configured is False


def test_env_overlay_wins_over_base_env_for_a_shared_key(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text(
        "NBR_FLB_URL=https://base.example\nNBR_FLB_USER=base_user\nNBR_FLB_PASS=base_pass\n"
    )
    (tmp_path / ".env.dev").write_text("NBR_FLB_URL=https://dev.example\n")
    monkeypatch.setenv("NBR_ENV", "dev")
    cfg = load_app_config()
    assert cfg.flb.url == "https://dev.example"  # overlay wins over the base file
    assert cfg.flb.user == "base_user"           # base fills the gap the overlay didn't set
    assert cfg.flb.password == "base_pass"


def test_real_env_var_wins_over_both_dotenv_files(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("NBR_FLB_URL=https://base.example\n")
    monkeypatch.setenv("NBR_FLB_URL", "https://shell.example")
    cfg = load_app_config()
    assert cfg.flb.url == "https://shell.example"


def test_appliance_credentials_validate_lists_every_problem():
    creds = ApplianceCredentials(url=None, user=None, password=None)
    with pytest.raises(ConfigError) as exc_info:
        creds.validate("NBR_FLB")
    message = str(exc_info.value)
    assert "NBR_FLB_URL" in message
    assert "NBR_FLB_USER" in message
    assert "NBR_FLB_PASS" in message


def test_appliance_credentials_validate_rejects_malformed_url():
    creds = ApplianceCredentials(url="nbr-84.example.com", user="u", password="p")
    with pytest.raises(ConfigError, match="http"):
        creds.validate("NBR_FLB")


def test_appliance_credentials_validate_passes_for_valid_creds():
    creds = ApplianceCredentials(url="https://nbr-84.example.com:4443", user="u", password="p")
    creds.validate("NBR_FLB")  # must not raise


def test_is_configured_reflects_real_state():
    assert ApplianceCredentials(url="https://x", user="u", password="p").is_configured is True
    assert ApplianceCredentials(url=None, user="u", password="p").is_configured is False


def test_share_credentials_validate():
    with pytest.raises(ConfigError):
        ShareCredentials(user=None, password=None).validate("WINFS3")
    ShareCredentials(user="u", password="p").validate("WINFS3")  # must not raise


def test_app_config_share_reads_host_prefixed_env_vars(monkeypatch):
    monkeypatch.setenv("WINFS3_USER", "share_user")
    monkeypatch.setenv("WINFS3_PASS", "share_pass")
    cfg = load_app_config()
    creds = cfg.share("winfs3")
    assert creds.user == "share_user"
    assert creds.password == "share_pass"
