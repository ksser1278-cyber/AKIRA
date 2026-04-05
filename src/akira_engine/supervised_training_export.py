from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .training_data import load_json, write_json, write_jsonl


ALLOWED_TRAIN_RIGHTS = {"cleared_for_training", "licensed_for_training"}
EVAL_RIGHTS = ALLOWED_TRAIN_RIGHTS | {"internal_only_holdout"}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not path.exists():
        return records
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            records.append(json.loads(text))
    return records


def _read_rights_map(path: Path | None) -> dict[str, str]:
    if path is None or not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and isinstance(payload.get("records"), list):
        out: dict[str, str] = {}
        for row in payload.get("records", []):
            if not isinstance(row, dict):
                continue
            track_id = str(row.get("track_id", "")).strip()
            rights_status = str(row.get("rights_status", "")).strip()
            if track_id and rights_status:
                out[track_id] = rights_status
        return out
    if isinstance(payload, dict):
        return {str(key): str(value) for key, value in payload.items() if str(key).strip() and str(value).strip()}
    return {}


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _normalize_section_name(name: str) -> str:
    lowered = _safe_text(name).lower()
    return lowered.replace("-", "_").replace(" ", "_")


def _blueprint_sections(record: dict[str, Any]) -> list[dict[str, Any]]:
    target = record.get("target", {})
    sections = target.get("recommended_structure", [])
    if not isinstance(sections, list):
        return []
    out: list[dict[str, Any]] = []
    for item in sections:
        if not isinstance(item, dict):
            continue
        section = _normalize_section_name(item.get("section"))
        if not section:
            continue
        out.append(
            {
                "section": section,
                "line_target": 4,
                "goal": _safe_text(item.get("goal")),
            }
        )
    return out


def _hook_constraints(record: dict[str, Any]) -> dict[str, Any]:
    hook_plan = record.get("target", {}).get("hook_plan", {})
    hook_density = _safe_text(hook_plan.get("hook_density")) or "medium"
    repetition_score = float(hook_plan.get("chorus_repetition_score", 0.0) or 0.0)
    repetition_pressure = "high" if repetition_score >= 0.5 else hook_density if hook_density in {"low", "medium", "high"} else "medium"
    hook_line_target = 2
    if int(hook_plan.get("hook_candidate_count", 0) or 0) >= 6:
        hook_line_target = 2
    return {
        "title_binding": "medium",
        "repetition_pressure": repetition_pressure,
        "hook_line_target": hook_line_target,
    }


def _style_constraints(record: dict[str, Any]) -> dict[str, Any]:
    target = record.get("target", {})
    style = target.get("style_constraints", {})
    return {
        "imagery_atoms": list(style.get("imagery_bank", [])[:8]) if isinstance(style.get("imagery_bank", []), list) else [],
        "forbidden_generic_atoms": [],
        "surface_rules": ["japanese_only", "no_meta_commentary"],
    }


def _phonetic_constraints(record: dict[str, Any]) -> dict[str, Any]:
    language_profile = record.get("input_context", {}).get("track_evidence", {}).get("language_profile", {})
    line_length_profile = language_profile.get("line_length_profile", {})
    short_ratio = line_length_profile.get("short_line_ratio")
    payload: dict[str, Any] = {}
    if isinstance(short_ratio, (int, float)):
        payload["short_line_ratio_target"] = max(0.0, min(1.0, float(short_ratio)))
    return payload


def _group_sections(normalized_sections: list[dict[str, Any]], blueprint_sections: list[dict[str, Any]]) -> list[tuple[str, list[str]]]:
    if not blueprint_sections:
        return []
    if not normalized_sections:
        return [(item["section"], []) for item in blueprint_sections]

    total_source = len(normalized_sections)
    total_target = len(blueprint_sections)
    groups: list[tuple[str, list[str]]] = []
    start = 0
    for idx, target in enumerate(blueprint_sections):
        remaining_source = total_source - start
        remaining_target = total_target - idx
        take = max(1, round(remaining_source / remaining_target))
        if idx == total_target - 1:
            end = total_source
        else:
            end = min(total_source - (remaining_target - 1), start + take)
        chunk = normalized_sections[start:end]
        lines: list[str] = []
        for section in chunk:
            for line in section.get("lines", []):
                text = _safe_text(line)
                if text:
                    lines.append(text)
        groups.append((target["section"], lines))
        start = end
    return groups


def _lyrics_markdown_from_normalized(record: dict[str, Any]) -> str:
    source_path = Path(record.get("source_paths", {}).get("normalized_document", ""))
    if not source_path.exists():
        return ""
    normalized = load_json(source_path)
    normalized_sections = normalized.get("sections", [])
    if not isinstance(normalized_sections, list):
        normalized_sections = []
    blueprint_sections = _blueprint_sections(record)
    groups = _group_sections(normalized_sections, blueprint_sections)
    blocks: list[str] = []
    for section_name, lines in groups:
        if not lines:
            continue
        blocks.append(f"[{section_name}]")
        blocks.extend(lines)
        blocks.append("")
    return "\n".join(blocks).strip()


def _chorus_markdown(record: dict[str, Any]) -> str:
    lyrics = _lyrics_markdown_from_normalized(record)
    if not lyrics:
        return ""
    lines = lyrics.splitlines()
    current_header = ""
    block: list[str] = []
    blocks: list[str] = []
    for line in lines:
        if line.startswith("[") and line.endswith("]"):
            if current_header and block:
                blocks.append("\n".join([current_header] + block))
            current_header = line
            block = []
            continue
        if current_header:
            block.append(line)
    if current_header and block:
        blocks.append("\n".join([current_header] + block))
    chorus_blocks = [item for item in blocks if item.startswith("[chorus]")]
    return chorus_blocks[0] if chorus_blocks else ""


def build_supervised_sample(record: dict[str, Any], *, task: str, rights_status: str) -> dict[str, Any] | None:
    if task not in {"full_song_generation", "hook_generation"}:
        return None

    title = _safe_text(record.get("title"))
    artist_id = _safe_text(record.get("artist_id"))
    mode_id = _safe_text(record.get("target", {}).get("primary_mode"))
    source_track_id = _safe_text(record.get("track_id"))
    if not title or not artist_id or not mode_id or not source_track_id:
        return None

    if task == "full_song_generation":
        lyrics_markdown = _lyrics_markdown_from_normalized(record)
        blueprint_sections = _blueprint_sections(record)
    else:
        lyrics_markdown = _chorus_markdown(record)
        blueprint_sections = [{"section": "chorus", "line_target": 4}]

    if not lyrics_markdown:
        return None

    sample_id = f"{source_track_id}_{task}_v1"
    split = _safe_text(record.get("split")) or "train"
    if split == "validation":
        split = "eval"
    metadata = {
        "source_track_id": source_track_id,
        "source_artist_id": artist_id,
        "source_tier": "structured_reference",
        "rights_status": rights_status,
        "task_origin": "derived_training_record",
        "contains_verbatim_lyrics": True,
        "normalization_version": "1.0",
    }
    return {
        "sample_id": sample_id,
        "schema_version": "1.0",
        "split": split,
        "task": task,
        "input": {
            "artist_id": artist_id,
            "mode_id": mode_id,
            "language": "ja",
            "title_seed": title,
            "theme_axes": list(record.get("target", {}).get("theme_axes", [])[:8]),
            "blueprint": {
                "sections": blueprint_sections,
                "hook_constraints": _hook_constraints(record),
            },
            "style_constraints": _style_constraints(record),
            "phonetic_constraints": _phonetic_constraints(record),
        },
        "output": {
            "title": title,
            "lyrics_markdown": lyrics_markdown,
        },
        "metadata": metadata,
    }


def export_supervised_training_samples(
    *,
    project_root: Path,
    derived_jsonl: Path,
    output_dir: Path,
    rights_map_path: Path | None = None,
    include_eval_only: bool = False,
    include_full_song: bool = False,
) -> dict[str, Any]:
    records = load_jsonl(derived_jsonl)
    rights_map = _read_rights_map(rights_map_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    samples: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    for record in records:
        if _safe_text(record.get("task_type")) != "track_blueprint":
            skipped.append(
                {
                    "record_id": _safe_text(record.get("record_id")),
                    "reason": "unsupported_task_type",
                }
            )
            continue

        source_track_id = _safe_text(record.get("track_id"))
        rights_status = rights_map.get(source_track_id, "unknown")
        if rights_status not in ALLOWED_TRAIN_RIGHTS and not (include_eval_only and rights_status in EVAL_RIGHTS):
            skipped.append(
                {
                    "record_id": _safe_text(record.get("record_id")),
                    "track_id": source_track_id,
                    "reason": f"rights_blocked:{rights_status}",
                }
            )
            continue

        task_list = ["hook_generation"]
        if include_full_song:
            task_list.append("full_song_generation")
        for task in task_list:
            sample = build_supervised_sample(record, task=task, rights_status=rights_status)
            if sample is None:
                skipped.append(
                    {
                        "record_id": _safe_text(record.get("record_id")),
                        "track_id": source_track_id,
                        "reason": f"failed_to_build:{task}",
                    }
                )
                continue
            if rights_status == "internal_only_holdout":
                sample["split"] = "test"
            samples.append(sample)

    jsonl_path = write_jsonl(output_dir / "supervised_samples.jsonl", samples)
    manifest = {
        "schema_version": "1.0",
        "project_root": str(project_root),
        "source_jsonl": str(derived_jsonl),
        "rights_map_path": str(rights_map_path) if rights_map_path else "",
        "outputs": {
            "supervised_samples": str(jsonl_path),
        },
        "counts": {
            "samples": len(samples),
            "skipped": len(skipped),
        },
        "tasks": {
            "hook_generation": sum(1 for item in samples if item.get("task") == "hook_generation"),
            "full_song_generation": sum(1 for item in samples if item.get("task") == "full_song_generation"),
        },
        "include_full_song": include_full_song,
        "skipped_records": skipped[:200],
    }
    manifest_path = write_json(output_dir / "supervised_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest
