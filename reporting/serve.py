"""Serve the generated Allure report over HTTP (Allure SPAs don't work from file://).

Usage:
  python -m reporting.serve [--port N]     # default: pick a free port; prints the URL

Self-healing: report dir discovered via ReportConfig; free port chosen automatically;
fails with a clear message if the report has not been generated yet.
"""
from __future__ import annotations

import argparse
import socket
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from .config import ReportConfig


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="reporting.serve")
    ap.add_argument("--port", type=int, default=None)
    ns = ap.parse_args(argv)

    cfg = ReportConfig()
    report = cfg.allure_report_dir
    if not (report / "index.html").exists():
        print(f"no report at {report} — run: python -m reporting.generate --latest", file=sys.stderr)
        return 2

    port = ns.port or _free_port()
    handler = partial(SimpleHTTPRequestHandler, directory=str(report))
    httpd = ThreadingHTTPServer(("127.0.0.1", port), handler)
    print(f"Allure report: http://localhost:{port}/  (Ctrl+C to stop)", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
