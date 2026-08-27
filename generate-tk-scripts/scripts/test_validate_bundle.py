#!/usr/bin/env python3

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

import validate_bundle


def make_breakdown(alias: bool = False) -> dict:
    item = {
        "video_breakdown": {
            "underlying_logic": "症状自测→新解释→产品承接→证明→下单",
            "video_type": "真人口播",
            "retention_method": "前三秒症状连击",
            "hook_0_3s": {
                "original_copy": "下午总想吃零食？",
                "optimized_copy": "下午三点一到就翻零食柜？",
                "key_changes": "增加具体时刻和动作",
                "intended_retention_effect": "提升相关性",
            },
            "audience": "下午或夜间容易嘴馋的成年人",
            "pain": "饮食计划被临时加餐打断",
            "result": "减少临时决策",
            "belief_and_action": "真实配方与冲泡证明→查看商品页",
            "element_coordination": "真人场景、包装、冲泡、商品页",
            "transferable_logic": "高频症状→归因反转→低门槛动作→CTA",
        },
        "elements": [],
        "scores": {},
        "duplicate_cluster": None,
    }
    identity = {"video_id": "12345", "duration_seconds": 12}
    timeline = [{"start": 0, "end": 3, "voiceover": "下午总想吃零食？"}]
    if alias:
        item["source_video"] = identity
        item["step1_extraction"] = {"timeline": timeline}
    else:
        item["video"] = identity
        item["timeline"] = timeline
    return {
        "pipeline_id": "tk-content-pipeline/v1",
        "artifact_type": "breakdown_bundle",
        "schema_version": 1,
        "generated_at": "2026-08-14T00:00:00+08:00",
        "batch_confirmation": {
            "step1_confirmed": True,
            "step2_completed": True,
            "step2_confirmed": True,
        },
        "videos": [item],
    }


VOICEOVERS = {
    ("iteration", "A"): "你是不是下午总想吃零食？先看真实配方。高纤维支持饱腹，按说明冲泡，点击查看。",
    ("iteration", "B"): "你是不是下午总想吃甜食？先看真实配方。高纤维支持饱腹，按说明冲泡，点击查看。",
    ("iteration", "C"): "你是不是晚上总想翻零食？先看真实配方。高纤维支持饱腹，按说明冲泡，点击查看。",
    ("reshell", "A"): "昨晚我又打开冰箱，才发现计划总被嘴馋打断。现在按说明冲一杯，再去商品页核对配方。",
    ("reshell", "B"): "左边靠忍，右边提前冲好一杯。高风险时段少做一次临时决定，详情到商品页查看。",
    ("reshell", "C"): "办公室零食抽屉每天都在提醒我。把固定冲泡放进下午流程，按包装使用后再决定。",
    ("new_logic", "A"): "先别信神奇承诺，只核对配方、用法和边界。三项都适合，再到商品页决定是否购买。",
    ("new_logic", "B"): "一个月临时零食花了多少？先算真实账单，再比较固定饱腹支持是否更适合日常。",
    ("new_logic", "C"): "别先看体重，记录三十天临时加餐次数。真实趋势能复查，再决定这个方案值不值得。",
}


def make_script(video_id: str, group: str, variant: str) -> dict:
    group_code, route = validate_bundle.GROUPS[group]
    text = VOICEOVERS[(group, variant)]
    midpoint = max(1, len(text) // 2)
    direction = {
        "iteration": {"A": "信任证明", "B": "痛点切入", "C": "留人节奏"}[variant],
        "reshell": {"A": "夜间厨房UGC", "B": "左右分屏对比", "C": "办公室抽屉独白"}[variant],
        "new_logic": {"A": "风险逆转→核对边界→购买", "B": "成本审计→替代比较→购买", "C": "可追踪记录→趋势证明→购买"}[variant],
    }[group]
    return {
        "script_id": f"SC-{video_id}-{group_code}-{variant}",
        "group": group,
        "route": route,
        "variant": variant,
        "test_variable": direction if group == "iteration" else "",
        "shell_direction": direction if group == "reshell" else "",
        "new_purchase_path": direction if group == "new_logic" else "",
        "fixed_invariants": (
            ["底层购买逻辑", "目标人群", "产品", "CTA"]
            if group == "iteration"
            else ["产品", "目标人群", "销售强度"]
        ),
        "hook_comparison": {
            "original_hook": "下午总想吃零食？",
            "optimized_hook": text.split("。", 1)[0] + "。",
            "key_changes": f"按{direction}方向优化",
            "intended_retention_effect": "增强具体代入并承接购买路径",
        },
        "segments": [
            {
                "start_second": 0,
                "end_second": 4,
                "voiceover": text[:midpoint],
                "visual_action": "真人场景与短字幕",
                "purpose": "留人",
            },
            {
                "start_second": 4,
                "end_second": 12,
                "voiceover": text[midpoint:],
                "visual_action": "包装、动作与商品页",
                "purpose": "下单",
            },
        ],
        "final_voiceover": text,
        "estimated_duration_seconds": 12,
        "duration_note": "",
        "humanity_review": {
            "status": "approved",
            "humanity_score": 4.5,
            "feed_score": 4.4,
            "sales_score": 4.2,
            "ai_tells": [],
            "read_aloud_issues": [],
            "revision_rounds": 1,
            "voice_evidence_gap": False,
        },
    }


def make_script_bundle() -> dict:
    scripts = [
        make_script("12345", group, variant)
        for group in validate_bundle.GROUPS
        for variant in validate_bundle.VARIANTS
    ]
    return {
        "pipeline_id": "tk-content-pipeline/v1",
        "artifact_type": "script_bundle",
        "schema_version": 1,
        "generated_at": "2026-08-14T00:05:00+08:00",
        "source_breakdown": "breakdown_bundle.json",
        "videos": [
            {
                "video_id": "12345",
                "source_duration_seconds": 12,
                "scripts": scripts,
            }
        ],
    }


def make_six_script_bundle() -> dict:
    value = make_script_bundle()
    value["videos"][0]["scripts"] = [
        make_script("12345", group, variant)
        for group in validate_bundle.GROUPS
        for variant in ("A", "B")
    ]
    return value


class BreakdownValidationTests(unittest.TestCase):
    def test_valid_canonical_breakdown(self) -> None:
        errors, warnings = validate_bundle.validate_breakdown(make_breakdown())
        self.assertEqual([], errors)
        self.assertEqual([], warnings)

    def test_compatibility_aliases_are_accepted_with_warnings(self) -> None:
        errors, warnings = validate_bundle.validate_breakdown(make_breakdown(alias=True))
        self.assertEqual([], errors)
        self.assertEqual(2, len(warnings))

    def test_unconfirmed_breakdown_is_rejected(self) -> None:
        value = make_breakdown()
        value["batch_confirmation"]["step2_confirmed"] = False
        errors, _ = validate_bundle.validate_breakdown(value)
        self.assertTrue(any("batch_confirmation" in error for error in errors))

    def test_legacy_step2_confirmation_is_accepted_with_warning(self) -> None:
        value = make_breakdown()
        value["batch_confirmation"] = {"step2_confirmed": True}
        errors, warnings = validate_bundle.validate_breakdown(value)
        self.assertEqual([], errors)
        self.assertTrue(any("accepted for compatibility" in warning for warning in warnings))


class ScriptValidationTests(unittest.TestCase):
    def test_valid_nine_script_bundle(self) -> None:
        errors, warnings = validate_bundle.validate_script(make_script_bundle())
        self.assertEqual([], errors)
        self.assertEqual([], warnings)

    def test_valid_six_script_bundle(self) -> None:
        errors, warnings = validate_bundle.validate_script(make_six_script_bundle())
        self.assertEqual([], errors)
        self.assertEqual([], warnings)

    def test_three_script_bundle_is_rejected(self) -> None:
        value = make_six_script_bundle()
        value["videos"][0]["scripts"] = value["videos"][0]["scripts"][::2]
        errors, _ = validate_bundle.validate_script(value)
        self.assertTrue(any("expected 6 or 9" in error for error in errors))

    def test_missing_variant_is_rejected(self) -> None:
        value = make_script_bundle()
        value["videos"][0]["scripts"].pop()
        errors, _ = validate_bundle.validate_script(value)
        self.assertTrue(any("expected 6 or 9" in error for error in errors))
        self.assertTrue(any("missing combinations" in error for error in errors))

    def test_missing_humanity_review_warns(self) -> None:
        value = make_six_script_bundle()
        value["videos"][0]["scripts"][0].pop("humanity_review")
        errors, warnings = validate_bundle.validate_script(value)
        self.assertEqual([], errors)
        self.assertTrue(any("humanity_review" in warning for warning in warnings))

    def test_low_humanity_score_warns(self) -> None:
        value = make_six_script_bundle()
        value["videos"][0]["scripts"][0]["humanity_review"]["humanity_score"] = 3.9
        errors, warnings = validate_bundle.validate_script(value)
        self.assertEqual([], errors)
        self.assertTrue(any("below delivery threshold" in warning for warning in warnings))

    def test_voiceover_must_match_segments(self) -> None:
        value = make_script_bundle()
        value["videos"][0]["scripts"][0]["final_voiceover"] += "额外一句。"
        errors, _ = validate_bundle.validate_script(value)
        self.assertTrue(any("concatenated segment voiceovers" in error for error in errors))

    def test_duplicate_group_direction_is_rejected(self) -> None:
        value = make_script_bundle()
        scripts = value["videos"][0]["scripts"]
        scripts[1]["test_variable"] = scripts[0]["test_variable"]
        errors, _ = validate_bundle.validate_script(value)
        self.assertTrue(any("directions must be 3 distinct" in error for error in errors))

    def test_cli_json_fixture_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "script_bundle.json"
            target.write_text(json.dumps(make_script_bundle(), ensure_ascii=False), encoding="utf-8")
            loaded = json.loads(target.read_text(encoding="utf-8"))
        errors, warnings = validate_bundle.validate_script(loaded)
        self.assertEqual(([], []), (errors, warnings))


if __name__ == "__main__":
    unittest.main(verbosity=2)
