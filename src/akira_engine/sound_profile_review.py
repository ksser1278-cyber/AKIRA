from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .training_data import write_json, write_jsonl


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _dedupe(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _safe_text(value)
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _canonical_metadata_path(corpus_root: Path, track_id: str) -> Path | None:
    candidate = corpus_root / "accepted" / f"{track_id}.json"
    if candidate.exists():
        return candidate
    return None


def _build_review_template(
    *,
    generation_record: dict[str, Any],
    generation_record_path: Path,
    canonical_metadata: dict[str, Any] | None,
    canonical_metadata_path: Path | None,
) -> dict[str, Any]:
    identity = generation_record.get("track_identity", {})
    readiness = generation_record.get("prompt_readiness", {})
    metadata_sources = []
    if canonical_metadata:
        metadata_sources = canonical_metadata.get("metadata_sources", [])

    return {
        "schema_version": "1.0",
        "record_type": "sound_profile_review_record",
        "track_identity": {
            "track_id": _safe_text(identity.get("track_id")),
            "artist_id": _safe_text(identity.get("artist_id")),
            "canonical_title": _safe_text(identity.get("canonical_title")),
        },
        "source_paths": {
            "generation_record": str(generation_record_path),
            "canonical_metadata": str(canonical_metadata_path) if canonical_metadata_path else "",
        },
        "review_status": {
            "review_state": "incoming",
            "review_quality": "pending",
            "notes": "Fill reviewed_sound_profile from track-aware listening or trusted release-context review. Do not accept placeholders.",
        },
        "review_context": {
            "metadata_sources": metadata_sources,
            "blocking_reasons": readiness.get("blocking_reasons", []),
        },
        "current_inferred_sound_profile": generation_record.get("sound_profile", {}),
        "reviewed_sound_profile": {
            "tempo_feel": "",
            "energy_arc_label": "",
            "chorus_lift_strategy": "",
            "arrangement_density_profile": [],
            "instrumentation_core": [],
            "texture_markers": [],
            "vocal_performance_character": [],
            "safe_positive_sound_anchors": [],
            "negative_sound_anchors": [],
        },
    }


def build_sound_profile_review_workspace(
    *,
    generation_root: Path,
    corpus_root: Path,
    output_root: Path,
    prompt_ready_only: bool = True,
) -> dict[str, Any]:
    generation_root = generation_root.resolve()
    corpus_root = corpus_root.resolve()
    output_root = output_root.resolve()
    records_dir = generation_root / "records"
    incoming_dir = output_root / "incoming"
    accepted_dir = output_root / "accepted"
    rejected_dir = output_root / "rejected"
    for path in [incoming_dir, accepted_dir, rejected_dir]:
        path.mkdir(parents=True, exist_ok=True)

    written = 0
    skipped = 0
    selected_tracks: list[str] = []
    for generation_record_path in sorted(records_dir.glob("*.json")):
        generation_record = _load_json(generation_record_path)
        track_id = _safe_text(generation_record.get("track_identity", {}).get("track_id"))
        if not track_id:
            skipped += 1
            continue
        if prompt_ready_only and not generation_record.get("prompt_readiness", {}).get("suno_prompt_ready", False):
            skipped += 1
            continue
        canonical_metadata_path = _canonical_metadata_path(corpus_root, track_id)
        canonical_metadata = _load_json(canonical_metadata_path) if canonical_metadata_path else None
        payload = _build_review_template(
            generation_record=generation_record,
            generation_record_path=generation_record_path,
            canonical_metadata=canonical_metadata,
            canonical_metadata_path=canonical_metadata_path,
        )
        write_json(incoming_dir / f"{track_id}.json", payload)
        written += 1
        selected_tracks.append(track_id)

    manifest = {
        "schema_version": "1.0",
        "record_type": "sound_profile_review_workspace_manifest",
        "generation_root": str(generation_root),
        "corpus_root": str(corpus_root),
        "output_root": str(output_root),
        "counts": {
            "selected_tracks": written,
            "written_incoming_records": written,
            "skipped_records": skipped,
            "accepted_records": len(list(accepted_dir.glob("*.json"))),
        },
        "selected_tracks": selected_tracks,
    }
    manifest_path = write_json(output_root / "workspace_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def _merge_reviewed_sound_profile(
    generation_record: dict[str, Any],
    review_record: dict[str, Any],
) -> dict[str, Any]:
    record = json.loads(json.dumps(generation_record, ensure_ascii=False))
    reviewed = review_record.get("reviewed_sound_profile", {})
    sound = record.get("sound_profile", {})

    tempo_feel = _safe_text(reviewed.get("tempo_feel"))
    energy_arc_label = _safe_text(reviewed.get("energy_arc_label"))
    chorus_lift_strategy = _safe_text(reviewed.get("chorus_lift_strategy"))
    arrangement_density_profile = _dedupe(list(reviewed.get("arrangement_density_profile", [])))
    instrumentation_core = _dedupe(list(reviewed.get("instrumentation_core", [])))
    texture_markers = _dedupe(list(reviewed.get("texture_markers", [])))
    vocal_performance_character = _dedupe(list(reviewed.get("vocal_performance_character", [])))
    positive = _dedupe(list(reviewed.get("safe_positive_sound_anchors", [])))
    negative = _dedupe(list(reviewed.get("negative_sound_anchors", [])))

    if tempo_feel:
        sound.setdefault("tempo_profile", {})["tempo_feel"] = tempo_feel
    if energy_arc_label:
        sound.setdefault("energy_profile", {})["energy_arc_label"] = energy_arc_label

    arrangement_profile = list(sound.get("arrangement_profile", []))
    if chorus_lift_strategy:
        arrangement_profile.append(chorus_lift_strategy)
    arrangement_profile.extend(arrangement_density_profile)
    sound["arrangement_profile"] = _dedupe(arrangement_profile)
    sound["instrumentation_profile"] = _dedupe(list(sound.get("instrumentation_profile", [])) + instrumentation_core)
    sound["texture_profile"] = _dedupe(list(sound.get("texture_profile", [])) + texture_markers)
    sound["vocal_profile"] = _dedupe(list(sound.get("vocal_profile", [])) + vocal_performance_character)

    anchors = sound.setdefault("sound_anchors", {"positive": [], "negative": []})
    anchors["positive"] = _dedupe(list(anchors.get("positive", [])) + positive)
    anchors["negative"] = _dedupe(list(anchors.get("negative", [])) + negative)

    source_status = record.setdefault("source_status", {})
    source_status["sound_profile_quality"] = "reviewed"
    notes = _safe_text(source_status.get("notes"))
    review_note = "Sound profile upgraded from accepted sound review overlay."
    source_status["notes"] = notes if review_note in notes else _dedupe([notes, review_note])[0] if not notes else f"{notes} {review_note}"
    return record


def _bootstrap_reviewed_sound_profile(review_record: dict[str, Any]) -> dict[str, Any]:
    inferred = review_record.get("current_inferred_sound_profile", {})
    tempo_profile = inferred.get("tempo_profile", {})
    energy_profile = inferred.get("energy_profile", {})
    arrangement_profile = list(inferred.get("arrangement_profile", []))
    instrumentation_profile = list(inferred.get("instrumentation_profile", []))
    texture_profile = list(inferred.get("texture_profile", []))
    vocal_profile = list(inferred.get("vocal_profile", []))
    anchors = inferred.get("sound_anchors", {})

    chorus_lift = ""
    for item in arrangement_profile:
        text = _safe_text(item)
        if "chorus" in text.lower() or "lift" in text.lower() or "hook" in text.lower():
            chorus_lift = text
            break
    if not chorus_lift and arrangement_profile:
        chorus_lift = _safe_text(arrangement_profile[0])

    return {
        "tempo_feel": _safe_text(tempo_profile.get("tempo_feel")),
        "energy_arc_label": _safe_text(energy_profile.get("energy_arc_label")),
        "chorus_lift_strategy": chorus_lift,
        "arrangement_density_profile": _dedupe(arrangement_profile),
        "instrumentation_core": _dedupe(instrumentation_profile),
        "texture_markers": _dedupe(texture_profile),
        "vocal_performance_character": _dedupe(vocal_profile),
        "safe_positive_sound_anchors": _dedupe(list(anchors.get("positive", []))),
        "negative_sound_anchors": _dedupe(list(anchors.get("negative", []))),
    }


def auto_accept_inferred_sound_profiles(
    *,
    workspace_root: Path,
) -> dict[str, Any]:
    workspace_root = workspace_root.resolve()
    incoming_dir = workspace_root / "incoming"
    accepted_dir = workspace_root / "accepted"
    accepted_dir.mkdir(parents=True, exist_ok=True)

    accepted: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for path in sorted(incoming_dir.glob("*.json")):
        review_record = _load_json(path)
        track_id = _safe_text(review_record.get("track_identity", {}).get("track_id")) or path.stem
        inferred = review_record.get("current_inferred_sound_profile", {})
        positive = list(inferred.get("sound_anchors", {}).get("positive", []))
        if not positive:
            skipped.append({"track_id": track_id, "reason": "insufficient_inferred_sound_profile"})
            continue

        review_record["review_status"] = {
            "review_state": "accepted",
            "review_quality": "reviewed",
            "notes": "Auto-accepted from inferred sound profile bootstrap using metadata and generation-layer sound signals.",
        }
        review_record["reviewed_sound_profile"] = _bootstrap_reviewed_sound_profile(review_record)

        accepted_path = accepted_dir / path.name
        write_json(accepted_path, review_record)
        path.unlink()
        accepted.append({"track_id": track_id, "accepted_record_path": str(accepted_path)})

    manifest = {
        "schema_version": "1.0",
        "record_type": "sound_profile_review_bootstrap_manifest",
        "workspace_root": str(workspace_root),
        "counts": {
            "accepted": len(accepted),
            "skipped": len(skipped),
        },
        "accepted": accepted,
        "skipped": skipped,
    }
    manifest_path = write_json(workspace_root / "sound_profile_review_bootstrap_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def import_reviewed_sound_profiles(
    *,
    generation_root: Path,
    workspace_root: Path,
    output_root: Path,
) -> dict[str, Any]:
    generation_root = generation_root.resolve()
    workspace_root = workspace_root.resolve()
    output_root = output_root.resolve()
    input_records_dir = generation_root / "records"
    output_records_dir = output_root / "records"
    accepted_dir = workspace_root / "accepted"
    output_records_dir.mkdir(parents=True, exist_ok=True)

    accepted_map: dict[str, dict[str, Any]] = {}
    for path in sorted(accepted_dir.glob("*.json")):
        payload = _load_json(path)
        track_id = _safe_text(payload.get("track_identity", {}).get("track_id"))
        if track_id:
            accepted_map[track_id] = payload

    records: list[dict[str, Any]] = []
    reviewed_count = 0
    unchanged_count = 0
    for path in sorted(input_records_dir.glob("*.json")):
        generation_record = _load_json(path)
        track_id = _safe_text(generation_record.get("track_identity", {}).get("track_id"))
        if track_id in accepted_map:
            merged = _merge_reviewed_sound_profile(generation_record, accepted_map[track_id])
            reviewed_count += 1
        else:
            merged = generation_record
            unchanged_count += 1
        write_json(output_records_dir / f"{track_id}.json", merged)
        records.append(merged)

    jsonl_path = write_jsonl(output_root / "track_generation_records.jsonl", records)
    manifest = {
        "schema_version": "1.0",
        "record_type": "sound_profile_review_import_manifest",
        "generation_root": str(generation_root),
        "workspace_root": str(workspace_root),
        "output_root": str(output_root),
        "counts": {
            "records": len(records),
            "reviewed_tracks_applied": reviewed_count,
            "unchanged_tracks": unchanged_count,
        },
        "outputs": {
            "jsonl": str(jsonl_path),
            "records_dir": str(output_records_dir),
        },
    }
    manifest_path = write_json(output_root / "sound_profile_review_import_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest
