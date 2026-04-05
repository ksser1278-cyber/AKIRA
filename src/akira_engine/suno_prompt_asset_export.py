from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .training_data import write_json, write_jsonl


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _dedupe(values: list[str], *, limit: int | None = None) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    blocked = {
        "unknown",
        "undetermined",
        "unresolved",
        "missing",
        "none",
        "null",
    }
    for value in values:
        text = _safe_text(value)
        if not text or text.lower() in blocked or text in seen:
            continue
        seen.add(text)
        deduped.append(text)
        if limit is not None and len(deduped) >= limit:
            break
    return deduped


def _join_compact(values: list[str], *, fallback: str) -> str:
    cleaned = _dedupe(values, limit=6)
    return ", ".join(cleaned) if cleaned else fallback


def _build_concept_line(record: dict[str, Any]) -> str:
    identity = record.get("track_identity", {})
    lyric_profile = record.get("lyric_profile", {})
    sound_profile = record.get("sound_profile", {})
    title = _safe_text(identity.get("canonical_title")) or "Untitled"
    mode = _safe_text((identity.get("mode_candidates") or [""])[0])
    imagery = _dedupe(lyric_profile.get("imagery_bank", []), limit=2)
    textures = _dedupe(sound_profile.get("texture_profile", []), limit=2)
    parts = [title]
    if mode:
        parts.append(mode.replace("_", " "))
    parts.extend(imagery)
    parts.extend(textures[:1])
    return " | ".join(parts)


def _build_sound_layer(record: dict[str, Any]) -> dict[str, Any]:
    sound_profile = record.get("sound_profile", {})
    tempo = sound_profile.get("tempo_profile", {})
    energy = sound_profile.get("energy_profile", {})
    genre_anchors = _dedupe([
        *sound_profile.get("groove_profile", []),
        *sound_profile.get("texture_profile", []),
    ], limit=6)
    tempo_anchors = _dedupe([
        _safe_text(tempo.get("tempo_band")),
        _safe_text(tempo.get("tempo_feel")),
        _safe_text(tempo.get("swing_or_straight")),
        _safe_text(energy.get("global_energy_level")),
        _safe_text(energy.get("energy_arc_label")),
    ], limit=5)
    arrangement_anchors = _dedupe(sound_profile.get("arrangement_profile", []), limit=6)
    production_anchors = _dedupe([
        *sound_profile.get("instrumentation_profile", []),
        *sound_profile.get("sound_anchors", {}).get("positive", []),
    ], limit=8)
    vocal_anchors = _dedupe(sound_profile.get("vocal_profile", []), limit=6)
    return {
        "style_prompt_detailed": _join_compact(
            [*genre_anchors, *arrangement_anchors, *production_anchors, *vocal_anchors],
            fallback="synthetic vocal song design unresolved",
        ),
        "style_prompt_compact": _join_compact(
            [*genre_anchors[:2], *arrangement_anchors[:2], *vocal_anchors[:1]],
            fallback="synthetic vocal pop",
        ),
        "genre_anchors": genre_anchors,
        "tempo_anchors": tempo_anchors,
        "arrangement_anchors": arrangement_anchors,
        "production_anchors": production_anchors,
        "vocal_anchors": vocal_anchors,
    }


def _build_lyric_layer(record: dict[str, Any]) -> dict[str, Any]:
    lyric_profile = record.get("lyric_profile", {})
    hook_behavior = _dedupe(lyric_profile.get("hook_behavior", []), limit=6)
    section_arc = _dedupe([
        *lyric_profile.get("section_behavior", []),
        *lyric_profile.get("emotional_arc", []),
    ], limit=8)
    imagery = _dedupe(lyric_profile.get("imagery_bank", []), limit=8)
    surface = _dedupe(lyric_profile.get("surface_profile", []), limit=6)
    return {
        "lyric_language_hint": "Japanese lyrics, no meta commentary, hook-forward phrasing",
        "hook_behavior_hint": hook_behavior,
        "section_arc_hint": section_arc,
        "imagery_hint": imagery,
        "surface_hint": surface,
    }


def _build_negative_layer(record: dict[str, Any]) -> dict[str, Any]:
    sound_profile = record.get("sound_profile", {})
    lyric_profile = record.get("lyric_profile", {})
    negative_sound = _dedupe(sound_profile.get("sound_anchors", {}).get("negative", []), limit=8)
    negative_lyric = _dedupe([
        "english summary lines",
        "meta cleanup commentary",
        "generic motivational filler",
        "flat verse-to-chorus transition",
        *["avoid " + item for item in lyric_profile.get("surface_profile", []) if _safe_text(item) == "undetermined"],
    ], limit=8)
    return {
        "exclude_styles": [
            "generic western pop",
            "prompt-shaped filler writing",
            "flat loop-only arrangement",
        ],
        "negative_sound_anchors": negative_sound,
        "negative_lyric_anchors": negative_lyric,
    }


def _build_prompt_asset(record: dict[str, Any]) -> dict[str, Any]:
    identity = record.get("track_identity", {})
    mode = _safe_text((identity.get("mode_candidates") or [""])[0])
    lyric_profile = record.get("lyric_profile", {})
    sound_profile = record.get("sound_profile", {})
    return {
        "schema_version": "1.0",
        "record_type": "suno_prompt_asset",
        "asset_identity": {
            "asset_id": f"{_safe_text(identity.get('track_id'))}_suno_prompt_asset",
            "track_id": _safe_text(identity.get("track_id")),
            "artist_id": _safe_text(identity.get("artist_id")) or "unknown_artist",
            "mode_id": mode,
        },
        "concept_layer": {
            "concept_line": _build_concept_line(record),
            "mood_core": _dedupe([
                *lyric_profile.get("emotional_arc", []),
                _safe_text(sound_profile.get("energy_profile", {}).get("global_energy_level")),
            ], limit=6),
            "story_core": _dedupe([
                *lyric_profile.get("section_behavior", []),
                *lyric_profile.get("imagery_bank", []),
            ], limit=6),
        },
        "sound_prompt_layer": _build_sound_layer(record),
        "lyric_prompt_layer": _build_lyric_layer(record),
        "negative_control_layer": _build_negative_layer(record),
        "optional_generation_controls": {
            "slider_guidance": {
                "style_influence": 0.7,
                "weirdness": 0.45,
                "prompt_influence": 0.75,
            },
            "persona_reuse_hint": "Reuse synthetic vocal character framing only when voicebank color remains coherent.",
            "edit_strategy_hint": "Preserve hook readability, then tighten arrangement and imagery density.",
            "inspire_pool_hint": _dedupe(sound_profile.get("producer_sound_markers", []), limit=4),
        },
    }


def export_suno_prompt_assets(
    *,
    generation_root: Path,
    output_root: Path,
    include_blocked: bool = False,
) -> dict[str, Any]:
    generation_root = generation_root.resolve()
    output_root = output_root.resolve()
    records_dir = generation_root / "records"
    asset_dir = output_root / "records"
    asset_dir.mkdir(parents=True, exist_ok=True)

    assets: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for path in sorted(records_dir.glob("*.json")):
        try:
            record = _load_json(path)
        except Exception as exc:
            skipped.append({"path": str(path), "reason": f"invalid_json:{type(exc).__name__}"})
            continue
        prompt_ready = bool(record.get("prompt_readiness", {}).get("suno_prompt_ready"))
        if not include_blocked and not prompt_ready:
            skipped.append({
                "path": str(path),
                "reason": "prompt_not_ready",
                "blocking_reasons": record.get("prompt_readiness", {}).get("blocking_reasons", []),
            })
            continue
        asset = _build_prompt_asset(record)
        assets.append(asset)
        write_json(asset_dir / f"{asset['asset_identity']['track_id']}.json", asset)

    jsonl_path = write_jsonl(output_root / "suno_prompt_assets.jsonl", assets)
    manifest = {
        "schema_version": "1.0",
        "record_type": "suno_prompt_asset_manifest",
        "generation_root": str(generation_root),
        "output_root": str(output_root),
        "include_blocked": include_blocked,
        "counts": {
            "assets": len(assets),
            "skipped": len(skipped),
        },
        "skipped": skipped,
        "outputs": {
            "jsonl": str(jsonl_path),
            "records_dir": str(asset_dir),
        },
    }
    manifest_path = write_json(output_root / "suno_prompt_asset_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest
