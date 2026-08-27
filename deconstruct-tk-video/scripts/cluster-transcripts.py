import argparse
import json
import re
from difflib import SequenceMatcher
from pathlib import Path


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def normalize(text):
    return re.sub(r"[^\w\u4e00-\u9fff]+", "", text.lower())


def transcript_features(item):
    transcript = read_json(item["transcript_path"])
    segments = transcript.get("segments", [])
    full = normalize(" ".join(str(segment.get("text", "")) for segment in segments))
    hook = normalize(
        " ".join(
            str(segment.get("text", ""))
            for segment in segments
            if float(segment.get("start", 0)) < 3.0
        )
    )
    source = item.get("source_video", {})
    return {
        "video_id": source.get("video_id") or item.get("video_sha256", "")[:12],
        "video_sha256": item.get("video_sha256", ""),
        "rank": source.get("rank"),
        "full": full,
        "hook": hook,
    }


def pair_relation(left, right):
    if left["video_sha256"] and left["video_sha256"] == right["video_sha256"]:
        return "exact_duplicate"
    if left["full"] and left["full"] == right["full"]:
        return "same_creative"
    if left["full"] and right["full"]:
        ratio = SequenceMatcher(None, left["full"], right["full"]).ratio()
        if ratio >= 0.92:
            return "near_duplicate"
    if left["hook"] and left["hook"] == right["hook"]:
        return "same_hook"
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Generate deterministic transcript/hash duplicate candidates."
    )
    parser.add_argument("prepared_media_manifest")
    parser.add_argument("--output")
    args = parser.parse_args()
    manifest_path = Path(args.prepared_media_manifest).resolve()
    manifest = read_json(manifest_path)
    features = [transcript_features(item) for item in manifest.get("videos", [])]
    parent = list(range(len(features)))
    relations = {}

    def find(value):
        while parent[value] != value:
            parent[value] = parent[parent[value]]
            value = parent[value]
        return value

    def union(left, right):
        a, b = find(left), find(right)
        if a != b:
            parent[b] = a

    for left in range(len(features)):
        for right in range(left + 1, len(features)):
            relation = pair_relation(features[left], features[right])
            if relation:
                union(left, right)
                relations[(left, right)] = relation

    groups = {}
    for index in range(len(features)):
        groups.setdefault(find(index), []).append(index)

    clusters = []
    by_video = {}
    relation_order = {
        "exact_duplicate": 4,
        "same_creative": 3,
        "near_duplicate": 2,
        "same_hook": 1,
    }
    for group_number, indexes in enumerate(groups.values(), start=1):
        indexes.sort(
            key=lambda value: (
                features[value]["rank"] is None,
                features[value]["rank"] or 10**9,
                value,
            )
        )
        master = indexes[0]
        master_id = features[master]["video_id"]
        member_ids = [features[index]["video_id"] for index in indexes]
        cluster_id = f"DC-{group_number:03d}"
        for index in indexes:
            if len(indexes) == 1:
                relationship = "unique"
            elif index == master:
                relationship = "master"
            else:
                candidates = []
                pair = (min(master, index), max(master, index))
                if pair in relations:
                    candidates.append(relations[pair])
                for other in indexes:
                    pair = (min(other, index), max(other, index))
                    if pair in relations:
                        candidates.append(relations[pair])
                relationship = max(candidates, key=lambda value: relation_order[value])
            by_video[features[index]["video_id"]] = {
                "cluster_id": cluster_id,
                "master_video_id": master_id,
                "relationship": relationship,
                "similar_video_ids": [value for value in member_ids if value != features[index]["video_id"]],
                "review_status": "candidate_requires_semantic_review",
            }
        clusters.append(
            {
                "cluster_id": cluster_id,
                "master_video_id": master_id,
                "member_video_ids": member_ids,
            }
        )

    payload = {
        "pipeline_id": "tk-content-pipeline/v1",
        "artifact_type": "duplicate_cluster_candidates",
        "source_manifest": str(manifest_path),
        "clusters": clusters,
        "by_video": by_video,
    }
    output = (
        Path(args.output).resolve()
        if args.output
        else manifest_path.parent / "duplicate_cluster_candidates.json"
    )
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(output), "clusters": len(clusters)}))


if __name__ == "__main__":
    main()
