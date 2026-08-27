import argparse
import json
import sys
from pathlib import Path


PIPELINE_ID = "tk-content-pipeline/v1"
REQUIRED_VIDEO_KEYS = {
    "status",
    "video",
    "transcript",
    "timeline",
    "frames",
    "video_breakdown",
    "elements",
    "scores",
    "duplicate_cluster",
}
FORBIDDEN_KEYS = {"new_scripts", "scripts", "lark", "base_rows", "step2_base_row"}


def require(condition, message, errors):
    if not condition:
        errors.append(message)


def validate_video(video, index, errors, allow_draft):
    prefix = f"videos[{index}]"
    missing = REQUIRED_VIDEO_KEYS.difference(video)
    require(not missing, f"{prefix} missing keys: {sorted(missing)}", errors)
    if missing:
        return
    require(video["status"] == "completed", f"{prefix}.status must be completed", errors)
    source = video["video"]
    require(bool(source.get("video_id")), f"{prefix}.video.video_id is required", errors)
    for key in ("source_url", "local_path", "account", "published_at", "duration_seconds", "metrics"):
        require(key in source, f"{prefix}.video.{key} is required", errors)
    transcript = video["transcript"]
    require(bool(transcript.get("full_chinese")), f"{prefix}.transcript.full_chinese is required", errors)
    require(isinstance(transcript.get("segments"), list), f"{prefix}.transcript.segments must be an array", errors)
    frames = video["frames"]
    require(isinstance(frames.get("evidence"), list), f"{prefix}.frames.evidence must be an array", errors)
    audit = frames.get("coverage_audit", {})
    if not allow_draft:
        require(audit.get("visual_status") == "passed", f"{prefix} visual coverage audit is not passed", errors)
    require(isinstance(video["timeline"], list), f"{prefix}.timeline must be an array", errors)
    breakdown = video["video_breakdown"]
    required_breakdown = {
        "underlying_logic",
        "video_type",
        "retention_method",
        "hook_0_3s",
        "audience",
        "pain",
        "result",
        "belief_and_action",
        "element_coordination",
        "transferable_logic",
    }
    require(not required_breakdown.difference(breakdown), f"{prefix}.video_breakdown is incomplete", errors)
    hook = breakdown.get("hook_0_3s", {})
    for key in ("original_copy", "optimized_copy", "key_changes", "intended_retention_effect"):
        require(bool(hook.get(key)), f"{prefix}.video_breakdown.hook_0_3s.{key} is required", errors)
    require(isinstance(video["elements"], list), f"{prefix}.elements must be an array", errors)
    scores = video["scores"]
    for key in ("hook", "pain", "trust_conversion", "transferability", "overall"):
        value = scores.get(key)
        require(isinstance(value, (int, float)) and 0 <= value <= 5, f"{prefix}.scores.{key} must be 0..5", errors)
    cluster = video["duplicate_cluster"]
    require(bool(cluster.get("relationship")), f"{prefix}.duplicate_cluster.relationship is required", errors)


def main():
    parser = argparse.ArgumentParser(description="Validate a final breakdown_bundle.json.")
    parser.add_argument("bundle")
    parser.add_argument("--allow-draft", action="store_true")
    args = parser.parse_args()
    try:
        payload = json.loads(Path(args.bundle).read_text(encoding="utf-8-sig"))
    except Exception as exc:
        print(json.dumps({"valid": False, "errors": [str(exc)]}, ensure_ascii=False))
        raise SystemExit(1)
    errors = []
    require(payload.get("pipeline_id") == PIPELINE_ID, f"pipeline_id must be {PIPELINE_ID}", errors)
    require(payload.get("artifact_type") == "breakdown_bundle", "artifact_type must be breakdown_bundle", errors)
    require(payload.get("schema_version") == 1, "schema_version must be 1", errors)
    require(bool(payload.get("generated_at")), "generated_at is required", errors)
    require(not FORBIDDEN_KEYS.intersection(payload), f"forbidden top-level keys: {sorted(FORBIDDEN_KEYS.intersection(payload))}", errors)
    videos = payload.get("videos")
    require(isinstance(videos, list) and bool(videos), "videos must be a non-empty array", errors)
    confirmation = payload.get("batch_confirmation", {})
    if not args.allow_draft:
        require(confirmation.get("step1_confirmed") is True, "batch_confirmation.step1_confirmed must be true", errors)
        require(confirmation.get("step2_completed") is True, "batch_confirmation.step2_completed must be true", errors)
        if "step2_confirmed" in confirmation:
            require(isinstance(confirmation.get("step2_confirmed"), bool), "batch_confirmation.step2_confirmed must be boolean when present", errors)
    if isinstance(videos, list):
        for index, video in enumerate(videos):
            validate_video(video, index, errors, args.allow_draft)
    result = {"valid": not errors, "errors": errors}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
