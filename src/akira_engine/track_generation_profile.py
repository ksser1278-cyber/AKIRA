from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .training_data import write_json, write_jsonl


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _slugify(text: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", text.lower())
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized


def _resolve_artist_id(payload: dict[str, Any]) -> str:
    producer = _safe_text(payload.get("credits", {}).get("producer"))
    if producer:
        return _slugify(producer) or "unknown_artist"

    for source in payload.get("metadata_sources", []):
        notes = _safe_text(source.get("notes"))
        match = re.search(r"artist:\d+:([^\s]+)", notes)
        if match:
            return _slugify(match.group(1)) or "unknown_artist"
    return "unknown_artist"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_lyric_technique_map(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None or not path.exists():
        return {}
    records: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except Exception:
            continue
        track_id = _safe_text(payload.get("track_identity", {}).get("track_id"))
        if track_id:
            records[track_id] = payload
    return records


def _platform_anchor(platform: str) -> list[str]:
    mapping = {
        "youtube": ["video-first release", "direct chorus payoff", "broad hook readability"],
        "niconico": ["subculture-native release", "hook-forward pacing", "vocaloid scene energy"],
        "bilibili": ["internet-native release", "digital-forward presentation"],
        "streaming": ["streaming-shaped arrangement"],
        "cd_release": ["album-framed arrangement"],
        "other": ["platform-agnostic arrangement"],
        "unknown": ["platform-agnostic arrangement"],
    }
    return mapping.get(platform, ["platform-agnostic arrangement"])


def _engine_anchor(engine_family: str) -> tuple[list[str], list[str], list[str]]:
    groove = {
        "vocaloid": ["programmed rhythmic precision", "tight phrase alignment"],
        "synthesizer_v": ["smooth phrase contour", "clean synthetic phrasing"],
        "cevio": ["speech-like phrasing", "controlled synthetic articulation"],
        "utau": ["hand-shaped phrasing", "characterful rough edges"],
        "voiceroid_song_culture": ["speech-song crossover phrasing"],
        "mixed": ["hybrid synthetic vocal handling"],
        "unknown": ["synthetic vocal framing"],
    }.get(engine_family, ["synthetic vocal framing"])
    vocal = {
        "vocaloid": ["synthetic lead vocal", "phrase-exact vocal attack"],
        "synthesizer_v": ["smooth synthetic lead", "controlled vibrato handling"],
        "cevio": ["speech-adjacent synthetic vocal"],
        "utau": ["character-led synthetic vocal", "rougher edge articulation"],
        "voiceroid_song_culture": ["spoken-sung character performance"],
        "mixed": ["multi-engine synthetic performance"],
        "unknown": ["synthetic voice presentation"],
    }.get(engine_family, ["synthetic voice presentation"])
    arrangement = {
        "vocaloid": ["hook-centered topline support"],
        "synthesizer_v": ["melodic sustain support"],
        "cevio": ["dialogic phrasing support"],
        "utau": ["character-forward lead framing"],
        "voiceroid_song_culture": ["speech-rhythm support"],
        "mixed": ["voice-character contrast handling"],
        "unknown": ["lead-vocal support"],
    }.get(engine_family, ["lead-vocal support"])
    return groove, vocal, arrangement


def _title_texture_markers(title: str) -> list[str]:
    lowered = title.lower()
    markers: list[str] = []
    if any(token in lowered for token in ["dream", "moon", "shadow", "night", "star"]):
        markers.append("atmospheric nocturnal texture")
    if any(token in lowered for token in ["noise", "distort", "broken", "chaos", "glitch"]):
        markers.append("abrasive digital texture")
    if any(token in lowered for token in ["love", "heart", "kiss", "me", "you"]):
        markers.append("direct emotional center")
    if any(token in lowered for token in ["game", "zero", "404", "code", "digital"]):
        markers.append("digital motif texture")
    if not markers:
        markers.append("general synthetic-pop texture")
    return markers


def _voicebank_markers(voicebanks: list[str]) -> list[str]:
    markers: list[str] = []
    for voicebank in voicebanks[:4]:
        value = _safe_text(voicebank)
        if not value:
            continue
        markers.append(f"{value} character color")
    return markers or ["synthetic voicebank color"]


def _positive_sound_anchors(payload: dict[str, Any]) -> list[str]:
    title = _safe_text(payload.get("track_identity", {}).get("canonical_title"))
    platform = _safe_text(payload.get("release_context", {}).get("original_platform")) or "unknown"
    engine_family = _safe_text(payload.get("vocal_synthesis", {}).get("engine_family")) or "unknown"
    producer = _safe_text(payload.get("credits", {}).get("producer")) or "unknown producer"
    anchors = [
        *(_platform_anchor(platform)),
        *(_title_texture_markers(title)),
        f"{producer} sound-family influence",
    ]
    groove, vocal, arrangement = _engine_anchor(engine_family)
    anchors.extend(groove[:1])
    anchors.extend(vocal[:1])
    anchors.extend(arrangement[:1])
    deduped: list[str] = []
    seen: set[str] = set()
    for anchor in anchors:
        if anchor not in seen:
            seen.add(anchor)
            deduped.append(anchor)
    return deduped[:10]


def _negative_sound_anchors(payload: dict[str, Any]) -> list[str]:
    platform = _safe_text(payload.get("release_context", {}).get("original_platform")) or "unknown"
    anchors = ["generic western pop", "flat loop-only arrangement"]
    if platform == "niconico":
        anchors.append("over-polished radio-pop finish")
    if platform == "youtube":
        anchors.append("underdeveloped chorus lift")
    return anchors[:8]


def _lyric_profile_from_technique(technique: dict[str, Any] | None) -> dict[str, Any]:
    if not technique:
        return {
            "section_behavior": [],
            "hook_behavior": [],
            "emotional_arc": [],
            "imagery_bank": [],
            "surface_profile": [],
        }
    return {
        "section_behavior": [
            _safe_text(item.get("normalized_role") or item.get("section_label"))
            for item in technique.get("structural_blueprint", {}).get("ordered_sections", [])
            if _safe_text(item.get("normalized_role") or item.get("section_label"))
        ][:12],
        "hook_behavior": [
            *[_safe_text(line) for line in technique.get("hook_construction", {}).get("hook_lines", []) if _safe_text(line)],
            _safe_text(technique.get("hook_construction", {}).get("hook_density")),
        ][:12],
        "emotional_arc": [
            _safe_text(technique.get("emotional_arc", {}).get("overall_arc_label")),
            *[_safe_text(item.get("emotion")) for item in technique.get("emotional_arc", {}).get("section_emotion_flow", []) if _safe_text(item.get("emotion"))],
        ][:12],
        "imagery_bank": [
            *[_safe_text(item) for item in technique.get("imagery_profile", {}).get("imagery_tags", []) if _safe_text(item)],
            *[_safe_text(item) for item in technique.get("imagery_profile", {}).get("motif_clusters", []) if _safe_text(item)],
        ][:12],
        "surface_profile": [
            _safe_text(technique.get("diction_surface", {}).get("register")),
            _safe_text(technique.get("diction_surface", {}).get("directness_level")),
            _safe_text(technique.get("diction_surface", {}).get("abstraction_level")),
            _safe_text(technique.get("narrative_stance", {}).get("dominant_perspective")),
        ],
    }


def _build_sound_profile(payload: dict[str, Any]) -> dict[str, Any]:
    title = _safe_text(payload.get("track_identity", {}).get("canonical_title"))
    engine_family = _safe_text(payload.get("vocal_synthesis", {}).get("engine_family")) or "unknown"
    voicebanks = payload.get("vocal_synthesis", {}).get("voicebanks", [])
    producer = _safe_text(payload.get("credits", {}).get("producer")) or "unknown producer"
    platform = _safe_text(payload.get("release_context", {}).get("original_platform")) or "unknown"
    groove, vocal, arrangement = _engine_anchor(engine_family)
    texture_markers = _title_texture_markers(title)
    return {
        "tempo_profile": {
            "bpm_estimate": None,
            "tempo_band": "unknown",
            "tempo_feel": "undetermined",
            "meter_signature": "unknown",
            "swing_or_straight": "undetermined",
        },
        "energy_profile": {
            "global_energy_level": "undetermined",
            "energy_arc_label": "undetermined",
            "peak_section": "unknown",
            "release_section": "unknown",
            "drop_presence": "unknown",
        },
        "groove_profile": groove,
        "arrangement_profile": [
            *arrangement,
            "chorus-lift behavior unresolved",
            *_platform_anchor(platform)[:1],
        ][:10],
        "instrumentation_profile": [
            "synthetic lead support",
            "programmed rhythm section",
            "instrumentation unresolved at metadata-only stage",
        ],
        "texture_profile": [
            *texture_markers,
            "metadata-derived texture estimate",
        ][:10],
        "vocal_profile": [
            *vocal,
            *_voicebank_markers(voicebanks),
        ][:10],
        "sound_anchors": {
            "positive": _positive_sound_anchors(payload),
            "negative": _negative_sound_anchors(payload),
        },
        "producer_sound_markers": [
            f"{producer} producer signature",
            f"{engine_family} synthetic vocal framing",
        ],
    }


def _prompt_readiness(payload: dict[str, Any], technique: dict[str, Any] | None) -> dict[str, Any]:
    blocking: list[str] = []
    metadata_quality = _safe_text(payload.get("collection_status", {}).get("metadata_quality")) or "seed"
    review_status = _safe_text(payload.get("collection_status", {}).get("canonical_review_status")) or "needs_review"
    if metadata_quality != "reviewed":
        blocking.append("metadata_not_reviewed")
    if review_status != "accepted":
        blocking.append("metadata_not_accepted")
    if technique is None:
        blocking.append("lyric_technique_missing")
    return {
        "suno_prompt_ready": not blocking,
        "blocking_reasons": blocking,
        "notes": "Metadata-only generation profile baseline. Add lyric technique record to fully unlock prompt packaging." if blocking else "Generation profile has metadata and lyric technique support.",
    }


def _build_generation_record(payload: dict[str, Any], technique: dict[str, Any] | None) -> dict[str, Any]:
    track_id = _safe_text(payload.get("track_identity", {}).get("track_id"))
    artist_id = _resolve_artist_id(payload)
    canonical_title = _safe_text(payload.get("track_identity", {}).get("canonical_title"))
    metadata_quality = _safe_text(payload.get("collection_status", {}).get("metadata_quality")) or "seed"
    return {
        "schema_version": "1.0",
        "record_type": "track_generation_record",
        "track_identity": {
            "track_id": track_id,
            "artist_id": artist_id,
            "canonical_title": canonical_title,
            "mode_candidates": technique.get("mode_evidence", {}).get("candidate_modes", []) if technique else [],
        },
        "source_status": {
            "metadata_quality": metadata_quality,
            "lyric_technique_quality": "reviewed" if technique else "missing",
            "sound_profile_quality": "partial",
            "notes": "Sound profile inferred from canonical metadata. Lyric profile merged from technique record when available.",
        },
        "lyric_profile": _lyric_profile_from_technique(technique),
        "sound_profile": _build_sound_profile(payload),
        "prompt_readiness": _prompt_readiness(payload, technique),
    }


def build_track_generation_records(
    *,
    corpus_root: Path,
    output_root: Path,
    lyric_technique_jsonl: Path | None = None,
) -> dict[str, Any]:
    corpus_root = corpus_root.resolve()
    output_root = output_root.resolve()
    accepted_dir = corpus_root / "accepted"
    records_dir = output_root / "records"
    records_dir.mkdir(parents=True, exist_ok=True)
    technique_map = _load_lyric_technique_map(lyric_technique_jsonl.resolve() if lyric_technique_jsonl else None)

    records: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for path in sorted(accepted_dir.glob("vocadb_*.json")):
        try:
            payload = _load_json(path)
        except Exception as exc:
            skipped.append({"path": str(path), "reason": f"invalid_json:{type(exc).__name__}"})
            continue
        track_id = _safe_text(payload.get("track_identity", {}).get("track_id"))
        if not track_id:
            skipped.append({"path": str(path), "reason": "missing_track_id"})
            continue
        record = _build_generation_record(payload, technique_map.get(track_id))
        records.append(record)
        write_json(records_dir / f"{track_id}.json", record)

    jsonl_path = write_jsonl(output_root / "track_generation_records.jsonl", records)
    manifest = {
        "schema_version": "1.0",
        "record_type": "track_generation_manifest",
        "corpus_root": str(corpus_root),
        "output_root": str(output_root),
        "lyric_technique_jsonl": str(lyric_technique_jsonl.resolve()) if lyric_technique_jsonl else "",
        "counts": {
            "records": len(records),
            "suno_prompt_ready": sum(1 for record in records if record["prompt_readiness"]["suno_prompt_ready"]),
            "blocked": sum(1 for record in records if not record["prompt_readiness"]["suno_prompt_ready"]),
            "skipped": len(skipped),
        },
        "skipped": skipped,
        "outputs": {
            "jsonl": str(jsonl_path),
            "records_dir": str(records_dir),
        },
    }
    manifest_path = write_json(output_root / "track_generation_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest
