from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .lyric_utils import contains_bad_script, contains_japanese, looks_corrupted_text, safe_text
from .songwriter_io import candidate_content_roots


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out


_LOW_SIGNAL_MODE_SUPPORT_TERMS = {
    "方",
    "感謝",
    "恩",
    "一生",
    "子供",
    "想い",
    "秘め",
    "愛言葉",
    "聴いてくれ",
    "世話になって",
    "誰と",
    "頂戴",
    "なくても",
    "僕は僕を見ない",
    "愛されない",
    "全部あげる",
    "知りたい",
    "好き",
    "大好き",
    "お別れ",
}


def _is_usable_mode_support_term(value: Any, *, max_len: int = 16) -> bool:
    text = safe_text(value)
    if not text:
        return False
    if not contains_japanese(text):
        return False
    if contains_bad_script(text) or looks_corrupted_text(text):
        return False
    compact = re.sub(r"\s+", "", text)
    if len(compact) < 2 or len(compact) > max_len:
        return False
    if text in _LOW_SIGNAL_MODE_SUPPORT_TERMS:
        return False
    if any(marker in text for marker in ("(", ")", "[", "]", "{", "}", "/", ":")):
        return False
    if re.search(r"[A-Za-z0-9]", text):
        return False
    return True


def _clean_mode_support_terms(values: list[Any], *, limit: int, max_len: int = 16) -> list[str]:
    cleaned: list[str] = []
    for value in values:
        text = safe_text(value)
        if not _is_usable_mode_support_term(text, max_len=max_len):
            continue
        if text in cleaned:
            continue
        cleaned.append(text)
        if len(cleaned) >= limit:
            break
    return cleaned


def _resolve_mode_support_audit_path(project_root: Path, mode_id: str) -> Path | None:
    clean_mode_id = str(mode_id or "").strip()
    if not clean_mode_id:
        return None
    for content_root in candidate_content_roots(project_root):
        candidate = (
            content_root
            / "reports"
            / "quality"
            / "mode_support_audit"
            / f"{clean_mode_id}_mode_support_audit.json"
        )
        if candidate.exists():
            return candidate
    return None


def _resolve_content_path(project_root: Path, raw_path: str) -> Path:
    path = Path(str(raw_path or "").strip())
    if path.exists():
        return path

    relative_path: Path | None = None
    candidate_roots = candidate_content_roots(project_root)
    for root in candidate_roots:
        try:
            relative_path = path.relative_to(root)
            break
        except ValueError:
            if root.name in path.parts:
                index = path.parts.index(root.name)
                if index + 1 < len(path.parts):
                    relative_path = Path(*path.parts[index + 1 :])
                    break

    if relative_path:
        for content_root in candidate_roots:
            candidate = content_root / relative_path
            if candidate.exists():
                return candidate
    return path


def load_mode_support_records(
    project_root: Path,
    mode_id: str,
    *,
    current_track_id: str = "",
    minimum_grades: tuple[str, ...] = ("gold", "usable"),
    limit: int = 3,
) -> list[dict[str, Any]]:
    audit_path = _resolve_mode_support_audit_path(project_root, mode_id)
    if not audit_path or not audit_path.exists():
        return []

    audit_payload = _load_json(audit_path)
    selected_records: list[dict[str, Any]] = []
    for item in audit_payload.get("records", []):
        grade = str(item.get("grade", "")).strip().lower()
        path = _resolve_content_path(project_root, str(item.get("path", "")).strip())
        track_id = str(item.get("track_id", "")).strip()
        if grade not in minimum_grades or not path.exists():
            continue
        if current_track_id and track_id == current_track_id:
            continue
        selected_records.append(_load_json(path))
        if len(selected_records) >= limit:
            break
    return selected_records


def load_mode_support_context(
    project_root: Path,
    mode_id: str,
    *,
    current_track_id: str = "",
    minimum_grades: tuple[str, ...] = ("gold", "usable"),
    limit: int = 3,
) -> dict[str, Any]:
    clean_mode_id = str(mode_id or "").strip()
    if not clean_mode_id:
        return {"available": False, "mode_id": clean_mode_id, "records": []}

    selected_records = load_mode_support_records(
        project_root,
        clean_mode_id,
        current_track_id=current_track_id,
        minimum_grades=minimum_grades,
        limit=limit,
    )
    if not selected_records:
        return {"available": False, "mode_id": clean_mode_id, "records": []}

    theme_axes: list[str] = []
    imagery_anchors: list[str] = []
    motif_atoms: list[str] = []
    scene_atoms: list[str] = []
    vocal_tones: list[str] = []
    production_palette: list[str] = []
    energy_arc: list[str] = []
    track_ids: list[str] = []
    artist_ids: list[str] = []

    for record in selected_records:
        identity = record.get("track_identity", {})
        song_intent = record.get("song_intent", {})
        prompt_conditioning = record.get("prompt_conditioning", {})
        section_analysis = record.get("section_analysis", [])
        track_ids.append(str(identity.get("track_id", "")).strip())
        artist_ids.append(str(identity.get("artist_id", "")).strip())
        theme_axes.extend(str(value) for value in song_intent.get("core_theme", []) if value)
        imagery_anchors.extend(str(value) for value in prompt_conditioning.get("imagery_anchors", []) if value)
        motif_atoms.extend(str(value) for value in song_intent.get("key_motifs", []) if value)
        vocal_tones.extend(str(value) for value in prompt_conditioning.get("vocal_tones", []) if value)
        production_palette.extend(str(value) for value in prompt_conditioning.get("production_palette", []) if value)
        energy_arc.extend(str(value) for value in prompt_conditioning.get("energy_arc", []) if value)
        for entry in section_analysis:
            scene_atoms.extend(str(value) for value in entry.get("vocabulary_focus", []) if value)
            summary = str(entry.get("narrative_job", "")).strip()
            if summary:
                scene_atoms.append(summary)

    clean_imagery = _clean_mode_support_terms(imagery_anchors, limit=8, max_len=12)
    clean_motifs = _clean_mode_support_terms(motif_atoms + clean_imagery, limit=10, max_len=12)
    clean_scene_atoms = _clean_mode_support_terms(scene_atoms, limit=8, max_len=18)

    return {
        "available": True,
        "mode_id": clean_mode_id,
        "records": [
            {
                "track_id": str(record.get("track_identity", {}).get("track_id", "")).strip(),
                "artist_id": str(record.get("track_identity", {}).get("artist_id", "")).strip(),
                "title": str(
                    record.get("track_identity", {}).get("title_core")
                    or record.get("track_identity", {}).get("title")
                    or ""
                ).strip(),
            }
            for record in selected_records
        ],
        "theme_axes": _unique(theme_axes)[:6],
        "imagery_anchors": clean_imagery,
        "motif_atoms": clean_motifs,
        "scene_atoms": clean_scene_atoms,
        "vocal_tones": _unique(vocal_tones)[:6],
        "production_palette": _unique(production_palette)[:6],
        "energy_arc": _unique(energy_arc)[:6],
        "artist_ids": _unique(artist_ids),
        "track_ids": _unique(track_ids),
    }
