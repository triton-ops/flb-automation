"""Shared fixtures for the tests/e2e/ pure-UI FLB automation suite.

Built on pytest-playwright (page/context/browser fixtures — see requirements-dev.txt) plus the
existing browser/pom/ Page-Object-Model layer. Every step (job build, run, FLR-browse verify,
cleanup) goes through the real Director web UI; no backend RPC calls from this suite.

See the approved design plan (build-out phases, POM-gap list) for the overall rationale.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import allure
import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from browser.pom.base.driver import CONFIG_PATH, CONFIG_PATH_FSB, load_config  # noqa: E402
from browser.pom.common.login_page import LoginPage  # noqa: E402


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


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Extend pytest-playwright's default context args: tolerate the appliance's self-signed
    cert, same as browser/pom/base/driver.py's browser_page() (ignore_https_errors=True)."""
    return {
        **browser_context_args,
        "ignore_https_errors": True,
        "viewport": {"width": 1600, "height": 900},
    }


@pytest.fixture(scope="session")
def nbr_config() -> dict:
    """FLB appliance (nbr-84) UI credentials — browser/config/ui_config.json."""
    return load_config(CONFIG_PATH)


@pytest.fixture(scope="session")
def nbr_config_fsb() -> dict:
    """FSB appliance (nbr-5) UI credentials — browser/config/ui_config_fsb.json. Unused by any
    suite yet (none of the 3 ported suites are FSB) — kept for when one is added."""
    return load_config(CONFIG_PATH_FSB)


@pytest.fixture
def logged_in_page(page, nbr_config):
    """A Playwright page already signed into the Director UI (nbr-84, FLB)."""
    page.set_default_timeout(20000)
    LoginPage(page).open(nbr_config["url"]).login(nbr_config["user"], nbr_config["password"])
    return page


@pytest.fixture
def flb_job_cleanup(request, logged_in_page):
    """Factory fixture: call flb_job_cleanup(job_name) during a test to register an AUTO_FLB_*/
    AUTO_FSB_* job for teardown. Always deletes on PASS. Also deletes on FAIL unless
    --keep-failed-jobs is passed (restores the old manual-workflow convention of leaving failed
    jobs in place for inspection) — see pytest_addoption above."""
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
    can check request.node.rep_call.passed/failed, and attach a screenshot + the test's recorded
    video to the Allure report — supplements pytest-playwright's own --screenshot/--video file
    output (see pyproject.toml's addopts).
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
    if rep.when == "teardown":
        # By this phase, pytest-playwright's own _artifacts_recorder fixture has already torn
        # down (its teardown runs before ours, since it's a dependency of page/context — see
        # pytest_playwright.py's did_finish_test), so video.webm is fully written and closed.
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
