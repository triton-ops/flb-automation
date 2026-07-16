"""Standalone cleanup: remove every job on an appliance whose name starts with `AUTO_FLB_`
(or `AUTO_FSB_` for the File Share Backup appliance) — the safety-fence prefix this whole
framework uses (see CLAUDE.md). Talks to the Director's raw ExtDirect endpoint directly
(`<url>/c/router`) via `requests` — no Playwright, no Claude/MCP required, so this can be run by
a human on its own, any time, to reset an appliance back to a clean state.

Usage:
    python browser/checks/cleanup_auto_flb_jobs.py                    # nbr-84, dry-run (list only)
    python browser/checks/cleanup_auto_flb_jobs.py --execute          # nbr-84, actually delete
    python browser/checks/cleanup_auto_flb_jobs.py --fsb --execute    # nbr-5, AUTO_FSB_ prefix
    python browser/checks/cleanup_auto_flb_jobs.py --prefix AUTO_FLB_NJM-679 --execute  # narrower
    python browser/checks/cleanup_auto_flb_jobs.py --keep-backups --execute  # remove [id, true]

Credentials/URL are read from browser/config/ui_config.json (FLB, nbr-84) or
browser/config/ui_config_fsb.json (FSB, nbr-5) — same files the rest of browser/ uses. Env vars
NBR_UI_URL / NBR_UI_USER / NBR_UI_PASS override the file, same convention as pom/base/driver.py.

Safety: only ever touches jobs whose name matches --prefix (default AUTO_FLB_ / AUTO_FSB_ with
--fsb). Never deletes anything else. Dry-run (list, no deletion) is the default; --execute is
required to actually remove jobs.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pom.base.driver import CONFIG_PATH as CONFIG_FLB  # noqa: E402
from pom.base.driver import CONFIG_PATH_FSB as CONFIG_FSB  # noqa: E402
from pom.base.driver import load_config  # noqa: E402  (single source of truth — see driver.py)


class NbrClient:
    """Minimal raw ExtDirect client — one POST per RPC to `<url>/c/router`."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.verify = False  # self-signed appliance cert
        self._tid = 0

    def call(self, action: str, method: str, data: list):
        self._tid += 1
        payload = {"action": action, "method": method, "data": data, "type": "rpc", "tid": self._tid}
        resp = self.session.post(f"{self.base_url}/c/router", json=payload, timeout=30)
        resp.raise_for_status()
        body = resp.json()
        if body.get("type") == "exception":
            raise RuntimeError(f"{action}.{method} failed: {body.get('message')}")
        return body.get("data")

    def login(self, username: str, password: str) -> None:
        result = self.call("AuthenticationManagement", "login", [username, password, False])
        if not result or result.get("result") != "OK":
            raise RuntimeError(f"Login failed: {result}")


def find_matching_jobs(client: NbrClient, prefix: str) -> list[dict]:
    jobs: list[dict] = []
    start = 0
    page = 200
    while True:
        resp = client.call("JobManagement", "getListJobs",
                            [{"start": start, "limit": page, "filters": [], "sorters": []}])
        children = resp.get("children", [])
        jobs.extend(c for c in children if c["name"].startswith(prefix))
        if len(children) < page:
            break
        start += page
    return jobs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fsb", action="store_true", help="target nbr-5 (FSB) instead of nbr-84 (FLB)")
    ap.add_argument("--prefix", default=None, help="override the safety-fence prefix to match")
    ap.add_argument("--execute", action="store_true", help="actually delete (default: dry-run/list)")
    ap.add_argument("--keep-backups", action="store_true",
                     help="pass keepPhysicalItems=true to remove() (keeps recovery points)")
    args = ap.parse_args()

    cfg = load_config(CONFIG_FSB if args.fsb else CONFIG_FLB)
    if not cfg.get("url") or not cfg.get("user") or not cfg.get("password"):
        print("ERROR: missing url/user/password (config file or NBR_UI_URL/NBR_UI_USER/NBR_UI_PASS)",
              file=sys.stderr)
        return 2
    prefix = args.prefix or ("AUTO_FSB_" if args.fsb else "AUTO_FLB_")

    requests.packages.urllib3.disable_warnings()  # self-signed cert, expected noise
    client = NbrClient(cfg["url"])
    client.login(cfg["user"], cfg["password"])

    matches = find_matching_jobs(client, prefix)
    if not matches:
        print(f"No jobs matching prefix '{prefix}' on {cfg['url']}.")
        return 0

    print(f"{len(matches)} job(s) matching '{prefix}' on {cfg['url']}:")
    for j in matches:
        print(f"  id={j['id']:<5} {j['name']}")

    if not args.execute:
        print("\nDry-run only — pass --execute to actually delete these jobs.")
        return 0

    keep = bool(args.keep_backups)
    print(f"\nDeleting {len(matches)} job(s) (keepPhysicalItems={keep})...")
    failures = []
    for j in matches:
        try:
            result = client.call("JobManagement", "remove", [j["id"], keep])
            status = result.get("result") if isinstance(result, dict) else result
            print(f"  id={j['id']:<5} {j['name']:<30} -> {status}")
            if status not in ("OK",):
                failures.append(j)
        except Exception as exc:  # noqa: BLE001 — report and continue
            print(f"  id={j['id']:<5} {j['name']:<30} -> ERROR: {exc}")
            failures.append(j)

    if failures:
        print(f"\n{len(failures)} job(s) failed to delete (see above) — often a lock; retry later.")
        return 1
    print("\nAll matched jobs deleted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
