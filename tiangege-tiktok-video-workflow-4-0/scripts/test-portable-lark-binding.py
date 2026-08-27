#!/usr/bin/env python3
"""Regression checks for portable, per-user Feishu destination binding."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from urllib.parse import urlparse


WORKFLOW_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = WORKFLOW_ROOT.parent
SHARED_ROOTS = (
    WORKFLOW_ROOT,
    SKILLS_ROOT / "archive-tk-materials",
    SKILLS_ROOT / "generate-tk-scripts",
)
PRIVATE_CONFIG = (
    Path(os.environ["LOCALAPPDATA"])
    / "tiangege-tiktok-workflow"
    / "lark-destination.json"
)
ARCHIVE_SCRIPT = SKILLS_ROOT / "archive-tk-materials" / "scripts" / "build-write-plan.py"


def load_archive_module():
    spec = importlib.util.spec_from_file_location("build_write_plan", ARCHIVE_SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def shared_text_files():
    for root in SHARED_ROOTS:
        for path in root.rglob("*"):
            if path.is_file() and path.suffix.lower() in {".md", ".json", ".py", ".yaml", ".yml"}:
                if path.resolve() != Path(__file__).resolve():
                    yield path


def sample_artifacts():
    account = {
        "pipeline_id": "tk-content-pipeline/v1",
        "artifact_type": "account_manifest",
        "videos": [{"video_id": "portable-test"}],
    }
    return account, None


def main() -> None:
    errors: list[str] = []

    if not PRIVATE_CONFIG.exists():
        errors.append(f"本机私有绑定不存在: {PRIVATE_CONFIG}")
        private_config = None
    else:
        private_config = json.loads(PRIVATE_CONFIG.read_text(encoding="utf-8-sig"))
        required_tables = {"original_videos", "step2_breakdowns", "elements", "scripts"}
        if private_config.get("binding_scope") != "local-user":
            errors.append("本机绑定缺少 binding_scope=local-user")
        if required_tables - set(private_config.get("tables", {})):
            errors.append("本机绑定没有覆盖 01/02/03/04")

    sensitive_values: set[str] = set()
    if private_config is not None:
        for key in ("workspace_name", "base_url", "base_token"):
            value = private_config.get(key)
            if isinstance(value, str) and value:
                sensitive_values.add(value)
        base_url = private_config.get("base_url")
        if isinstance(base_url, str) and urlparse(base_url).hostname:
            sensitive_values.add(urlparse(base_url).hostname or "")
        for table in private_config.get("tables", {}).values():
            if not isinstance(table, dict):
                continue
            for key in ("id", "view_id"):
                value = table.get(key)
                if isinstance(value, str) and value:
                    sensitive_values.add(value)
            primary = table.get("primary_field")
            if isinstance(primary, dict) and isinstance(primary.get("id"), str):
                sensitive_values.add(primary["id"])

    for path in shared_text_files():
        text = path.read_text(encoding="utf-8-sig")
        leaked = sorted(value for value in sensitive_values if value and value in text)
        if leaked:
            errors.append(f"共享 Skill 泄露了 {len(leaked)} 个本机目标标识: {path}")

    module = load_archive_module()
    account, breakdown = sample_artifacts()
    try:
        unbound = module.build_plan(account, breakdown, None)
    except TypeError:
        errors.append("build_plan 尚不支持显式的个人目标配置")
    else:
        if unbound.get("safe_to_write") is not False:
            errors.append("未绑定机器生成了可写计划")
        if unbound.get("target", {}).get("binding_status") != "unbound":
            errors.append("未绑定计划没有标记 binding_status=unbound")
        table_ids = [item.get("table_id") for item in unbound.get("tables", {}).values()]
        if any(table_ids):
            errors.append("未绑定计划仍携带真实 table_id")

    if private_config is not None:
        try:
            bound = module.build_plan(account, breakdown, private_config)
        except TypeError:
            pass
        else:
            if bound.get("target", {}).get("binding_status") != "bound":
                errors.append("本机私有配置未被识别为 bound")
            if bound.get("target", {}).get("workspace_name") != private_config.get("workspace_name"):
                errors.append("本机计划没有使用私有配置中的 workspace_name")

    print(json.dumps({"valid": not errors, "private_config": str(PRIVATE_CONFIG), "errors": errors}, ensure_ascii=False, indent=2))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
