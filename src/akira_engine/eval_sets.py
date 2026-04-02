from __future__ import annotations

import json
from pathlib import Path
from typing import Any


TASK_FILES = {
    "mode_selector_eval": "mode_selector.jsonl",
    "structure_planner_eval": "structure_planner.jsonl",
    "hook_planner_eval": "hook_planner.jsonl",
    "style_prompt_eval": "style_prompt_builder.jsonl",
    "full_song_brief_eval": "full_song_brief.jsonl",
}

HELD_OUT_SPLITS = {"validation", "test"}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


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


def track_lookup(track_records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {record["track_id"]: record for record in track_records}


def infer_difficulty(track_record: dict[str, Any]) -> str:
    evidence = track_record.get("input_context", {}).get("track_evidence", {})
    hook_strategy = evidence.get("hook_strategy", {})
    language_profile = evidence.get("language_profile", {})

    score = 0
    if evidence.get("observed_section_count", 0) >= 14:
        score += 2
    elif evidence.get("observed_section_count", 0) >= 10:
        score += 1

    if hook_strategy.get("hook_density") == "high":
        score += 1
    if hook_strategy.get("hook_candidate_count", 0) >= 7:
        score += 1
    if language_profile.get("english_insertion_level") in {"medium", "high"}:
        score += 1
    if len(track_record.get("target", {}).get("theme_axes", [])) >= 6:
        score += 1

    if score >= 4:
        return "hard"
    if score >= 2:
        return "medium"
    return "easy"


def base_metadata(track_record: dict[str, Any], experiment_record: dict[str, Any]) -> dict[str, Any]:
    evidence = track_record.get("input_context", {}).get("track_evidence", {})
    hook_strategy = evidence.get("hook_strategy", {})
    target = track_record.get("target", {})
    return {
        "observed_section_count": evidence.get("observed_section_count"),
        "overall_arc_label": evidence.get("overall_arc_label"),
        "hook_density": hook_strategy.get("hook_density"),
        "hook_candidate_count": hook_strategy.get("hook_candidate_count"),
        "theme_axis_count": len(experiment_record.get("target", {}).get("theme_axes", []) or target.get("theme_axes", [])),
        "selected_mode": experiment_record.get("target", {}).get("primary_mode") or target.get("primary_mode"),
    }


def task_rubric(task_name: str) -> list[dict[str, Any]]:
    rubrics = {
        "mode_selector_eval": [
            {
                "dimension": "mode_fit",
                "weight": 0.35,
                "description": "Chosen mode matches the emotional movement, imagery, and arc evidence.",
            },
            {
                "dimension": "theme_grounding",
                "weight": 0.25,
                "description": "Theme axes are grounded in the supplied track evidence, not guessed generically.",
            },
            {
                "dimension": "artist_alignment",
                "weight": 0.20,
                "description": "Decision stays compatible with the artist style card and mode candidates.",
            },
            {
                "dimension": "safety",
                "weight": 0.20,
                "description": "No verbatim lyric reuse and no direct artist naming as a copying instruction.",
            },
        ],
        "structure_planner_eval": [
            {
                "dimension": "form_coherence",
                "weight": 0.30,
                "description": "Section order is coherent and reusable as a song plan.",
            },
            {
                "dimension": "arc_alignment",
                "weight": 0.25,
                "description": "Structure reflects the observed build, release, or circular arc.",
            },
            {
                "dimension": "hook_release",
                "weight": 0.25,
                "description": "Chorus placement and late-song release match the hook evidence.",
            },
            {
                "dimension": "artist_alignment",
                "weight": 0.10,
                "description": "Structure stays compatible with Ado-derived defaults.",
            },
            {
                "dimension": "safety",
                "weight": 0.10,
                "description": "Plan stays non-verbatim and stylistically adjacent.",
            },
        ],
        "hook_planner_eval": [
            {
                "dimension": "hook_density_fit",
                "weight": 0.30,
                "description": "Hook density matches the observed repetition profile.",
            },
            {
                "dimension": "repetition_strategy",
                "weight": 0.25,
                "description": "Repeated lines and openings are used in a deliberate, reusable way.",
            },
            {
                "dimension": "theme_hook_linkage",
                "weight": 0.20,
                "description": "Hook plan reinforces the track's themes and imagery rather than sitting separately.",
            },
            {
                "dimension": "artist_alignment",
                "weight": 0.10,
                "description": "Hook choices feel compatible with the artist style card.",
            },
            {
                "dimension": "safety",
                "weight": 0.15,
                "description": "No direct lyric copying or artist imitation instructions.",
            },
        ],
        "style_prompt_eval": [
            {
                "dimension": "style_fidelity",
                "weight": 0.30,
                "description": "Prompt captures the right style lane, energy, and sonic direction.",
            },
            {
                "dimension": "imagery_theme_coverage",
                "weight": 0.25,
                "description": "Prompt includes the right imagery families and theme axes.",
            },
            {
                "dimension": "section_guidance",
                "weight": 0.20,
                "description": "Section emphasis supports reusable generation instead of vague mood tagging.",
            },
            {
                "dimension": "conciseness",
                "weight": 0.10,
                "description": "Prompt stays compact and SUNO-ready.",
            },
            {
                "dimension": "safety",
                "weight": 0.15,
                "description": "Prompt avoids verbatim lyrics and direct artist-copy instructions.",
            },
        ],
        "full_song_brief_eval": [
            {
                "dimension": "mode_and_theme_fit",
                "weight": 0.20,
                "description": "Mode and theme axes fit the held-out evidence.",
            },
            {
                "dimension": "structure_quality",
                "weight": 0.25,
                "description": "Structure is coherent, reusable, and aligned to the observed arc.",
            },
            {
                "dimension": "hook_strategy_quality",
                "weight": 0.20,
                "description": "Hook plan is well-matched to repetition and release signals.",
            },
            {
                "dimension": "constraint_quality",
                "weight": 0.15,
                "description": "Style constraints and language policy are realistic and useful.",
            },
            {
                "dimension": "prompt_seed_quality",
                "weight": 0.10,
                "description": "Prompt seed is concise and reflects the combined evidence.",
            },
            {
                "dimension": "safety",
                "weight": 0.10,
                "description": "Brief remains derived-only and avoids direct lyric reuse.",
            },
        ],
    }
    return rubrics[task_name]


def reference_summary(task_name: str, track_record: dict[str, Any], experiment_record: dict[str, Any]) -> dict[str, Any]:
    evidence = track_record.get("input_context", {}).get("track_evidence", {})
    target = experiment_record.get("target", {})
    track_target = track_record.get("target", {})
    summary = {
        "expected_primary_mode": target.get("primary_mode") or track_target.get("primary_mode"),
        "expected_theme_axes": target.get("theme_axes", []) or track_target.get("theme_axes", []),
        "overall_arc_label": evidence.get("overall_arc_label"),
    }

    if task_name == "structure_planner_eval":
        summary["expected_sections"] = [
            item.get("section")
            for item in target.get("recommended_structure", [])
            if item.get("section")
        ]
    elif task_name == "hook_planner_eval":
        summary["expected_hook_density"] = target.get("hook_plan", {}).get("hook_density")
        summary["expected_repeated_line_count"] = target.get("hook_plan", {}).get("repeated_line_count")
    elif task_name == "style_prompt_eval":
        summary["expected_primary_mode"] = (
            experiment_record.get("input_context", {}).get("track_evidence", {}).get("selected_mode")
            or track_target.get("primary_mode")
        )
        summary["expected_theme_axes"] = (
            experiment_record.get("input_context", {}).get("track_evidence", {}).get("theme_axes", [])
            or track_target.get("theme_axes", [])
        )
        summary["style_of_music"] = target.get("style_of_music")
        summary["section_emphasis"] = target.get("section_emphasis", [])
    elif task_name == "full_song_brief_eval":
        summary["expected_sections"] = [
            item.get("section")
            for item in target.get("recommended_structure", [])
            if item.get("section")
        ]
        summary["expected_hook_density"] = target.get("hook_plan", {}).get("hook_density")
        summary["style_prompt_seed"] = {
            "style_of_music": target.get("style_prompt_seed", {}).get("style_of_music"),
            "section_emphasis": target.get("style_prompt_seed", {}).get("section_emphasis", []),
        }
    return summary


def judge_instructions(task_name: str) -> str:
    return (
        f"Evaluate the candidate {task_name} output against the input context and reference target. "
        "Score each rubric dimension from 0 to 5, then convert the weighted total to a 0-100 score. "
        "Penalize missing structure, generic themes, direct lyric reuse, and direct artist-copy wording."
    )


def safety_checks() -> list[str]:
    return [
        "Do not reward verbatim lyric reuse.",
        "Do not reward direct artist-name copying instructions.",
        "Prefer derived imagery, structure, and hook behavior over surface imitation.",
    ]


def build_eval_record(
    task_name: str,
    experiment_record: dict[str, Any],
    track_record: dict[str, Any],
) -> dict[str, Any]:
    return {
        "eval_id": f"{experiment_record['record_id']}-eval",
        "split": experiment_record["split"],
        "task_type": task_name,
        "artist_id": experiment_record["artist_id"],
        "artist_name": experiment_record["artist_name"],
        "track_id": experiment_record["track_id"],
        "title": experiment_record["title"],
        "difficulty": infer_difficulty(track_record),
        "contains_copyrighted_lyrics": False,
        "source_paths": track_record.get("source_paths", {}),
        "instruction": experiment_record["instruction"],
        "input_context": experiment_record["input_context"],
        "reference_target": experiment_record["target"],
        "reference_summary": reference_summary(task_name, track_record, experiment_record),
        "rubric": task_rubric(task_name),
        "judge_instructions": judge_instructions(task_name),
        "safety_checks": safety_checks(),
        "metadata": base_metadata(track_record, experiment_record),
    }


def build_eval_sets(
    package_dir: Path,
    *,
    experiments_dir: Path | None = None,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    track_records = load_jsonl(package_dir / "track_blueprints.jsonl")
    track_by_id = track_lookup(track_records)
    held_out_tracks = [record for record in track_records if record["split"] in HELD_OUT_SPLITS]
    if not held_out_tracks:
        raise ValueError(f"No held-out tracks found in {package_dir}")

    artist_id = held_out_tracks[0]["artist_id"]
    final_experiments_dir = experiments_dir or (package_dir.parent.parent / "experiments" / artist_id)
    final_output_dir = output_dir or (package_dir.parent.parent / "evals" / artist_id)
    final_output_dir.mkdir(parents=True, exist_ok=True)

    outputs: dict[str, str] = {}
    counts: dict[str, int] = {}
    split_counts = {split: 0 for split in sorted(HELD_OUT_SPLITS)}
    difficulty_counts = {"easy": 0, "medium": 0, "hard": 0}

    for split in HELD_OUT_SPLITS:
        split_counts[split] = sum(1 for record in held_out_tracks if record["split"] == split)
    for record in held_out_tracks:
        difficulty_counts[infer_difficulty(record)] += 1

    for task_name, filename in TASK_FILES.items():
        experiment_records = load_jsonl(final_experiments_dir / filename)
        eval_records: list[dict[str, Any]] = []
        for experiment_record in experiment_records:
            if experiment_record["split"] not in HELD_OUT_SPLITS:
                continue
            track_record = track_by_id[experiment_record["track_id"]]
            eval_record = build_eval_record(task_name, experiment_record, track_record)
            eval_records.append(eval_record)

        output_path = write_jsonl(final_output_dir / f"{task_name}.jsonl", eval_records)
        outputs[task_name] = str(output_path)
        counts[task_name] = len(eval_records)

    manifest = {
        "schema_version": "1.0",
        "artist_id": artist_id,
        "source_package_dir": str(package_dir),
        "source_experiments_dir": str(final_experiments_dir),
        "output_dir": str(final_output_dir),
        "heldout_source_records": len(held_out_tracks),
        "split_counts": split_counts,
        "difficulty_counts": difficulty_counts,
        "counts": counts,
        "outputs": outputs,
    }
    manifest_path = write_json(final_output_dir / "eval_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def render_eval_report(manifest: dict[str, Any]) -> str:
    lines = [
        f"# {manifest['artist_id']} Eval Sets",
        "",
        f"- Source package dir: `{manifest['source_package_dir']}`",
        f"- Source experiments dir: `{manifest['source_experiments_dir']}`",
        f"- Held-out track records: `{manifest['heldout_source_records']}`",
        "",
        "## Split Counts",
        "",
    ]
    for split_name, count in manifest.get("split_counts", {}).items():
        lines.append(f"- `{split_name}`: {count}")
    lines.extend(
        [
            "",
            "## Difficulty Counts",
            "",
        ]
    )
    for difficulty, count in manifest.get("difficulty_counts", {}).items():
        lines.append(f"- `{difficulty}`: {count}")
    lines.extend(
        [
            "",
            "## Outputs",
            "",
        ]
    )
    for task_name, count in manifest.get("counts", {}).items():
        lines.append(f"- `{task_name}`: {count}")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- These sets keep only validation and test records so generation experiments can be compared on held-out evidence.",
            "- Every eval record includes a weighted rubric, a compact reference summary, and safety checks.",
            "- Use these files to benchmark planning quality before attempting larger multi-artist runs.",
            "",
        ]
    )
    return "\n".join(lines)
