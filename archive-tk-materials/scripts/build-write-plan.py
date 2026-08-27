#!/usr/bin/env python3
"""Validate TK pipeline artifacts and build an offline Lark Base write plan."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PIPELINE_ID = "tk-content-pipeline/v1"
TABLE_SPECS = {
    "original_videos": {"name": "01 原视频库", "business_key": "视频ID"},
    "step2_breakdowns": {"name": "02 竞品拆解库", "business_key": "拆解ID"},
    "elements": {"name": "03 元素库", "business_key": "元素ID"},
}
METRIC_LABELS = {
    "retention": "留存",
    "click": "点击",
    "cart": "加购",
    "conversion": "转化",
    "留存": "留存",
    "点击": "点击",
    "加购": "加购",
    "转化": "转化",
}
STATUS_LABELS = {
    "candidate": "候选",
    "initial": "初步有效",
    "single_win": "单次胜出",
    "multi_win": "多次胜出",
    "stable": "稳定高表现",
}
CONFIDENCE_LABELS = {"low": "低", "medium": "中", "high": "高"}


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} 顶层必须是 JSON object")
    return value


def default_lark_config_path() -> Path | None:
    explicit = os.environ.get("TIANGEGE_TK_LARK_CONFIG")
    if explicit:
        return Path(explicit).expanduser()
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "tiangege-tiktok-workflow" / "lark-destination.json"
    return None


def validate_target_config(config: dict[str, Any] | None) -> list[str]:
    if config is None:
        return ["未绑定本机飞书目标；计划仅供本地预览，禁止写入"]
    errors: list[str] = []
    if config.get("binding_scope") != "local-user":
        errors.append("飞书目标配置必须声明 binding_scope=local-user")
    if config.get("pipeline_id") != PIPELINE_ID:
        errors.append("飞书目标配置 pipeline_id 必须是 tk-content-pipeline/v1")
    if not config.get("workspace_name") or not config.get("base_token"):
        errors.append("飞书目标配置缺少 workspace_name 或 base_token")
    tables = config.get("tables") if isinstance(config.get("tables"), dict) else {}
    for logical_name, spec in TABLE_SPECS.items():
        table = tables.get(logical_name) if isinstance(tables.get(logical_name), dict) else {}
        if not table.get("id"):
            errors.append(f"飞书目标配置缺少 tables.{logical_name}.id")
        if table.get("business_key") != spec["business_key"]:
            errors.append(f"tables.{logical_name}.business_key 必须是 {spec['business_key']}")
    return errors


def compact(values: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value not in (None, "", [], {})}


def first(*values: Any) -> Any:
    for value in values:
        if value is not None and value != "":
            return value
    return None


def account_label(value: Any) -> Any:
    if isinstance(value, dict):
        return first(value.get("handle"), value.get("profile_url"))
    return value


def account_platform(value: Any) -> Any:
    return value.get("platform") if isinstance(value, dict) else None


def normalize_metrics(item: dict[str, Any]) -> dict[str, Any]:
    metrics = item.get("metrics") if isinstance(item.get("metrics"), dict) else {}
    return {
        key: first(metrics.get(key), item.get(key))
        for key in ("plays", "likes", "comments", "shares")
    }


def video_id(item: dict[str, Any]) -> str:
    video = item.get("video") if isinstance(item.get("video"), dict) else {}
    source_video = item.get("source_video") if isinstance(item.get("source_video"), dict) else {}
    return str(first(video.get("video_id"), source_video.get("video_id"), item.get("video_id"), "")).strip()


def canonical_fingerprint(element: dict[str, Any]) -> str:
    body = {
        "copy": element.get("copy"),
        "zh": element.get("zh"),
        "visual": element.get("visual"),
        "module": element.get("module"),
        "start": element.get("start"),
        "end": element.get("end"),
    }
    raw = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def normalize_account_videos(manifest: dict[str, Any] | None, errors: list[str]) -> dict[str, dict[str, Any]]:
    if manifest is None:
        return {}
    if manifest.get("pipeline_id") != PIPELINE_ID:
        errors.append("account_manifest.pipeline_id 必须是 tk-content-pipeline/v1")
    if manifest.get("artifact_type") != "account_manifest":
        errors.append("账号采集产物 artifact_type 必须是 account_manifest")
    items = manifest.get("videos", manifest.get("items", []))
    if not isinstance(items, list):
        errors.append("account_manifest.videos 必须是数组")
        return {}
    account_meta = manifest.get("account") if isinstance(manifest.get("account"), dict) else {}
    result: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"account_manifest.videos[{index}] 必须是 object")
            continue
        vid = video_id(item)
        if not vid:
            errors.append(f"account_manifest.videos[{index}] 缺少 video_id")
            continue
        normalized = dict(item)
        normalized["video_id"] = vid
        normalized["source_url"] = first(item.get("source_url"), item.get("url"))
        normalized["metrics"] = normalize_metrics(item)
        normalized["account"] = first(account_label(item.get("account")), account_meta.get("handle"), account_meta.get("profile_url"))
        normalized["platform"] = first(item.get("platform"), account_platform(item.get("account")), account_meta.get("platform"), "TikTok")
        if vid in result:
            errors.append(f"account_manifest 出现重复 video_id: {vid}")
        result[vid] = normalized
    return result


def normalize_breakdowns(bundle: dict[str, Any] | None, errors: list[str]) -> list[dict[str, Any]]:
    if bundle is None:
        return []
    if bundle.get("pipeline_id") != PIPELINE_ID:
        errors.append("breakdown_bundle.pipeline_id 必须是 tk-content-pipeline/v1")
    if bundle.get("artifact_type") != "breakdown_bundle":
        errors.append("视频拆解产物 artifact_type 必须是 breakdown_bundle")
    items = bundle.get("videos")
    if items is None and (bundle.get("video") or bundle.get("video_id")):
        items = [bundle]
    if not isinstance(items, list):
        errors.append("breakdown_bundle.videos 必须是数组")
        return []
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"breakdown_bundle.videos[{index}] 必须是 object")
            continue
        vid = video_id(item)
        if not vid:
            errors.append(f"breakdown_bundle.videos[{index}] 缺少 video.video_id")
            continue
        if vid in seen:
            errors.append(f"breakdown_bundle 出现重复 video_id: {vid}")
            continue
        seen.add(vid)
        result.append(item)
    return result


def build_original_row(vid: str, acquired: dict[str, Any], breakdown: dict[str, Any] | None) -> dict[str, Any]:
    breakdown = breakdown or {}
    source_video = breakdown.get("video") if isinstance(breakdown.get("video"), dict) else {}
    if not source_video and isinstance(breakdown.get("source_video"), dict):
        source_video = breakdown["source_video"]
    merged = dict(acquired)
    merged.update({key: value for key, value in source_video.items() if value is not None and value != ""})
    metrics = normalize_metrics({**acquired, **merged})
    top_comment = merged.get("top_comment") if isinstance(merged.get("top_comment"), dict) else {}
    acquisition = acquired.get("acquisition") if isinstance(acquired.get("acquisition"), dict) else {}
    error = acquisition.get("error")
    fields = compact({
        "平台": first(merged.get("platform"), account_platform(merged.get("account")), "TikTok"),
        "竞品账号": first(account_label(merged.get("account")), account_label(acquired.get("account"))),
        "视频ID": vid,
        "视频链接": first(merged.get("source_url"), merged.get("url")),
        "发布时间": merged.get("published_at"),
        "视频时长秒": first(merged.get("duration_seconds"), breakdown.get("duration_seconds")),
        "播放量": metrics.get("plays"),
        "点赞量": metrics.get("likes"),
        "评论量": metrics.get("comments"),
        "转发量": metrics.get("shares"),
        "Top1评论原文": top_comment.get("text"),
        "Top1评论点赞": top_comment.get("likes"),
        "Top1评论摘要": top_comment.get("summary"),
        "处理状态": "异常" if error else ("待审核" if breakdown else "处理中"),
        "审核状态": "待审核",
        "异常说明": error,
        "本批更新时间": datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S"),
    })
    return {
        "business_key": vid,
        "business_key_field": "视频ID",
        "fields": fields,
        "source_local_path": first(merged.get("local_path"), merged.get("video_path")),
    }


def timeline_full_zh(item: dict[str, Any]) -> str:
    timeline = item.get("timeline") if isinstance(item.get("timeline"), list) else []
    if not timeline and isinstance(item.get("step1_extraction"), dict):
        candidate = item["step1_extraction"].get("timeline")
        timeline = candidate if isinstance(candidate, list) else []
    parts = []
    for segment in timeline:
        if isinstance(segment, dict):
            value = first(segment.get("zh"), segment.get("chinese"), segment.get("source_text"))
            if value:
                parts.append(str(value).strip())
    return "\n".join(part for part in parts if part)


def first_product_exposure(item: dict[str, Any]) -> Any:
    elements = item.get("elements") if isinstance(item.get("elements"), list) else []
    starts = [
        element.get("start")
        for element in elements
        if isinstance(element, dict)
        and element.get("module") in ("产品切入", "产品机制", "卖点")
        and isinstance(element.get("start"), (int, float))
    ]
    if not starts:
        return None
    value = min(starts)
    return f"{value:g} 秒"


def build_breakdown_row(vid: str, item: dict[str, Any], local_path: Any, errors: list[str]) -> dict[str, Any] | None:
    source = item.get("step2_base_row") if isinstance(item.get("step2_base_row"), dict) else {}
    breakdown = item.get("video_breakdown") if isinstance(item.get("video_breakdown"), dict) else {}
    if not breakdown and not source:
        errors.append(f"{vid}: 缺少 video_breakdown，不能写入 02")
        return None
    source = dict(source)
    transcript = item.get("transcript") if isinstance(item.get("transcript"), dict) else {}
    video = item.get("video") if isinstance(item.get("video"), dict) else {}
    if not video and isinstance(item.get("source_video"), dict):
        video = item["source_video"]
    scores = item.get("scores") if isinstance(item.get("scores"), dict) else {}
    video_type = breakdown.get("video_type") if isinstance(breakdown.get("video_type"), dict) else {}
    source["breakdown_id"] = first(source.get("breakdown_id"), f"BD-{vid}")
    source["original_video_zh_full"] = first(source.get("original_video_zh_full"), transcript.get("full_chinese"), timeline_full_zh(item))
    source["duration_seconds"] = first(source.get("duration_seconds"), video.get("duration_seconds"))
    source["content_type"] = first(source.get("content_type"), video_type.get("primary"))
    source["visual_shell_tags"] = first(source.get("visual_shell_tags"), video_type.get("shell"))
    source["first_product_exposure"] = first(source.get("first_product_exposure"), first_product_exposure(item))
    source["underlying_purchase_logic"] = first(source.get("underlying_purchase_logic"), breakdown.get("underlying_logic"))
    source["element_coordination"] = first(source.get("element_coordination"), breakdown.get("element_coordination"))
    source["hook_score"] = first(source.get("hook_score"), scores.get("hook"))
    source["pain_score"] = first(source.get("pain_score"), scores.get("pain"))
    source["trust_conversion_score"] = first(source.get("trust_conversion_score"), scores.get("trust_conversion"))
    source["transferability_score"] = first(source.get("transferability_score"), scores.get("transferability"))
    if not source.get("original_video_zh_full"):
        errors.append(f"{vid}: 原视频中文内容为空，不能写入 02")
        return None
    mapping = {
        "breakdown_id": "拆解ID", "original_video_zh_full": "原视频中文内容",
        "brand": "品牌", "product_category": "产品类别", "duration_seconds": "时长秒",
        "content_type": "内容类型", "visual_shell_tags": "视觉外壳标签",
        "first_product_exposure": "产品首次露出", "audience_level_1": "人群一级标签",
        "audience_level_2": "人群二级标签", "pain_tags": "痛点标签",
        "depositable_modules": "可沉淀模块", "primary_tactics": "主打法标签",
        "underlying_purchase_logic": "底层购买逻辑", "product_bridge_logic": "产品承接逻辑",
        "element_coordination": "元素协同", "trust_evidence_tags": "信任证据标签",
        "action_trigger_tags": "行动触发标签", "oxy_transfer_method": "OXY迁移方式",
        "breakdown_usable_status": "拆解可用状态", "hook_score": "Hook评分",
        "pain_score": "痛点评分", "trust_conversion_score": "信任与转化评分",
        "transferability_score": "可迁移性评分",
    }
    fields = compact({target: source.get(key) for key, target in mapping.items()})
    return {
        "business_key": source["breakdown_id"],
        "business_key_field": "拆解ID",
        "fields": fields,
        "link_to_original_business_key": vid,
        "attachments": compact({"视频预览": local_path}),
    }


def as_metric_list(value: Any) -> list[str]:
    values = value if isinstance(value, list) else [value]
    return [METRIC_LABELS[item] for item in values if item in METRIC_LABELS]


def build_element_rows(vid: str, account: Any, item: dict[str, Any], warnings: list[str]) -> list[dict[str, Any]]:
    elements = item.get("elements") if isinstance(item.get("elements"), list) else []
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, element in enumerate(elements):
        if not isinstance(element, dict):
            warnings.append(f"{vid}: elements[{index}] 非 object，已跳过")
            continue
        shell = element.get("shell") if isinstance(element.get("shell"), dict) else {}
        fingerprint = first(element.get("content_fingerprint"), canonical_fingerprint(element))
        start = first(element.get("start"), 0)
        end = first(element.get("end"), start)
        module = first(element.get("module"), "")
        key = str(first(element.get("element_id"), f"{vid}|{start}-{end}|{module}|{fingerprint}"))
        if key in seen:
            warnings.append(f"{vid}: 重复元素ID {key}，仅保留首条")
            continue
        seen.add(key)
        backend_metric = element.get("backend_metric")
        fields = compact({
            "元素ID": key,
            "来源视频业务键": vid,
            "来源视频ID": vid,
            "来源账号": account,
            "开始秒": start,
            "结束秒": end,
            "模块": module,
            "子类型": element.get("subtype"),
            "原文": element.get("source_text"),
            "中文文案": first(element.get("zh"), element.get("copy")),
            "画面内容": element.get("visual"),
            "人物": shell.get("person"),
            "场景": shell.get("scene"),
            "口播方式": shell.get("delivery"),
            "字幕": shell.get("subtitle"),
            "镜头与构图": first(shell.get("shot_and_composition"), " / ".join(str(v) for v in (shell.get("shot"), shell.get("composition")) if v)),
            "素材形式": shell.get("material_type"),
            "候选指标": as_metric_list(element.get("candidate_metric")),
            "归因置信度": CONFIDENCE_LABELS.get(element.get("attribution_confidence"), element.get("attribution_confidence")),
            "验证状态": STATUS_LABELS.get(element.get("status"), element.get("status", "候选")),
            "审核状态": "待审核",
            "后台指标JSON": json.dumps(backend_metric, ensure_ascii=False) if backend_metric is not None else None,
            "内容指纹": fingerprint,
        })
        rows.append({"business_key": key, "business_key_field": "元素ID", "fields": fields})
    return rows


def build_plan(
    account_manifest: dict[str, Any] | None,
    breakdown_bundle: dict[str, Any] | None,
    target_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    write_blockers = validate_target_config(target_config)
    acquired = normalize_account_videos(account_manifest, errors)
    breakdowns = normalize_breakdowns(breakdown_bundle, errors)
    breakdown_by_id = {video_id(item): item for item in breakdowns}
    all_ids = list(dict.fromkeys([*acquired.keys(), *breakdown_by_id.keys()]))

    originals: list[dict[str, Any]] = []
    breakdown_rows: list[dict[str, Any]] = []
    element_rows: list[dict[str, Any]] = []
    for vid in all_ids:
        acquired_item = acquired.get(vid, {})
        breakdown_item = breakdown_by_id.get(vid)
        original_row = build_original_row(vid, acquired_item, breakdown_item)
        originals.append(original_row)
        if breakdown_item:
            row = build_breakdown_row(vid, breakdown_item, original_row.get("source_local_path"), errors)
            if row:
                breakdown_rows.append(row)
            element_rows.extend(build_element_rows(vid, original_row["fields"].get("竞品账号"), breakdown_item, warnings))

    config_tables = target_config.get("tables", {}) if target_config else {}
    binding_status = "bound" if not write_blockers else "unbound"
    return {
        "pipeline_id": PIPELINE_ID,
        "artifact_type": "lark_write_plan",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "safe_to_write": not errors and not write_blockers,
        "target": {
            "binding_status": binding_status,
            "binding_scope": target_config.get("binding_scope") if target_config else None,
            "workspace_name": target_config.get("workspace_name") if target_config else None,
            "tables": [
                config_tables.get(name, {}).get("name", spec["name"])
                for name, spec in TABLE_SPECS.items()
            ],
        },
        "tables": {
            "original_videos": {"table_id": config_tables.get("original_videos", {}).get("id"), "business_key_field": "视频ID", "rows": originals},
            "step2_breakdowns": {"table_id": config_tables.get("step2_breakdowns", {}).get("id"), "business_key_field": "拆解ID", "rows": breakdown_rows},
            "elements": {"table_id": config_tables.get("elements", {}).get("id"), "business_key_field": "元素ID", "rows": element_rows},
        },
        "summary": {"original_video_rows": len(originals), "breakdown_rows": len(breakdown_rows), "element_rows": len(element_rows), "errors": len(errors), "warnings": len(warnings), "write_blockers": len(write_blockers)},
        "errors": errors,
        "warnings": warnings,
        "write_blockers": write_blockers,
    }


def self_test() -> int:
    account = {
        "pipeline_id": PIPELINE_ID,
        "artifact_type": "account_manifest",
        "account": {"platform": "TikTok", "handle": "demo"},
        "videos": [{"video_id": "v1", "source_url": "https://example/v1", "account": {"platform": "tiktok", "handle": "demo", "profile_url": "https://www.tiktok.com/@demo"}, "metrics": {"plays": 10, "likes": None, "comments": 0, "shares": None}, "acquisition": {"status": "cached", "error": None}}],
    }
    breakdown = {
        "pipeline_id": PIPELINE_ID,
        "artifact_type": "breakdown_bundle",
        "videos": [{
            "video": {"video_id": "v1", "duration_seconds": 18},
            "transcript": {"full_chinese": "示例中文"},
            "timeline": [{"start": 0, "end": 3, "zh": "示例中文"}],
            "video_breakdown": {"underlying_logic": "先证明再转化", "video_type": {"primary": "口播", "shell": ["真人"]}, "element_coordination": "口播与演示同步"},
            "scores": {"hook": 4, "pain": 3, "trust_conversion": 4, "transferability": 5},
            "elements": [{"start": 0, "end": 3, "module": "Hook", "copy": "示例", "status": "candidate", "candidate_metric": "retention", "attribution_confidence": "low"}],
        }],
    }
    target = {
        "pipeline_id": PIPELINE_ID,
        "binding_scope": "local-user",
        "workspace_name": "self-test",
        "base_token": "self-test-token",
        "tables": {
            name: {"id": f"self-test-{name}", "name": spec["name"], "business_key": spec["business_key"]}
            for name, spec in TABLE_SPECS.items()
        },
    }
    plan = build_plan(account, breakdown, target)
    counts = plan["summary"]
    invalid = build_plan({**account, "pipeline_id": "wrong/v0"}, breakdown, target)
    unbound = build_plan(account, breakdown, None)
    ok = (
        plan["safe_to_write"]
        and counts["original_video_rows"] == 1
        and counts["breakdown_rows"] == 1
        and counts["element_rows"] == 1
        and plan["tables"]["original_videos"]["rows"][0]["fields"]["竞品账号"] == "demo"
        and not invalid["safe_to_write"]
        and invalid["summary"]["errors"] == 1
        and not unbound["safe_to_write"]
        and unbound["target"]["binding_status"] == "unbound"
        and all(table["table_id"] is None for table in unbound["tables"].values())
    )
    print(json.dumps({"self_test": "passed" if ok else "failed", "summary": counts, "invalid_input_blocked": not invalid["safe_to_write"]}, ensure_ascii=False))
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--account-manifest", type=Path)
    parser.add_argument("--breakdown-bundle", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--lark-config", type=Path, help="本机个人飞书目标配置；默认读取 TIANGEGE_TK_LARK_CONFIG 或 LOCALAPPDATA")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if not args.account_manifest and not args.breakdown_bundle:
        parser.error("至少提供 --account-manifest 或 --breakdown-bundle")
    if not args.output:
        parser.error("必须提供 --output")
    try:
        account = read_json(args.account_manifest) if args.account_manifest else None
        breakdown = read_json(args.breakdown_bundle) if args.breakdown_bundle else None
        config_path = args.lark_config or default_lark_config_path()
        target_config = read_json(config_path) if config_path and config_path.exists() else None
        plan = build_plan(account, breakdown, target_config)
        plan["target"]["config_path"] = str(config_path.resolve()) if config_path and config_path.exists() else None
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(plan["summary"], ensure_ascii=False))
        return 0 if not plan["errors"] else 2
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
