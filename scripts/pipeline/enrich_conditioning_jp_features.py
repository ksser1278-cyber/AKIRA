from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.akira_engine.japanese_lyric_features import build_japanese_lyric_profile


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Enrich track conditioning records with Japanese-lyric profile fields.",
    )
    parser.add_argument("--artist-id", required=True, help="Artist id under data/reference_tracks.")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path("."),
        help="Project root path.",
    )
    parser.add_argument(
        "--reference-root",
        type=Path,
        default=Path("data") / "reference_tracks",
        help="Root directory containing conditioning records.",
    )
    return parser.parse_args()


def update_section_fields(record: dict) -> dict:
    profile = build_japanese_lyric_profile(record)
    record["japanese_lyric_profile"] = profile

    section_map = {
        (item["section_name"], item["section_type"]): item
        for item in profile.get("section_features", [])
    }

    lyric_sections = record.get("lyric_ground_truth", {}).get("sections", [])
    for section in lyric_sections:
        feature = section_map.get((section.get("section_name", ""), section.get("section_type", "")))
        if not feature:
            continue
        for key in ("jp_section_role", "mora_density", "spoken_speed_bias", "title_drop_role", "phrase_energy_role"):
            section[key] = feature[key]

    analysis_sections = record.get("section_analysis", [])
    for section in analysis_sections:
        feature = section_map.get((section.get("section_name", ""), section.get("section_type", "")))
        if not feature:
            continue
        for key in ("jp_section_role", "mora_density", "spoken_speed_bias", "title_drop_role", "phrase_energy_role"):
            section[key] = feature[key]
    return record


def main() -> None:
    args = parse_args()
    project_root = args.project_root.resolve()
    reference_root = args.reference_root if args.reference_root.is_absolute() else (project_root / args.reference_root).resolve()
    artist_root = reference_root / args.artist_id
    records = sorted(artist_root.glob("*.conditioning.json"))
    if not records:
        raise SystemExit(f"No conditioning records found in {artist_root}")

    updated = 0
    for path in records:
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload = update_section_fields(payload)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        updated += 1

    print(f"Updated records: {updated}")
    print(f"Artist root: {artist_root}")


if __name__ == "__main__":
    main()
