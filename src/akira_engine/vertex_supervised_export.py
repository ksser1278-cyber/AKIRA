from __future__ import annotations

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


def _system_instruction() -> dict[str, Any]:
    return {
        "role": "system",
        "parts": [
            {
                "text": (
                    "You are AKIRA ENGINE, a Japanese lyric-writing model. "
                    "Follow the provided task, structure, and surface constraints exactly. "
                    "Return clean Japanese lyrics only, with no meta commentary."
                )
            }
        ],
    }


def _user_payload(sample: dict[str, Any]) -> str:
    payload = {
        "task": sample.get("task"),
        "input": sample.get("input", {}),
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _model_payload(sample: dict[str, Any]) -> str:
    payload = {
        "title": sample.get("output", {}).get("title", ""),
        "lyrics_markdown": sample.get("output", {}).get("lyrics_markdown", ""),
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _vertex_example(sample: dict[str, Any]) -> dict[str, Any]:
    return {
        "systemInstruction": _system_instruction(),
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": _user_payload(sample),
                    }
                ],
            },
            {
                "role": "model",
                "parts": [
                    {
                        "text": _model_payload(sample),
                    }
                ],
            },
        ],
    }


def export_vertex_supervised_jsonl(
    *,
    project_root: Path,
    train_jsonl: Path,
    eval_jsonl: Path | None,
    output_dir: Path,
    base_model: str = "gemini-2.5-flash",
) -> dict[str, Any]:
    train_rows = _load_jsonl(train_jsonl)
    eval_rows = _load_jsonl(eval_jsonl) if eval_jsonl else []
    output_dir.mkdir(parents=True, exist_ok=True)

    vertex_train = [_vertex_example(row) for row in train_rows]
    vertex_eval = [_vertex_example(row) for row in eval_rows]

    train_output = write_jsonl(output_dir / "vertex_train.jsonl", vertex_train)
    eval_output = write_jsonl(output_dir / "vertex_eval.jsonl", vertex_eval)
    job_template = {
        "provider": "vertex_ai",
        "tuning_type": "supervised",
        "base_model": base_model,
        "dataset_format": "jsonl",
        "train_dataset_uri": "gs://REPLACE_WITH_BUCKET/vertex_train.jsonl",
        "validation_dataset_uri": "gs://REPLACE_WITH_BUCKET/vertex_eval.jsonl",
        "recommended_region": "us-central1",
        "suggested_parameters": {
            "epoch_count": 3,
            "adapter_size": 1,
            "learning_rate_multiplier": 1.0,
        },
        "notes": [
            "Vertex AI Gemini supervised tuning requires Cloud Storage JSONL input.",
            "This pilot is a smoke dataset and is below the documented best-results example count.",
        ],
    }
    template_output = write_json(output_dir / "vertex_job_template.json", job_template)
    manifest = {
        "schema_version": "1.0",
        "project_root": str(project_root),
        "source": {
            "train_jsonl": str(train_jsonl),
            "eval_jsonl": str(eval_jsonl) if eval_jsonl else "",
        },
        "outputs": {
            "vertex_train_jsonl": str(train_output),
            "vertex_eval_jsonl": str(eval_output),
            "vertex_job_template": str(template_output),
        },
        "counts": {
            "train_samples": len(vertex_train),
            "eval_samples": len(vertex_eval),
        },
        "base_model": base_model,
    }
    manifest_output = write_json(output_dir / "vertex_export_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_output)
    return manifest
