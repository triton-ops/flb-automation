"""BackupCopyRecoveryPage — recovery for a Backup Copy job's target backup. CALIBRATED live
2026-07-08 against nbr-84 (built and ran two temporary AUTO_FLB_ calibration jobs copying
BACKUP_OBJECT-40 (Linux_16.84, an FLB/PHYSICAL source) to different repos, then removed both).

The key finding (confirmed at BOTH the RPC and UI layers): a Backup Copy job's own top-level
`hvType` is always the fixed `"VMWARE"` (see BackupCopyPage) — but its RECOVER MENU and the
FLR RPC layer both key off the ORIGINAL source type of whatever was copied, not that fixed
`"VMWARE"` value or the job's own `type:"BACKUP_COPY"`.

- **UI**: selecting a Backup Copy job and clicking Recover opens the SAME 'GRANULAR RECOVERY'
  menu every job type shares (Individual files / File level recovery / File share recovery /
  Object recovery for .../ etc., plus a 'PHYSICAL MACHINE FULL RECOVERY' section) — it is NOT
  a distinct 'Backup Copy recovery' menu. Only the items matching the copied backup's ORIGINAL
  source type are enabled; the rest render greyed-out but are still present in the DOM.
  Confirmed live: copying an FLB (PHYSICAL) backup enables 'File level recovery' and disables
  'File share recovery' in that exact menu.
- **RPC**: `FileLevelRecoveryManagement.createSession` needs `hvType` matching the ORIGINAL
  source (`"PHYSICAL"` for a copied FLB backup — verified live, mount + browse succeeded
  against the copy's own BACKUP_OBJECT/savepoint id; `"NAS"` for a copied FSB backup is
  expected by the same logic but not separately verified here — see
  FileShareRecoveryPage/recipes/file-backup-recipes.md R7 for the FSB-native case that WAS
  verified). The Backup Copy job's own fixed `"VMWARE"` hvType is NEVER the right value for
  this call, matching the UI's own behavior.

Environment note (not a POM bug): a freshly-completed Backup Copy's savepoint can come back
`isAccessible:false` on some repos (observed on an S3-compatible Cloudian target — the UI's own
Recover button was correctly greyed out too, consistent with the RPC state) while an otherwise
identical copy to a LOCAL repo was `isAccessible:true` immediately. If Recover is disabled for
a Backup Copy job, check the target repo's own health/accessibility before assuming a locator
or recipe problem.

USAGE:
  This class provides recovery entry points for BOTH Backup Copy source types. Choose the entry
  method matching the ORIGINAL source type of what was copied:

  pg = BackupCopyRecoveryPage(page)
  pg.recover_file_level(job_name, nth)   # copied backup's original source was FLB (PHYSICAL)
  pg.recover_file_share(job_name, nth)   # copied backup's original source was FSB (NAS)

  Both methods are available (inherited from FileShareRecoveryPage chain). click_cancel()
  (inherited) handles both FLB-style one-click close and FSB-style confirm popover generically.
"""
from __future__ import annotations

from .file_share_recovery_page import FileShareRecoveryPage


class BackupCopyRecoveryPage(FileShareRecoveryPage):
    """Recovery page for Backup Copy jobs.

    Inherits from FileShareRecoveryPage to ensure both recover_file_level() and
    recover_file_share() methods are available, since:
    - recover_file_level() comes from grandparent FileLevelRecoveryPage (for FLB-sourced copies)
    - recover_file_share() comes from parent FileShareRecoveryPage (for FSB-sourced copies)

    Callers must know the original source type of the Backup Copy job and call the matching
    recovery entry method accordingly.
    """
    pass
