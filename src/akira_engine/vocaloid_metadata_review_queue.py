from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .training_data import write_json


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_markdown(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def build_vocaloid_metadata_review_queue(*, review_manifest_path: Path, output_root: Path) -> dict[str, Any]:
    review_manifest = _load_json(review_manifest_path.resolve())
    output_root = output_root.resolve()
    review_candidate_dir = output_root / "review_candidate"
    needs_manual_dir = output_root / "needs_manual_review"
    low_confidence_dir = output_root / "low_confidence"
    accepted_dir = output_root / "accepted"
    rejected_dir = output_root / "rejected"
    needs_patch_dir = output_root / "needs_patch"
    for directory in [
        review_candidate_dir,
        needs_manual_dir,
        low_confidence_dir,
        accepted_dir,
        rejected_dir,
        needs_patch_dir,
    ]:
        directory.mkdir(parents=True, exist_ok=True)

    queued_records: list[dict[str, Any]] = []
    for record in review_manifest.get("records", []):
        source_path = Path(record["path"]).resolve()
        track_id = _safe_text(record.get("track_id"))
        auto_status = _safe_text(record.get("auto_status"))
        if auto_status == "review_candidate":
            target_dir = review_candidate_dir
        elif auto_status == "needs_manual_review":
            target_dir = needs_manual_dir
        else:
            target_dir = low_confidence_dir

        queue_record = {
            "track_id": track_id,
            "canonical_title": _safe_text(record.get("canonical_title")),
            "producer": _safe_text(record.get("producer")),
            "auto_status": auto_status,
            "flags": record.get("flags", []),
            "source_path": str(source_path),
            "queue_path": str(target_dir / source_path.name),
        }
        if source_path.exists():
            (target_dir / source_path.name).write_text(source_path.read_text(encoding="utf-8"), encoding="utf-8")
        queued_records.append(queue_record)

    lines = [
        "# Vocaloid Metadata Manual Review Queue",
        "",
        "## Decision Targets",
        "",
        "- move clean approved records to `accepted/`",
        "- move unusable records to `rejected/`",
        "- move fixable records to `needs_patch/`",
        "",
        "## Auto Queue Counts",
        "",
        f"- `review_candidate`: {review_manifest['counts'].get('review_candidate', 0)}",
        f"- `needs_manual_review`: {review_manifest['counts'].get('needs_manual_review', 0)}",
        f"- `low_confidence`: {review_manifest['counts'].get('low_confidence', 0)}",
        "",
        "## Review Rule",
        "",
        "- accept only Vocaloid-canonical tracks",
        "- reject obvious remix, cover, or malformed placeholder records",
        "- send metadata-fixable records to `needs_patch/`",
        "",
        "## Source Manifest",
        "",
        f"- `{review_manifest_path.resolve()}`",
    ]
    readme_path = _write_markdown(output_root / "README.md", "\n".join(lines) + "\n")

    manifest = {
        "schema_version": "1.0",
        "record_type": "vocaloid_metadata_review_queue_manifest",
        "review_manifest_path": str(review_manifest_path.resolve()),
        "output_root": str(output_root),
        "counts": {
            "queued_records": len(queued_records),
            "review_candidate": sum(1 for record in queued_records if record["auto_status"] == "review_candidate"),
            "needs_manual_review": sum(1 for record in queued_records if record["auto_status"] == "needs_manual_review"),
            "low_confidence": sum(1 for record in queued_records if record["auto_status"] == "low_confidence"),
        },
        "queue_dirs": {
            "review_candidate": str(review_candidate_dir),
            "needs_manual_review": str(needs_manual_dir),
            "low_confidence": str(low_confidence_dir),
            "accepted": str(accepted_dir),
            "rejected": str(rejected_dir),
            "needs_patch": str(needs_patch_dir),
        },
        "records": queued_records,
        "readme_path": str(readme_path),
    }
    manifest_path = write_json(output_root / "queue_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest
