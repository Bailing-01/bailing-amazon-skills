#!/usr/bin/env python3
"""Verify the 4.0 orchestrator exposes script generation without weakening gates."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "SKILL.md"
CONTRACT = ROOT / "references" / "workflow-contract.md"
OPENAI_YAML = ROOT / "agents" / "openai.yaml"


def main() -> None:
    errors: list[str] = []
    files = {
        "SKILL.md": SKILL.read_text(encoding="utf-8-sig"),
        "workflow-contract.md": CONTRACT.read_text(encoding="utf-8-sig"),
        "openai.yaml": OPENAI_YAML.read_text(encoding="utf-8-sig"),
    }
    skill = files["SKILL.md"]
    contract = files["workflow-contract.md"]
    metadata = files["openai.yaml"]

    required_skill_markers = {
        "$generate-tk-scripts": "106 stage is not delegated",
        "script_bundle.json": "script artifact is missing",
        "gpt-5.6-sol": "required semantic model is missing",
        "默认六版": "default six-script route is missing",
        "明确要求九版": "explicit nine-script expansion is missing",
        "review": "review mode is missing",
        "auto-local": "auto-local mode is missing",
        "auto-all": "auto-all mode is missing",
        "04 新脚本库": "Feishu 04 boundary is missing",
        "step2_confirmed=true": "confirmed breakdown gate is missing",
    }
    for marker, message in required_skill_markers.items():
        if marker not in skill:
            errors.append(f"SKILL.md: {message}: {marker}")

    forbidden_skill_markers = {
        "且不需要 106 新脚本生成": "frontmatter still excludes scripts",
        "禁止调用 `$generate-tk-scripts`": "body still forbids 106",
        "4.0 必须在 105 停止": "workflow still stops at 105",
        "默认三版": "workflow still defaults to three scripts",
    }
    for marker, message in forbidden_skill_markers.items():
        if marker in skill:
            errors.append(f"SKILL.md: {message}: {marker}")

    required_contract_markers = {
        "106 脚本": "contract has no 106 stage",
        "104→106": "contract has no canonical breakdown-to-script handoff",
        "script_bundle.json": "contract has no script artifact",
        "默认六版": "contract has no default route count",
        "明确要求九版": "contract has no nine-script condition",
        "飞书 04": "contract has no separate Feishu 04 authorization",
        "auto-local": "contract has no local automation mode",
        "auto-all": "contract has no external automation mode",
    }
    for marker, message in required_contract_markers.items():
        if marker not in contract:
            errors.append(f"workflow-contract.md: {message}: {marker}")

    forbidden_contract_markers = {
        "终点固定为 105": "contract still fixes the endpoint at 105",
        "106、脚本生成和飞书 04 不属于 4.0": "contract still excludes scripts",
        "默认三版": "contract still defaults to three scripts",
    }
    for marker, message in forbidden_contract_markers.items():
        if marker in contract:
            errors.append(f"workflow-contract.md: {message}: {marker}")

    metadata_markers = {
        "$tiangege-tiktok-video-workflow-4-0": "default prompt does not invoke the skill",
        "脚本": "UI metadata does not advertise script output",
    }
    for marker, message in metadata_markers.items():
        if marker not in metadata:
            errors.append(f"openai.yaml: {message}: {marker}")
    if "不生成新脚本" in metadata:
        errors.append("openai.yaml: default prompt still forbids script output")

    if "01/02/03" not in skill or "04" not in skill:
        errors.append("SKILL.md: material and script write scopes are not both explicit")
    if "同步飞书" not in skill and "自动入库" not in skill:
        errors.append("SKILL.md: explicit external-write authorization terms are missing")
    auto_all_rule = "同时明确要求自动执行和“同步飞书/自动入库”"
    if auto_all_rule not in skill:
        errors.append(f"SKILL.md: auto-all trigger is ambiguous: {auto_all_rule}")
    if auto_all_rule not in contract:
        errors.append(f"workflow-contract.md: auto-all trigger is ambiguous: {auto_all_rule}")

    result = {
        "valid": not errors,
        "checked_files": [str(path) for path in (SKILL, CONTRACT, OPENAI_YAML)],
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
