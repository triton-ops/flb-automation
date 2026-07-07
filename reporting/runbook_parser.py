"""RunbookParser + MetadataExtractor — runbooks are the single source of truth for metadata.

Parses the existing runbook markdown format (cases/**/<ID>.md) tolerantly (fail-soft: missing
fields degrade to sensible defaults, never crash). Test authors write metadata ONCE, in the
runbook; Allure labels are derived automatically.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

_SEVERITY = {"blocker": "blocker", "critical": "critical", "major": "normal",
             "minor": "minor", "trivial": "trivial"}


@dataclass
class RunbookMeta:
    test_id: str = "UNKNOWN"
    title: str = "Unknown test case"
    feature: str = "File-Level Backup"
    epic: str = "FLB-Share Product"
    story: str = ""
    owner: str = ""
    severity: str = "normal"
    priority: str = ""
    tags: list[str] = field(default_factory=list)
    suite: str = "cases"
    backup_type: str = "FLB"
    repository_type: str = ""
    transporter: str = ""
    environment: str = ""
    appliance: str = ""
    description: str = ""
    feasibility: str = ""
    path: str = ""

    def as_labels(self) -> list[dict]:
        labels = [
            {"name": "epic", "value": self.epic},
            {"name": "feature", "value": self.feature},
            {"name": "suite", "value": self.suite},
            {"name": "owner", "value": self.owner or "unknown"},
            {"name": "severity", "value": self.severity},
            {"name": "framework", "value": "flb-automation"},
        ]
        if self.story:
            labels.append({"name": "story", "value": self.story})
        for t in self.tags:
            labels.append({"name": "tag", "value": t})
        # domain labels (filterable in Allure)
        for name, value in (("repositoryType", self.repository_type),
                            ("backupType", self.backup_type),
                            ("transporter", self.transporter),
                            ("environment", self.environment or self.appliance)):
            if value:
                labels.append({"name": name, "value": value})
        return labels


def _bullet(md: str, key: str) -> str:
    m = re.search(rf"^- \*\*{re.escape(key)}:?\*\*:?\s*(.+)$", md, re.M)
    return m.group(1).strip() if m else ""


def parse_runbook(path: Path) -> RunbookMeta:
    meta = RunbookMeta(path=str(path))
    try:
        md = Path(path).read_text(encoding="utf-8")
    except OSError:
        return meta  # fail-soft: report still generates with defaults

    meta.suite = Path(path).parent.name or "cases"

    m = re.search(r"^#\s+(\S+)\s+—\s+(.+)$", md, re.M)
    if m:
        meta.test_id, meta.title = m.group(1), m.group(2).strip()

    feature = _bullet(md, "Feature")
    if feature:
        meta.feature = re.sub(r"\s*<!--.*?-->\s*", "", feature).strip()
        meta.backup_type = "FSB" if "share" in feature.lower() else "FLB"

    appl = _bullet(md, "Appliance")
    if appl:
        meta.appliance = appl.split("—")[0].strip()
        meta.environment = meta.appliance.split(" ")[0]

    # Metadata: testcase_id=..., author=..., date=..., product=..., status=...
    meta_line = _bullet(md, "Metadata")
    kv = dict(re.findall(r"(\w+)=([^,]+)", meta_line))
    meta.test_id = kv.get("testcase_id", meta.test_id).strip()
    meta.owner = kv.get("author", "").strip()

    meta.feasibility = _bullet(md, "Feasibility")

    src = _bullet(md, "Source TC")
    sev = re.search(r"\b(Blocker|Critical|Major|Minor|Trivial)\b", src, re.I)
    if sev:
        meta.priority = sev.group(1)
        meta.severity = _SEVERITY.get(sev.group(1).lower(), "normal")
    for tag in re.findall(r"label[s]?\s+([\w\-]+)", src, re.I):
        meta.tags.append(tag)
    story = re.search(r"US\d+|UC\d+(?:\s*&\s*UC\d+)?", md)
    if story:
        meta.story = story.group(0)

    # Repository fixture -> repositoryType (first bold value on the Repository line)
    m = re.search(r"^- Repository:\s*\*\*([^*]+)\*\*", md, re.M)
    if m:
        meta.repository_type = m.group(1).strip().rstrip(":")

    m = re.search(r"^## Objective\s*\n(.*?)(?=\n##|\Z)", md, re.S | re.M)
    if m:
        meta.description = re.sub(r"\s+", " ", m.group(1)).strip()

    return meta


def find_runbook(cases_dir: Path, test_id: str) -> Path | None:
    """Discover the runbook for a test id anywhere under cases/ (no hard-coded folder)."""
    hits = sorted(cases_dir.rglob(f"{test_id}.md"))
    return hits[0] if hits else None
