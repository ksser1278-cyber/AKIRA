from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .training_data import write_json, write_jsonl
from .training_rights_map import ALLOWED_RIGHTS_STATUSES, load_rights_map


ALLOWED_SOURCE_FAMILIES = {
    "direct_license",
    "owned_original",
    "partner_corpus",
    "internal_eval_only",
}
ALLOWED_TASKS = {
    "hook_generation",
    "section_generation",
    "chorus_rewrite",
    "final_release_rewrite",
    "full_song_generation",
}


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _contains_broken_text(value: str) -> bool:
    return "\ufffd" in value or "�" in value or "?" in value


def _resolve_asset_path(*, project_root: Path, pilot_root: Path, asset_ref: str) -> Path:
    asset_ref = _safe_text(asset_ref)
    if not asset_ref:
        return pilot_root / "__missing__"
    candidate = Path(asset_ref)
    if candidate.is_absolute():
        return candidate

    direct = (pilot_root / candidate).resolve()
    if direct.exists():
        return direct

    acquisition_root = (project_root / "datasets" / "_global" / "rights_cleared_corpus_acquisition").resolve()
    via_acquisition = (acquisition_root / candidate).resolve()
    if via_acquisition.exists():
        return via_acquisition

    return direct


def _validate_training_source_record(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if _safe_text(record.get("schema_version")) != "1.0":
        errors.append("schema_version_mismatch")
    if _safe_text(record.get("record_type")) != "training_source_record":
        errors.append("record_type_mismatch")

    track_identity = record.get("track_identity", {})
    source_package = record.get("source_package", {})
    rights_review = record.get("rights_review", {})
    content_assets = record.get("content_assets", {})
    training_scope = record.get("training_scope", {})

    if not _safe_text(track_identity.get("track_id")):
        errors.append("missing_track_id")
    if not _safe_text(track_identity.get("artist_id")):
        errors.append("missing_artist_id")
    title = _safe_text(track_identity.get("title"))
    if not title:
        errors.append("missing_title")
    elif _contains_broken_text(title):
        errors.append("broken_title_text")

    source_family = _safe_text(source_package.get("source_family"))
    if source_family not in ALLOWED_SOURCE_FAMILIES:
        errors.append("invalid_source_family")

    rights_status = _safe_text(rights_review.get("rights_status"))
    if rights_status not in ALLOWED_RIGHTS_STATUSES:
        errors.append("invalid_rights_status")

    lyric_ref = _safe_text(content_assets.get("lyric_text_ref"))
    section_map_ref = _safe_text(content_assets.get("section_map_ref"))
    if not lyric_ref:
        errors.append("missing_lyric_text_ref")
    if not section_map_ref:
        errors.append("missing_section_map_ref")

    allowed_tasks = training_scope.get("allowed_tasks", [])
    if not isinstance(allowed_tasks, list) or not allowed_tasks:
        errors.append("missing_allowed_tasks")
    else:
        invalid_tasks = [task for task in allowed_tasks if _safe_text(task) not in ALLOWED_TASKS]
        if invalid_tasks:
            errors.append("invalid_allowed_tasks")

    return errors


def _read_lines_from_lyric_asset(path: Path) -> list[str]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines


def _load_section_map(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return _load_json(path)


def _build_hook_sample(*, record: dict[str, Any], lyric_lines: list[str], section_map: dict[str, Any]) -> dict[str, Any] | None:
    track_identity = record["track_identity"]
    rights_review = record["rights_review"]
    source_package = record["source_package"]
    hook_lines = section_map.get("hook_lines", [])
    if not isinstance(hook_lines, list):
        hook_lines = []
    cleaned_hook_lines = [_safe_text(line) for line in hook_lines if _safe_text(line)]

    body_lines = lyric_lines
    if lyric_lines and lyric_lines[0].lower() == "[chorus]":
        body_lines = lyric_lines[1:]
    if not body_lines:
        body_lines = cleaned_hook_lines
    if not body_lines:
        return None
    if any(_contains_broken_text(line) for line in body_lines + cleaned_hook_lines):
        return None

    rights_status = _safe_text(rights_review.get("rights_status"))
    split = "train"
    if rights_status == "internal_only_holdout":
        split = "test"

    markdown_lines = ["[chorus]", *body_lines]
    return {
        "sample_id": f"{track_identity['track_id']}_hook_generation_v1",
        "schema_version": "1.0",
        "split": split,
        "task": "hook_generation",
        "input": {
            "artist_id": _safe_text(track_identity.get("artist_id")),
            "mode_id": "owned_original_hook_pilot",
            "language": "ja",
            "title_seed": _safe_text(track_identity.get("title")),
            "theme_axes": [],
            "blueprint": {
                "sections": [
                    {
                        "section": "chorus",
                        "line_target": len(body_lines),
                        "goal": "Deliver a compact owned-original chorus hook.",
                    }
                ],
                "hook_constraints": {
                    "title_binding": "medium",
                    "repetition_pressure": "medium",
                    "hook_line_target": max(1, min(2, len(cleaned_hook_lines) or len(body_lines))),
                },
            },
            "style_constraints": {
                "imagery_atoms": [],
                "forbidden_generic_atoms": [],
                "surface_rules": ["japanese_only", "no_meta_commentary"],
            },
            "phonetic_constraints": {},
        },
        "output": {
            "title": _safe_text(track_identity.get("title")),
            "lyrics_markdown": "\n".join(markdown_lines),
        },
        "metadata": {
            "source_track_id": _safe_text(track_identity.get("track_id")),
            "source_artist_id": _safe_text(track_identity.get("artist_id")),
            "source_tier": "rights_cleared_owned_original",
            "rights_status": rights_status,
            "task_origin": "training_source_record",
            "contains_verbatim_lyrics": True,
            "normalization_version": "1.0",
            "source_family": _safe_text(source_package.get("source_family")),
            "evidence_ref": _safe_text(source_package.get("evidence_ref")),
        },
    }


def import_owned_original_hook_pilot(
    *,
    project_root: Path,
    pilot_root: Path,
    rights_map_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    final_pilot_root = pilot_root.resolve()
    accepted_dir = final_pilot_root / "accepted"
    accepted_paths = sorted(accepted_dir.glob("*.json"))

    existing_rights = load_rights_map(rights_map_path if rights_map_path.exists() else None)
    samples: list[dict[str, Any]] = []
    imported_records: list[dict[str, Any]] = []
    skipped_records: list[dict[str, Any]] = []

    for record_path in accepted_paths:
        record = _load_json(record_path)
        errors = _validate_training_source_record(record)
        if errors:
            skipped_records.append(
                {
                    "record_path": str(record_path),
                    "reason": ",".join(errors),
                }
            )
            continue

        track_identity = record["track_identity"]
        rights_review = record["rights_review"]
        content_assets = record["content_assets"]
        training_scope = record["training_scope"]
        track_id = _safe_text(track_identity.get("track_id"))

        lyric_path = _resolve_asset_path(
            project_root=final_project_root,
            pilot_root=final_pilot_root,
            asset_ref=_safe_text(content_assets.get("lyric_text_ref")),
        )
        section_map_path = _resolve_asset_path(
            project_root=final_project_root,
            pilot_root=final_pilot_root,
            asset_ref=_safe_text(content_assets.get("section_map_ref")),
        )
        lyric_lines = _read_lines_from_lyric_asset(lyric_path)
        section_map = _load_section_map(section_map_path)
        if not lyric_lines or any(_contains_broken_text(line) for line in lyric_lines):
            skipped_records.append(
                {
                    "record_path": str(record_path),
                    "track_id": track_id,
                    "reason": "invalid_lyric_asset",
                }
            )
            continue

        existing_rights[track_id] = {
            "track_id": track_id,
            "artist_id": _safe_text(track_identity.get("artist_id")),
            "rights_status": _safe_text(rights_review.get("rights_status")) or "unknown",
            "source_basis": _safe_text(rights_review.get("source_basis")),
            "notes": _safe_text(rights_review.get("notes")),
        }

        allowed_tasks = {_safe_text(task) for task in training_scope.get("allowed_tasks", [])}
        if "hook_generation" in allowed_tasks:
            sample = _build_hook_sample(
                record=record,
                lyric_lines=lyric_lines,
                section_map=section_map,
            )
            if sample is None:
                skipped_records.append(
                    {
                        "record_path": str(record_path),
                        "track_id": track_id,
                        "reason": "failed_to_build_hook_sample",
                    }
                )
                continue
            samples.append(sample)

        imported_records.append(
            {
                "track_id": track_id,
                "artist_id": _safe_text(track_identity.get("artist_id")),
                "rights_status": _safe_text(rights_review.get("rights_status")),
                "record_path": str(record_path),
            }
        )

    rights_payload = {
        "schema_version": "1.0",
        "updated_at": datetime.now().date().isoformat(),
        "records": sorted(
            existing_rights.values(),
            key=lambda item: (item.get("artist_id", ""), item.get("track_id", "")),
        ),
    }
    rights_output = write_json(rights_map_path, rights_payload)
    samples_output = write_jsonl(output_dir / "supervised_samples.jsonl", samples)
    manifest = {
        "schema_version": "1.0",
        "project_root": str(final_project_root),
        "pilot_root": str(final_pilot_root),
        "rights_map_path": str(rights_output),
        "outputs": {
            "supervised_samples": str(samples_output),
        },
        "counts": {
            "accepted_records_scanned": len(accepted_paths),
            "imported_records": len(imported_records),
            "samples": len(samples),
            "skipped": len(skipped_records),
        },
        "imported_records": imported_records,
        "skipped_records": skipped_records,
    }
    manifest_path = write_json(output_dir / "import_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest
