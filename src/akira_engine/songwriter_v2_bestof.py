from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def summary_from_reviews(reviews: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "count": len(reviews),
        "average_total": round(sum(float(item["scores"]["total"]) for item in reviews) / max(1, len(reviews)), 2),
        "below_75": sum(1 for item in reviews if float(item["scores"]["total"]) < 75),
        "between_75_and_85": sum(1 for item in reviews if 75 <= float(item["scores"]["total"]) < 85),
        "above_85": sum(1 for item in reviews if float(item["scores"]["total"]) >= 85),
    }


def build_bestof_scoring_manifest(scoring_manifests: list[Path], output_dir: Path) -> dict[str, Any]:
    best_reviews: dict[str, dict[str, Any]] = {}
    run_root = ""

    for manifest_path in scoring_manifests:
        payload = load_json(manifest_path)
        if not run_root and payload.get("run_root"):
            run_root = str(payload["run_root"])
        for review in payload.get("reviews", []):
            track_id = str(review["track_id"])
            current_best = best_reviews.get(track_id)
            score = float(review.get("scores", {}).get("total", 0.0))
            if current_best is None or score > float(current_best.get("scores", {}).get("total", 0.0)):
                selected = dict(review)
                selected["source_scoring_manifest"] = str(manifest_path)
                best_reviews[track_id] = selected

    copied_reviews: list[dict[str, Any]] = []
    predictions_dir = output_dir / "imported_predictions"
    predictions_dir.mkdir(parents=True, exist_ok=True)

    for track_id, review in sorted(best_reviews.items()):
        source_prediction = Path(review["prediction_path"])
        copied_prediction = predictions_dir / f"{track_id}.md"
        shutil.copyfile(source_prediction, copied_prediction)
        selected = dict(review)
        selected["prediction_path"] = str(copied_prediction)
        copied_reviews.append(selected)

    copied_reviews.sort(key=lambda item: float(item["scores"]["total"]), reverse=True)
    payload = {
        "schema_version": "1.0",
        "source_scoring_manifests": [str(path) for path in scoring_manifests],
        "run_root": run_root,
        "output_dir": str(output_dir),
        "summary": summary_from_reviews(copied_reviews),
        "reviews": copied_reviews,
    }
    manifest_path = write_json(output_dir / "scoring_manifest.json", payload)
    payload["manifest_path"] = str(manifest_path)
    return payload


def render_bestof_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Songwriter V2 Best-Of Selection",
        "",
        f"- Source manifests: `{len(payload['source_scoring_manifests'])}`",
        f"- Selected tracks: `{summary['count']}`",
        f"- Average total: `{summary['average_total']}`",
        f"- Below 75: `{summary['below_75']}`",
        f"- 75 to 85: `{summary['between_75_and_85']}`",
        f"- 85 plus: `{summary['above_85']}`",
        "",
        "## Tracks",
        "",
    ]
    for review in payload["reviews"]:
        lines.extend(
            [
                f"### {review['track_id']}",
                f"- Total: `{review['scores']['total']}`",
                f"- Source scoring manifest: `{review['source_scoring_manifest']}`",
                f"- Prediction: `{review['prediction_path']}`",
                "",
            ]
        )
    return "\n".join(lines)
