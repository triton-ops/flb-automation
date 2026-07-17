"""Cross-suite helpers extracted from per-suite _helpers.py files — ONLY functions verified to be
100% identical (or a strict, backward-compatible superset) in behavior across every suite that had
its own copy. This is a deliberate, narrow exception to this project's per-suite _helpers.py
convention (see e.g. test_flbv2v3_FLRFunctional/_helpers.py's own docstring for why suite
isolation is the default): build_flb_job() is NOT here and never should be — its signature and
behavior genuinely diverge per suite (IncludeExclude's inclusion/exclusion patterns and
keyword-only `machine`, Inventory's `repository` param, FLRFunctional's `run_on_demand` toggle),
and forcing one shared signature across three independently-evolving wizard-building call sites
would trade a small amount of duplication for a much larger amount of parameter-juggling
complexity — not a good trade while the FLB wizard's own UI can still drift.

Each function below is safe to share because it contains ZERO suite-specific business logic —
it's pure generic plumbing (poll a job's dashboard status, browse an FLR recovery point, reshape
a list of dicts, verify a downloaded file's checksum against a caller-supplied manifest) that
every suite already called in an identical or near-identical way. See each function's own
docstring for the specific evidence.
"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

import allure

from browser.pom.backup_types.file_level_recovery_page import FileLevelRecoveryPage
from browser.pom.common.checksum import load_manifest, sha256_of_bytes
from browser.pom.common.data_protection_page import DataProtectionPage

MANIFESTS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "test-data" / "manifests"
DOWNLOADS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "results" / "test-results" / "_downloads"


def attach_test_data(job_name: str | None = None, **fields: object) -> None:
    """Attach a structured 'test data' JSON blob (whatever parameters this run actually used —
    machine, drill path, manifest, etc.) to the current test's Allure entry, plus a searchable
    `job_name` label when the test builds a real AUTO_FLB_*/AUTO_FSB_* job. Call once per test,
    right after computing the parameters passed into build_flb_job() (see each suite's own
    build_flb_job() call site — this is generic plumbing, safe to share for the same reason as
    every other function in this module: zero suite-specific business logic)."""
    data: dict[str, object] = {"job_name": job_name, **fields} if job_name else dict(fields)
    allure.attach(
        json.dumps(data, indent=2, default=str),
        name="test-data",
        attachment_type=allure.attachment_type.JSON,
    )
    if job_name:
        allure.dynamic.label("job_name", job_name)


def run_and_wait_flb_job(page, job_name: str, timeout_ms: int = 300_000) -> str:
    """Run `job_name` and poll its dashboard status to a terminal state. Returns the final
    status string (e.g. 'Successful', 'Failed', 'Stopped').

    SAFE TO SHARE: byte-for-byte identical code in all three suites that had it
    (test_flbv2v3_IncludeExclude, test_flbv2v3_Inventory, test_flbv2v3_FLRFunctional) — verified
    via diff, not assumed. The only difference found was a shorter docstring in the
    FLRFunctional copy (missing the "Returns the final status string..." sentence); the
    docstring here is the more complete of the two, carries no suite-specific meaning, and
    changing it doesn't touch behavior. Contains no suite-specific logic: it just selects a job
    by name and polls DataProtectionPage.wait_for_job_status() — a generic capability every
    suite needs identically, since 'run a job and wait for it to finish' has no business-rule
    variation across suites."""
    dp = DataProtectionPage(page)
    dp.open()
    page.wait_for_timeout(1500)
    dp.run_job(job_name)
    return dp.wait_for_job_status(job_name, timeout_ms=timeout_ms, poll_ms=10_000)


def flr_browse(page, job_name: str, path_segments: list[str], nth: int = 0) -> list[dict]:
    """Open File Level Recovery for `job_name`, drill through `path_segments`, read the
    right-hand listing, then cancel the wizard. Browse-only — never selects a recovery type or
    executes a recovery. Returns the recovered items as [{'name', 'modified', 'size'}, ...].

    SAFE TO SHARE, with one explicit judgment call: the CODE BODY is byte-for-byte identical
    across all three suites (verified via diff) EXCEPT for FLRFunctional's version, which adds
    an optional `nth: int = 0` parameter passed straight through to
    FileLevelRecoveryPage.recover_file_level(job_name, nth=nth) — needed there to disambiguate
    same-named jobs when a test builds >1 recovery point for one job (see NJM-70312).
    `recover_file_level()` itself already defaults `nth` to 0, so calling it with `nth=0`
    (the default used by every IncludeExclude/Inventory caller today, since they never pass
    this argument) is IDENTICAL in behavior to calling it without the argument at all — the
    added parameter is a strict, backward-compatible superset, not suite-specific business
    logic (it's a generic disambiguator already built into the POM method this wraps, not a
    business rule). IncludeExclude/Inventory callers are unaffected by this superset signature:
    they don't pass `nth` and get the exact same default behavior as before. Docstrings also
    differed cosmetically (Inventory's was missing the "Returns the recovered items as..."
    sentence); the more complete wording is kept here."""
    flr = FileLevelRecoveryPage(page)
    flr.recover_file_level(job_name, nth=nth)
    page.wait_for_timeout(2000)
    flr.click_next()
    page.wait_for_timeout(2000)
    flr.wait_files_ready(timeout=180_000)
    recovered_items = flr.list_folder_contents(path_segments)
    flr.click_cancel()
    page.wait_for_timeout(1000)
    return recovered_items


def extract_item_names(recovered_items: list[dict]) -> list[str]:
    """SAFE TO SHARE: literally byte-for-byte identical (code AND docstring-free one-liner) in
    all three suites — verified via diff, zero differences of any kind. A pure, stateless list
    reshape with no suite-specific meaning; there is no version of 'get the name field out of
    each dict' that could plausibly diverge per suite."""
    return [item["name"] for item in recovered_items]


def verify_checksum(page, job_name: str, path_segments: list[str], filename: str, manifest_name: str) -> None:
    """Open File Level Recovery for `job_name`, drill to `path_segments`, download `filename`
    via the wizard's real Download recovery type, then assert its SHA-256 matches the entry in
    test-data/manifests/<manifest_name> — the actual content-integrity check a filename-only
    FLR-browse assertion doesn't perform. Raises AssertionError on mismatch; call directly
    inside a test rather than wrapping it.

    SAFE TO SHARE: the two suites that had their own copy (Inventory, FLRFunctional) were
    verified via direct comparison to be functionally identical — same 5 parameters, same
    recover -> drill -> select -> download -> hash -> compare sequence, same zip-unwrapping
    logic. `manifest_name`/`filename`/`path_segments` are caller-supplied DATA, not suite-specific
    CODE, exactly like `flr_browse()`'s `path_segments` argument above — passing different data
    into a generic function doesn't make the function itself suite-specific. The two copies had
    only cosmetic differences (docstring wording, whether `zipfile`/`Path` were imported at
    module level or inside the function) — a prior extraction pass excluded this function based
    on an assumption that it carried suite-specific manifest logic, without actually diffing the
    two bodies; it doesn't."""
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
    zip_path = flr.download_selected(DOWNLOADS_DIR)
    with zipfile.ZipFile(zip_path) as zf:
        matches = [n for n in zf.namelist() if Path(n).name == filename]
        assert matches, f"{filename!r} not found inside downloaded archive {zip_path} (entries: {zf.namelist()})"
        actual = sha256_of_bytes(zf.read(matches[0]))
    # download_selected() already closes the wizard (step 4's 'Close' button) — no click_cancel()
    # needed here (that's for the browse-only flow, which stays on step 2).
    assert actual == expected, (
        f"{filename} checksum mismatch: recovered {actual}, manifest ({manifest_name}) expects {expected}"
    )
