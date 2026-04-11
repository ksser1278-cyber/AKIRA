from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median
from typing import Any

from .conditioning_brief_dataset import canonical_section
from .mode_support_runtime import load_mode_support_context
from .lyric_utils import (
    unique_preserve_order,
    contains_japanese,
    contains_bad_script,
    looks_corrupted_text,
    safe_text,
    extract_japanese_lexical_atoms,
)
from .section_evidence_bank import build_section_evidence_bank
from .songwriter_io import (
    candidate_content_roots,
    load_artist_profile,
    load_conditioning_records,
    load_generated_mode_assignments,
    resolve_primary_mode,
    resolve_default_track_id,
    matching_conditioning_record,
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))




def _top(values: list[str], limit: int) -> list[str]:
    counts = Counter(value for value in values if str(value or "").strip())
    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [value for value, _ in ordered[:limit]]


def _is_weak_narrative_goal(value: str) -> bool:
    text = safe_text(value)
    if not text:
        return True
    lowered = text.lower()
    if lowered.startswith("standard ") and lowered.endswith(" flow"):
        return True
    if lowered in {
        "intro",
        "verse_1",
        "verse_2",
        "pre_chorus",
        "pre_chorus_2",
        "chorus",
        "chorus_final",
        "bridge",
        "outro",
    }:
        return True
    if not contains_japanese(text):
        generic_english_prefixes = (
            "sets the ",
            "standard ",
            "drives the ",
            "explosive delivery",
            "highest energy state",
            "subverts expectations",
            "introduces ",
            "keeps the ",
            "final release",
        )
        if lowered.startswith(generic_english_prefixes):
            return True
    return False


def _unique(values: list[str]) -> list[str]:
    return unique_preserve_order([safe_text(value) for value in values if safe_text(value)])




def _clean_demo_terms(values: list[str], limit: int) -> list[str]:
    cleaned: list[str] = []
    for value in values:
        text = safe_text(value)
        if not text:
            continue
        if not _is_usable_runtime_atom(text, max_len=12):
            continue
        cleaned.append(text)
        if len(cleaned) >= limit:
            break
    return _unique(cleaned)


def _clean_demo_phrase(value: Any, *, max_len: int = 24) -> str:
    text = safe_text(value)
    if not text:
        return ""
    if not _is_clean_japanese_surface(text):
        return ""
    if len(text.replace(" ", "")) > max_len:
        return ""
    return text


_CLEAN_JAPANESE_SURFACE_PATTERN = re.compile(r"^[\u3040-\u30ff\u3400-\u9fff々ー・、。！？「」『』（）\s]+$")
_WEAK_HOOK_TOKENS = {
    "言い",
    "在り",
    "逃げ",
    "記憶",
    "始まり",
    "始まりまし",
    "理想",
    "夜道",
    "体温",
    "残響",
    "訳",
    "ニンゲン",
    "見下し",
    "物足り",
    "空振り",
    "理想論",
    "タカラモノ",
}
_WEAK_RUNTIME_SUFFIXES = (
    "まし",
    "ですか",
    "でした",
    "する",
    "した",
    "して",
    "ます",
    "です",
    "ない",
    "たい",
    "よう",
    "られ",
    "れる",
    "せる",
    "だっ",
    "とか",
    "だけ",
    "ほど",
    "より",
    "から",
)
_MODE_HOOK_FALLBACKS: dict[str, list[str]] = {
    "dark_cute_breakdown": ["飴の罰", "毒遊び", "笑う毒", "玩具熱", "甘い傷"],
    "direct_emotional_pop": ["夜の窓", "残響灯", "心拍線", "朝の傷", "薄明"],
    "default": ["幻灯", "残響灯", "夜歩き", "薄明", "余熱"],
}


def _is_clean_japanese_surface(value: Any) -> bool:
    text = safe_text(value)
    if not text:
        return False
    if not contains_japanese(text):
        return False
    if contains_bad_script(text) or looks_corrupted_text(text):
        return False
    return bool(_CLEAN_JAPANESE_SURFACE_PATTERN.fullmatch(text))


def _is_usable_runtime_atom(value: Any, *, max_len: int = 12) -> bool:
    text = safe_text(value)
    if not _is_clean_japanese_surface(text):
        return False
    compact = text.replace(" ", "").replace("　", "")
    if not (2 <= len(compact) <= max_len):
        return False
    lowered = compact.lower()
    if compact in _WEAK_HOOK_TOKENS:
        return False
    if any(token in lowered or token in compact for token in _RUNTIME_META_BLOCKLIST):
        return False
    if compact.endswith(_WEAK_RUNTIME_SUFFIXES):
        return False
    if re.search(r"[\u3400-\u9fff々][\u3040-\u309f]{2,}$", compact):
        return False
    if re.fullmatch(r"[\u3040-\u309f]+", compact) and len(compact) <= 3:
        return False
    return True


def _is_strong_runtime_hook(value: Any) -> bool:
    text = safe_text(value)
    if not _is_usable_runtime_atom(text, max_len=8):
        return False
    compact = text.replace(" ", "")
    if re.fullmatch(r"[\u3040-\u309f]+", compact):
        return len(compact) >= 4
    return True


def _derive_runtime_hook(
    *,
    mode: str,
    title_seed: str,
    conditioning_atoms: dict[str, Any],
    motifs: list[str],
) -> str:
    if _is_strong_runtime_hook(title_seed):
        return safe_text(title_seed)

    trusted_track_id = safe_text(conditioning_atoms.get("track_id"))
    candidates: list[str] = []
    if trusted_track_id:
        for key in ("title_atoms", "hook_atoms"):
            raw = conditioning_atoms.get(key, [])
            if isinstance(raw, list):
                candidates.extend([safe_text(item) for item in raw if safe_text(item)])
        for candidate in candidates:
            if _is_strong_runtime_hook(candidate):
                return candidate

    fallbacks = _MODE_HOOK_FALLBACKS.get(mode, _MODE_HOOK_FALLBACKS["default"])
    for candidate in fallbacks:
        if _is_strong_runtime_hook(candidate):
            return candidate
    return "幻灯"


def _clean_demo_phrase_list(values: list[Any], *, limit: int, max_len: int = 24) -> list[str]:
    cleaned: list[str] = []
    for value in values:
        text = _clean_demo_phrase(value, max_len=max_len)
        if not text:
            continue
        cleaned.append(text)
        if len(cleaned) >= limit:
            break
    return _unique(cleaned)


def _sanitize_archetype_sections(sections: dict[str, str]) -> dict[str, str]:
    sanitized: dict[str, str] = {}
    for key, value in sections.items():
        text = safe_text(value)
        if not text:
            continue
        kept_lines: list[str] = []
        for raw_line in text.splitlines():
            line = raw_line.rstrip()
            stripped = line.strip()
            if not stripped:
                continue
            if contains_bad_script(stripped) or looks_corrupted_text(stripped):
                continue
            kept_lines.append(line)
        if kept_lines:
            sanitized[safe_text(key)] = "\n".join(kept_lines)
    return sanitized


def _sanitize_archetype_context(context: dict[str, Any]) -> dict[str, Any]:
    payload = dict(context)
    payload["artist_sections"] = _sanitize_archetype_sections(
        payload.get("artist_sections", {}) if isinstance(payload.get("artist_sections", {}), dict) else {}
    )
    payload["mode_sections"] = _sanitize_archetype_sections(
        payload.get("mode_sections", {}) if isinstance(payload.get("mode_sections", {}), dict) else {}
    )
    return payload


def _sanitize_section_card(card: dict[str, Any]) -> dict[str, Any]:
    section = safe_text(card.get("section"))
    required_motifs = _clean_demo_phrase_list(list(card.get("required_motifs", [])), limit=6, max_len=12)
    required_imagery = _clean_demo_phrase_list(list(card.get("required_imagery", [])), limit=4, max_len=12)
    imagery_focus = _clean_demo_phrase_list(list(card.get("imagery_focus", [])), limit=4, max_len=12)
    emotion_focus = _clean_demo_phrase_list(list(card.get("emotion_focus", [])), limit=3, max_len=16)
    narrative_goals = [
        safe_text(item)
        for item in card.get("narrative_goals", [])
        if safe_text(item) and not contains_bad_script(safe_text(item)) and not looks_corrupted_text(safe_text(item))
    ][:3]
    scene = _clean_demo_phrase(card.get("scene"), max_len=12)
    if not scene:
        scene = (required_imagery or imagery_focus or required_motifs or [""])[0]
    goal = safe_text(card.get("goal"))
    if not goal or contains_bad_script(goal) or looks_corrupted_text(goal):
        goal = section or "section"
    return {
        **card,
        "section": section,
        "canonical_section": safe_text(card.get("canonical_section") or section),
        "goal": goal,
        "required_motifs": required_motifs,
        "required_imagery": required_imagery,
        "scene": scene,
        "emotion_focus": emotion_focus or ([goal] if goal else []),
        "narrative_goals": narrative_goals or ([goal] if goal else []),
        "imagery_focus": imagery_focus,
    }


_RUNTIME_META_BLOCKLIST = {
    "タイトル",
    "フック",
    "コーラス",
    "ブリッジ",
    "ヴァース",
    "セクション",
    "歌詞",
    "title",
    "hook",
    "chorus",
    "bridge",
    "verse",
    "section",
    "lyric",
}

_RUNTIME_ATOM_TRIM_SUFFIXES = (
    "という",
    "とは",
    "とか",
    "だって",
    "まで",
    "だけ",
    "ほど",
    "より",
    "から",
    "たり",
    "です",
    "ます",
    "ない",
    "たい",
    "の",
    "は",
    "が",
    "を",
    "へ",
    "で",
    "と",
    "も",
    "か",
    "よ",
    "ね",
    "な",
    "だ",
    "た",
)


def _trim_runtime_atom(text: str) -> str:
    atom = safe_text(text)
    if not atom:
        return ""
    changed = True
    while changed:
        changed = False
        for suffix in _RUNTIME_ATOM_TRIM_SUFFIXES:
            if atom.endswith(suffix) and len(atom) - len(suffix) >= 2:
                atom = atom[: -len(suffix)]
                changed = True
                break
    return atom


def _safe_runtime_atoms(values: list[Any], *, limit: int = 8, max_len: int = 8) -> list[str]:
    atoms: list[str] = []
    for value in values:
        text = safe_text(value)
        if not text or contains_bad_script(text):
            continue
        for atom in extract_japanese_lexical_atoms([text], limit=6):
            cleaned = _trim_runtime_atom(atom)
            if cleaned:
                atoms.append(cleaned)
        if contains_japanese(text) and " " not in text and "　" not in text:
            cleaned = _trim_runtime_atom(text)
            if cleaned:
                atoms.append(cleaned)

    cleaned_atoms: list[str] = []
    for atom in unique_preserve_order(atoms):
        if not _is_usable_runtime_atom(atom, max_len=max_len):
            continue
        cleaned_atoms.append(atom)
        if len(cleaned_atoms) >= limit:
            break
    return cleaned_atoms


def _conditioning_runtime_atoms(artist_id: str, mode_id: str, title_seed: str) -> dict[str, Any]:
    records = load_conditioning_records(artist_id)
    if not records:
        return {
            "track_id": "",
            "title_atoms": [],
            "hook_atoms": [],
            "motifs": [],
            "contrast_terms": [],
        }

    normalized_title_seed = re.sub(r"\s+", "", safe_text(title_seed)).lower()
    best_record: dict[str, Any] | None = None
    best_key: tuple[int, int, int, float] | None = None
    for record in records:
        generation_safety = record.get("generation_safety", {}) if isinstance(record.get("generation_safety", {}), dict) else {}
        verdict = safe_text(generation_safety.get("verdict"))
        if verdict not in {"planner_safe", "benchmark_safe"}:
            continue
        roles = record.get("song_intent", {}).get("narrative_role", [])
        if isinstance(roles, str):
            roles = [roles]
        role_list = [safe_text(item) for item in roles if safe_text(item)]
        identity = record.get("track_identity", {}) if isinstance(record.get("track_identity", {}), dict) else {}
        title_candidates = [
            safe_text(identity.get("title_core")),
            safe_text(identity.get("title")),
            safe_text(identity.get("track_id")),
        ]
        normalized_candidates = {
            re.sub(r"\s+", "", candidate).lower()
            for candidate in title_candidates
            if candidate
        }
        lyric = record.get("lyric_ground_truth", {}) if isinstance(record.get("lyric_ground_truth", {}), dict) else {}
        hook_lines = lyric.get("hook_lines", [])
        if not isinstance(hook_lines, list):
            hook_lines = []
        if not hook_lines and not any(contains_japanese(candidate) and not contains_bad_script(candidate) for candidate in title_candidates):
            continue
        title_match = 1 if normalized_title_seed and normalized_title_seed in normalized_candidates else 0
        mode_match = 1 if mode_id and mode_id in role_list else 0
        benchmark_bonus = 1 if verdict == "benchmark_safe" else 0
        score = float(generation_safety.get("score", 0.0) or 0.0)
        key = (title_match, mode_match, benchmark_bonus, score)
        if best_key is None or key > best_key:
            best_key = key
            best_record = record

    if not best_record:
        return {
            "track_id": "",
            "title_atoms": [],
            "hook_atoms": [],
            "motifs": [],
            "contrast_terms": [],
        }

    identity = best_record.get("track_identity", {}) if isinstance(best_record.get("track_identity", {}), dict) else {}
    lyric = best_record.get("lyric_ground_truth", {}) if isinstance(best_record.get("lyric_ground_truth", {}), dict) else {}
    sections = lyric.get("sections", [])
    if not isinstance(sections, list):
        sections = []

    title_values = [
        identity.get("title_core"),
        identity.get("title"),
    ]
    hook_values: list[Any] = list(lyric.get("hook_lines", [])[:3]) if isinstance(lyric.get("hook_lines", []), list) else []
    section_values: list[Any] = []
    for section in sections[:3]:
        if not isinstance(section, dict):
            continue
        lines = section.get("lines", [])
        if isinstance(lines, list):
            section_values.extend(lines[:2])
    contrast_device = best_record.get("song_intent", {}).get("contrast_device", [])
    if isinstance(contrast_device, str):
        contrast_values = [contrast_device]
    elif isinstance(contrast_device, list):
        contrast_values = contrast_device
    else:
        contrast_values = []

    title_atoms = _safe_runtime_atoms(title_values + hook_values[:1], limit=3, max_len=8)
    hook_atoms = _safe_runtime_atoms(title_values + hook_values + section_values, limit=6, max_len=8)
    motifs = _safe_runtime_atoms(hook_values + section_values + contrast_values, limit=8, max_len=8)
    contrast_terms = _safe_runtime_atoms(contrast_values, limit=4, max_len=8)
    return {
        "track_id": safe_text(identity.get("track_id")),
        "title_atoms": title_atoms,
        "hook_atoms": hook_atoms,
        "motifs": motifs,
        "contrast_terms": contrast_terms,
    }


def _section_goal_defaults(mode_id: str) -> dict[str, list[str]]:
    if mode_id == "direct_emotional_pop":
        return {
            "intro": ["空気を立ち上げる", "感情の温度を置く"],
            "verse_1": ["関係の圧を示す", "身体反応を先に置く"],
            "pre_chorus": ["緊張を圧縮する", "後戻りできない状態へ寄せる"],
            "chorus": ["感情を解放する", "タイトルを核に束ねる"],
            "verse_2": ["傷の具体を見せる", "関係の歪みを深める"],
            "pre_chorus_2": ["再加速する", "言い逃れを潰す"],
            "bridge": ["本音を露出させる", "最終解放の前に剥がす"],
            "chorus_final": ["最終解放に入る", "タイトルを確定させる"],
            "outro": ["余熱を残す"],
        }
    if mode_id == "dark_cute_breakdown":
        return {
            "intro": ["不穏な甘さを置く"],
            "verse_1": ["可愛さの裏の痛みを見せる", "触れた傷を置く"],
            "pre_chorus": ["崩壊の兆候を寄せる"],
            "chorus": ["甘さと毒を同時に出す", "タイトルを傷に結ぶ"],
            "verse_2": ["依存と拒絶を混ぜる"],
            "pre_chorus_2": ["崩れを加速する"],
            "bridge": ["傷をむき出しにする"],
            "chorus_final": ["落下を確定させる", "後戻り不能にする"],
            "outro": ["不穏さを残す"],
        }
    return {
        "intro": ["皮肉の空気を置く"],
        "verse_1": ["観察と違和感を並べる", "表面の顔を剥がす"],
        "pre_chorus": ["息苦しさを圧縮する"],
        "chorus": ["皮肉を標語化する", "タイトルを核にする"],
        "verse_2": ["本音の漏れを見せる"],
        "pre_chorus_2": ["建前を追い込む"],
        "bridge": ["仮面を一度外す"],
        "chorus_final": ["開き直りで押し切る", "タイトルを再固定する"],
        "outro": ["残響だけ残す"],
    }


def _delivery_from_function(function_name: str, section_name: str) -> str:
    function_key = safe_text(function_name)
    if function_key in {"breakdown", "collapse_release", "emotional_release", "final_release", "release"}:
        return "release"
    if function_key in {"glitch_ramp", "glitch_ramp_2", "tension_ramp"}:
        return "lift"
    if function_key in {"false_lullaby", "exposure"}:
        return "break"
    if "chorus" in safe_text(section_name):
        return "release"
    return "narrative"


def _section_imagery_defaults(mode_id: str) -> dict[str, list[str]]:
    if mode_id == "dark_cute_breakdown":
        return {
            "intro": ["蛍光", "体温", "甘いノイズ"],
            "verse_1": ["爪", "傷跡", "視線"],
            "pre_chorus": ["息", "鼓動", "めまい"],
            "chorus": ["毒", "熱", "笑顔"],
            "verse_2": ["ガラス", "しびれ", "残響"],
            "pre_chorus_2": ["脈", "まぶた", "ノイズ"],
            "bridge": ["血", "ひび", "反射"],
            "chorus_final": ["落下", "火花", "叫び"],
            "outro": ["余熱", "静電気", "残り香"],
        }
    if mode_id == "direct_emotional_pop":
        return {
            "intro": ["雨", "指先", "夜明け"],
            "verse_1": ["息", "喉", "窓"],
            "pre_chorus": ["鼓動", "沈黙", "体温"],
            "chorus": ["声", "涙", "光"],
            "verse_2": ["靴音", "影", "痛み"],
            "pre_chorus_2": ["熱", "まばたき", "ざわめき"],
            "bridge": ["傷", "血流", "祈り"],
            "chorus_final": ["叫び", "閃光", "震え"],
            "outro": ["余韻", "呼吸", "ぬくもり"],
        }
    return {
        "intro": ["ネオン", "沈黙", "体温"],
        "verse_1": ["視線", "喉", "雑音"],
        "pre_chorus": ["鼓動", "息", "ひずみ"],
        "chorus": ["熱", "痛み", "光"],
        "verse_2": ["影", "雨粒", "残響"],
        "pre_chorus_2": ["めまい", "ノイズ", "脈"],
        "bridge": ["ひび", "血", "反射"],
        "chorus_final": ["叫び", "火花", "落下"],
        "outro": ["余熱", "静けさ", "残り香"],
    }


def _load_markdown_sections(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    sections: dict[str, list[str]] = {}
    current = "preamble"
    sections[current] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        # Support both # and ## for sections to capture detailed archetypes
        if line.startswith("# ") or line.startswith("## "):
            # Strip both levels and cleaning numbering (e.g. "1. Core Identity" -> "Core Identity")
            header_text = line.lstrip("#").strip()
            # Remove leading numbers and dots (e.g. "1. ")
            current = re.sub(r"^\d+\.\s*", "", header_text)
            sections[current] = []
            continue
        sections.setdefault(current, []).append(line)
    return {
        key: "\n".join(value).strip()
        for key, value in sections.items()
        if "\n".join(value).strip()
    }


_REQUIRED_ARCHETYPE_FIELDS = (
    "core_identity",
    "title_patterns",
    "hook_construction",
    "verse_behavior",
    "bridge_final_chorus_behavior",
    "common_imagery",
    "emotional_arc_types",
    "leakage_risks",
    "safe_originality_zone",
)


def _has_structured_content(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return value is not None


_CANONICAL_ARCHETYPE_FIELD_TYPES: dict[str, tuple[type, ...]] = {
    "core_identity": (list,),
    "title_patterns": (list,),
    "hook_construction": (dict,),
    "verse_behavior": (dict,),
    "bridge_final_chorus_behavior": (dict,),
    "common_imagery": (list,),
    "emotional_arc_types": (list,),
    "leakage_risks": (dict,),
    "safe_originality_zone": (list,),
}


def _is_valid_canonical_archetype(payload: dict[str, Any]) -> bool:
    if not isinstance(payload, dict):
        return False
    for key in _REQUIRED_ARCHETYPE_FIELDS:
        value = payload.get(key)
        expected_types = _CANONICAL_ARCHETYPE_FIELD_TYPES.get(key, ())
        if expected_types and not isinstance(value, expected_types):
            return False
        if not _has_structured_content(value):
            return False
    return True


def _canonical_archetype_to_sections(payload: dict[str, Any]) -> dict[str, str]:
    title_lines = [
        f"- pattern: {safe_text(item.get('pattern_id') or item.get('description'), 'unknown')} | "
        f"strength: {safe_text(item.get('strength'), 'unknown')} | "
        f"risk: {safe_text(item.get('leakage_risk'), 'unknown')}"
        for item in payload.get("title_patterns", [])
        if isinstance(item, dict)
    ]
    hook = payload.get("hook_construction", {}) if isinstance(payload.get("hook_construction"), dict) else {}
    verse = payload.get("verse_behavior", {}) if isinstance(payload.get("verse_behavior"), dict) else {}
    bridge = (
        payload.get("bridge_final_chorus_behavior", {})
        if isinstance(payload.get("bridge_final_chorus_behavior"), dict)
        else {}
    )
    leakage = payload.get("leakage_risks", {}) if isinstance(payload.get("leakage_risks"), dict) else {}

    def _bullet_block(values: Any) -> str:
        if isinstance(values, list):
            return "\n".join(f"- {safe_text(item)}" for item in values if safe_text(item))
        return ""

    sections = {
        "Core Identity": _bullet_block(payload.get("core_identity", [])),
        "Title Patterns": "\n".join(title_lines),
        "Hook Construction": "\n".join(
            [
                f"- density: {safe_text(hook.get('density'))}",
                f"- ignition: {safe_text(hook.get('ignition'))}",
                f"- repetition: {safe_text(hook.get('repetition'))}",
                f"- line_length: {safe_text(hook.get('line_length'))}",
            ]
            + [f"- forbidden: {safe_text(item)}" for item in hook.get("forbidden", []) if safe_text(item)]
        ).strip(),
        "Verse Behavior": "\n".join(
            [f"- role: {safe_text(item)}" for item in verse.get("role", []) if safe_text(item)]
            + [f"- stance: {safe_text(item)}" for item in verse.get("stance", []) if safe_text(item)]
            + [
                f"- pace: {safe_text(verse.get('pace'))}",
                f"- shift_pattern: {safe_text(verse.get('shift_pattern'))}",
            ]
        ).strip(),
        "Bridge Final Chorus Behavior": "\n".join(
            [
                f"- bridge_role: {safe_text(bridge.get('bridge_role'))}",
                f"- final_chorus_role: {safe_text(bridge.get('final_chorus_role'))}",
            ]
            + [
                f"- release_marker: {safe_text(item)}"
                for item in bridge.get("release_markers", [])
                if safe_text(item)
            ]
        ).strip(),
        "Common Imagery": _bullet_block(payload.get("common_imagery", [])),
        "Emotional Arc Types": _bullet_block(payload.get("emotional_arc_types", [])),
        "Leakage Risks": "\n".join(
            f"- {category}: {', '.join(safe_text(item) for item in values if safe_text(item))}"
            for category, values in leakage.items()
            if isinstance(values, list) and any(safe_text(item) for item in values)
        ).strip(),
        "Safe Originality Zone": _bullet_block(payload.get("safe_originality_zone", [])),
    }
    return {key: value for key, value in sections.items() if safe_text(value)}


def _load_artist_archetype_sections(project_root: Path, artist_id: str) -> tuple[dict[str, str], str, str]:
    invalid_paths: list[str] = []
    for content_root in candidate_content_roots(project_root):
        base = content_root / "data" / "_global" / "artist_archetypes"
        artist_dir = base / artist_id
        json_path = artist_dir / "archetype.json"
        md_path = artist_dir / "archetype.md"
        if not json_path.exists():
            json_path = base / f"{artist_id}_archetype.json"
        if not md_path.exists():
            md_path = base / f"{artist_id}_archetype.md"

        if json_path.exists():
            try:
                payload = _load_json(json_path)
                if _is_valid_canonical_archetype(payload):
                    return _canonical_archetype_to_sections(payload), str(json_path), "json"
            except (OSError, json.JSONDecodeError, TypeError, ValueError):
                invalid_paths.append(str(json_path))

        if md_path.exists():
            return _load_markdown_sections(md_path), str(md_path), "markdown"

    if invalid_paths:
        return {}, invalid_paths[0], "json_invalid"
    return {}, "", ""


def _audit_records(audit_path: Path, minimum_grades: tuple[str, ...], *, limit: int | None = None) -> list[dict[str, Any]]:
    if not audit_path.exists():
        return []
    payload = _load_json(audit_path)
    results: list[dict[str, Any]] = []
    for item in payload.get("records", []):
        grade = str(item.get("grade", "")).strip().lower()
        record_path = Path(str(item.get("path", "")).strip())
        if grade not in minimum_grades or not record_path.exists():
            continue
        record = _load_json(record_path)
        record["_audit_grade"] = grade
        record["_audit_score"] = float(item.get("score", 0))
        results.append(record)
        if limit is not None and len(results) >= limit:
            break
    return results


def _filter_tracks(records: list[dict[str, Any]], allowed_track_ids: set[str]) -> list[dict[str, Any]]:
    if not allowed_track_ids:
        return list(records)
    return [
        record
        for record in records
        if safe_text(record.get("track_identity", {}).get("track_id")) in allowed_track_ids
    ]


def _conditioning_track_id(record: dict[str, Any]) -> str:
    return safe_text(record.get("track_identity", {}).get("track_id"))


def _conditioning_score(record: dict[str, Any]) -> float:
    qc = record.get("quality_control", {})
    for key in ("critic_score", "quality_score", "score"):
        try:
            value = float(qc.get(key, 0.0))
        except (TypeError, ValueError):
            value = 0.0
        if value > 0:
            return value
    return 0.0


def _prompt_ready_conditioning_records(
    project_root: Path,
    artist_id: str,
    mode_id: str,
    *,
    expansion_limit: int = 6,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Backward-compatible wrapper for the canonical high-trust loader."""
    from .conditioning.mod import load_trusted_conditioning_records
    return load_trusted_conditioning_records(artist_id, expansion_limit=expansion_limit)


def _derive_title_patterns(records: list[dict[str, Any]]) -> list[str]:
    patterns: list[str] = []
    for record in records:
        title = safe_text(record.get("track_identity", {}).get("title_core") or record.get("track_identity", {}).get("title"))
        lyric = record.get("lyric_ground_truth", {})
        hooks = lyric.get("hook_lines", [])
        questions = lyric.get("question_lines", [])
        if not title:
            continue
        if len(title) <= 6:
            patterns.append("compact_title")
        else:
            patterns.append("phrase_title")
        if any(title in str(line) for line in hooks):
            patterns.append("title_bound_hook")
        if questions:
            patterns.append("question_pressure")
        if record.get("japanese_lyric_profile", {}).get("title_ignition_style") == "formulaic":
            patterns.append("formulaic_title_drop")
        if record.get("japanese_lyric_profile", {}).get("title_ignition_style") == "ironic":
            patterns.append("ironic_title_drop")
    return _top(patterns, 5)


def _derive_hook_blueprint(records: list[dict[str, Any]], mode_support_context: dict[str, Any]) -> dict[str, Any]:
    hook_counts: list[int] = []
    repetition_counts: list[int] = []
    hook_forces: list[str] = []
    title_styles: list[str] = []
    line_targets: list[int] = []

    for record in records:
        lyric = record.get("lyric_ground_truth", {})
        jp_profile = record.get("japanese_lyric_profile", {})
        hook_counts.append(len(lyric.get("hook_lines", [])))
        repetition_counts.append(len(lyric.get("repetition_patterns", [])))
        hook_forces.append(safe_text(jp_profile.get("hook_copy_force"), "medium"))
        title_styles.append(safe_text(jp_profile.get("title_ignition_style"), "direct"))
        for section in lyric.get("sections", []):
            if str(section.get("section_type", "")).strip() == "chorus":
                line_targets.append(len(section.get("lines", [])))

    dominant_hook_force = _top(hook_forces, 1)[0] if hook_forces else "medium"
    dominant_title_style = _top(title_styles, 1)[0] if title_styles else "direct"
    line_target = int(round(median(line_targets))) if line_targets else 4

    return {
        "hook_density": "high" if dominant_hook_force in {"high", "heavy"} else "medium",
        "title_ignition_style": dominant_title_style,
        "chorus_line_target": max(3, line_target),
        "hook_line_target": max(2, int(round(median(hook_counts)))) if hook_counts else 2,
        "repetition_pressure": "high" if sum(repetition_counts) >= max(2, len(records)) else "medium",
        "mode_support_bias": {
            "theme_axes": list(mode_support_context.get("theme_axes", [])),
            "motif_atoms": list(mode_support_context.get("motif_atoms", []))[:6],
        },
    }


def _derive_section_cards(records: list[dict[str, Any]], mode_id: str) -> list[dict[str, Any]]:
    evidence_bank = build_section_evidence_bank(records, mode_id=mode_id)
    section_evidence = evidence_bank.get("sections", {})
    preferred_order = [
        "intro",
        "verse_1",
        "pre_chorus",
        "chorus",
        "verse_2",
        "pre_chorus_2",
        "bridge",
        "chorus_final",
        "outro",
    ]
    goal_defaults = _section_goal_defaults(mode_id)
    imagery_defaults = _section_imagery_defaults(mode_id)
    cards: list[dict[str, Any]] = []

    def default_line_target(section_name: str) -> int:
        if section_name == "chorus_final":
            return 6
        if section_name in {"intro", "pre_chorus", "pre_chorus_2", "bridge", "outro"}:
            return 3
        if "chorus" in section_name:
            return 4
        return 4

    mandated = {"intro", "verse_1", "chorus", "bridge", "chorus_final", "outro"}
    if mode_id == "dark_cute_breakdown":
        mandated |= {"pre_chorus", "verse_2", "pre_chorus_2"}
    elif mode_id == "direct_emotional_pop":
        mandated |= {"pre_chorus", "verse_2"}
    
    for section_name in preferred_order:
        evidence = section_evidence.get(section_name, {})
        if not evidence and section_name not in mandated:
            continue
            
        cleaned_imagery = _clean_demo_terms(
            list(evidence.get("imagery_focus", [])),
            limit=4,
        ) or imagery_defaults.get(section_name, ["Standard Tension Flow"])
        goals = [
            safe_text(goal)
            for goal in evidence.get("narrative_goals", [])
            if safe_text(goal)
        ]
        if not goals or all(_is_weak_narrative_goal(goal) for goal in goals):
            goals = goal_defaults.get(section_name, [section_name])
        line_target = max(default_line_target(section_name), int(evidence.get("line_target", 0) or 0))
        phrase_energy_roles = [
            safe_text(value)
            for value in evidence.get("phrase_energy_roles", [])
            if safe_text(value)
        ][:2]
        title_drop_roles = [
            safe_text(value)
            for value in evidence.get("title_drop_roles", [])
            if safe_text(value)
        ][:2]
        if not evidence:
            line_target = default_line_target(section_name)
            phrase_energy_roles = []
            title_drop_roles = []

        cards.append(
            {
                "section": section_name,
                "line_target": line_target,
                "narrative_goals": goals,
                "imagery_focus": cleaned_imagery,
                "phrase_energy_roles": phrase_energy_roles,
                "title_drop_roles": title_drop_roles,
                "evidence_track_ids": list(evidence.get("evidence_track_ids", [])),
                "title_drop_policy": safe_text(evidence.get("title_drop_policy")),
                "hook_pressure": safe_text(evidence.get("hook_pressure"), "medium"),
            }
        )
    return cards


def _derive_leakage_guardrails(
    artist_id: str,
    anchor_records: list[dict[str, Any]],
    expansion_records: list[dict[str, Any]],
    representative_profile: dict[str, Any],
) -> dict[str, Any]:
    titles = [
        safe_text(record.get("track_identity", {}).get("title_core") or record.get("track_identity", {}).get("title"))
        for record in anchor_records + expansion_records
    ]
    track_ids = [
        safe_text(record.get("track_identity", {}).get("track_id"))
        for record in anchor_records + expansion_records
    ]
    forbidden_patterns = [
        "Do not reuse any full anchor hook line verbatim.",
        "Do not mirror a single anchor title-drop pattern across every chorus.",
        "Do not let one track-specific object noun dominate the whole song.",
    ]
    if artist_id == "deco27":
        forbidden_patterns.append("Avoid over-binding the title to one direct confession anchor.")
    if artist_id == "pinocchiop":
        forbidden_patterns.append("Avoid slogan irony that maps too closely to one public-facing anchor hook.")

    return {
        "forbidden_track_ids": _unique(track_ids),
        "forbidden_titles": _unique(titles),
        "representative_default_track_id": safe_text(representative_profile.get("default_demo_track_id")),
        "risk_patterns": forbidden_patterns,
        "safe_originality_rule": "Use shared artist/mode rules, but do not lift one anchor's hook skeleton intact.",
    }


def _resolve_existing_relative_path(project_root: Path, relative_path: Path) -> Path | None:
    for content_root in candidate_content_roots(project_root):
        candidate = content_root / relative_path
        if candidate.exists():
            return candidate
    return None


def _find_artist_profile(project_root: Path, artist_id: str) -> Path:
    candidate = _resolve_existing_relative_path(
        project_root,
        Path("artists") / artist_id / "representative_demo_profile.json",
    )
    if not candidate:
        raise FileNotFoundError(
            f"Representative demo profile not found under content roots for artist_id={artist_id}"
        )
    return candidate


def _load_archetype_context(project_root: Path, artist_id: str, mode_id: str) -> dict[str, Any]:
    artist_ids = [aid.strip() for aid in str(artist_id).split("+") if aid.strip()]
    
    combined_artist_sections: dict[str, str] = {}
    combined_paths: list[str] = []
    combined_sources: list[str] = []
    
    for aid in artist_ids:
        sections, source_path, source_format = _load_artist_archetype_sections(project_root, aid)
        if sections:
            if source_path:
                combined_paths.append(source_path)
            if source_format:
                combined_sources.append(f"{aid}:{source_format}")
            for key, val in sections.items():
                if key in combined_artist_sections:
                    combined_artist_sections[key] += f"\n\n--- [{aid} context] ---\n{val}"
                else:
                    combined_artist_sections[key] = val
                    
    mode_path = _resolve_existing_relative_path(
        project_root,
        Path("data") / "_global" / "mode_archetypes" / f"{mode_id}.md",
    )
    mode_sections = _load_markdown_sections(mode_path) if mode_path else {}
    
    return {
        "artist_archetype_path": "; ".join(combined_paths),
        "artist_archetype_source": "; ".join(combined_sources),
        "mode_archetype_path": str(mode_path) if mode_path and mode_path.exists() else "",
        "artist_sections": combined_artist_sections,
        "mode_sections": mode_sections,
        "available": bool(combined_artist_sections or mode_sections),
        "is_hybrid": len(artist_ids) > 1
    }


def build_demo_plan(
    project_root: Path,
    artist_id: str,
    *,
    mode_id: str | None = None,
    intent: str = "",
    title_seed: str = "",
    conditioning_record: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artist_ids = [aid.strip() for aid in str(artist_id).split("+") if aid.strip()]
    primary_id = artist_ids[0]
    
    profile_path = _find_artist_profile(project_root, primary_id)
    representative_profile = _load_json(profile_path)
    effective_mode_id = safe_text(mode_id) or safe_text(representative_profile.get("mode_priority", ["ironic_meta"])[0])
    archetype_context = _sanitize_archetype_context(
        _load_archetype_context(project_root, artist_id, effective_mode_id)
    )

    all_anchor_records: list[dict[str, Any]] = []
    all_expansion_records: list[dict[str, Any]] = []

    if conditioning_record:
        runtime_track_id = safe_text(conditioning_record.get("track_identity", {}).get("track_id"))
        runtime_allowed_layers = (
            conditioning_record.get("generation_safety", {}).get("allowed_layers", {})
            if isinstance(conditioning_record.get("generation_safety", {}), dict)
            else {}
        )
        runtime_is_real_track = runtime_track_id and not runtime_track_id.endswith("_conditioning_vnext")
        runtime_is_anchor_safe = bool(runtime_allowed_layers.get("planner")) and runtime_is_real_track

        if conditioning_record.get("use_for_grounding", True) and runtime_is_anchor_safe:
            all_anchor_records = [conditioning_record]
            all_expansion_records = [conditioning_record]
        else:
            all_expansion_records = [conditioning_record]

    if not all_anchor_records:
        for aid in artist_ids:
            active_audit_path = _resolve_existing_relative_path(
                project_root,
                Path("reports") / "quality" / "conditioning" / f"{aid}_conditioning_audit_active.json",
            )
            expansion_audit_path = _resolve_existing_relative_path(
                project_root,
                Path("reports") / "quality" / "conditioning" / f"{aid}_producer_expansion_audit.json",
            )
            
            anchors = _audit_records(active_audit_path, ("gold",)) if active_audit_path else []
            expansions = _audit_records(expansion_audit_path, ("gold", "usable"), limit=6) if expansion_audit_path else []

            if not anchors or not expansions:
                fallback_anchors, fallback_expansions = _prompt_ready_conditioning_records(
                    project_root,
                    aid,
                    effective_mode_id,
                    expansion_limit=6,
                )
                if not anchors:
                    anchors = fallback_anchors
                if not expansions:
                    expansions = fallback_expansions
            
            all_anchor_records.extend(anchors)
            all_expansion_records.extend(expansions)

    if not all_anchor_records:
        raise ValueError(f"No anchor records available for artist synthesis: {artist_id}")

    anchor_records = all_anchor_records
    expansion_records = all_expansion_records

    core_anchor_ids = {
        safe_text(item.get("track_id"))
        for item in representative_profile.get("core_anchor_tracks", [])
        if safe_text(item.get("mode_id")) == effective_mode_id
    }
    # Only filter primary artist's anchors if they exist in the aggregate
    if core_anchor_ids:
        filtered_anchor_records = _filter_tracks(anchor_records, core_anchor_ids)
        if filtered_anchor_records:
            anchor_records = filtered_anchor_records

    if not anchor_records:
        raise ValueError(f"No anchor records available for artist_id={artist_id}")

    mode_support_context = load_mode_support_context(
        project_root,
        effective_mode_id,
        current_track_id="",
        minimum_grades=("gold", "usable"),
        limit=4,
    )

    artist_names = _unique(
        [safe_text(record.get("track_identity", {}).get("artist_name")) for record in anchor_records]
    )
    theme_axes = _top(
        [
            str(value)
            for record in anchor_records + expansion_records
            for value in record.get("song_intent", {}).get("core_theme", [])
            if value
        ]
        + list(mode_support_context.get("theme_axes", [])),
        10,
    )
    imagery_anchors = _clean_demo_phrase_list(
        [
            str(value)
            for record in anchor_records + expansion_records
            for value in record.get("prompt_conditioning", {}).get("imagery_anchors", [])
            if value
        ]
        + list(mode_support_context.get("imagery_anchors", [])),
        limit=12,
        max_len=12,
    )
    vocal_tones = _clean_demo_phrase_list(
        [
            str(value)
            for record in anchor_records + expansion_records
            for value in record.get("prompt_conditioning", {}).get("vocal_tones", [])
            if value
        ]
        + list(mode_support_context.get("vocal_tones", [])),
        limit=8,
        max_len=16,
    )
    production_palette = _clean_demo_phrase_list(
        [
            str(value)
            for record in anchor_records + expansion_records
            for value in record.get("prompt_conditioning", {}).get("production_palette", [])
            if value
        ]
        + list(mode_support_context.get("production_palette", [])),
        limit=8,
        max_len=16,
    )
    energy_arc = _top(
        [
            str(value)
            for record in anchor_records + expansion_records
            for value in record.get("prompt_conditioning", {}).get("energy_arc", [])
            if value
        ]
        + list(mode_support_context.get("energy_arc", [])),
        8,
    )

    title_patterns = _derive_title_patterns(anchor_records + expansion_records)
    section_evidence_bank = build_section_evidence_bank(anchor_records + expansion_records, mode_id=effective_mode_id)
    hook_blueprint = _derive_hook_blueprint(anchor_records + expansion_records, mode_support_context)
    hook_blueprint.update(section_evidence_bank.get("hook_blueprint", {}))
    section_cards = [
        _sanitize_section_card(card)
        for card in _derive_section_cards(anchor_records + expansion_records, effective_mode_id)
    ]
    leakage_guardrails = _derive_leakage_guardrails(
        artist_id,
        anchor_records,
        expansion_records,
        representative_profile,
    )

    seed_phrases = _clean_demo_phrase_list(
        [
            str(value)
            for record in anchor_records + expansion_records
            for value in record.get("song_intent", {}).get("key_motifs", [])
            if value
        ]
        + list(mode_support_context.get("motif_atoms", []))
        + list(mode_support_context.get("scene_atoms", [])),
        limit=12,
        max_len=12,
    )

    return {
        "schema_version": "1.0",
        "record_type": "artist_demo_plan",
        "planner_version": "demo_planner_v2_dataset_driven",
        "artist_id": artist_id,
        "artist_display_name": artist_names[0] if artist_names else artist_id,
        "mode_id": effective_mode_id,
        "intent": safe_text(intent, "Create a new demo song that sounds artist-faithful without copying one anchor track."),
        "title_seed": safe_text(title_seed),
        "representative_profile_path": str(profile_path),
        "archetype_context": archetype_context,
        "evidence": {
            "anchor_track_ids": [
                safe_text(record.get("track_identity", {}).get("track_id")) for record in anchor_records
            ],
            "producer_expansion_track_ids": [
                safe_text(record.get("track_identity", {}).get("track_id")) for record in expansion_records
            ],
            "mode_support_track_ids": list(mode_support_context.get("track_ids", [])),
            "mode_support_artists": list(mode_support_context.get("artist_ids", [])),
        },
        "composite_style": {
            "theme_axes": theme_axes,
            "imagery_anchors": imagery_anchors,
            "vocal_tones": vocal_tones,
            "production_palette": production_palette,
            "energy_arc": energy_arc,
            "title_patterns": title_patterns,
            "seed_phrases": seed_phrases,
        },
        "hook_blueprint": hook_blueprint,
        "section_cards": section_cards,
        "section_evidence": {
            "record_count": int(section_evidence_bank.get("record_count", 0) or 0),
            "selected_track_ids": list(section_evidence_bank.get("selected_track_ids", [])),
            "available_sections": sorted(section_evidence_bank.get("sections", {}).keys()),
        },
        "mode_support_context": mode_support_context,
        "leakage_guardrails": leakage_guardrails,
        "generation_notes": [
            "Use artist-level common evidence, not one anchor track's exact hook lines.",
            "Let title-binding come from title pattern and hook density, not from direct title reuse.",
            "Use mode support only as secondary evidence; anchor leakage is a higher-priority risk.",
            "Prefer archetype-safe originality zones over any single-track imitation.",
        ],
    }


def render_demo_plan_report(plan: dict[str, Any]) -> str:
    lines = [
        f"# Demo Plan: {plan['artist_id']} / {plan['mode_id']}",
        "",
        f"- Planner: `{plan['planner_version']}`",
        f"- Artist: `{plan['artist_display_name']}`",
        f"- Mode: `{plan['mode_id']}`",
        f"- Intent: {plan['intent']}",
    ]
    if plan.get("title_seed"):
        lines.append(f"- Title seed: `{plan['title_seed']}`")
    lines.extend(
        [
            "",
            "## Archetype Context",
            f"- Artist archetype: {plan['archetype_context'].get('artist_archetype_path') or 'none'}",
            f"- Mode archetype: {plan['archetype_context'].get('mode_archetype_path') or 'none'}",
        ]
    )
    artist_core = safe_text(plan["archetype_context"].get("artist_sections", {}).get("Core Identity"))
    mode_core = safe_text(plan["archetype_context"].get("mode_sections", {}).get("Core Definition"))
    artist_safe = safe_text(plan["archetype_context"].get("artist_sections", {}).get("Safe Originality Zone"))
    mode_safe = safe_text(plan["archetype_context"].get("mode_sections", {}).get("Safe Originality Zone"))
    if artist_core:
        lines.append(f"- Artist core: {artist_core.splitlines()[0]}")
    if mode_core:
        lines.append(f"- Mode core: {mode_core.splitlines()[0]}")
    if artist_safe:
        lines.append(f"- Artist safe originality: {artist_safe.splitlines()[0]}")
    if mode_safe:
        lines.append(f"- Mode safe originality: {mode_safe.splitlines()[0]}")
    lines.extend(
        [
            "",
            "## Evidence",
            f"- Anchors: {', '.join(plan['evidence']['anchor_track_ids'])}",
            f"- Producer expansion: {', '.join(plan['evidence']['producer_expansion_track_ids']) or 'none'}",
            f"- Mode support: {', '.join(plan['evidence']['mode_support_track_ids']) or 'none'}",
            "",
            "## Composite Style",
            f"- Theme axes: {', '.join(plan['composite_style']['theme_axes'])}",
            f"- Imagery anchors: {', '.join(plan['composite_style']['imagery_anchors'])}",
            f"- Vocal tones: {', '.join(plan['composite_style']['vocal_tones'])}",
            f"- Production palette: {', '.join(plan['composite_style']['production_palette'])}",
            f"- Energy arc: {', '.join(plan['composite_style']['energy_arc'])}",
            f"- Title patterns: {', '.join(plan['composite_style']['title_patterns'])}",
            "",
            "## Hook Blueprint",
            f"- Hook density: `{plan['hook_blueprint']['hook_density']}`",
            f"- Title ignition style: `{plan['hook_blueprint']['title_ignition_style']}`",
            f"- Chorus line target: `{plan['hook_blueprint']['chorus_line_target']}`",
            f"- Hook line target: `{plan['hook_blueprint']['hook_line_target']}`",
            f"- Repetition pressure: `{plan['hook_blueprint']['repetition_pressure']}`",
            "",
            "## Section Cards",
        ]
    )
    for card in plan.get("section_cards", []):
        lines.append(
            f"- `{card['section']}`: lines `{card['line_target']}`, goals `{', '.join(card['narrative_goals']) or 'n/a'}`, imagery `{', '.join(card['imagery_focus']) or 'n/a'}`"
        )
    lines.extend(
        [
            "",
            "## Leakage Guardrails",
            f"- Forbidden tracks: {', '.join(plan['leakage_guardrails']['forbidden_track_ids'])}",
            f"- Forbidden titles: {', '.join(plan['leakage_guardrails']['forbidden_titles'])}",
            f"- Safe originality rule: {plan['leakage_guardrails']['safe_originality_rule']}",
        ]
    )
    for rule in plan["leakage_guardrails"].get("risk_patterns", []):
        lines.append(f"- Risk: {rule}")
    return "\n".join(lines) + "\n"





def _rotating_take(items: list[str], count: int, offset: int) -> list[str]:
    if not items:
        return []
    out = []
    for i in range(count):
        out.append(items[(offset + i) % len(items)])
    return out


def normalize_demo_plan_for_runtime(plan: dict[str, Any], vnext_plan: Any | None = None) -> dict[str, Any]:
    mode = safe_text(plan.get("mode_id"))
    artist_id = safe_text(plan.get("artist_id"))
    title_seed = safe_text(plan.get("title_seed"))
    composite = plan.get("composite_style", {}) or {}
    leakage = plan.get("leakage_guardrails", {}) or {}
    artist_profile = load_artist_profile(artist_id) or {}
    clean_theme_axes = _unique(
        [
            safe_text(value)
            for value in composite.get("theme_axes", [])
            if safe_text(value)
            and not contains_bad_script(safe_text(value))
            and not looks_corrupted_text(safe_text(value))
        ]
    )[:10]
    clean_energy_arc = _unique(
        [
            safe_text(value)
            for value in composite.get("energy_arc", [])
            if safe_text(value)
            and not contains_bad_script(safe_text(value))
            and not looks_corrupted_text(safe_text(value))
        ]
    )[:8]

    seed_phrases = _clean_demo_terms(composite.get("seed_phrases", []), limit=12)
    imagery = _clean_demo_terms(composite.get("imagery_anchors", []), limit=12)
    conditioning_atoms = _conditioning_runtime_atoms(artist_id, mode, title_seed)
    motifs = _unique(seed_phrases + imagery)
    if not motifs:
        motifs = list(conditioning_atoms.get("motifs", []))
    if not motifs:
        motifs = _MODE_HOOK_FALLBACKS.get(mode, _MODE_HOOK_FALLBACKS["default"])[:3]

    fallback_hook = _derive_runtime_hook(
        mode=mode,
        title_seed=title_seed,
        conditioning_atoms=conditioning_atoms,
        motifs=motifs,
    )
    track_id = title_seed or safe_text(conditioning_atoms.get("track_id")) or f"{artist_id}_{mode}_demo"
    title_atoms = [atom for atom in conditioning_atoms.get("title_atoms", []) if _is_usable_runtime_atom(atom, max_len=8)]
    hook_atoms = [atom for atom in conditioning_atoms.get("hook_atoms", []) if _is_usable_runtime_atom(atom, max_len=8)]
    contrast_terms = [
        atom for atom in conditioning_atoms.get("contrast_terms", []) if _is_usable_runtime_atom(atom, max_len=8)
    ]
    clean_required_images = imagery[:3]

    # Map vNext structural cards if plan exists
    vnext_card_map: dict[str, dict[str, Any]] = {}
    if vnext_plan:
        cards = vnext_plan.section_cards if hasattr(vnext_plan, "section_cards") else vnext_plan.get("section_cards", [])
        for vc in cards:
            s_name = vc.section if hasattr(vc, "section") else vc.get("section")
            if not s_name:
                continue
            vnext_card_map[s_name] = {
                "function": vc.function if hasattr(vc, "function") else vc.get("function", ""),
                "required_imagery": list(vc.required_imagery) if hasattr(vc, "required_imagery") else list(vc.get("required_imagery", [])),
                "required_motifs": list(vc.required_motifs) if hasattr(vc, "required_motifs") else list(vc.get("required_motifs", [])),
                "narrative_goals": list(vc.narrative_goals) if hasattr(vc, "narrative_goals") else list(vc.get("narrative_goals", [])),
                "line_target": vc.line_target if hasattr(vc, "line_target") else vc.get("line_target", 0),
                "cadence_target": vc.cadence_target if hasattr(vc, "cadence_target") else vc.get("cadence_target", ""),
                "abstraction_ceiling": vc.abstraction_ceiling if hasattr(vc, "abstraction_ceiling") else vc.get("abstraction_ceiling", 0.0),
                "title_drop_policy": vc.title_drop_policy if hasattr(vc, "title_drop_policy") else vc.get("title_drop_policy", ""),
                "hook_pressure": vc.hook_pressure if hasattr(vc, "hook_pressure") else vc.get("hook_pressure", ""),
                "evidence_track_ids": list(vc.evidence_track_ids) if hasattr(vc, "evidence_track_ids") else list(vc.get("evidence_track_ids", [])),
            }

    normalized_cards: list[dict[str, Any]] = []
    for idx, card in enumerate(plan.get("section_cards", [])):
        s_name = safe_text(card.get("section"))
        vnext_meta = vnext_card_map.get(s_name, {})
        goals = [
            safe_text(x)
            for x in card.get("narrative_goals", [])
            if safe_text(x)
            and not contains_bad_script(safe_text(x))
            and not looks_corrupted_text(safe_text(x))
        ]
        if not goals or all(_is_weak_narrative_goal(goal) for goal in goals):
            goals = list(_section_goal_defaults(mode).get(s_name, [s_name]))
        vnext_goals = [
            goal
            for goal in _clean_demo_phrase_list(list(vnext_meta.get("narrative_goals", [])), limit=3, max_len=48)
            if not _is_weak_narrative_goal(goal)
        ]
        if vnext_goals:
            goals = _unique(vnext_goals + goals)
        imagery_terms = _clean_demo_phrase_list(list(card.get("imagery_focus", [])), limit=4, max_len=12)
        if not imagery_terms:
            imagery_terms = _rotating_take(imagery, 2, idx)
        emotion_terms = _clean_demo_phrase_list(goals, limit=2, max_len=16)
        section_motifs = _unique(imagery_terms + _rotating_take(motifs, 2, idx * 2))
        if not section_motifs:
            section_motifs = _rotating_take(motifs, 2, idx * 2)
        vnext_required_motifs = _clean_demo_phrase_list(list(vnext_meta.get("required_motifs", [])), limit=4, max_len=12)
        if vnext_required_motifs:
            section_motifs = _unique(vnext_required_motifs + section_motifs)
        section_scene = imagery_terms[0] if imagery_terms else (motifs[(idx + 5) % len(motifs)] if motifs else "")
        if s_name == "chorus_final":
            section_motifs = _unique([fallback_hook] + section_motifs)
            if not section_scene and fallback_hook != "...":
                section_scene = fallback_hook
        required_imagery = _clean_demo_phrase_list(list(vnext_meta.get("required_imagery", [])), limit=4, max_len=12)
        if not required_imagery:
            required_imagery = imagery_terms[:2]
        function_name = safe_text(vnext_meta.get("function"), "release" if "chorus" in s_name else "narrative")
        line_target = int(vnext_meta.get("line_target", 0) or card.get("line_target", 4) or 4)
        cadence_target = safe_text(vnext_meta.get("cadence_target"), "medium")
        abstraction_ceiling = float(vnext_meta.get("abstraction_ceiling", 0.18) or 0.18)
        title_drop_policy = safe_text(vnext_meta.get("title_drop_policy")) or (
            "primary"
            if s_name == "chorus_final"
            else "anchor"
            if s_name == "chorus"
            else "withhold"
            if "pre_chorus" in s_name or s_name == "bridge"
            else "sparse"
        )
        hook_pressure = safe_text(vnext_meta.get("hook_pressure"), "medium")

        normalized_cards.append(
            {
                "section": s_name,
                "canonical_section": s_name,
                "goal": goals[0] if goals else s_name,
                "line_target": line_target,
                "required_motifs": section_motifs,
                "required_imagery": required_imagery,
                "scene": section_scene,
                "emotion_focus": emotion_terms or goals[:2],
                "narrative_goals": goals,
                "imagery_focus": imagery_terms,
                "delivery": _delivery_from_function(function_name, s_name),
                "function": function_name,
                "cadence_target": cadence_target,
                "abstraction_ceiling": abstraction_ceiling,
                "title_drop_policy": title_drop_policy,
                "hook_pressure": hook_pressure,
                "evidence_track_ids": list(vnext_meta.get("evidence_track_ids", [])),
                "phrase_energy_roles": list(card.get("phrase_energy_roles", [])),
                "title_drop_roles": list(card.get("title_drop_roles", [])),
            }
        )

    ordered_headers = [f"[{card['section']}]" for card in normalized_cards if safe_text(card.get("section"))]
    hook_density = safe_text(plan.get("hook_blueprint", {}).get("hook_density"), "medium")
    title_ignition_style = safe_text(plan.get("hook_blueprint", {}).get("title_ignition_style"), "direct")
    sanitized_demo_plan = {
        **plan,
        "composite_style": {
            **(plan.get("composite_style", {}) or {}),
            "theme_axes": clean_theme_axes,
            "imagery_anchors": imagery,
            "seed_phrases": seed_phrases,
            "energy_arc": clean_energy_arc,
        },
        "section_cards": normalized_cards,
    }
    return {
        **plan,
        "track_id": track_id,
        "primary_mode": mode,
        "motif_roster": [
            {
                "motif_id": "seed_motifs",
                "motifs": motifs[:8],
            }
        ],
        "hook_blueprint": {
            **(plan.get("hook_blueprint", {}) or {}),
            "core_text": fallback_hook,
            "hook_density": hook_density,
        },
        "hook_density": hook_density,
        "artist_profile": artist_profile,
        "theme_axes": clean_theme_axes,
        "dominant_emotions": clean_theme_axes[:4],
        "voice": {
            "voice": "first_person",
            "address": "second_person",
        },
        "arc_label": " -> ".join(clean_energy_arc[:3]) or mode,
        "form_profile": {
            "section_order": [card["section"] for card in normalized_cards],
            "tags": [mode, "artist_demo"],
            "target_line_total": sum(int(card.get("line_target", 0) or 0) for card in normalized_cards),
        },
        "conditioning_context": {
            "available": True,
            "track_id": safe_text(conditioning_atoms.get("track_id")),
            "contrast_device": clean_theme_axes[:3],
            "dramatic_arc": clean_energy_arc[:4],
            "phrase_source_types": ["artist_demo_plan"],
            "hook_copy_force": hook_density,
            "title_ignition_style": title_ignition_style,
            "critic_focus": ["title binding", "motif landing", "final release"],
            "title_atoms": title_atoms or ([fallback_hook] if fallback_hook != "..." else []),
            "hook_atoms": hook_atoms or (([fallback_hook] if fallback_hook != "..." else []) + motifs[:3]),
            "contrast_terms": contrast_terms,
        },
        "final_release_requirements": {
            "must_be_clearer_than_chorus": True,
            "must_introduce_forward_motion": True,
            "release_markers": ["ここから", "最後まで", "壊していく", "終わらせない", "手放さない"],
            "required_new_images": clean_required_images,
        },
        "output_contract": {
            "title_line": f"# {fallback_hook}",
            "ordered_headers": ordered_headers,
            "format_rules": [
                "Use the required markdown section headers in order.",
                "Keep all lyric lines in Japanese.",
                "Do not omit chorus_final.",
            ],
        },
        "constraints": {
            "language": "Japanese",
        },
        "artist_synthesis_context": {
            "demo_plan": sanitized_demo_plan,
            "forbidden_titles": list(leakage.get("forbidden_titles", [])),
        },
        "section_cards": normalized_cards,
    }
