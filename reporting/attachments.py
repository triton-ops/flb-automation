"""AttachmentManager — the ONLY place that writes attachment files into allure-results.

Handles both inline content and on-disk paths; missing files are skipped gracefully with a
warning (the report still generates). MIME -> extension mapping is centralized here.
"""
from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from .model import Attachment

_EXT = {
    "application/json": ".json", "text/plain": ".txt", "text/markdown": ".md",
    "image/png": ".png", "image/jpeg": ".jpg", "text/csv": ".csv",
    "application/octet-stream": ".bin", "text/html": ".html",
}


class AttachmentManager:
    def __init__(self, allure_results_dir: Path):
        self.dir = Path(allure_results_dir)
        self.warnings: list[str] = []

    def materialize(self, att: Attachment) -> dict | None:
        """Write the attachment into allure-results; return the Allure attachment dict."""
        self.dir.mkdir(parents=True, exist_ok=True)
        ext = _EXT.get(att.mime) or (Path(att.path).suffix if att.path else ".bin") or ".bin"
        source = f"{uuid.uuid4()}-attachment{ext}"
        target = self.dir / source
        try:
            if att.content is not None:
                target.write_bytes(att.content)
            elif att.path:
                src = Path(att.path)
                if not src.exists():
                    self.warnings.append(f"attachment missing, skipped: {att.name} ({src})")
                    return None
                if att.mime == "application/octet-stream":
                    guessed = {".png": "image/png", ".jpg": "image/jpeg", ".json": "application/json",
                               ".md": "text/markdown", ".txt": "text/plain", ".log": "text/plain",
                               ".html": "text/html"}.get(src.suffix.lower())
                    if guessed:
                        att.mime = guessed
                        source = f"{uuid.uuid4()}-attachment{src.suffix.lower()}"
                        target = self.dir / source
                shutil.copyfile(src, target)
            else:
                return None
        except OSError as e:
            self.warnings.append(f"attachment failed, skipped: {att.name} ({e})")
            return None
        return {"name": att.name, "source": source, "type": att.mime}
