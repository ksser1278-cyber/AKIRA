from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def enrich_conditioning_with_audio(record: dict[str, Any], audio_track: dict[str, Any]) -> dict[str, Any]:
    enriched = json.loads(json.dumps(record, ensure_ascii=False))

    reported = enriched.setdefault("audio_fact_layer", {}).setdefault("reported_facts", {})
    proxy = enriched.setdefault("audio_fact_layer", {}).setdefault("proxy_inference", {})
    qc = enriched.setdefault("quality_control", {})
    warnings = qc.setdefault("warnings", [])
    missing_fields = qc.setdefault("missing_fields", [])
    manual_review = qc.setdefault("manual_review_required_for", [])

    duration_seconds = audio_track.get("duration_seconds")
    if duration_seconds:
        minutes = int(duration_seconds // 60)
        seconds = int(round(duration_seconds % 60))
        display = f"{minutes}:{seconds:02d}"
        release = enriched.setdefault("track_identity", {}).setdefault("release", {})
        release["runtime"] = {
            "display": display,
            "seconds": int(round(duration_seconds)),
            "status": "confirmed",
            "sources": [
                {
                    "label": "Local owned audio file probe",
                    "origin": "other",
                    "notes": audio_track.get("source_filename", ""),
                }
            ],
        }
        if "runtime" in missing_fields:
            missing_fields.remove("runtime")

    confirmed_instrumentation = reported.get("confirmed_instrumentation", [])
    if not confirmed_instrumentation:
        reported["confirmed_instrumentation"] = []

    reported["audio_file_probe"] = {
        "format_name": audio_track.get("format_name"),
        "codec_name": audio_track.get("codec_name"),
        "sample_rate_hz": audio_track.get("sample_rate_hz"),
        "channels": audio_track.get("channels"),
        "channel_layout": audio_track.get("channel_layout"),
        "bit_rate": audio_track.get("bit_rate"),
        "status": "confirmed",
        "sources": [
            {
                "label": "Local owned audio file probe",
                "origin": "other",
                "notes": audio_track.get("source_filename", ""),
            }
        ],
    }

    loudness = audio_track.get("loudness", {})
    dynamics = audio_track.get("dynamics", {})
    energy_curve = audio_track.get("energy_curve", {})

    measured_audio = {
        "integrated_lufs": loudness.get("integrated_lufs"),
        "lra_lu": loudness.get("lra_lu"),
        "rms_median_db": dynamics.get("rms_median_db"),
        "rms_span_db": dynamics.get("rms_span_db"),
        "early_rms_db": energy_curve.get("early_rms_db"),
        "mid_rms_db": energy_curve.get("mid_rms_db"),
        "late_rms_db": energy_curve.get("late_rms_db"),
        "late_minus_early_db": energy_curve.get("late_minus_early_db"),
        "peak_zone": energy_curve.get("peak_zone"),
        "status": "confirmed",
        "sources": [
            {
                "label": "Local owned audio file analysis",
                "origin": "other",
                "notes": audio_track.get("source_filename", ""),
            }
        ],
    }
    reported["measured_audio_profile"] = measured_audio

    evidence_basis = set(proxy.get("evidence_basis", []))
    evidence_basis.add("human_listening")
    evidence_basis.add("other")
    proxy["evidence_basis"] = sorted(evidence_basis)

    proxy.setdefault("confidence", "medium")

    late_lift = energy_curve.get("late_minus_early_db")
    peak_zone = energy_curve.get("peak_zone")
    if late_lift is not None:
        dynamics_arc = [item for item in proxy.get("dynamics_arc", []) if isinstance(item, str)]
        if late_lift >= 2.0 and "measured late energy lift" not in dynamics_arc:
            dynamics_arc.append("measured late energy lift")
        if late_lift <= 0.3 and "measured stable end energy" not in dynamics_arc:
            dynamics_arc.append("measured stable end energy")
        proxy["dynamics_arc"] = dynamics_arc

    if peak_zone and isinstance(proxy.get("arrangement_arc"), list):
        arrangement_arc = [item for item in proxy["arrangement_arc"] if isinstance(item, str)]
        marker = f"measured peak zone: {peak_zone}"
        if marker not in arrangement_arc:
            arrangement_arc.append(marker)
        proxy["arrangement_arc"] = arrangement_arc

    note = "Audio-derived runtime, loudness, and energy curve attached from owned file."
    if note not in warnings:
        warnings.append(note)

    if "exact instrumentation claims" not in manual_review:
        manual_review.append("exact instrumentation claims")

    return enriched


def enrich_artist_records(project_root: Path, artist_id: str, audio_summary: dict[str, Any]) -> list[Path]:
    records_dir = project_root / "data" / artist_id / "reference_tracks"
    updated_paths: list[Path] = []

    by_track_id = {track["track_id"]: track for track in audio_summary.get("tracks", []) if track.get("exists")}

    for path in sorted(records_dir.glob("*.conditioning.json")):
        record = load_json(path)
        track_id = record.get("track_identity", {}).get("track_id")
        audio_track = by_track_id.get(track_id)
        if not audio_track:
            continue
        enriched = enrich_conditioning_with_audio(record, audio_track)
        path.write_text(json.dumps(enriched, ensure_ascii=False, indent=2), encoding="utf-8")
        updated_paths.append(path)

    return updated_paths
