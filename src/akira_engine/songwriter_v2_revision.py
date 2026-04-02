from __future__ import annotations

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


def weakest_dimensions(scores: dict[str, Any], *, limit: int = 3) -> list[tuple[str, float]]:
    ranked = [
        (name, float(value))
        for name, value in scores.items()
        if name != "total"
    ]
    ranked.sort(key=lambda item: (item[1], item[0]))
    return ranked[:limit]


def build_revision_request_record(review: dict[str, Any]) -> dict[str, Any]:
    run_dir = Path(review["run_dir"])
    plan = load_json(run_dir / "plan.json")
    prompt_package = load_json(run_dir / "prompt_package.json")
    original_markdown = Path(review["prediction_path"]).read_text(encoding="utf-8")
    weak_spots = weakest_dimensions(review["scores"])
    total_target_lines = sum(int(card.get("line_target", 0) or 0) for card in plan.get("section_cards", []))
    output_contract = {
        "format": "markdown",
        "required_sections": plan.get("output_contract", {}).get("ordered_headers", []),
        "minimum_characters": max(220, total_target_lines * 12),
        "must_include": [
            "A title line starting with '# '",
            "All required section headers in order",
            "Original Japanese lyrics only",
        ],
        "must_not_include": [
            "artist names",
            "citations",
            "analysis prose",
        ],
    }

    revision_lines = [
        prompt_package["generator_prompt"],
        "",
        "Revision task:",
        "- Rewrite the full lyric from scratch while keeping the same markdown format contract.",
        "- Keep the strongest ideas from the current draft only if they still serve the plan.",
        "- Do not shorten the song or drop any required sections.",
        "- Make the result feel more specific, concrete, and complete than the current draft.",
        "- Preserve the varied section scale instead of flattening every section to the same size.",
        "",
        "Critic notes to address:",
        *[f"- {note}" for note in review.get("critic_notes", [])],
        "",
        "Weak score dimensions to improve:",
        *[f"- {name}: {value}" for name, value in weak_spots],
        "",
        "Current draft to revise:",
        original_markdown,
        "",
        "Return one complete markdown lyric only.",
    ]

    return {
        "request_id": f"{plan['track_id']}-revision-request",
        "track_id": plan["track_id"],
        "artist_id": plan["artist_id"],
        "run_dir": str(run_dir),
        "output_filename": f"{plan['track_id']}.md",
        "schema_version": "1.0",
        "system_prompt": prompt_package["system_prompt"],
        "user_prompt": "\n".join(revision_lines),
        "critic_prompt": prompt_package["critic_prompt"],
        "output_contract": output_contract,
        "revision_context": {
            "original_total": review["scores"]["total"],
            "critic_notes": review.get("critic_notes", []),
            "weak_dimensions": weak_spots,
        },
    }


def build_revision_request_bundle(
    scoring_manifest: Path,
    output_dir: Path,
    *,
    score_threshold: float,
    max_revisions: int | None,
) -> dict[str, Any]:
    scoring = load_json(scoring_manifest)
    reviews = list(scoring.get("reviews", []))
    candidates = [review for review in reviews if float(review.get("scores", {}).get("total", 0.0)) < score_threshold]
    candidates.sort(key=lambda item: float(item.get("scores", {}).get("total", 0.0)))
    if max_revisions is not None:
        candidates = candidates[:max_revisions]

    records = [build_revision_request_record(review) for review in candidates]
    jsonl_path = write_jsonl(output_dir / "requests.jsonl", records)
    manifest = {
        "schema_version": "1.0",
        "source_scoring_manifest": str(scoring_manifest),
        "run_root": scoring.get("run_root"),
        "output_dir": str(output_dir),
        "score_threshold": score_threshold,
        "request_count": len(records),
        "requests_jsonl": str(jsonl_path),
        "tracks": [record["track_id"] for record in records],
    }
    manifest_path = write_json(output_dir / "request_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def render_revision_request_report(manifest: dict[str, Any]) -> str:
    lines = [
        "# Songwriter V2 Revision Request Export",
        "",
        f"- Source scoring manifest: `{manifest['source_scoring_manifest']}`",
        f"- Score threshold: `{manifest['score_threshold']}`",
        f"- Request count: `{manifest['request_count']}`",
        f"- Requests JSONL: `{manifest['requests_jsonl']}`",
        "",
        "## Tracks",
        "",
    ]
    for track_id in manifest["tracks"]:
        lines.append(f"- `{track_id}`")
    return "\n".join(lines)


def render_revision_comparison_report(
    original_scoring: dict[str, Any],
    revised_scoring: dict[str, Any],
) -> str:
    original_reviews = {item["track_id"]: item for item in original_scoring.get("reviews", [])}
    revised_reviews = {item["track_id"]: item for item in revised_scoring.get("reviews", [])}
    shared_ids = sorted(set(original_reviews) & set(revised_reviews))

    lines = [
        "# Songwriter V2 Revision Comparison",
        "",
        f"- Original scoring manifest: `{original_scoring.get('manifest_path', '')}`",
        f"- Revised scoring manifest: `{revised_scoring.get('manifest_path', '')}`",
        f"- Revised tracks: `{len(shared_ids)}`",
        "",
    ]
    if shared_ids:
        original_average = round(
            sum(float(original_reviews[track_id]["scores"]["total"]) for track_id in shared_ids) / len(shared_ids),
            2,
        )
        revised_average = round(
            sum(float(revised_reviews[track_id]["scores"]["total"]) for track_id in shared_ids) / len(shared_ids),
            2,
        )
        lines.extend(
            [
                f"- Original subset average: `{original_average}`",
                f"- Revised subset average: `{revised_average}`",
                f"- Average delta: `{round(revised_average - original_average, 2)}`",
                "",
                "## Track Deltas",
                "",
            ]
        )
        deltas: list[tuple[float, str, float, float]] = []
        for track_id in shared_ids:
            before = float(original_reviews[track_id]["scores"]["total"])
            after = float(revised_reviews[track_id]["scores"]["total"])
            deltas.append((after - before, track_id, before, after))
        deltas.sort(reverse=True)
        for delta, track_id, before, after in deltas:
            lines.extend(
                [
                    f"### {track_id}",
                    f"- Before: `{before}`",
                    f"- After: `{after}`",
                    f"- Delta: `{round(delta, 2)}`",
                    "",
                ]
            )
    else:
        lines.append("- No revised tracks were scored.")
    return "\n".join(lines)
