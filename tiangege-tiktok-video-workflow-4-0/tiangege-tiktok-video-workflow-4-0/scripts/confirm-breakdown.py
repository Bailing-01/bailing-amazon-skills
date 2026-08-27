#!/usr/bin/env python3
"""Idempotently record explicit step-2 approval on a completed breakdown bundle."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


PIPELINE_ID = "tk-content-pipeline/v1"


def fail(message: str) -> None:
    print(json.dumps({"confirmed": False, "error": message}, ensure_ascii=False))
    raise SystemExit(1)


def validate_bundle(path: Path) -> None:
    validator = (
        Path(__file__).resolve().parents[2]
        / "deconstruct-tk-video"
        / "scripts"
        / "validate-breakdown-bundle.py"
    )
    if not validator.is_file():
        fail(f"deconstruct validator not found: {validator}")

    result = subprocess.run(
        [sys.executable, str(validator), str(path)],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        detail = (result.stdout or result.stderr).strip()
        fail(f"breakdown bundle validation failed: {detail}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Mark a completed breakdown_bundle.json as explicitly approved."
    )
    parser.add_argument("bundle", help="Path to breakdown_bundle.json")
    args = parser.parse_args()

    path = Path(args.bundle).expanduser().resolve()
    if not path.is_file():
        fail(f"bundle not found: {path}")

    validate_bundle(path)

    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:  # noqa: BLE001
        fail(f"invalid JSON: {exc}")

    if payload.get("pipeline_id") != PIPELINE_ID:
        fail(f"pipeline_id must be {PIPELINE_ID}")
    if payload.get("artifact_type") != "breakdown_bundle":
        fail("artifact_type must be breakdown_bundle")
    if payload.get("schema_version") != 1:
        fail("schema_version must be 1")
    if not isinstance(payload.get("videos"), list) or not payload["videos"]:
        fail("videos must be a non-empty array")

    confirmation = payload.get("batch_confirmation")
    if not isinstance(confirmation, dict):
        fail("batch_confirmation must be an object")
    if confirmation.get("step1_confirmed") is not True:
        fail("step1_confirmed must be true before step-2 approval")
    if confirmation.get("step2_completed") is not True:
        fail("step2_completed must be true before step-2 approval")

    if confirmation.get("step2_confirmed") is True:
        print(
            json.dumps(
                {
                    "confirmed": True,
                    "changed": False,
                    "bundle": str(path),
                    "step2_confirmed_at": confirmation.get("step2_confirmed_at"),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    confirmation["step2_confirmed"] = True
    confirmation["step2_confirmed_at"] = (
        datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    )

    handle, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise

    print(
        json.dumps(
            {
                "confirmed": True,
                "changed": True,
                "bundle": str(path),
                "step2_confirmed_at": confirmation["step2_confirmed_at"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
