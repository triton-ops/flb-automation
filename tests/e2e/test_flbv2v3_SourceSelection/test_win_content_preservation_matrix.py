r"""NJM-68971 / 68977 / 68978 / 68979 / 68981 / 68982 / 68983 — [FLB v2] FLB - Functional -
Verify Backup/Recovery of special-name / special-type files on Windows:

  * NJM-68971 — Non-ASCII (Unicode) filenames  (Cyrillic файл.txt, CJK 测试文件.docx, Arabic ملف.pdf)
  * NJM-68983 — Dotfiles                        (.hidden_config, .env.sample)
  * NJM-68982 — Files without an extension      (READMEnoext, Makefile)
  * NJM-68981 — Various file extensions         (sample.iso, sample.exe)
  * NJM-68978 — Common archive files            (sample.zip, sample.rar)
  * NJM-68977 — Hidden files                    (hidden_attr.txt, +h attribute)
  * NJM-68979 — Shortcut files (.lnk)           (shortcut.lnk)

PARAMETRIZE PATTERN (see docs/parametrize-pattern.md, same as the FLRFunctional OS-support matrix):
these 7 TCs' Xray steps are structurally identical — back up a Windows folder containing the
special file(s), run the job, open FLR, select the special file(s), recover them to a CIFS share,
verify the recovered content matches the source — differing ONLY in which filename(s) the row
targets. They therefore share one body and one seeded fixture, with one pytest.param per TC
(each carrying its own jira marker + id).

FIXTURE (seeded 2026-07-18, registered in test-data/test-data.md §7): C:\SpecialFiles_ForFLB on
Window11 (win11 / 10.10.16.157), a single flat folder holding all 13 probe files above.
Source SHA-256 oracle: test-data/manifests/manifest-win11-specialfiles.sha256. Re-seed with the
idempotent WinRM PowerShell in that manifest's test-data.md §7 entry.

SCOPE NOTE (same convention as the whole FLRFunctional suite): pytest asserts the job reached
Successful and the FLR wizard confirmed the recovery started. The TC's verdict-carrying step
("recovered filenames/content match the originals") is the agent-driven destination check —
comparing the landed Recovered-items-*.zip's entries on win-fs3 against the manifest above — and
is reported alongside this test's result, not as a pytest assertion (pytest can't call the
remoting tools). Each row backs up the WHOLE folder (so hidden files and the .lnk are in scope
regardless of picker display) and recovers only its own target file(s).
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, recover_to_share, run_and_wait_flb_job

pytestmark = [
    pytest.mark.flb, pytest.mark.sourceselection,
    # All rows build a job against the same Window11 source — serialize them (and against any
    # other Window11-sourced test) so two jobs never hit one source at once (see
    # docs/xdist-parallelization.md and the no-concurrent-jobs-same-source rule).
    pytest.mark.xdist_group(name="Window11"),
]

MACHINE = "Window11"
FIXTURE_FOLDER = "SpecialFiles_ForFLB"
MANIFEST = "manifest-win11-specialfiles.sha256"

# (jira_id, label, [filenames to recover]) — one row per TC.
CONTENT_MATRIX = [
    pytest.param(
        "NJM-68971", "unicode filenames",
        ["файл.txt", "测试文件.docx", "ملف.pdf"],
        marks=pytest.mark.jira("NJM-68971"), id="NJM-68971-unicode",
    ),
    pytest.param(
        "NJM-68983", "dotfiles",
        [".hidden_config", ".env.sample"],
        marks=pytest.mark.jira("NJM-68983"), id="NJM-68983-dotfiles",
    ),
    pytest.param(
        "NJM-68982", "extensionless files",
        ["READMEnoext", "Makefile"],
        marks=pytest.mark.jira("NJM-68982"), id="NJM-68982-extensionless",
    ),
    pytest.param(
        "NJM-68981", "various extensions (.iso/.exe)",
        ["sample.iso", "sample.exe"],
        marks=pytest.mark.jira("NJM-68981"), id="NJM-68981-extensions",
    ),
    pytest.param(
        "NJM-68978", "archive files (.zip/.rar)",
        ["sample.zip", "sample.rar"],
        marks=pytest.mark.jira("NJM-68978"), id="NJM-68978-archives",
    ),
    pytest.param(
        "NJM-68977", "hidden files",
        ["hidden_attr.txt"],
        marks=pytest.mark.jira("NJM-68977"), id="NJM-68977-hidden",
    ),
    pytest.param(
        "NJM-68979", "shortcut files (.lnk)",
        ["shortcut.lnk"],
        marks=pytest.mark.jira("NJM-68979"), id="NJM-68979-lnk",
    ),
]


@pytest.mark.parametrize("jira_id,label,filenames", CONTENT_MATRIX)
def test_special_file_backup_recovery(logged_in_page, flb_job_cleanup, jira_id, label, filenames):
    allure.dynamic.title(f"{jira_id} — backup/recovery of {label} (Windows, recover to CIFS)")
    page = logged_in_page
    job_name = flb_job_cleanup(f"AUTO_FLB_{jira_id}")

    build_flb_job(page, job_name, MACHINE, ["Local Disk (C:)"], [FIXTURE_FOLDER])
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed for {label}: {status}"

    started = recover_to_share(
        page, job_name, ["C:", FIXTURE_FOLDER], filenames, "cifs"
    )
    assert started, f"the FLR wizard did not confirm the recovery started for {label}"
