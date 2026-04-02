from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .dataset import DatasetBuildSummary, build_dataset


@dataclass
class CorpusSummary:
    corpus_path: Path
    manifest_path: Path
    total_records: int
    unique_artists: int
    split_counts: dict[str, int]


def discover_artist_inputs(artists_root: Path) -> list[tuple[Path, Path]]:
    artist_inputs: list[tuple[Path, Path]] = []
    for child in sorted(artists_root.iterdir()):
        if not child.is_dir() or child.name.startswith("_"):
            continue
        profile_path = child / "profile.json"
        seeds_path = child / "seeds.json"
        if profile_path.exists() and seeds_path.exists():
            artist_inputs.append((profile_path, seeds_path))
    return artist_inputs


def build_all_datasets(
    artists_root: Path, output_dir: Path | None = None
) -> list[DatasetBuildSummary]:
    summaries: list[DatasetBuildSummary] = []
    for profile_path, seeds_path in discover_artist_inputs(artists_root):
        artist_id = profile_path.parent.name
        output_path = None
        if output_dir is not None:
            output_path = output_dir / f"{artist_id}_lyric_blueprints.jsonl"
        summaries.append(
            build_dataset(
                profile_path=profile_path,
                seed_path=seeds_path,
                output_path=output_path,
            )
        )
    return summaries


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        cleaned = line.strip()
        if cleaned:
            records.append(json.loads(cleaned))
    return records


def dataset_files_from_directory(datasets_root: Path) -> list[Path]:
    return sorted(datasets_root.glob("*_lyric_blueprints.jsonl"))


def default_corpus_path() -> Path:
    return Path("datasets") / "corpus" / "lyric_blueprints_all.jsonl"


def default_manifest_path() -> Path:
    return Path("datasets") / "corpus" / "lyric_blueprints_manifest.json"


def build_manifest(records: list[dict[str, Any]], source_files: list[Path]) -> dict[str, Any]:
    split_counts = Counter(record["split"] for record in records)
    artist_stats: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "records": 0,
            "splits": Counter(),
            "modes": set(),
        }
    )

    for record in records:
        artist_id = record["artist_id"]
        artist_stats[artist_id]["records"] += 1
        artist_stats[artist_id]["splits"][record["split"]] += 1
        artist_stats[artist_id]["modes"].add(record["mode_id"])

    manifest_artists: dict[str, Any] = {}
    for artist_id, stats in artist_stats.items():
        manifest_artists[artist_id] = {
            "records": stats["records"],
            "splits": dict(stats["splits"]),
            "modes": sorted(stats["modes"]),
        }

    return {
        "schema_version": "1.0",
        "dataset_name": "akira_engine_lyric_blueprints",
        "total_records": len(records),
        "unique_artists": len(manifest_artists),
        "split_counts": dict(split_counts),
        "artists": manifest_artists,
        "source_files": [str(path) for path in source_files],
    }


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(record, ensure_ascii=False) for record in records]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_corpus(
    dataset_paths: list[Path],
    corpus_path: Path | None = None,
    manifest_path: Path | None = None,
) -> CorpusSummary:
    unique_records: dict[str, dict[str, Any]] = {}
    for dataset_path in dataset_paths:
        for record in read_jsonl(dataset_path):
            unique_records.setdefault(record["record_id"], record)

    merged_records = list(unique_records.values())
    final_corpus_path = corpus_path or default_corpus_path()
    final_manifest_path = manifest_path or default_manifest_path()
    write_jsonl(final_corpus_path, merged_records)

    manifest = build_manifest(merged_records, dataset_paths)
    final_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    final_manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    return CorpusSummary(
        corpus_path=final_corpus_path,
        manifest_path=final_manifest_path,
        total_records=len(merged_records),
        unique_artists=manifest["unique_artists"],
        split_counts=manifest["split_counts"],
    )
