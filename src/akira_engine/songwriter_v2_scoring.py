from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .songwriter_v2 import critique_candidate


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def discover_run_dirs(run_root: Path) -> list[Path]:
    plan_paths = sorted(run_root.rglob("plan.json"))
    return [path.parent for path in plan_paths]


def score_external_predictions(run_root: Path, predictions_dir: Path, output_dir: Path) -> dict[str, Any]:
    run_dirs = discover_run_dirs(run_root)
    reviews: list[dict[str, Any]] = []

    for run_dir in run_dirs:
        plan_path = run_dir / "plan.json"
        plan = load_json(plan_path)
        track_id = plan["track_id"]
        prediction_path = predictions_dir / f"{track_id}.md"
        if not prediction_path.exists():
            continue
        markdown_text = prediction_path.read_text(encoding="utf-8")
        critique = critique_candidate(
            plan,
            {
                "candidate_id": f"{track_id}-external",
                "title": markdown_text.splitlines()[0].replace("# ", "").strip() if markdown_text.startswith("# ") else track_id,
                "markdown": markdown_text,
            },
        )
        reviews.append(
            {
                "track_id": track_id,
                "prediction_path": str(prediction_path),
                "run_dir": str(run_dir),
                **critique,
            }
        )

    summary = {
        "count": len(reviews),
        "average_total": round(sum(item["scores"]["total"] for item in reviews) / max(1, len(reviews)), 2),
        "below_75": sum(1 for item in reviews if item["scores"]["total"] < 75),
        "between_75_and_85": sum(1 for item in reviews if 75 <= item["scores"]["total"] < 85),
        "above_85": sum(1 for item in reviews if item["scores"]["total"] >= 85),
    }
    payload = {
        "schema_version": "1.0",
        "run_root": str(run_root),
        "predictions_dir": str(predictions_dir),
        "summary": summary,
        "reviews": sorted(reviews, key=lambda item: item["scores"]["total"], reverse=True),
    }
    manifest_path = write_json(output_dir / "scoring_manifest.json", payload)
    payload["manifest_path"] = str(manifest_path)
    return payload


def render_scoring_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Songwriter V2 External Scoring",
        "",
        f"- Run root: `{payload['run_root']}`",
        f"- Predictions dir: `{payload['predictions_dir']}`",
        f"- Reviewed predictions: `{summary['count']}`",
        f"- Average total: `{summary['average_total']}`",
        f"- Below 75: `{summary['below_75']}`",
        f"- 75 to 85: `{summary['between_75_and_85']}`",
        f"- 85 plus: `{summary['above_85']}`",
        "",
        "## Reviews",
        "",
    ]
    for review in payload["reviews"]:
        scores = review["scores"]
        lines.extend(
            [
                f"### {review['track_id']}",
                f"- Prediction: `{review['prediction_path']}`",
                f"- Total: `{scores['total']}`",
                f"- Motif coverage: `{scores['motif_coverage']}`",
                f"- Plan alignment: `{scores['plan_alignment']}`",
                f"- Hook control: `{scores['hook_control']}`",
                f"- Specificity: `{scores['specificity']}`",
                f"- Novelty: `{scores['novelty']}`",
                f"- Final release: `{scores['final_release']}`",
                f"- JP hook force: `{scores['jp_hook_force']}`",
                f"- JP section flow: `{scores['jp_section_flow']}`",
                f"- Notes: {'; '.join(review['critic_notes'])}",
                "",
            ]
        )
    return "\n".join(lines)
