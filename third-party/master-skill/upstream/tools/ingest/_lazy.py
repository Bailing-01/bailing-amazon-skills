"""_lazy.py — shared lazy-install helper for the ingest tools.

Usage:
    from _lazy import ensure_pkg
    ensure_pkg("pymupdf", import_name="fitz")
    import fitz

If the import fails, prompts the user (interactive tty) before running
`python3 -m pip install <pkg>`. Pass AUTO_YES=1 in env to skip prompts.
On non-tty stdin without AUTO_YES, raises SystemExit so the caller can
print a friendly install message.
"""
from __future__ import annotations

import importlib
import os
import subprocess
import sys


def _confirm(question: str) -> bool:
    if os.environ.get("AUTO_YES") == "1":
        print(f"{question} [auto-yes]", file=sys.stderr)
        return True
    if not sys.stdin.isatty():
        print(
            f"ERROR: stdin not a tty; refusing to silently install. "
            f"Set AUTO_YES=1 or run interactively. ({question})",
            file=sys.stderr,
        )
        return False
    try:
        ans = input(f"{question} [y/N] ")
    except EOFError:
        return False
    return ans.strip().lower().startswith("y")


def check_pkg(pkg: str, import_name: str | None = None) -> bool:
    """Return True if pkg is importable, False otherwise. Doesn't prompt or
    install. Used by --check-deps mode in ingest tools."""
    name = import_name or pkg
    try:
        importlib.import_module(name)
        return True
    except ImportError:
        return False


def ensure_pkg(pkg: str, import_name: str | None = None) -> None:
    """Try to import `import_name` (default: same as pkg). On ImportError,
    prompt to `pip install pkg` and retry. Raises SystemExit if user declines
    or pip fails."""
    name = import_name or pkg
    if check_pkg(pkg, import_name):
        return
    print(f"\n[lazy-install] {pkg} not installed.", file=sys.stderr)
    print(f"             will install via:  python3 -m pip install {pkg}", file=sys.stderr)
    if not _confirm(f"Proceed with python3 -m pip install {pkg}?"):
        print(
            f"ABORT: {pkg} required. Run manually:\n  python3 -m pip install {pkg}",
            file=sys.stderr,
        )
        raise SystemExit(4)
    # Send pip output to stderr so stdout stays clean for JSON output
    rc = subprocess.call(
        [sys.executable, "-m", "pip", "install", pkg],
        stdout=sys.stderr,
        stderr=sys.stderr,
    )
    if rc != 0:
        print(f"ERROR: pip install {pkg} failed (exit {rc})", file=sys.stderr)
        raise SystemExit(5)
    importlib.invalidate_caches()
    try:
        importlib.import_module(name)
    except ImportError as e:
        print(f"ERROR: still can't import {name} after install: {e}", file=sys.stderr)
        raise SystemExit(6)
