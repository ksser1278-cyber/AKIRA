from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.reporting import write_utf8_json, write_utf8_text
from akira_engine.round2_expansion import load_json, write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge round2 seed payloads into seed scaffolds and queues.")
    parser.add_argument("--artist-id", required=True)
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--project-root", default=".")
    return parser.parse_args()


def render_report(payload: dict[str, object]) -> str:
    lines = [
        f"# Round2 Seed Merge: {payload['artist_id']}",
        "",
        f"- Input dir: `{payload['input_dir']}`",
        f"- Merged files: `{payload['merged_count']}`",
        f"- Unchanged files: `{payload['unchanged_count']}`",
        "",
        "## Results",
        "",
    ]
    for item in payload["results"]:
        lines.extend(
            [
                f"### {item['track_id']}",
                f"- Changed: `{item['changed']}`",
                f"- Target: `{item['target_path']}`",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    input_dir = Path(args.input_dir).resolve()
    reference_dir = project_root / "data" / args.artist_id / "reference_tracks"
    queue_path = reference_dir / "round2_queue.json"
    seed_dir = reference_dir / "round2_seed_scaffolds"
    queue_payload = load_json(queue_path)
    queue_lookup = {str(item.get("track_id", "")).strip(): item for item in queue_payload.get("queue", [])}

    results = []
    for path in sorted(input_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        track_id = str(payload.get("track_id", "")).strip()
        slug = track_id.removeprefix(f"{args.artist_id}_")
        target_path = seed_dir / f"{slug}.seed.json"
        existing = load_json(target_path) if target_path.exists() else None
        new_payload = {
            "schema_version": "1.0",
            "record_type": "round2_draft_seed",
            "track_identity": {
                "artist_id": args.artist_id,
                "track_id": track_id,
                "title": str(payload.get("title", "")).strip(),
            },
            "dataset_role": {
                "recommended_dataset_tier": str(queue_lookup.get(track_id, {}).get("recommended_dataset_tier", "producer_expansion")).strip(),
                "likely_mode": str(payload.get("likely_mode", "")).strip(),
                "secondary_modes": queue_lookup.get(track_id, {}).get("secondary_modes", []),
                "priority": str(queue_lookup.get(track_id, {}).get("priority_label", "medium")).strip(),
            },
            "seed_brief": {
                "title_pattern": str(payload.get("title_pattern", "")).strip(),
                "hook_behavior": payload.get("hook_behavior", []),
                "section_flow_guess": payload.get("section_flow_guess", []),
                "imagery_classes": payload.get("imagery_classes", []),
                "emotional_arc": payload.get("emotional_arc", []),
                "leakage_watchouts": payload.get("leakage_watchouts", []),
                "prompt_seed_terms": payload.get("prompt_seed_terms", []),
                "grounding_status": str(payload.get("grounding_status", "")).strip(),
            },
            "candidate_context": {
                "why_it_matters": queue_lookup.get(track_id, {}).get("why_it_matters", []),
                "style_gap_filled": queue_lookup.get(track_id, {}).get("style_gap_filled", []),
                "overlap_risk_with_existing_set": "",
                "grounding_feasibility": "",
                "provenance_feasibility": "",
                "audio_feasibility": "",
            },
        }
        changed = existing != new_payload
        if changed:
            write_json(target_path, new_payload)
        queue_item = queue_lookup.get(track_id)
        if queue_item:
            queue_item["has_draft_seed"] = True
            if str(queue_item.get("status", "")).strip() == "candidate_only":
                queue_item["status"] = "seeded"
        results.append({"track_id": track_id, "target_path": str(target_path), "changed": changed})

    write_json(queue_path, queue_payload)

    output = {
        "schema_version": "1.0",
        "artist_id": args.artist_id,
        "input_dir": str(input_dir),
        "merged_count": sum(1 for item in results if item["changed"]),
        "unchanged_count": sum(1 for item in results if not item["changed"]),
        "results": results,
    }
    out_dir = project_root / "reports" / "quality" / "conditioning_merge"
    out_dir.mkdir(parents=True, exist_ok=True)
    write_utf8_json(out_dir / f"{args.artist_id}_round2_seed_merge.json", output)
    write_utf8_text(
        out_dir / f"{args.artist_id}_round2_seed_merge.md",
        render_report(output),
        trailing_newline=False,
    )


if __name__ == "__main__":
    main()
