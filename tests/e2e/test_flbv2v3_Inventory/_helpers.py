"""Shared build/run/verify helpers for the FLBv2v3_Inventory suite (NJM-182726).

Each TC verifies FLB end-to-end workflow (create -> run -> FLR recover -> compare) on a specific
OS/filesystem source. Most Windows/Linux TCs share the same 7-file MixedTypes verification
fileset (see test-data/test-data.md's MixedTypes convention, seeded identically in shape across
every source in this suite).

NOTE — shared-source serialization: several TCs here target the SAME physical machine as other
TCs in this suite (e.g. NJM-67807 and NJM-68933 both use Linux_16.84/PM-2). Per the project's
"no concurrent jobs against the same source" finding (a source VID locks/stalls rather than
queueing), these tests must not be run concurrently with each other (e.g. via pytest-xdist) —
plain sequential `pytest` execution is safe since each test's build+run+poll+cleanup completes
before the next test starts.
"""
from __future__ import annotations

import zipfile
from pathlib import Path

from browser.pom.backup_types.file_level_recovery_page import FileLevelRecoveryPage
from browser.pom.backup_types.flb_wizard_page import FlbWizardPage
from browser.pom.common.checksum import load_manifest, sha256_of_bytes
from browser.pom.common.data_protection_page import DataProtectionPage

MANIFESTS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "test-data" / "manifests"

MIXED_TYPES_FILES = {
    "sample.pdf", "sample.xml", "sample.json", "sample.docx", "sample.sys", "sample.jpg", "sample.mp4",
}


def build_flb_job(
    page,
    job_name: str,
    machine: str,
    drill_path: list[str],
    checks: list[str],
    *,
    is_linux: bool = False,
    repository: str = "Onboard repository",
) -> FlbWizardPage:
    """Build (but do not run) an FLB job via the wizard through Finish."""
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
    flb.set_run_on_demand()
    flb.click_next()  # Options
    flb.set_job_name(job_name)
    flb.finish()
    page.wait_for_timeout(2000)
    return flb


def run_and_wait_flb_job(page, job_name: str, timeout_ms: int = 300_000) -> str:
    """Run `job_name` and poll its dashboard status to a terminal state. Returns the final
    status string (e.g. 'Successful', 'Failed', 'Stopped')."""
    dp = DataProtectionPage(page)
    dp.open()
    page.wait_for_timeout(1500)
    dp.run_job(job_name)
    return dp.wait_for_job_status(job_name, timeout_ms=timeout_ms, poll_ms=10_000)


def flr_browse(page, job_name: str, path_segments: list[str]) -> list[dict]:
    """Open File Level Recovery for `job_name`, drill through `path_segments`, read the
    right-hand listing, then cancel the wizard. Browse-only — never selects a recovery type
    or executes a recovery."""
    flr = FileLevelRecoveryPage(page)
    flr.recover_file_level(job_name)
    page.wait_for_timeout(2000)
    flr.click_next()
    page.wait_for_timeout(2000)
    flr.wait_files_ready(timeout=180_000)
    recovered_items = flr.list_folder_contents(path_segments)
    flr.click_cancel()
    page.wait_for_timeout(1000)
    return recovered_items


def extract_item_names(recovered_items: list[dict]) -> list[str]:
    return [item["name"] for item in recovered_items]


def verify_checksum(page, job_name: str, path_segments: list[str], filename: str, manifest_name: str) -> None:
    """Open File Level Recovery for `job_name`, drill to `path_segments`, download `filename`
    via the wizard's real Download recovery type, then assert its SHA-256 matches the entry in
    test-data/manifests/<manifest_name> — the actual content-integrity check the filename-only
    FLR-browse assertions elsewhere in this suite don't perform. Raises AssertionError on
    mismatch; call directly inside a test rather than wrapping it."""
    manifest = load_manifest(MANIFESTS_DIR / manifest_name)
    expected = manifest.get(filename)
    assert expected, f"{filename!r} not found in manifest {manifest_name}"

    flr = FileLevelRecoveryPage(page)
    flr.recover_file_level(job_name)
    page.wait_for_timeout(2000)
    flr.click_next()
    page.wait_for_timeout(2000)
    flr.wait_files_ready(timeout=180_000)
    flr.drill_to(path_segments)
    flr.select_file_in_current_folder(filename)
    # CALIBRATED live 2026-07-16: the FLR wizard's Download recovery type always wraps its
    # output in a 'Recovered-items-<timestamp>.zip' archive, even for a single selected file —
    # confirmed via magic-byte inspection (PK\x03\x04) of a raw downloaded file that otherwise
    # hashed cleanly through the whole pipeline. Extract the target entry from inside the zip
    # (matched by basename — the archive mirrors the source's folder structure) and hash ITS
    # bytes, not the archive container's.
    download_dir = Path(__file__).resolve().parent.parent.parent.parent / "results" / "test-results" / "_downloads"
    zip_path = flr.download_selected(download_dir)
    with zipfile.ZipFile(zip_path) as zf:
        matches = [n for n in zf.namelist() if Path(n).name == filename]
        assert matches, f"{filename!r} not found inside downloaded archive {zip_path} (entries: {zf.namelist()})"
        actual = sha256_of_bytes(zf.read(matches[0]))
    # download_selected() already closes the wizard (step 4's 'Close' button) — no click_cancel()
    # needed here (that's for the browse-only flow, which stays on step 2).
    assert actual == expected, (
        f"{filename} checksum mismatch: recovered {actual}, manifest ({manifest_name}) expects {expected}"
    )
