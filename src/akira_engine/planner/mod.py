from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.akira_engine.normalize.mod import contains_bad_script, contains_japanese
from src.akira_engine.section_evidence_bank import build_section_evidence_bank
from src.akira_engine.songwriter_io import load_conditioning_records


@dataclass
class SectionCard:
    section: str
    function: str
    required_motifs: list[str] = field(default_factory=list)
    imagery_focus: list[str] = field(default_factory=list)
    required_imagery: list[str] = field(default_factory=list)
    narrative_goals: list[str] = field(default_factory=list)
    line_target: int = 4
    cadence_target: str = "medium"
    abstraction_ceiling: float = 0.2
    title_drop_policy: str = "sparse"
    hook_pressure: str = "medium"
    evidence_track_ids: list[str] = field(default_factory=list)


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


def _section_blueprint(mode_id: str) -> list[dict[str, Any]]:
    if mode_id == "dark_cute_breakdown":
        return [
            {"section": "intro", "function": "setup", "line_target": 4, "cadence_target": "medium", "abstraction_ceiling": 0.20},
            {"section": "verse_1", "function": "observation", "line_target": 4, "cadence_target": "tight", "abstraction_ceiling": 0.18},
            {"section": "pre_chorus", "function": "glitch_ramp", "line_target": 3, "cadence_target": "tight", "abstraction_ceiling": 0.15},
            {"section": "chorus", "function": "breakdown", "line_target": 4, "cadence_target": "percussive", "abstraction_ceiling": 0.12},
            {"section": "verse_2", "function": "escalation", "line_target": 4, "cadence_target": "tight", "abstraction_ceiling": 0.16},
            {"section": "pre_chorus_2", "function": "glitch_ramp_2", "line_target": 3, "cadence_target": "percussive", "abstraction_ceiling": 0.13},
            {"section": "bridge", "function": "false_lullaby", "line_target": 3, "cadence_target": "broken", "abstraction_ceiling": 0.20},
            {"section": "chorus_final", "function": "collapse_release", "line_target": 6, "cadence_target": "explosive", "abstraction_ceiling": 0.10},
            {"section": "outro", "function": "aftertaste", "line_target": 3, "cadence_target": "cooldown", "abstraction_ceiling": 0.18},
        ]
    if mode_id == "direct_emotional_pop":
        return [
            {"section": "intro", "function": "setup", "line_target": 3, "cadence_target": "medium", "abstraction_ceiling": 0.22},
            {"section": "verse_1", "function": "confession", "line_target": 4, "cadence_target": "flowing", "abstraction_ceiling": 0.20},
            {"section": "pre_chorus", "function": "tension_ramp", "line_target": 3, "cadence_target": "lifting", "abstraction_ceiling": 0.18},
            {"section": "chorus", "function": "emotional_release", "line_target": 4, "cadence_target": "open", "abstraction_ceiling": 0.14},
            {"section": "verse_2", "function": "deepening", "line_target": 4, "cadence_target": "flowing", "abstraction_ceiling": 0.18},
            {"section": "bridge", "function": "exposure", "line_target": 3, "cadence_target": "suspended", "abstraction_ceiling": 0.20},
            {"section": "chorus_final", "function": "final_release", "line_target": 5, "cadence_target": "open", "abstraction_ceiling": 0.12},
            {"section": "outro", "function": "afterglow", "line_target": 3, "cadence_target": "cooldown", "abstraction_ceiling": 0.20},
        ]
    return [
        {"section": "intro", "function": "setup", "line_target": 3, "cadence_target": "medium", "abstraction_ceiling": 0.22},
        {"section": "verse_1", "function": "observation", "line_target": 4, "cadence_target": "medium", "abstraction_ceiling": 0.20},
        {"section": "pre_chorus", "function": "tension_ramp", "line_target": 3, "cadence_target": "tight", "abstraction_ceiling": 0.18},
        {"section": "chorus", "function": "release", "line_target": 4, "cadence_target": "open", "abstraction_ceiling": 0.14},
        {"section": "bridge", "function": "exposure", "line_target": 3, "cadence_target": "broken", "abstraction_ceiling": 0.20},
        {"section": "chorus_final", "function": "final_release", "line_target": 5, "cadence_target": "open", "abstraction_ceiling": 0.12},
        {"section": "outro", "function": "aftertaste", "line_target": 3, "cadence_target": "cooldown", "abstraction_ceiling": 0.20},
    ]


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
    section_blueprint = _section_blueprint(mode_id)
    conditioning_records = load_conditioning_records(artist_id)
    evidence_bank = build_section_evidence_bank(conditioning_records, mode_id=mode_id)
    section_evidence = evidence_bank.get("sections", {})

    cards: list[SectionCard] = []
    for spec in section_blueprint:
        section = spec["section"]
        evidence = section_evidence.get(section, {})
        focus = list(evidence.get("imagery_focus") or imagery_bank.get(section, ["鼓動", "残響"]))
        required_motifs = list(evidence.get("required_motifs") or focus[:2])
        required_imagery = list(evidence.get("required_imagery") or focus[:2])
        narrative_goals = list(evidence.get("narrative_goals") or [])
        cards.append(
            SectionCard(
                section=section,
                function=str(spec["function"]),
                required_motifs=required_motifs[:4],
                imagery_focus=list(focus),
                required_imagery=required_imagery[:4] if Policy.MANDATORY_SENSORY_ANCHORS else [],
                narrative_goals=narrative_goals[:3],
                line_target=max(int(spec["line_target"]), int(evidence.get("line_target", 0) or 0)),
                cadence_target=str(evidence.get("cadence_target") or spec["cadence_target"]),
                abstraction_ceiling=float(evidence.get("abstraction_ceiling") or spec["abstraction_ceiling"]),
                title_drop_policy=str(
                    evidence.get("title_drop_policy")
                    or ("primary" if section == "chorus_final" else "anchor" if section == "chorus" else "sparse")
                ),
                hook_pressure=str(evidence.get("hook_pressure") or ("high" if "chorus" in section else "medium")),
                evidence_track_ids=list(evidence.get("evidence_track_ids") or []),
            )
        )

    motif_roster = [
        {
            "motif_id": "core_sensory",
            "motifs": list(
                evidence_bank.get("global_motifs")
                or imagery_bank.get("chorus", ["鼓動", "残響", "破片"])
            )[:6],
        }
    ]

    hook_core = title_seed if contains_japanese(title_seed) and not contains_bad_script(title_seed) else ""
    hook_blueprint = {
        "core_text": hook_core or "幻灯",
        "hook_density": "high" if mode_id == "dark_cute_breakdown" else "medium",
        "chorus_line_target": 4,
        "repetition_pressure": "high" if mode_id == "dark_cute_breakdown" else "medium",
    }
    hook_blueprint.update(evidence_bank.get("hook_blueprint", {}))
    hook_blueprint["core_text"] = hook_core or hook_blueprint.get("core_text") or "幻灯"
    return PlanResult(
        track_id=track_id,
        artist_id=artist_id,
        mode_id=mode_id,
        title_seed=title_seed,
        section_cards=cards,
        motif_roster=motif_roster,
        hook_blueprint=hook_blueprint,
        status="planned",
    )
