"""Backup Copy Recovery POM dry-run: verify BackupCopyRecoveryPage structure and method
availability for both FLB (PHYSICAL) and FSB (NAS) sourced backup copies.

This is a CODE-ONLY dry run (no UI interaction, no live appliance calls). It validates:
1. BackupCopyRecoveryPage correctly inherits from FileShareRecoveryPage
2. Both recover_file_level() and recover_file_share() methods are available
3. The inheritance chain provides the right methods from the right parents

Run: cd browser && python checks/check_backup_copy_recovery.py
"""
from __future__ import annotations

import sys
from pathlib import Path
from inspect import signature

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pom.backup_types.backup_copy_recovery_page import BackupCopyRecoveryPage
from pom.backup_types.file_level_recovery_page import FileLevelRecoveryPage
from pom.backup_types.file_share_recovery_page import FileShareRecoveryPage

TC = "check_backup_copy_recovery"
results = []


def check_inheritance():
    """Verify correct inheritance chain."""
    # BackupCopyRecoveryPage should inherit from FileShareRecoveryPage
    assert issubclass(BackupCopyRecoveryPage, FileShareRecoveryPage), \
        "BackupCopyRecoveryPage must inherit from FileShareRecoveryPage"

    # FileShareRecoveryPage should inherit from FileLevelRecoveryPage
    assert issubclass(FileShareRecoveryPage, FileLevelRecoveryPage), \
        "FileShareRecoveryPage must inherit from FileLevelRecoveryPage"

    # BackupCopyRecoveryPage is thus also a FileLevelRecoveryPage
    assert issubclass(BackupCopyRecoveryPage, FileLevelRecoveryPage), \
        "BackupCopyRecoveryPage must be a subclass of FileLevelRecoveryPage"

    results.append(("Inheritance chain correct", True))


def check_method_availability():
    """Verify both recovery methods are available on BackupCopyRecoveryPage."""
    # Check recover_file_level method (from FileLevelRecoveryPage)
    assert hasattr(BackupCopyRecoveryPage, 'recover_file_level'), \
        "BackupCopyRecoveryPage must have recover_file_level method"
    assert callable(getattr(BackupCopyRecoveryPage, 'recover_file_level')), \
        "recover_file_level must be callable"

    # Check recover_file_share method (from FileShareRecoveryPage)
    assert hasattr(BackupCopyRecoveryPage, 'recover_file_share'), \
        "BackupCopyRecoveryPage must have recover_file_share method"
    assert callable(getattr(BackupCopyRecoveryPage, 'recover_file_share')), \
        "recover_file_share must be callable"

    results.append(("Both recovery methods available", True))


def check_method_signatures():
    """Verify method signatures match expectations."""
    # recover_file_level(job_name, nth=0)
    flr_sig = signature(BackupCopyRecoveryPage.recover_file_level)
    flr_params = list(flr_sig.parameters.keys())
    assert 'job_name' in flr_params and 'nth' in flr_params, \
        f"recover_file_level signature mismatch: {flr_params}"

    # recover_file_share(job_name, nth=0)
    fsr_sig = signature(BackupCopyRecoveryPage.recover_file_share)
    fsr_params = list(fsr_sig.parameters.keys())
    assert 'job_name' in fsr_params and 'nth' in fsr_params, \
        f"recover_file_share signature mismatch: {fsr_params}"

    results.append(("Method signatures correct", True))


def check_docstrings():
    """Verify docstrings are present and helpful."""
    # Class docstring should exist
    assert BackupCopyRecoveryPage.__doc__, \
        "BackupCopyRecoveryPage must have a docstring"
    assert 'Backup Copy' in BackupCopyRecoveryPage.__doc__, \
        "Class docstring must mention 'Backup Copy'"
    assert 'FLB' in BackupCopyRecoveryPage.__doc__ or 'PHYSICAL' in BackupCopyRecoveryPage.__doc__, \
        "Class docstring should mention FLB/PHYSICAL source type"
    assert 'FSB' in BackupCopyRecoveryPage.__doc__ or 'NAS' in BackupCopyRecoveryPage.__doc__, \
        "Class docstring should mention FSB/NAS source type"

    # Module docstring should include usage examples
    import pom.backup_types.backup_copy_recovery_page as module
    assert module.__doc__, "Module must have a docstring"
    assert 'recover_file_level' in module.__doc__, \
        "Module docstring should show recover_file_level usage"
    assert 'recover_file_share' in module.__doc__, \
        "Module docstring should show recover_file_share usage"
    assert 'FLB' in module.__doc__ or 'PHYSICAL' in module.__doc__, \
        "Module docstring should explain FLB/PHYSICAL usage"
    assert 'FSB' in module.__doc__ or 'NAS' in module.__doc__, \
        "Module docstring should explain FSB/NAS usage"

    results.append(("Docstrings present and comprehensive", True))


def main() -> int:
    """Run all dry-run checks."""
    print(f"\n[{TC}] Running Backup Copy Recovery POM dry-run...\n")

    try:
        check_inheritance()
        check_method_availability()
        check_method_signatures()
        check_docstrings()
    except AssertionError as e:
        results.append((str(e), False))
        print(f"\n[{TC}] ERROR: {e}\n")
        return 1
    except Exception as e:
        results.append((f"Unexpected error: {e}", False))
        print(f"\n[{TC}] EXCEPTION: {e}\n")
        return 1

    # Print results
    print(f"\n[{TC}] Results:")
    for label, passed in results:
        status = 'PASS' if passed else 'FAIL'
        print(f"   {status}  {label}")

    allpass = all(p for _, p in results)
    if allpass:
        print(f"\n[{TC}] ALL PASS — BackupCopyRecoveryPage structure verified")
        print(f"[{TC}] Both recover_file_level() and recover_file_share() available")
        print(f"[{TC}] Ready for UI-based integration tests")
    else:
        print(f"\n[{TC}] FAILURES — See above")

    return 0 if allpass else 1


if __name__ == "__main__":
    raise SystemExit(main())
