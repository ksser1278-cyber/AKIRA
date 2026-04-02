from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in records) + ("\n" if records else ""),
        encoding="utf-8",
    )
    return path


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_markdown(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def weak_dimensions(scores: dict[str, Any], *, limit: int = 3) -> list[dict[str, Any]]:
    ranked = [
        {"dimension": name, "value": float(value)}
        for name, value in scores.items()
        if name != "total"
    ]
    ranked.sort(key=lambda item: (item["value"], item["dimension"]))
    return ranked[:limit]


def plan_snapshot(run_dir: Path) -> dict[str, Any]:
    plan = load_json(run_dir / "plan.json")
    return {
        "track_id": plan.get("track_id"),
        "artist_id": plan.get("artist_id"),
        "title_seed": plan.get("title_seed"),
        "primary_mode": plan.get("primary_mode"),
        "arc_label": plan.get("arc_label"),
        "theme_axes": plan.get("theme_axes", []),
        "dominant_emotions": plan.get("dominant_emotions", []),
        "hook_core": plan.get("hook_blueprint", {}).get("core_text"),
        "section_order": [card.get("section") for card in plan.get("section_cards", []) if card.get("section")],
    }


def build_gold_review_record(review: dict[str, Any], scoring_manifest_path: Path) -> dict[str, Any]:
    prediction_path = Path(review["prediction_path"])
    run_dir = Path(review["run_dir"])
    markdown = load_markdown(prediction_path)
    scores = review["scores"]
    return {
        "schema_version": "1.0",
        "record_id": f"{review['track_id']}-gold-review",
        "track_id": review["track_id"],
        "artist_id": plan_snapshot(run_dir).get("artist_id"),
        "source_scoring_manifest": str(scoring_manifest_path),
        "prediction_path": str(prediction_path),
        "run_dir": str(run_dir),
        "title": review.get("title") or review["track_id"],
        "markdown": markdown,
        "scores": scores,
        "critic_notes": review.get("critic_notes", []),
        "weak_dimensions": weak_dimensions(scores),
        "plan_snapshot": plan_snapshot(run_dir),
        "annotation_template": {
            "decision": "",
            "overall_rating_1_to_5": None,
            "title_rating_1_to_5": None,
            "hook_rating_1_to_5": None,
            "imagery_rating_1_to_5": None,
            "section_flow_rating_1_to_5": None,
            "keep_for_goldset": False,
            "notes": "",
            "best_lines": [],
            "weak_lines": [],
        },
    }


def render_gold_review_packet(record: dict[str, Any]) -> str:
    snapshot = record["plan_snapshot"]
    scores = record["scores"]
    weak_dimensions_text = ", ".join(
        f"{item['dimension']}={item['value']}" for item in record["weak_dimensions"]
    )
    lines = [
        f"# Gold Review: {record['track_id']}",
        "",
        f"- Title: `{record['title']}`",
        f"- Prediction path: `{record['prediction_path']}`",
        f"- Source scoring manifest: `{record['source_scoring_manifest']}`",
        f"- Total score: `{scores['total']}`",
        f"- Weak dimensions: `{weak_dimensions_text}`",
        f"- Critic notes: `{'; '.join(record['critic_notes'])}`",
        "",
        "## Plan Snapshot",
        "",
        f"- Mode: `{snapshot['primary_mode']}`",
        f"- Arc: `{snapshot['arc_label']}`",
        f"- Theme axes: `{', '.join(snapshot['theme_axes'])}`",
        f"- Emotions: `{', '.join(snapshot['dominant_emotions'])}`",
        f"- Hook core: `{snapshot['hook_core']}`",
        f"- Section order: `{', '.join(snapshot['section_order'])}`",
        "",
        "## Annotation Template",
        "",
        "- decision:",
        "- overall_rating_1_to_5:",
        "- title_rating_1_to_5:",
        "- hook_rating_1_to_5:",
        "- imagery_rating_1_to_5:",
        "- section_flow_rating_1_to_5:",
        "- keep_for_goldset:",
        "- notes:",
        "- best_lines:",
        "- weak_lines:",
        "",
        "## Candidate",
        "",
        record["markdown"].strip(),
        "",
    ]
    return "\n".join(lines)


def build_gold_review_bundle(
    scoring_manifest: Path,
    output_dir: Path,
    *,
    min_score: float,
    max_records: int | None,
) -> dict[str, Any]:
    payload = load_json(scoring_manifest)
    reviews = list(payload.get("reviews", []))
    reviews = [review for review in reviews if float(review.get("scores", {}).get("total", 0.0)) >= min_score]
    reviews.sort(key=lambda item: float(item.get("scores", {}).get("total", 0.0)), reverse=True)
    if max_records is not None:
        reviews = reviews[:max_records]

    records: list[dict[str, Any]] = []
    packet_paths: list[str] = []
    for review in reviews:
        record = build_gold_review_record(review, scoring_manifest)
        packet_path = output_dir / "packets" / f"{record['track_id']}.md"
        packet_path.parent.mkdir(parents=True, exist_ok=True)
        packet_path.write_text(render_gold_review_packet(record), encoding="utf-8")
        record["review_packet_path"] = str(packet_path)
        packet_paths.append(str(packet_path))
        records.append(record)

    jsonl_path = write_jsonl(output_dir / "gold_reviews.jsonl", records)
    manifest = {
        "schema_version": "1.0",
        "source_scoring_manifest": str(scoring_manifest),
        "output_dir": str(output_dir),
        "record_count": len(records),
        "min_score": min_score,
        "gold_reviews_jsonl": str(jsonl_path),
        "packet_paths": packet_paths,
        "tracks": [record["track_id"] for record in records],
    }
    manifest_path = write_json(output_dir / "gold_review_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def render_gold_review_report(manifest: dict[str, Any]) -> str:
    lines = [
        "# Gold Review Bundle",
        "",
        f"- Source scoring manifest: `{manifest['source_scoring_manifest']}`",
        f"- Minimum score: `{manifest['min_score']}`",
        f"- Record count: `{manifest['record_count']}`",
        f"- JSONL: `{manifest['gold_reviews_jsonl']}`",
        "",
        "## Tracks",
        "",
    ]
    for track_id in manifest["tracks"]:
        lines.append(f"- `{track_id}`")
    return "\n".join(lines)


def stable_preference_swap(track_id: str) -> bool:
    digest = hashlib.md5(track_id.encode("utf-8")).hexdigest()
    return int(digest[:2], 16) % 2 == 0


def build_preference_pair_record(
    track_id: str,
    left_review: dict[str, Any],
    right_review: dict[str, Any],
    *,
    left_label: str,
    right_label: str,
    left_manifest: Path,
    right_manifest: Path,
) -> dict[str, Any]:
    left_markdown = load_markdown(Path(left_review["prediction_path"]))
    right_markdown = load_markdown(Path(right_review["prediction_path"]))

    left_option = {
        "source_label": left_label,
        "prediction_path": left_review["prediction_path"],
        "markdown": left_markdown,
        "scores": left_review["scores"],
        "critic_notes": left_review.get("critic_notes", []),
    }
    right_option = {
        "source_label": right_label,
        "prediction_path": right_review["prediction_path"],
        "markdown": right_markdown,
        "scores": right_review["scores"],
        "critic_notes": right_review.get("critic_notes", []),
    }

    if stable_preference_swap(track_id):
        option_a, option_b = right_option, left_option
    else:
        option_a, option_b = left_option, right_option

    return {
        "schema_version": "1.0",
        "record_id": f"{track_id}-preference",
        "track_id": track_id,
        "artist_id": load_json(Path(left_review["run_dir"]) / "plan.json").get("artist_id"),
        "source_manifests": {
            "left": str(left_manifest),
            "right": str(right_manifest),
        },
        "option_a": option_a,
        "option_b": option_b,
        "annotation_template": {
            "winner": "",
            "confidence_1_to_5": None,
            "reason": "",
            "better_hook": "",
            "better_imagery": "",
            "better_structure": "",
        },
    }


def render_preference_packet(record: dict[str, Any]) -> str:
    lines = [
        f"# Preference Review: {record['track_id']}",
        "",
        "Choose the stronger lyric without looking at the hidden score metadata first.",
        "",
        "## Annotation Template",
        "",
        "- winner: `A` or `B`",
        "- confidence_1_to_5:",
        "- reason:",
        "- better_hook:",
        "- better_imagery:",
        "- better_structure:",
        "",
        "## Option A",
        "",
        record["option_a"]["markdown"].strip(),
        "",
        "## Option B",
        "",
        record["option_b"]["markdown"].strip(),
        "",
        "## Hidden Metadata",
        "",
        f"- A source: `{record['option_a']['source_label']}`",
        f"- B source: `{record['option_b']['source_label']}`",
        f"- A total: `{record['option_a']['scores']['total']}`",
        f"- B total: `{record['option_b']['scores']['total']}`",
        "",
    ]
    return "\n".join(lines)


def build_preference_bundle(
    left_scoring_manifest: Path,
    right_scoring_manifest: Path,
    output_dir: Path,
    *,
    left_label: str,
    right_label: str,
    max_pairs: int | None,
) -> dict[str, Any]:
    left_payload = load_json(left_scoring_manifest)
    right_payload = load_json(right_scoring_manifest)
    left_reviews = {review["track_id"]: review for review in left_payload.get("reviews", [])}
    right_reviews = {review["track_id"]: review for review in right_payload.get("reviews", [])}

    shared_track_ids = sorted(set(left_reviews) & set(right_reviews))
    if max_pairs is not None:
        shared_track_ids = shared_track_ids[:max_pairs]

    records: list[dict[str, Any]] = []
    packet_paths: list[str] = []
    for track_id in shared_track_ids:
        record = build_preference_pair_record(
            track_id,
            left_reviews[track_id],
            right_reviews[track_id],
            left_label=left_label,
            right_label=right_label,
            left_manifest=left_scoring_manifest,
            right_manifest=right_scoring_manifest,
        )
        packet_path = output_dir / "packets" / f"{track_id}.md"
        packet_path.parent.mkdir(parents=True, exist_ok=True)
        packet_path.write_text(render_preference_packet(record), encoding="utf-8")
        record["review_packet_path"] = str(packet_path)
        packet_paths.append(str(packet_path))
        records.append(record)

    jsonl_path = write_jsonl(output_dir / "preference_pairs.jsonl", records)
    manifest = {
        "schema_version": "1.0",
        "left_scoring_manifest": str(left_scoring_manifest),
        "right_scoring_manifest": str(right_scoring_manifest),
        "left_label": left_label,
        "right_label": right_label,
        "output_dir": str(output_dir),
        "pair_count": len(records),
        "preference_pairs_jsonl": str(jsonl_path),
        "packet_paths": packet_paths,
        "tracks": [record["track_id"] for record in records],
    }
    manifest_path = write_json(output_dir / "preference_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def render_preference_report(manifest: dict[str, Any]) -> str:
    lines = [
        "# Preference Bundle",
        "",
        f"- Left scoring manifest: `{manifest['left_scoring_manifest']}`",
        f"- Right scoring manifest: `{manifest['right_scoring_manifest']}`",
        f"- Left label: `{manifest['left_label']}`",
        f"- Right label: `{manifest['right_label']}`",
        f"- Pair count: `{manifest['pair_count']}`",
        f"- JSONL: `{manifest['preference_pairs_jsonl']}`",
        "",
        "## Tracks",
        "",
    ]
    for track_id in manifest["tracks"]:
        lines.append(f"- `{track_id}`")
    return "\n".join(lines)
