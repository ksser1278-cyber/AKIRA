from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .generator import (
    GenerationRequest,
    build_package_data,
    load_profile,
    resolve_mode,
    slugify,
)


REQUIRED_SEED_KEYS = {
    "schema_version",
    "artist_id",
    "records",
}

REQUIRED_RECORD_KEYS = {
    "mode_id",
    "theme",
    "emotion",
    "narrative",
    "split",
}


@dataclass
class DatasetBuildSummary:
    output_path: Path
    total_records: int
    split_counts: dict[str, int]


def load_seed_file(path: Path) -> dict[str, Any]:
    seed_file = json.loads(path.read_text(encoding="utf-8"))
    missing = sorted(REQUIRED_SEED_KEYS - seed_file.keys())
    if missing:
        raise ValueError(f"Seed file is missing required keys: {', '.join(missing)}")

    invalid_records: list[int] = []
    for index, record in enumerate(seed_file["records"], start=1):
        missing_record_keys = REQUIRED_RECORD_KEYS - record.keys()
        if missing_record_keys:
            invalid_records.append(index)
    if invalid_records:
        bad_rows = ", ".join(str(index) for index in invalid_records)
        raise ValueError(f"Seed records missing required keys at positions: {bad_rows}")
    return seed_file


def default_dataset_output_path(artist_id: str) -> Path:
    return Path("datasets") / "processed" / f"{artist_id}_lyric_blueprints.jsonl"


def build_records_from_seed_file(profile_path: Path, seed_path: Path) -> list[dict[str, Any]]:
    profile = load_profile(profile_path)
    seed_file = load_seed_file(seed_path)
    if seed_file["artist_id"] != profile["artist_id"]:
        raise ValueError(
            f"Seed file artist_id '{seed_file['artist_id']}' does not match profile '{profile['artist_id']}'"
        )
    return [build_dataset_record(profile, record) for record in seed_file["records"]]


def build_instruction(profile: dict[str, Any], mode: dict[str, Any], record: dict[str, Any]) -> str:
    primary_language = profile["language_policy"]["primary_language"]
    return (
        f"Create a {primary_language} lyric blueprint for a {mode['label']} J-Pop track. "
        f"Use the theme '{record['theme']}', the emotion '{record['emotion']}', and the narrative "
        f"'{record['narrative']}'. Avoid direct artist naming and keep the output aligned with the "
        f"provided style constraints, title ideas, hooks, and section goals."
    )


def build_input_context(profile: dict[str, Any], mode: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
    return {
        "artist_summary": profile["summary"],
        "mode_description": mode["description"],
        "theme": record["theme"],
        "emotion": record["emotion"],
        "narrative": record["narrative"],
        "style_tags": profile["base_style_tags"] + mode["style_tags"],
        "vocal_textures": profile["vocal_profile"]["textures"],
        "vocal_delivery": profile["vocal_profile"]["delivery"],
        "lyric_focus": mode["lyric_focus"],
        "imagery_bank": profile["lyric_rules"]["imagery_bank"],
        "avoid_terms": profile["lyric_rules"]["avoid_terms"],
        "allowed_themes": profile["lyric_rules"]["themes"],
        "tempo_range_bpm": mode["tempo_bpm"],
        "keywords": record.get("keywords", []),
    }


def build_target_blueprint(
    profile: dict[str, Any], mode: dict[str, Any], record: dict[str, Any]
) -> dict[str, Any]:
    request = GenerationRequest(
        artist_file=Path("."),
        mode_id=record["mode_id"],
        theme=record["theme"],
        emotion=record["emotion"],
        narrative=record["narrative"],
        keywords=record.get("keywords", []),
    )
    package = build_package_data(request, profile, mode)
    return {
        "style_of_music": package["style_of_music"],
        "title_ideas": package["title_ideas"],
        "hook_ideas": package["hook_ideas"],
        "suggested_structure": package["lyrics_blueprint"]["suggested_structure"],
        "section_blueprint": package["lyrics_blueprint"]["section_blueprint"],
        "generation_notes": package["generation_notes"],
    }


def build_dataset_record(profile: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
    mode = resolve_mode(profile, record["mode_id"])
    record_id = (
        f"{profile['artist_id']}-"
        f"{record['mode_id']}-"
        f"{slugify(record['theme'])}-"
        f"{slugify(record['emotion'])}"
    )
    return {
        "record_id": record_id,
        "split": record["split"],
        "artist_id": profile["artist_id"],
        "artist_name": profile["display_name"],
        "mode_id": mode["mode_id"],
        "mode_label": mode["label"],
        "source_type": "structured_style_profile",
        "contains_copyrighted_lyrics": False,
        "instruction": build_instruction(profile, mode, record),
        "input_context": build_input_context(profile, mode, record),
        "target_blueprint": build_target_blueprint(profile, mode, record),
        "safety_notes": {
            "avoid_languages": profile["language_policy"]["avoid_languages"],
            "avoid_terms": profile["lyric_rules"]["avoid_terms"],
            "note": "This dataset stores style constraints and lyric blueprints, not scraped commercial lyrics.",
        },
    }


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(record, ensure_ascii=False) for record in records]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_dataset(profile_path: Path, seed_path: Path, output_path: Path | None = None) -> DatasetBuildSummary:
    records = build_records_from_seed_file(profile_path, seed_path)
    profile = load_profile(profile_path)
    final_output = output_path or default_dataset_output_path(profile["artist_id"])
    write_jsonl(final_output, records)
    split_counts = dict(Counter(record["split"] for record in records))
    return DatasetBuildSummary(
        output_path=final_output,
        total_records=len(records),
        split_counts=split_counts,
    )
