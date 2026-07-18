"""Shared build/run/verify helpers for the FLBv2v3_ObjectStorage suite (NJM-182721, execution C).

Covers backup-to-repository TCs across the object storage / cloud repositories documented in
test-data/environment.md's "FLB target repositories (nbr-84)" section: Amazon S3 (Amazon_Repo /
Amazon_Immutable), Azure Blob (Azure_Repo / Azure_Immutable), Wasabi (Wasabi_Repo /
Wasabi-immutable), Backblaze (BlackBlaze_Immutable — no plain non-immutable Backblaze repo exists
on nbr-84; reused without the immutability option for the non-immutable TC, same substitution
convention environment.md already documents for Cloudian/Ceph_S3), Local-Immutable, and Onboard.

⚠ IMPORTANT CAVEAT (from environment.md, re-verified 2026-07-08): none of the `*_Immutable`-named
repos have actually been proven to produce a real immutable savepoint yet — this suite's
immutable-repo tests are genuinely first-time, unproven territory. Report honestly what happens
(pass, fail, or "immutability had no observable effect"), never force a fake pass.

Reuses the SAME MixedTypes fixture + per-OS SHA-256 manifest oracle every other suite already
relies on (test-data/manifests/manifest-win11-mixed.sha256, manifest-linux-mixed.sha256) — the
repo destination is the variable under test here, not the fixture content, so no new fixture is
seeded. build_flb_job() is cloned (not imported) from the sibling suites deliberately, per
_lib/_shared_helpers.py's own documented convention (build_flb_job() diverges per suite and the
FLB wizard UI can still drift).

INCREMENTAL-RUN METHODOLOGY (corrected 2026-07-19 — see run_full_then_incremental()'s own
docstring for the full reasoning): a real incremental backup captures the CHANGE since the last
backup (confirmed both by the Confluence "File Level Backup v1" FRD — "Transporter performs the
incremental backup using the base files" — and live: re-running an already-backed-up job's
Backup-type combo defaults to 'Incremental', not 'Full'). An earlier version of this suite tried
to force a second recovery point by re-editing the job's OWN item SELECTION between runs — that
does not exercise incremental-backup semantics at all (it changes what's in scope, not what
changed on disk) and depended on a since-fixed picker_drill() bug. Genuinely changing source
content between runs would need live SSH/WinRM access from INSIDE the pytest process, which this
project does not have (the same deferred gap test_flbv2v3_IncludeExclude/test_njm_185023.py
already documented — mcp__remoting__* is only callable by the agent driving a session, not by
Python code a pytest run executes) — so, matching that same precedent's honest compromise, this
suite runs the SAME job twice unmodified (full, then a second run which the product itself
defaults to Incremental) rather than editing the selection.
"""
from __future__ import annotations

from browser.pom.backup_types.flb_wizard_page import FlbWizardPage
from browser.pom.common.data_protection_page import DataProtectionPage
from tests.e2e._lib._shared_helpers import (
    attach_test_data,
    extract_item_names,
    flr_browse,
    run_and_wait_flb_job,
    verify_checksum,
)

__all__ = [
    "attach_test_data",
    "build_flb_job",
    "extract_item_names",
    "flr_browse",
    "run_and_wait_flb_job",
    "run_full_then_incremental",
    "verify_checksum",
]


def build_flb_job(
    page,
    job_name: str,
    machine: str,
    drill_path: list[str],
    checks: list[str],
    *,
    is_linux: bool = False,
    repository: str = "Onboard repository",
    encryption: bool = False,
    run_on_demand: bool = True,
) -> FlbWizardPage:
    """Build (but do not run) an FLB job via the wizard through Finish. Same contract as the
    sibling suites' build_flb_job(), plus `encryption` (default False, unchanged behavior for
    every caller that doesn't pass it) — toggles the Options step's already-calibrated
    'Backup encryption' combo (FlbWizardPage.set_encryption(), CALIBRATED live 2026-07-08)."""
    attach_test_data(
        job_name=job_name, machine=machine, drill_path=drill_path, checks=checks,
        is_linux=is_linux, repository=repository, encryption=encryption, run_on_demand=run_on_demand,
    )
    dp = DataProtectionPage(page)
    dp.open().open_create_menu().start_file_level_backup()
    flb = FlbWizardPage(page).on_sources_step()
    if is_linux:
        flb.expand_linux()
    else:
        flb.expand_windows()
    flb.select_machine(machine)
    flb.open_item_picker()
    flb.select_items(drill_path, checks)
    flb.picker_apply()
    flb.click_next()  # Inclusion
    flb.click_next()  # Exclusion
    flb.click_next()  # Destination
    flb.select_repository(repository)
    flb.click_next()  # Schedule
    if run_on_demand:
        flb.set_run_on_demand()
    flb.click_next()  # Options
    flb.set_job_name(job_name)
    if encryption:
        flb.set_encryption(True)
    flb.finish()
    page.wait_for_timeout(2000)
    return flb


def run_full_then_incremental(page, job_name: str, timeout_ms: int = 600_000) -> tuple[str, str]:
    """Run `job_name` twice, unmodified, and return (full_status, incremental_status).

    RE-CALIBRATED live 2026-07-19: confirmed directly in the Director UI — once a job already
    has a recovery point, its own 'Run this job?' dialog's 'Backup type' combo defaults to
    'Incremental' (screenshot-verified: selected value 'Incremental', not 'Full', with no
    interaction needed). run_and_wait_flb_job() → DataProtectionPage.run_job() already just
    clicks through this dialog's default, so calling it a SECOND time on the same job already
    performs a genuine incremental run — no Source-step re-selection, no explicit backup-type
    combo interaction, and no edit_job()/picker_drill() round-trip needed at all. See this
    module's own docstring for why a between-runs SOURCE CONTENT change (the more literal
    reading of 'incremental') isn't exercised here.

    CALIBRATED live 2026-07-19: run_job()'s own docstring already documents the dashboard's Run
    toolbar button re-enabling with a lag after a job just finished (extended to a 60s
    click_visible timeout there) — but back-to-back calls with NO gap at all still hit that
    60s ceiling in practice. A short settle wait between the two runs (the dashboard's status
    transition needs a moment to fully propagate after wait_for_job_status() already reported
    'Successful') reliably avoids it."""
    full_status = run_and_wait_flb_job(page, job_name, timeout_ms=timeout_ms)
    page.wait_for_timeout(5000)
    incremental_status = run_and_wait_flb_job(page, job_name, timeout_ms=timeout_ms)
    return full_status, incremental_status
