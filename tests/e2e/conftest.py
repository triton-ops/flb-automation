"""Shared fixtures for the tests/e2e/ pure-UI FLB automation suite.

Built on pytest-playwright (page/context/browser fixtures — see requirements-dev.txt) plus the
existing browser/pom/ Page-Object-Model layer. Every step (job build, run, FLR-browse verify,
cleanup) goes through the real Director web UI; no backend RPC calls from this suite.

See the approved design plan (build-out phases, POM-gap list) for the overall rationale. See
docs/allure-reporting.md for everything this file automatically attaches to each test's Allure
entry (screenshot, video, trace, console/network log, test data, environment info).
"""
from __future__ import annotations

import os
import platform
import sys
from importlib.metadata import version as pkg_version
from pathlib import Path

import allure
import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from browser.pom.base.config import ApplianceCredentials, load_app_config  # noqa: E402
from browser.pom.common.login_page import LoginPage  # noqa: E402

_CONSOLE_LOG_KEY = pytest.StashKey[list]()
_NETWORK_LOG_KEY = pytest.StashKey[list]()


def pytest_addoption(parser):
    parser.addoption(
        "--keep-failed-jobs",
        action="store_true",
        default=False,
        help=(
            "Do not delete AUTO_FLB_*/AUTO_FSB_* jobs created by a FAILED test. Default is to "
            "always clean up (pass or fail) so the shared appliance stays debris-free across a "
            "repeatable suite; pass this flag to restore the old manual-workflow convention of "
            "leaving failed jobs in place for inspection."
        ),
    )
    parser.addoption(
        "--visual-update-snapshots",
        action="store_true",
        default=False,
        help=(
            "Overwrite visual-regression baselines (tests/e2e/__snapshots__/) instead of diffing "
            "against them — see docs/visual-regression-pattern.md. Only affects tests using the "
            "assert_matches_snapshot() helper; pass deliberately whenever a fixture's own expected "
            "appearance changes on purpose."
        ),
    )


def pytest_sessionstart(session):
    """Write results/allure-results/environment.properties — Allure's classic (still-supported,
    see docs/allure-reporting.md) convention for the report overview's Environment widget: the
    NBR environment this run targeted (see browser/pom/base/config.py), the browser, and the
    machine. Written once per session, not per test — these don't vary test-to-test."""
    try:
        cfg = load_app_config()
    except Exception:
        return  # a config error surfaces properly via the nbr_config fixture; don't crash here
    results_dir = _REPO_ROOT / "results" / "allure-results"
    results_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        f"NBR_ENV={cfg.environment.value}",
        f"NBR_FLB_URL={cfg.flb.url or '(not configured)'}",
        f"Browser=Chromium {pkg_version('playwright')} (Playwright)",
        f"Machine={platform.node()} ({platform.system()} {platform.release()})",
        f"Python={platform.python_version()}",
    ]
    (results_dir / "environment.properties").write_text("\n".join(lines) + "\n", encoding="utf-8")


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Extend pytest-playwright's default context args: tolerate the appliance's self-signed
    cert, same as browser/pom/base/driver.py's browser_page() (ignore_https_errors=True)."""
    return {
        **browser_context_args,
        "ignore_https_errors": True,
        "viewport": {"width": 1600, "height": 900},
    }


@pytest.fixture
def page(page, request, output_path):
    """Wraps pytest-playwright's own `page` fixture: auto-collects browser console messages and
    network activity for Allure evidence (see docs/allure-reporting.md) — every test using `page`
    (directly, or via logged_in_page below) gets this for free, attached automatically in
    pytest_runtest_makereport's teardown block. Requesting `output_path` here (even though it's
    unused directly) is deliberate: pytest only populates `item.funcargs` with fixtures actually
    named as a parameter somewhere in the requested chain, and pytest-playwright's own
    `output_path` fixture (which the makereport hook needs, to find video.webm/trace.zip) is
    otherwise never named directly by any test — confirmed empirically (item.funcargs omitted it
    until this fixture requested it explicitly)."""
    console_log: list[str] = []
    network_log: list[str] = []
    page.on("console", lambda msg: console_log.append(f"[{msg.type}] {msg.text}"))
    page.on("request", lambda req: network_log.append(f"--> {req.method} {req.url}"))
    page.on("response", lambda res: network_log.append(f"<-- {res.status} {res.url}"))
    request.node.stash[_CONSOLE_LOG_KEY] = console_log
    request.node.stash[_NETWORK_LOG_KEY] = network_log
    return page


@pytest.fixture(scope="session")
def nbr_config() -> ApplianceCredentials:
    """FLB appliance (nbr-84) UI credentials — see browser/pom/base/config.py. Validated here
    (not just loaded) since virtually every test depends on a working FLB login — a missing/
    malformed credential fails fast with a clear ConfigError instead of a confusing downstream
    Playwright/login failure."""
    flb = load_app_config().flb
    flb.validate("NBR_FLB")
    return flb


@pytest.fixture(scope="session")
def nbr_config_fsb() -> ApplianceCredentials:
    """FSB appliance (nbr-5) UI credentials — see browser/pom/base/config.py. Unused by any
    suite yet (none of the 3 ported suites are FSB) — kept for when one is added; not
    auto-validated here since nothing consumes it yet (matches its current unused status)."""
    return load_app_config().fsb


@pytest.fixture
def logged_in_page(page, nbr_config):
    """A Playwright page already signed into the Director UI (nbr-84, FLB)."""
    page.set_default_timeout(20000)
    LoginPage(page).open(nbr_config.url).login(nbr_config.user, nbr_config.password)
    return page


@pytest.fixture
def flb_job_cleanup(request, logged_in_page):
    """Factory fixture: call flb_job_cleanup(job_name) during a test to register an AUTO_FLB_*/
    AUTO_FSB_* job for teardown. Always deletes on PASS. Also deletes on FAIL unless
    --keep-failed-jobs is passed (restores the old manual-workflow convention of leaving failed
    jobs in place for inspection) — see pytest_addoption above.

    Deletes via JobManagementPage.delete_job(), which as of 2026-07-19 also removes the job's
    underlying backup/recovery point (selects 'Delete the job and the backups', not the default
    'keep the backups' radio) — see that method's own docstring. Before this fix, every test run
    across the whole project's history had been silently leaving its backup data behind on the
    target repository, accumulating real debris over time (found live on the Onboard repository:
    119 backups, many long-orphaned)."""
    from browser.pom.common.job_management_page import JobManagementPage

    created: list[str] = []

    def _register(job_name: str) -> str:
        created.append(job_name)
        return job_name

    yield _register

    rep_call = getattr(request.node, "rep_call", None)
    if rep_call is not None and rep_call.failed and request.config.getoption("--keep-failed-jobs"):
        return
    jm = JobManagementPage(logged_in_page)
    for job_name in created:
        try:
            jm.delete_job(job_name)
        except Exception:
            pass


def _test_case_label(item) -> str:
    """`NJM-<id>_<test function name>` when the test carries the suite's `pytest.mark.jira(...)`
    marker, else just the test function name — used to name the video attachment after the actual
    test case rather than a generic label, so downloaded videos from a batch run stay
    distinguishable."""
    jira_marker = item.get_closest_marker("jira")
    jira_id = jira_marker.args[0] if jira_marker and jira_marker.args else None
    return f"{jira_id}_{item.name}" if jira_id else item.name


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Stash each phase's report on the test item (standard pytest recipe) so teardown fixtures
    can check request.node.rep_call.passed/failed, and attach failure evidence + every test's
    recorded video/console/network activity to the Allure report — supplements pytest-playwright's
    own --screenshot/--video/--tracing file output (see pyproject.toml's addopts). Full list of
    what's attached and why: docs/allure-reporting.md.
    """
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)
    if rep.when == "call" and rep.failed:
        pw_page = item.funcargs.get("logged_in_page") or item.funcargs.get("page")
        if pw_page is not None:
            try:
                allure.attach(
                    pw_page.screenshot(full_page=True),
                    name="failure-screenshot",
                    attachment_type=allure.attachment_type.PNG,
                )
            except Exception:
                pass
        # rep.longreprtext is pytest's own rendered failure reason (assertion message + relevant
        # traceback) — attach it as its own entry too, not just relying on Allure's default
        # "test body" panel, so it's visible even in a summary/collapsed view of the report.
        try:
            allure.attach(
                rep.longreprtext,
                name="failure-reason",
                attachment_type=allure.attachment_type.TEXT,
            )
        except Exception:
            pass
    if rep.when == "teardown":
        # By this phase, pytest-playwright's own _artifacts_recorder fixture has already torn
        # down (its teardown runs before ours, since it's a dependency of page/context — see
        # pytest_playwright.py's did_finish_test), so video.webm/trace.zip are fully written and
        # closed.
        output_path = item.funcargs.get("output_path")
        if output_path:
            video_path = os.path.join(output_path, "video.webm")
            if os.path.exists(video_path):
                try:
                    allure.attach.file(
                        video_path,
                        name=f"{_test_case_label(item)}-video",
                        attachment_type=allure.attachment_type.WEBM,
                    )
                except Exception:
                    pass
            # trace.zip only exists for a failed test (pyproject.toml's --tracing=retain-on-failure)
            # — attach whenever pytest-playwright actually wrote one, view with
            # `playwright show-trace <file>`.
            trace_path = os.path.join(output_path, "trace.zip")
            if os.path.exists(trace_path):
                try:
                    allure.attach.file(
                        trace_path,
                        name=f"{_test_case_label(item)}-trace",
                        attachment_type="application/zip",
                        extension="zip",
                    )
                except Exception:
                    pass
        console_log = item.stash.get(_CONSOLE_LOG_KEY, None)
        if console_log:
            try:
                allure.attach(
                    "\n".join(console_log),
                    name="console-log",
                    attachment_type=allure.attachment_type.TEXT,
                )
            except Exception:
                pass
        network_log = item.stash.get(_NETWORK_LOG_KEY, None)
        if network_log:
            try:
                allure.attach(
                    "\n".join(network_log),
                    name="network-log",
                    attachment_type=allure.attachment_type.TEXT,
                )
            except Exception:
                pass
