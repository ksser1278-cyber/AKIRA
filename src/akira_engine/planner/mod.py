from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.akira_engine.normalize.mod import contains_bad_script, contains_japanese


@dataclass
class SectionCard:
    section: str
    function: str
    required_motifs: list[str] = field(default_factory=list)
    imagery_focus: list[str] = field(default_factory=list)
    required_imagery: list[str] = field(default_factory=list)
    line_target: int = 4
    cadence_target: str = "medium"
    abstraction_ceiling: float = 0.2


@dataclass
class PlanResult:
    track_id: str
    artist_id: str
    mode_id: str
    title_seed: str
    section_cards: list[SectionCard] = field(default_factory=list)
    motif_roster: list[dict[str, Any]] = field(default_factory=list)
    hook_blueprint: dict[str, Any] = field(default_factory=dict)
    status: str = "pending"


def _clean_terms(values: list[Any], fallback: list[str], *, limit: int = 6) -> list[str]:
    cleaned: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text:
            continue
        if not contains_japanese(text):
            continue
        if contains_bad_script(text):
            continue
        if len(text) > 12:
            continue
        if text not in cleaned:
            cleaned.append(text)
        if len(cleaned) >= limit:
            break
    if cleaned:
        return cleaned
    return list(fallback[:limit])


def _atlas_terms(project_root: Path, key: str, fallback: list[str]) -> list[str]:
    atlas_path = project_root / "outputs" / "atlas_v2_trusted.json"
    if not atlas_path.exists():
        return list(fallback)
    try:
        atlas = json.loads(atlas_path.read_text(encoding="utf-8"))
    except Exception:
        return list(fallback)
    values = atlas.get(key, [])
    if not isinstance(values, list):
        return list(fallback)
    return _clean_terms(values, fallback)


def _get_sensory_imagery(mode_id: str, project_root: Path) -> dict[str, list[str]]:
    body = _atlas_terms(project_root, "body", ["鼓動", "指先", "傷", "息", "喉", "体温"])
    scene = _atlas_terms(project_root, "scene", ["街灯", "教室", "路地", "遊園地", "部屋", "夜道"])
    sound = _atlas_terms(project_root, "sound", ["ノイズ", "残響", "警報", "足音", "ざらつき", "反響"])

    def pick(values: list[str], index: int, fallback: str) -> str:
        return values[index % len(values)] if values else fallback

    if mode_id == "dark_cute_breakdown":
        return {
            "intro": _clean_terms(["キャンディ", "遊園地", "笑顔", pick(scene, 3, "遊園地")], ["キャンディ", "遊園地", "笑顔"]),
            "verse_1": _clean_terms([pick(body, 0, "鼓動"), "傷", "玩具", pick(scene, 1, "教室")], ["鼓動", "傷", "玩具"]),
            "pre_chorus": _clean_terms([pick(sound, 0, "ノイズ"), "警報", "胸騒ぎ"], ["ノイズ", "警報", "胸騒ぎ"]),
            "chorus": _clean_terms(["キャンディ", "毒", "グリッチ", pick(body, 2, "体温")], ["キャンディ", "毒", "グリッチ"]),
            "bridge": _clean_terms(["暗室", "沈黙", pick(body, 4, "体温"), pick(sound, 1, "残響")], ["暗室", "沈黙", "残響"]),
            "chorus_final": _clean_terms(["断線", "悲鳴", "破片", pick(body, 5, "鼓動")], ["断線", "悲鳴", "破片"]),
            "outro": _clean_terms([pick(sound, 1, "残響"), pick(scene, 5, "夜道"), "毒"], ["残響", "夜道", "毒"]),
        }

    if mode_id == "direct_emotional_pop":
        return {
            "intro": _clean_terms(["窓", "夜風", "ため息"], ["窓", "夜風", "ため息"]),
            "verse_1": _clean_terms([pick(scene, 0, "街灯"), pick(body, 0, "指先"), "記憶"], ["街灯", "指先", "記憶"]),
            "pre_chorus": _clean_terms(["波音", "体温", "沈黙"], ["波音", "体温", "沈黙"]),
            "chorus": _clean_terms(["涙", "声", "心臓"], ["涙", "声", "心臓"]),
            "bridge": _clean_terms(["静寂", "朝焼け", pick(sound, 1, "残響")], ["静寂", "朝焼け", "残響"]),
            "chorus_final": _clean_terms(["余韻", "鼓動", "光"], ["余韻", "鼓動", "光"]),
            "outro": _clean_terms(["残響", "歩幅", "夜明け"], ["残響", "歩幅", "夜明け"]),
        }

    return {
        "intro": _clean_terms([pick(scene, 0, "街灯"), pick(body, 0, "鼓動"), "息"], ["街灯", "鼓動", "息"]),
        "verse_1": _clean_terms([pick(body, 1, "指先"), "記憶", pick(scene, 1, "路地")], ["指先", "記憶", "路地"]),
        "pre_chorus": _clean_terms([pick(sound, 0, "ノイズ"), "沈黙", "心臓"], ["ノイズ", "沈黙", "心臓"]),
        "chorus": _clean_terms(["声", "残響", "破片"], ["声", "残響", "破片"]),
        "bridge": _clean_terms(["静寂", "暗転", pick(sound, 1, "反響")], ["静寂", "暗転", "反響"]),
        "chorus_final": _clean_terms(["爆発", "余熱", "閃光"], ["爆発", "余熱", "閃光"]),
        "outro": _clean_terms(["残響", "歩幅", "夜明け"], ["残響", "歩幅", "夜明け"]),
    }


def run_planner_stage(
    project_root: Path,
    artist_id: str,
    mode_id: str,
    title_seed: str = "",
) -> PlanResult:
    from src.akira_engine.production_policy import BASELINE_2026_03_31 as Policy

    track_id = f"{artist_id}_{mode_id}_{title_seed or 'demo'}"
    imagery_bank = _get_sensory_imagery(mode_id, project_root)
    sections = ["intro", "verse_1", "pre_chorus", "chorus", "bridge", "chorus_final", "outro"]

    cards: list[SectionCard] = []
    for section in sections:
        focus = imagery_bank.get(section, ["鼓動", "残響"])
        cards.append(
            SectionCard(
                section=section,
                function="narrative" if "verse" in section else "release" if "chorus" in section else "setup",
                required_motifs=list(focus[:2]),
                imagery_focus=list(focus),
                required_imagery=list(focus[:2]) if Policy.MANDATORY_SENSORY_ANCHORS else [],
                line_target=4 if section not in {"chorus_final"} else 5,
                abstraction_ceiling=0.15 if "chorus" in section else 0.25,
            )
        )

    motif_roster = [
        {
            "motif_id": "core_sensory",
            "motifs": list(imagery_bank.get("chorus", ["鼓動", "残響", "破片"]))[:3],
        }
    ]

    hook_core = title_seed if contains_japanese(title_seed) and not contains_bad_script(title_seed) else ""
    return PlanResult(
        track_id=track_id,
        artist_id=artist_id,
        mode_id=mode_id,
        title_seed=title_seed,
        section_cards=cards,
        motif_roster=motif_roster,
        hook_blueprint={
            "core_text": hook_core or "幻灯",
            "hook_density": "medium",
            "chorus_line_target": 4,
        },
        status="planned",
    )
