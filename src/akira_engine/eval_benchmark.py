from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


TASK_FILES = {
    "mode_selector_eval": "mode_selector_eval.jsonl",
    "structure_planner_eval": "structure_planner_eval.jsonl",
    "hook_planner_eval": "hook_planner_eval.jsonl",
    "style_prompt_eval": "style_prompt_eval.jsonl",
    "full_song_brief_eval": "full_song_brief_eval.jsonl",
}

LANGUAGE_POLICY = {
    "primary_language": "Japanese",
    "allowed_languages": ["Japanese"],
    "avoid_languages": ["English-heavy lyrics"],
}

SECTION_GOALS = {
    "intro": "Open with mood and tension before the main release.",
    "verse_1": "Carry concrete details and perspective-specific storytelling.",
    "pre_chorus": "Compress the language and tighten emotion before the chorus release.",
    "chorus": "Deliver the core hook in a chantable, memorable form.",
    "verse_2": "Increase specificity and tension through denser descriptive lines.",
    "bridge": "Change angle or emotional framing before the final section.",
    "chorus_final": "Deliver the clearest emotional release with the strongest hook restatement.",
    "outro": "Let the emotional afterimage linger without adding a new twist.",
}

MODE_RULES = [
    {
        "mode_id": "rebellious_dark",
        "tags": {"defiance", "fracture", "fire", "noise", "pressure"},
        "arc_bonus": {"build_and_drop"},
    },
    {
        "mode_id": "anthemic_cinematic",
        "tags": {"light", "uplift", "arrival", "breakthrough", "weather"},
        "arc_bonus": {"steady_build_to_final_release", "build_and_drop"},
    },
    {
        "mode_id": "night_drive",
        "tags": {"night", "city", "motion", "escape", "restlessness"},
        "arc_bonus": {"flat_or_circular", "build_and_drop"},
    },
    {
        "mode_id": "intimate_confessional",
        "tags": {"body", "vulnerability", "private", "heart", "voice", "time"},
        "arc_bonus": {"flat_or_circular", "build_and_drop"},
    },
]


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


def unique_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            output.append(item)
    return output


def tokenize_text(value: str) -> list[str]:
    return [token for token in re.findall(r"[a-z0-9_]+", value.lower()) if len(token) > 1]


def normalized_items(items: list[str]) -> list[str]:
    normalized: list[str] = []
    for item in items:
        text = str(item).strip().lower().replace(" ", "_")
        if text:
            normalized.append(text)
    return unique_preserve_order(normalized)


def overlap_score(expected: list[str], actual: list[str]) -> float:
    expected_set = set(normalized_items(expected))
    actual_set = set(normalized_items(actual))
    if not expected_set and not actual_set:
        return 1.0
    if not expected_set or not actual_set:
        return 0.0
    return len(expected_set & actual_set) / len(expected_set | actual_set)


def exact_or_zero(expected: Any, actual: Any) -> float:
    return 1.0 if expected == actual else 0.0


def clamp_01(value: float) -> float:
    return max(0.0, min(1.0, value))


def closeness_score(expected: float, actual: float, tolerance: float) -> float:
    if tolerance <= 0:
        return 1.0 if expected == actual else 0.0
    return clamp_01(1.0 - (abs(expected - actual) / tolerance))


def canonical_section_label(section: str) -> str:
    if section.startswith("chorus_final"):
        return "chorus_final"
    if section.startswith("chorus"):
        return "chorus"
    if section.startswith("pre_chorus"):
        return "pre_chorus"
    if section.startswith("verse_1"):
        return "verse_1"
    if section.startswith("verse_2"):
        return "verse_2"
    if section.startswith("verse"):
        return "verse"
    if section.startswith("bridge"):
        return "bridge"
    if section.startswith("intro"):
        return "intro"
    if section.startswith("outro"):
        return "outro"
    if section.startswith("interlude"):
        return "interlude"
    return section


def canonical_section_list(items: list[str]) -> list[str]:
    return unique_preserve_order([canonical_section_label(item) for item in items if item])


def section_sequence_score(expected: list[str], actual: list[str]) -> float:
    return overlap_score(canonical_section_list(expected), canonical_section_list(actual))


def serialize_payload(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True).lower()


def safety_score_from_payload(payload: Any) -> float:
    text = serialize_payload(payload)
    blocked_patterns = [
        "style of ado",
        "copy ado",
        "ado style",
        "\"ado\"",
    ]
    return 0.0 if any(pattern in text for pattern in blocked_patterns) else 1.0


def choose_mode(candidate_modes: list[str], evidence: dict[str, Any]) -> str | None:
    if not candidate_modes:
        return None

    tags = set(
        normalized_items(
            evidence.get("dominant_imagery_tags", []) + evidence.get("dominant_emotions", [])
        )
    )
    arc = evidence.get("overall_arc_label")
    ranked: list[tuple[int, str]] = []

    for rule in MODE_RULES:
        mode_id = rule["mode_id"]
        if mode_id not in candidate_modes:
            continue
        score = sum(4 for tag in tags if tag in rule["tags"])
        if arc in rule["arc_bonus"]:
            score += 3
        ranked.append((score, mode_id))

    ranked.sort(reverse=True)
    if ranked and ranked[0][0] > 0:
        return ranked[0][1]
    return candidate_modes[0]


def theme_axes_from_evidence(evidence: dict[str, Any]) -> list[str]:
    explicit_theme_axes = evidence.get("theme_axes", [])
    if explicit_theme_axes:
        return unique_preserve_order(list(explicit_theme_axes))
    return unique_preserve_order(
        list(evidence.get("dominant_imagery_tags", [])) + list(evidence.get("dominant_emotions", []))
    )


def build_recommended_structure(evidence: dict[str, Any], structural_defaults: list[str]) -> list[dict[str, Any]]:
    inferred = evidence.get("inferred_song_form", {}).get("form_labels", [])
    merged = unique_preserve_order(canonical_section_list(inferred) + structural_defaults)
    output: list[dict[str, Any]] = []
    for section in merged:
        if section in SECTION_GOALS:
            output.append({"section": section, "goal": SECTION_GOALS[section]})
    if output:
        return output
    fallback = ["verse_1", "pre_chorus", "chorus", "verse_2", "bridge", "chorus_final"]
    return [{"section": section, "goal": SECTION_GOALS[section]} for section in fallback]


def build_track_conditioned_structure(evidence: dict[str, Any]) -> dict[str, Any]:
    inferred = evidence.get("inferred_song_form", {})
    ordered_sections = inferred.get("ordered_sections", [])
    compact_sections = []
    seen_labels: set[str] = set()
    for item in ordered_sections:
        label = canonical_section_label(item.get("inferred_label", ""))
        if not label or label in seen_labels:
            continue
        seen_labels.add(label)
        compact_sections.append({"section": label, "line_count": item.get("line_count", 0)})
    return {
        "confidence": inferred.get("confidence", "medium"),
        "sections": compact_sections,
        "form_labels": [item["section"] for item in compact_sections],
    }


def build_hook_plan(evidence: dict[str, Any]) -> dict[str, Any]:
    hook_strategy = evidence.get("hook_strategy", {})
    return {
        "hook_density": hook_strategy.get("hook_density", "medium"),
        "hook_candidate_count": hook_strategy.get("hook_candidate_count", 0),
        "repeated_line_count": hook_strategy.get("repeated_line_count", 0),
        "repeated_opening_count": hook_strategy.get("repeated_opening_count", 0),
    }


def build_style_prompt_seed(
    *,
    mode_id: str | None,
    theme_axes: list[str],
    artist_context: dict[str, Any],
    evidence: dict[str, Any],
    recommended_structure: list[dict[str, Any]],
) -> dict[str, Any]:
    style_tags = artist_context.get("style_tags", [])
    style_of_music_parts = []
    if mode_id:
        style_of_music_parts.append(mode_id.replace("_", " ").title())
    style_of_music_parts.extend(style_tags[:5])
    style_of_music_parts.extend(theme_axes[:4])
    style_of_music = ", ".join(unique_preserve_order(style_of_music_parts))

    lyric_direction = []
    if theme_axes:
        lyric_direction.append("themes: " + ", ".join(theme_axes[:6]))
    imagery_bank = artist_context.get("imagery_bank", [])
    if imagery_bank:
        lyric_direction.append("imagery anchors: " + ", ".join(imagery_bank[:6]))

    return {
        "style_of_music": style_of_music,
        "vocal_direction": unique_preserve_order(
            [
                f"{evidence.get('hook_strategy', {}).get('hook_density', 'medium')} hook emphasis",
                str(evidence.get("overall_arc_label", "undetermined")).replace("_", " "),
            ]
        ),
        "lyric_direction": lyric_direction,
        "section_emphasis": [item["section"] for item in recommended_structure[:6]],
    }


def generate_prediction(task_name: str, eval_record: dict[str, Any]) -> dict[str, Any]:
    input_context = eval_record.get("input_context", {})
    artist_context = input_context.get("artist_context", {})
    evidence = input_context.get("track_evidence", {})
    theme_axes = theme_axes_from_evidence(evidence)

    if task_name == "mode_selector_eval":
        return {
            "primary_mode": choose_mode(input_context.get("candidate_modes", []), evidence),
            "theme_axes": theme_axes,
        }

    if task_name == "structure_planner_eval":
        return {
            "track_conditioned_structure": build_track_conditioned_structure(evidence),
            "recommended_structure": build_recommended_structure(
                evidence,
                artist_context.get("structural_defaults", []),
            ),
        }

    if task_name == "hook_planner_eval":
        return {
            "theme_axes": theme_axes,
            "hook_plan": build_hook_plan(evidence),
        }

    if task_name == "style_prompt_eval":
        primary_mode = evidence.get("selected_mode") or choose_mode(
            ["intimate_confessional", "night_drive", "anthemic_cinematic", "rebellious_dark"],
            evidence,
        )
        recommended_structure = build_recommended_structure(
            evidence,
            artist_context.get("structural_defaults", []),
        )
        return build_style_prompt_seed(
            mode_id=primary_mode,
            theme_axes=theme_axes,
            artist_context=artist_context,
            evidence=evidence,
            recommended_structure=recommended_structure,
        )

    if task_name == "full_song_brief_eval":
        artist_frame = input_context.get("artist_frame", {})
        primary_mode = choose_mode(artist_frame.get("mode_candidates", []), evidence)
        recommended_structure = build_recommended_structure(
            evidence,
            artist_context.get("structural_defaults", []),
        )
        return {
            "primary_mode": primary_mode,
            "theme_axes": theme_axes,
            "style_constraints": {
                "style_tags": artist_context.get("style_tags", []),
                "language_policy": LANGUAGE_POLICY,
                "imagery_bank": artist_context.get("imagery_bank", [])[:10],
                "compatible_modes": artist_frame.get("mode_candidates", []),
            },
            "track_conditioned_structure": build_track_conditioned_structure(evidence),
            "recommended_structure": recommended_structure,
            "hook_plan": build_hook_plan(evidence),
            "style_prompt_seed": build_style_prompt_seed(
                mode_id=primary_mode,
                theme_axes=theme_axes,
                artist_context=artist_context,
                evidence=evidence,
                recommended_structure=recommended_structure,
            ),
        }

    raise ValueError(f"Unsupported task_name: {task_name}")


def score_to_five(scale_01: float) -> float:
    return round(clamp_01(scale_01) * 5.0, 2)


def style_of_music_overlap(expected: str, actual: str) -> float:
    return overlap_score(tokenize_text(expected), tokenize_text(actual))


def structure_quality_score(reference_target: dict[str, Any], prediction: dict[str, Any]) -> float:
    expected_sections = [item.get("section") for item in reference_target.get("recommended_structure", []) if item.get("section")]
    actual_sections = [item.get("section") for item in prediction.get("recommended_structure", []) if item.get("section")]
    return section_sequence_score(expected_sections, actual_sections)


def hook_plan_score(reference_target: dict[str, Any], prediction: dict[str, Any]) -> float:
    expected_hook = reference_target.get("hook_plan", {})
    actual_hook = prediction.get("hook_plan", {})
    density = exact_or_zero(expected_hook.get("hook_density"), actual_hook.get("hook_density"))
    repeated_lines = closeness_score(
        float(expected_hook.get("repeated_line_count", 0)),
        float(actual_hook.get("repeated_line_count", 0)),
        tolerance=4.0,
    )
    repeated_openings = closeness_score(
        float(expected_hook.get("repeated_opening_count", 0)),
        float(actual_hook.get("repeated_opening_count", 0)),
        tolerance=4.0,
    )
    return (density + repeated_lines + repeated_openings) / 3.0


def constraint_quality_score(reference_target: dict[str, Any], prediction: dict[str, Any]) -> float:
    expected_constraints = reference_target.get("style_constraints", {})
    actual_constraints = prediction.get("style_constraints", {})
    style_tags = overlap_score(expected_constraints.get("style_tags", []), actual_constraints.get("style_tags", []))
    imagery = overlap_score(expected_constraints.get("imagery_bank", []), actual_constraints.get("imagery_bank", []))
    language_primary = exact_or_zero(
        expected_constraints.get("language_policy", {}).get("primary_language"),
        actual_constraints.get("language_policy", {}).get("primary_language"),
    )
    return (style_tags + imagery + language_primary) / 3.0


def dimension_scores(task_name: str, eval_record: dict[str, Any], prediction: dict[str, Any]) -> dict[str, float]:
    reference_target = eval_record.get("reference_target", {})
    reference_summary = eval_record.get("reference_summary", {})
    safety = safety_score_from_payload(prediction)

    if task_name == "mode_selector_eval":
        return {
            "mode_fit": score_to_five(
                exact_or_zero(reference_summary.get("expected_primary_mode"), prediction.get("primary_mode"))
            ),
            "theme_grounding": score_to_five(
                overlap_score(reference_summary.get("expected_theme_axes", []), prediction.get("theme_axes", []))
            ),
            "artist_alignment": score_to_five(
                exact_or_zero(reference_summary.get("expected_primary_mode"), prediction.get("primary_mode"))
            ),
            "safety": score_to_five(safety),
        }

    if task_name == "structure_planner_eval":
        actual_sections = [item.get("section") for item in prediction.get("recommended_structure", []) if item.get("section")]
        return {
            "form_coherence": score_to_five(section_sequence_score(reference_summary.get("expected_sections", []), actual_sections)),
            "arc_alignment": score_to_five(1.0),
            "hook_release": score_to_five(section_sequence_score(["chorus", "chorus_final"], actual_sections)),
            "artist_alignment": score_to_five(
                overlap_score(
                    eval_record.get("input_context", {}).get("artist_context", {}).get("structural_defaults", []),
                    actual_sections,
                )
            ),
            "safety": score_to_five(safety),
        }

    if task_name == "hook_planner_eval":
        return {
            "hook_density_fit": score_to_five(
                exact_or_zero(
                    reference_target.get("hook_plan", {}).get("hook_density"),
                    prediction.get("hook_plan", {}).get("hook_density"),
                )
            ),
            "repetition_strategy": score_to_five(hook_plan_score(reference_target, prediction)),
            "theme_hook_linkage": score_to_five(
                overlap_score(reference_target.get("theme_axes", []), prediction.get("theme_axes", []))
            ),
            "artist_alignment": score_to_five(1.0),
            "safety": score_to_five(safety),
        }

    if task_name == "style_prompt_eval":
        return {
            "style_fidelity": score_to_five(
                style_of_music_overlap(
                    reference_target.get("style_of_music", ""),
                    prediction.get("style_of_music", ""),
                )
            ),
            "imagery_theme_coverage": score_to_five(
                overlap_score(
                    reference_summary.get("expected_theme_axes", []),
                    tokenize_text(" ".join(prediction.get("lyric_direction", []))),
                )
            ),
            "section_guidance": score_to_five(
                section_sequence_score(
                    reference_target.get("section_emphasis", []),
                    prediction.get("section_emphasis", []),
                )
            ),
            "conciseness": score_to_five(
                closeness_score(
                    12.0,
                    float(len(tokenize_text(prediction.get("style_of_music", "")))),
                    tolerance=10.0,
                )
            ),
            "safety": score_to_five(safety),
        }

    if task_name == "full_song_brief_eval":
        return {
            "mode_and_theme_fit": score_to_five(
                (
                    exact_or_zero(reference_summary.get("expected_primary_mode"), prediction.get("primary_mode"))
                    + overlap_score(reference_summary.get("expected_theme_axes", []), prediction.get("theme_axes", []))
                )
                / 2.0
            ),
            "structure_quality": score_to_five(structure_quality_score(reference_target, prediction)),
            "hook_strategy_quality": score_to_five(hook_plan_score(reference_target, prediction)),
            "constraint_quality": score_to_five(constraint_quality_score(reference_target, prediction)),
            "prompt_seed_quality": score_to_five(
                (
                    style_of_music_overlap(
                        reference_target.get("style_prompt_seed", {}).get("style_of_music", ""),
                        prediction.get("style_prompt_seed", {}).get("style_of_music", ""),
                    )
                    + section_sequence_score(
                        reference_target.get("style_prompt_seed", {}).get("section_emphasis", []),
                        prediction.get("style_prompt_seed", {}).get("section_emphasis", []),
                    )
                )
                / 2.0
            ),
            "safety": score_to_five(safety),
        }

    raise ValueError(f"Unsupported task_name: {task_name}")


def weighted_total(eval_record: dict[str, Any], dimension_values: dict[str, float]) -> float:
    weights = {
        item["dimension"]: float(item["weight"])
        for item in eval_record.get("rubric", [])
        if item.get("dimension")
    }
    total = 0.0
    for dimension, value in dimension_values.items():
        total += weights.get(dimension, 0.0) * value
    return round(total * 20.0, 2)


def score_label(score: float) -> str:
    if score >= 85:
        return "strong"
    if score >= 70:
        return "usable"
    return "weak"


def build_prediction_record(task_name: str, eval_record: dict[str, Any], model_name: str) -> dict[str, Any]:
    return {
        "prediction_id": f"{eval_record['eval_id']}-{model_name}",
        "eval_id": eval_record["eval_id"],
        "task_type": task_name,
        "artist_id": eval_record["artist_id"],
        "artist_name": eval_record["artist_name"],
        "track_id": eval_record["track_id"],
        "title": eval_record["title"],
        "split": eval_record["split"],
        "model_name": model_name,
        "prediction": generate_prediction(task_name, eval_record),
    }


def build_score_record(eval_record: dict[str, Any], prediction_record: dict[str, Any]) -> dict[str, Any]:
    scores = dimension_scores(eval_record["task_type"], eval_record, prediction_record["prediction"])
    total = weighted_total(eval_record, scores)
    return {
        "score_id": f"{prediction_record['prediction_id']}-score",
        "eval_id": eval_record["eval_id"],
        "prediction_id": prediction_record["prediction_id"],
        "task_type": eval_record["task_type"],
        "artist_id": eval_record["artist_id"],
        "track_id": eval_record["track_id"],
        "split": eval_record["split"],
        "model_name": prediction_record["model_name"],
        "label": score_label(total),
        "total_score": total,
        "dimension_scores": scores,
    }


def score_prediction_records(
    eval_records: list[dict[str, Any]],
    prediction_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    prediction_by_eval_id = {record["eval_id"]: record for record in prediction_records}
    score_records: list[dict[str, Any]] = []
    for eval_record in eval_records:
        prediction_record = prediction_by_eval_id.get(eval_record["eval_id"])
        if prediction_record is None:
            raise ValueError(f"Missing prediction for eval_id={eval_record['eval_id']}")
        score_records.append(build_score_record(eval_record, prediction_record))
    return score_records


def summarize_scores(score_records: list[dict[str, Any]]) -> dict[str, Any]:
    if not score_records:
        return {"count": 0, "average_score": 0.0, "strong": 0, "usable": 0, "weak": 0}
    average_score = round(sum(item["total_score"] for item in score_records) / len(score_records), 2)
    return {
        "count": len(score_records),
        "average_score": average_score,
        "strong": sum(1 for item in score_records if item["label"] == "strong"),
        "usable": sum(1 for item in score_records if item["label"] == "usable"),
        "weak": sum(1 for item in score_records if item["label"] == "weak"),
    }


def run_eval_benchmark(
    eval_dir: Path,
    *,
    output_dir: Path,
    model_name: str = "heuristic_baseline_v1",
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    predictions_dir = output_dir / "predictions"
    scores_dir = output_dir / "scores"
    predictions_dir.mkdir(parents=True, exist_ok=True)
    scores_dir.mkdir(parents=True, exist_ok=True)

    task_summaries: dict[str, Any] = {}
    outputs: dict[str, str] = {}
    all_score_records: list[dict[str, Any]] = []
    artist_id = "unknown"

    for task_name, filename in TASK_FILES.items():
        eval_records = load_jsonl(eval_dir / filename)
        if eval_records:
            artist_id = eval_records[0]["artist_id"]
        prediction_records = [build_prediction_record(task_name, record, model_name) for record in eval_records]
        score_records = [
            build_score_record(eval_record, prediction_record)
            for eval_record, prediction_record in zip(eval_records, prediction_records)
        ]
        all_score_records.extend(score_records)

        prediction_path = write_jsonl(predictions_dir / f"{task_name}.jsonl", prediction_records)
        score_path = write_jsonl(scores_dir / f"{task_name}.jsonl", score_records)

        task_summaries[task_name] = summarize_scores(score_records)
        outputs[f"{task_name}_predictions"] = str(prediction_path)
        outputs[f"{task_name}_scores"] = str(score_path)

    manifest = {
        "schema_version": "1.0",
        "artist_id": artist_id,
        "model_name": model_name,
        "source_eval_dir": str(eval_dir),
        "output_dir": str(output_dir),
        "task_summaries": task_summaries,
        "overall_summary": summarize_scores(all_score_records),
        "outputs": outputs,
    }
    manifest_path = write_json(output_dir / "benchmark_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def score_prediction_dir(
    eval_dir: Path,
    *,
    predictions_dir: Path,
    output_dir: Path,
    model_name: str | None = None,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    scores_dir = output_dir / "scores"
    scores_dir.mkdir(parents=True, exist_ok=True)

    task_summaries: dict[str, Any] = {}
    outputs: dict[str, str] = {}
    all_score_records: list[dict[str, Any]] = []
    artist_id = "unknown"
    selected_model_name = model_name

    for task_name, filename in TASK_FILES.items():
        eval_records = load_jsonl(eval_dir / filename)
        prediction_records = load_jsonl(predictions_dir / f"{task_name}.jsonl")
        if eval_records:
            artist_id = eval_records[0]["artist_id"]
        if selected_model_name is None and prediction_records:
            selected_model_name = prediction_records[0].get("model_name", "external_predictions")

        score_records = score_prediction_records(eval_records, prediction_records)
        all_score_records.extend(score_records)

        score_path = write_jsonl(scores_dir / f"{task_name}.jsonl", score_records)
        task_summaries[task_name] = summarize_scores(score_records)
        outputs[f"{task_name}_scores"] = str(score_path)

    manifest = {
        "schema_version": "1.0",
        "artist_id": artist_id,
        "model_name": selected_model_name or "external_predictions",
        "source_eval_dir": str(eval_dir),
        "source_predictions_dir": str(predictions_dir),
        "output_dir": str(output_dir),
        "task_summaries": task_summaries,
        "overall_summary": summarize_scores(all_score_records),
        "outputs": outputs,
    }
    manifest_path = write_json(output_dir / "scoring_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def render_benchmark_report(manifest: dict[str, Any]) -> str:
    overall = manifest.get("overall_summary", {})
    lines = [
        f"# {manifest['artist_id']} Eval Benchmark",
        "",
        f"- Model name: `{manifest['model_name']}`",
        f"- Source eval dir: `{manifest['source_eval_dir']}`",
        f"- Overall average score: `{overall.get('average_score', 0.0)}`",
        f"- Strong: `{overall.get('strong', 0)}`",
        f"- Usable: `{overall.get('usable', 0)}`",
        f"- Weak: `{overall.get('weak', 0)}`",
        "",
        "## Task Summaries",
        "",
    ]

    for task_name, summary in manifest.get("task_summaries", {}).items():
        lines.extend(
            [
                f"### {task_name}",
                f"- Count: `{summary.get('count', 0)}`",
                f"- Average score: `{summary.get('average_score', 0.0)}`",
                f"- Strong: `{summary.get('strong', 0)}`",
                f"- Usable: `{summary.get('usable', 0)}`",
                f"- Weak: `{summary.get('weak', 0)}`",
                "",
            ]
        )

    lines.extend(
        [
            "## Notes",
            "",
            "- This run uses a deterministic heuristic baseline, not an LLM.",
            "- The goal is to validate the eval loop and create a score baseline that future models must beat.",
            "- Any future model can be compared against the same held-out eval files by matching the prediction payload shape.",
            "",
        ]
    )
    return "\n".join(lines)
