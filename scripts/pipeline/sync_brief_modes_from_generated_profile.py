from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


MODE_COMPATIBILITY = {
    "intimate_confessional": ["intimate_confessional", "night_drive"],
    "night_drive": ["night_drive", "anthemic_cinematic"],
    "anthemic_cinematic": ["anthemic_cinematic", "night_drive"],
}

MODE_LABELS = {
    "intimate_confessional": "Intimate Confessional",
    "night_drive": "Night Drive",
    "anthemic_cinematic": "Anthemic Cinematic",
}


def normalize_lookup_text(value: Any) -> str:
    raw = str(value or "").strip().lower()
    return re.sub(r"[^0-9a-z\u3041-\u3096\u30a1-\u30fa\u30fc\u4e00-\u9fff]+", "", raw)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync full_song_brief primary_mode values from style_prompt_profile.generated.json.",
    )
    parser.add_argument(
        "--source-jsonl",
        required=True,
        type=Path,
        help="Path to a full_song_brief-style JSONL file.",
    )
    parser.add_argument(
        "--generated-profile",
        required=True,
        type=Path,
        help="Path to style_prompt_profile.generated.json.",
    )
    parser.add_argument(
        "--output-jsonl",
        type=Path,
        help="Optional output path. Defaults to in-place overwrite.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in records) + ("\n" if records else ""),
        encoding="utf-8",
    )


def build_assignment_lookup(generated_profile: dict[str, Any]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    generated = generated_profile.get("generated_from_conditioning", {})
    for item in generated.get("track_mode_assignments", []):
        mode_id = str(item.get("mode_id", "")).strip()
        if not mode_id:
            continue
        for candidate in [
            item.get("track_id"),
            item.get("title_core"),
            item.get("title"),
        ]:
            normalized = normalize_lookup_text(candidate)
            if normalized:
                lookup[normalized] = mode_id
    return lookup


def extend_lookup_from_conditioning(
    lookup: dict[str, str],
    generated_profile: dict[str, Any],
) -> dict[str, str]:
    generated = generated_profile.get("generated_from_conditioning", {})
    reference_dir_value = str(generated.get("reference_record_dir", "")).strip()
    if not reference_dir_value:
        return lookup

    reference_dir = Path(reference_dir_value)
    if not reference_dir.exists():
        return lookup

    for path in sorted(reference_dir.glob("*.conditioning.json")):
        try:
            payload = load_json(path)
        except json.JSONDecodeError:
            continue

        identity = payload.get("track_identity", {})
        provenance = payload.get("source_provenance", {})
        track_lookup_keys = [
            identity.get("track_id"),
            identity.get("title"),
            identity.get("title_core"),
        ]

        resolved_mode = None
        for key in track_lookup_keys:
            normalized = normalize_lookup_text(key)
            if normalized and normalized in lookup:
                resolved_mode = lookup[normalized]
                break
        if not resolved_mode:
            continue

        for source in provenance.get("lyric_sources", []):
            normalized = normalize_lookup_text(source.get("label"))
            if normalized:
                lookup[normalized] = resolved_mode

    return lookup


def target_block(record: dict[str, Any]) -> dict[str, Any]:
    if "target" in record and isinstance(record["target"], dict):
        return record["target"]
    if "reference_target" in record and isinstance(record["reference_target"], dict):
        return record["reference_target"]
    record["target"] = {}
    return record["target"]


def rewrite_style_of_music(style_of_music: str, mode_id: str) -> str:
    label = MODE_LABELS.get(mode_id, mode_id.replace("_", " ").title())
    parts = [part.strip() for part in str(style_of_music or "").split(",") if part.strip()]
    if not parts:
        return f"{label}, J-Pop"

    known_labels = {value.lower() for value in MODE_LABELS.values()}
    if parts[0].lower() in known_labels:
        parts[0] = label
    else:
        parts.insert(0, label)
    return ", ".join(parts)


def sync_mode_metadata(record: dict[str, Any], resolved_mode: str) -> None:
    for candidate in [record.get("target"), record.get("reference_target")]:
        if not isinstance(candidate, dict):
            continue

        style_constraints = candidate.setdefault("style_constraints", {})
        style_constraints["compatible_modes"] = MODE_COMPATIBILITY.get(resolved_mode, [resolved_mode])
        candidate["primary_mode"] = resolved_mode

        style_prompt_seed = candidate.get("style_prompt_seed")
        if isinstance(style_prompt_seed, dict):
            style_prompt_seed["style_of_music"] = rewrite_style_of_music(
                style_prompt_seed.get("style_of_music", ""),
                resolved_mode,
            )

    reference_summary = record.get("reference_summary")
    if isinstance(reference_summary, dict):
        reference_summary["expected_primary_mode"] = resolved_mode
        style_prompt_seed = reference_summary.get("style_prompt_seed")
        if isinstance(style_prompt_seed, dict):
            style_prompt_seed["style_of_music"] = rewrite_style_of_music(
                style_prompt_seed.get("style_of_music", ""),
                resolved_mode,
            )

    input_context = record.get("input_context")
    if isinstance(input_context, dict):
        track_evidence = input_context.get("track_evidence")
        if isinstance(track_evidence, dict) and "selected_mode" in track_evidence:
            track_evidence["selected_mode"] = resolved_mode
        if "selected_mode" in input_context:
            input_context["selected_mode"] = resolved_mode


def resolve_mode(record: dict[str, Any], lookup: dict[str, str]) -> str | None:
    candidates = [
        record.get("track_id"),
        record.get("title"),
    ]
    for candidate in candidates:
        normalized = normalize_lookup_text(candidate)
        if normalized and normalized in lookup:
            return lookup[normalized]
    return None


def sync_record_modes(records: list[dict[str, Any]], lookup: dict[str, str]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    updated_count = 0
    unchanged_count = 0
    missing_count = 0
    for record in records:
        resolved_mode = resolve_mode(record, lookup)
        if not resolved_mode:
            missing_count += 1
            continue

        target = target_block(record)
        previous_mode = str(target.get("primary_mode", "")).strip()
        sync_mode_metadata(record, resolved_mode)

        if previous_mode == resolved_mode:
            unchanged_count += 1
        else:
            updated_count += 1

    return records, {
        "updated": updated_count,
        "unchanged": unchanged_count,
        "missing_assignment": missing_count,
    }


def main() -> None:
    args = parse_args()
    records = load_jsonl(args.source_jsonl.resolve())
    generated_profile = load_json(args.generated_profile.resolve())
    lookup = build_assignment_lookup(generated_profile)
    lookup = extend_lookup_from_conditioning(lookup, generated_profile)

    synced_records, summary = sync_record_modes(records, lookup)
    output_path = (args.output_jsonl or args.source_jsonl).resolve()
    write_jsonl(output_path, synced_records)

    print(json.dumps(
        {
            "output_jsonl": str(output_path),
            "record_count": len(synced_records),
            "summary": summary,
        },
        ensure_ascii=False,
        indent=2,
    ))


if __name__ == "__main__":
    main()
