from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def mode_card_lookup(style_card: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        card.get("mode_id"): card
        for card in style_card.get("target", {}).get("mode_cards", [])
        if card.get("mode_id")
    }


def compact_artist_context(style_card: dict[str, Any]) -> dict[str, Any]:
    target = style_card.get("target", {})
    return {
        "summary": target.get("summary", ""),
        "style_tags": target.get("style_tags", []),
        "imagery_bank": target.get("imagery_bank", []),
        "core_themes": target.get("core_themes", []),
        "structural_defaults": target.get("structural_defaults", []),
    }


def style_prompt_seed(track_record: dict[str, Any], style_card: dict[str, Any]) -> dict[str, Any]:
    target = track_record.get("target", {})
    style_constraints = target.get("style_constraints", {})
    mode_lookup = mode_card_lookup(style_card)
    primary_mode = target.get("primary_mode")
    mode_card = mode_lookup.get(primary_mode, {})
    hook_plan = target.get("hook_plan", {})
    track_evidence = track_record.get("input_context", {}).get("track_evidence", {})

    style_tags = unique_preserve_order(style_constraints.get("style_tags", []))
    theme_axes = unique_preserve_order(target.get("theme_axes", []))
    lyric_focus = unique_preserve_order(mode_card.get("lyric_focus", []))
    arc_label = track_evidence.get("overall_arc_label", "undetermined").replace("_", " ")
    hook_density = hook_plan.get("hook_density", "medium")

    style_of_music_parts = []
    if mode_card.get("label"):
        style_of_music_parts.append(mode_card["label"])
    style_of_music_parts.extend(style_tags[:6])
    style_of_music_parts.extend(theme_axes[:4])
    style_of_music = ", ".join(unique_preserve_order(style_of_music_parts))

    vocal_direction_parts = [
        f"{hook_density} hook emphasis",
        arc_label,
    ]
    if lyric_focus:
        vocal_direction_parts.extend(lyric_focus[:3])

    lyric_direction_parts = []
    if theme_axes:
        lyric_direction_parts.append("themes: " + ", ".join(theme_axes[:6]))
    if lyric_focus:
        lyric_direction_parts.append("focus: " + ", ".join(lyric_focus[:5]))
    if style_constraints.get("imagery_bank"):
        lyric_direction_parts.append("imagery anchors: " + ", ".join(style_constraints["imagery_bank"][:6]))

    return {
        "style_of_music": style_of_music,
        "vocal_direction": unique_preserve_order(vocal_direction_parts),
        "lyric_direction": lyric_direction_parts,
        "section_emphasis": [
            item.get("section")
            for item in target.get("recommended_structure", [])[:6]
            if item.get("section")
        ],
    }


def base_record(
    task_name: str,
    track_record: dict[str, Any],
    style_card: dict[str, Any],
) -> dict[str, Any]:
    return {
        "record_id": f"{track_record['record_id']}-{task_name}",
        "split": track_record["split"],
        "task_type": task_name,
        "artist_id": track_record["artist_id"],
        "artist_name": track_record["artist_name"],
        "track_id": track_record["track_id"],
        "title": track_record["title"],
        "contains_copyrighted_lyrics": False,
        "source_paths": track_record.get("source_paths", {}),
        "artist_style_card_id": style_card.get("record_id"),
    }


def build_mode_selector_record(track_record: dict[str, Any], style_card: dict[str, Any]) -> dict[str, Any]:
    record = base_record("mode_selector", track_record, style_card)
    input_context = track_record.get("input_context", {})
    target = track_record.get("target", {})
    record.update(
        {
            "instruction": (
                "Choose the best Ado-adjacent writing mode for this track evidence. "
                "Use imagery, emotional movement, and hook behavior to select the mode."
            ),
            "input_context": {
                "artist_context": compact_artist_context(style_card),
                "track_evidence": {
                    "dominant_imagery_tags": input_context.get("track_evidence", {}).get("dominant_imagery_tags", []),
                    "dominant_emotions": input_context.get("track_evidence", {}).get("dominant_emotions", []),
                    "overall_arc_label": input_context.get("track_evidence", {}).get("overall_arc_label"),
                    "hook_strategy": input_context.get("track_evidence", {}).get("hook_strategy", {}),
                },
                "candidate_modes": target.get("style_constraints", {}).get("compatible_modes", []),
            },
            "target": {
                "primary_mode": target.get("primary_mode"),
                "theme_axes": target.get("theme_axes", []),
            },
        }
    )
    return record


def build_structure_planner_record(track_record: dict[str, Any], style_card: dict[str, Any]) -> dict[str, Any]:
    record = base_record("structure_planner", track_record, style_card)
    input_context = track_record.get("input_context", {})
    target = track_record.get("target", {})
    record.update(
        {
            "instruction": (
                "Turn the observed section evidence into a reusable song structure plan. "
                "Keep the structure compatible with Ado-style escalation and hook release."
            ),
            "input_context": {
                "artist_context": {
                    "structural_defaults": compact_artist_context(style_card).get("structural_defaults", []),
                },
                "track_evidence": {
                    "observed_section_count": input_context.get("track_evidence", {}).get("observed_section_count"),
                    "inferred_song_form": input_context.get("track_evidence", {}).get("inferred_song_form", {}),
                    "overall_arc_label": input_context.get("track_evidence", {}).get("overall_arc_label"),
                },
                "selected_mode": target.get("primary_mode"),
            },
            "target": {
                "track_conditioned_structure": target.get("track_conditioned_structure", {}),
                "recommended_structure": target.get("recommended_structure", []),
            },
        }
    )
    return record


def build_hook_planner_record(track_record: dict[str, Any], style_card: dict[str, Any]) -> dict[str, Any]:
    record = base_record("hook_planner", track_record, style_card)
    input_context = track_record.get("input_context", {})
    target = track_record.get("target", {})
    record.update(
        {
            "instruction": (
                "Design the hook strategy for this track concept. "
                "Infer how aggressive, repetitive, and section-focused the hook should be."
            ),
            "input_context": {
                "artist_context": {
                    "style_tags": compact_artist_context(style_card).get("style_tags", []),
                    "imagery_bank": compact_artist_context(style_card).get("imagery_bank", []),
                },
                "track_evidence": {
                    "dominant_imagery_tags": input_context.get("track_evidence", {}).get("dominant_imagery_tags", []),
                    "dominant_emotions": input_context.get("track_evidence", {}).get("dominant_emotions", []),
                    "hook_strategy": input_context.get("track_evidence", {}).get("hook_strategy", {}),
                    "language_profile": input_context.get("track_evidence", {}).get("language_profile", {}),
                },
            },
            "target": {
                "primary_mode": target.get("primary_mode"),
                "hook_plan": target.get("hook_plan", {}),
                "theme_axes": target.get("theme_axes", []),
            },
        }
    )
    return record


def build_style_prompt_record(track_record: dict[str, Any], style_card: dict[str, Any]) -> dict[str, Any]:
    record = base_record("style_prompt_builder", track_record, style_card)
    input_context = track_record.get("input_context", {})
    target = track_record.get("target", {})
    record.update(
        {
            "instruction": (
                "Build a SUNO-ready style prompt seed from the derived artist and track evidence. "
                "Do not quote lyrics; summarize style, energy, imagery, and section emphasis."
            ),
            "input_context": {
                "artist_context": compact_artist_context(style_card),
                "track_evidence": {
                    "theme_axes": target.get("theme_axes", []),
                    "overall_arc_label": input_context.get("track_evidence", {}).get("overall_arc_label"),
                    "hook_strategy": input_context.get("track_evidence", {}).get("hook_strategy", {}),
                    "selected_mode": target.get("primary_mode"),
                },
            },
            "target": style_prompt_seed(track_record, style_card),
        }
    )
    return record


def build_full_brief_record(track_record: dict[str, Any], style_card: dict[str, Any]) -> dict[str, Any]:
    record = base_record("full_song_brief", track_record, style_card)
    target = track_record.get("target", {})
    record.update(
        {
            "instruction": (
                "Produce a complete Ado-adjacent generation brief from the derived evidence. "
                "Return mode, structure, hook plan, style constraints, and prompt seed."
            ),
            "input_context": {
                "artist_context": compact_artist_context(style_card),
                "track_evidence": track_record.get("input_context", {}).get("track_evidence", {}),
                "artist_frame": track_record.get("input_context", {}).get("artist_frame", {}),
            },
            "target": {
                **target,
                "style_prompt_seed": style_prompt_seed(track_record, style_card),
            },
        }
    )
    return record


def build_experiment_sets(package_dir: Path, output_dir: Path | None = None) -> dict[str, Any]:
    track_records = load_jsonl(package_dir / "track_blueprints.jsonl")
    style_cards = load_jsonl(package_dir / "artist_style_cards.jsonl")
    if not style_cards:
        raise ValueError(f"No artist style card found in {package_dir}")
    style_card = style_cards[0]
    artist_id = style_card["artist_id"]

    final_output_dir = output_dir or (package_dir.parent.parent / "experiments" / artist_id)
    final_output_dir.mkdir(parents=True, exist_ok=True)

    task_builders = {
        "mode_selector": build_mode_selector_record,
        "structure_planner": build_structure_planner_record,
        "hook_planner": build_hook_planner_record,
        "style_prompt_builder": build_style_prompt_record,
        "full_song_brief": build_full_brief_record,
    }

    outputs: dict[str, str] = {}
    counts: dict[str, int] = {}
    for task_name, builder in task_builders.items():
        task_records = [builder(track_record, style_card) for track_record in track_records]
        output_path = write_jsonl(final_output_dir / f"{task_name}.jsonl", task_records)
        outputs[task_name] = str(output_path)
        counts[task_name] = len(task_records)

    manifest = {
        "schema_version": "1.0",
        "artist_id": artist_id,
        "source_package_dir": str(package_dir),
        "output_dir": str(final_output_dir),
        "counts": counts,
        "outputs": outputs,
        "source_records": len(track_records),
    }
    manifest_path = write_json(final_output_dir / "experiment_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def render_experiment_report(manifest: dict[str, Any]) -> str:
    lines = [
        f"# {manifest['artist_id']} Experiment Sets",
        "",
        f"- Source package dir: `{manifest['source_package_dir']}`",
        f"- Source track records: `{manifest['source_records']}`",
        "",
        "## Outputs",
        "",
    ]
    for task_name, count in manifest.get("counts", {}).items():
        lines.append(f"- `{task_name}`: {count}")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- `mode_selector` is for style-lane classification experiments.",
            "- `structure_planner` is for section-order and song-form planning experiments.",
            "- `hook_planner` is for hook density and repetition strategy experiments.",
            "- `style_prompt_builder` is for SUNO-style prompt conditioning experiments.",
            "- `full_song_brief` is for end-to-end planning from derived evidence.",
            "",
        ]
    )
    return "\n".join(lines)
