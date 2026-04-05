from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .training_data import write_json, write_jsonl


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            rows.append(json.loads(text))
    return rows


def _stable_bucket(sample_id: str) -> int:
    return int(hashlib.md5(sample_id.encode("utf-8")).hexdigest()[:8], 16) % 100


def _pilot_split(sample_id: str) -> str:
    bucket = _stable_bucket(sample_id)
    if bucket < 80:
        return "train"
    return "eval"


def build_supervised_training_pilot_bundle(
    *,
    project_root: Path,
    source_jsonl: Path,
    output_dir: Path,
    pilot_name: str = "owned_original_hook_v1",
) -> dict[str, Any]:
    records = _load_jsonl(source_jsonl)
    output_dir.mkdir(parents=True, exist_ok=True)

    train_rows: list[dict[str, Any]] = []
    eval_rows: list[dict[str, Any]] = []

    for row in records:
        sample = dict(row)
        split = _pilot_split(str(sample.get("sample_id", "")))
        sample["split"] = split
        if split == "train":
            train_rows.append(sample)
        else:
            eval_rows.append(sample)

    train_path = write_jsonl(output_dir / "train.jsonl", train_rows)
    eval_path = write_jsonl(output_dir / "eval.jsonl", eval_rows)
    manifest = {
        "schema_version": "1.0",
        "pilot_name": pilot_name,
        "project_root": str(project_root),
        "source_jsonl": str(source_jsonl),
        "outputs": {
            "train_jsonl": str(train_path),
            "eval_jsonl": str(eval_path),
        },
        "counts": {
            "source_samples": len(records),
            "train": len(train_rows),
            "eval": len(eval_rows),
        },
        "tasks": sorted({str(item.get("task", "")) for item in records if str(item.get("task", "")).strip()}),
        "artists": sorted({str(item.get("input", {}).get("artist_id", "")) for item in records if str(item.get("input", {}).get("artist_id", "")).strip()}),
    }
    manifest_path = write_json(output_dir / "pilot_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest
