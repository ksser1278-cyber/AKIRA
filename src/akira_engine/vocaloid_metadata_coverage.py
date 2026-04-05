from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from .training_data import write_json


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def build_vocaloid_metadata_coverage_report(*, corpus_root: Path, output_root: Path) -> dict[str, Any]:
    corpus_root = corpus_root.resolve()
    output_root = output_root.resolve()
    accepted_dir = corpus_root / "accepted"
    producer_counts: Counter[str] = Counter()
    voicebank_counts: Counter[str] = Counter()
    engine_counts: Counter[str] = Counter()
    platform_counts: Counter[str] = Counter()
    records: list[dict[str, Any]] = []

    for path in sorted(accepted_dir.glob("vocadb_*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        track_id = _safe_text(payload.get("track_identity", {}).get("track_id"))
        title = _safe_text(payload.get("track_identity", {}).get("canonical_title"))
        producer = _safe_text(payload.get("credits", {}).get("producer")) or "unknown"
        engine = _safe_text(payload.get("vocal_synthesis", {}).get("engine_family")) or "unknown"
        platform = _safe_text(payload.get("release_context", {}).get("original_platform")) or "unknown"
        voicebanks = payload.get("vocal_synthesis", {}).get("voicebanks", []) or ["unknown"]

        producer_counts[producer] += 1
        engine_counts[engine] += 1
        platform_counts[platform] += 1
        for voicebank in voicebanks:
            voicebank_counts[_safe_text(voicebank) or "unknown"] += 1

        records.append(
            {
                "track_id": track_id,
                "canonical_title": title,
                "producer": producer,
                "engine_family": engine,
                "original_platform": platform,
                "voicebanks": voicebanks,
                "path": str(path),
            }
        )

    report = {
        "schema_version": "1.0",
        "record_type": "vocaloid_metadata_coverage_report",
        "corpus_root": str(corpus_root),
        "counts": {
            "records": len(records),
            "unique_producers": len(producer_counts),
            "unique_voicebanks": len(voicebank_counts),
        },
        "top_producers": producer_counts.most_common(20),
        "top_voicebanks": voicebank_counts.most_common(20),
        "engine_family_counts": dict(engine_counts),
        "original_platform_counts": dict(platform_counts),
        "records": records,
    }
    manifest_path = write_json(output_root / "vocaloid_metadata_coverage_report.json", report)
    report["manifest_path"] = str(manifest_path)
    md_lines = [
        "# Vocaloid Metadata Coverage Report",
        "",
        "## Counts",
        "",
        f"- `records`: {report['counts']['records']}",
        f"- `unique_producers`: {report['counts']['unique_producers']}",
        f"- `unique_voicebanks`: {report['counts']['unique_voicebanks']}",
        "",
        "## Top Producers",
        "",
    ]
    for producer, count in report["top_producers"]:
        md_lines.append(f"- `{producer}`: {count}")
    md_lines.extend(["", "## Top Voicebanks", ""])
    for voicebank, count in report["top_voicebanks"]:
        md_lines.append(f"- `{voicebank}`: {count}")
    (output_root / "vocaloid_metadata_coverage_report.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    return report
