from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from src.akira_engine.normalize.mod import contains_japanese, contains_bad_script

@dataclass
class SectionCard:
    section: str
    function: str
    required_motifs: list[str] = field(default_factory=list)
    imagery_focus: list[str] = field(default_factory=list)
    required_imagery: list[str] = field(default_factory=list) # vNext Mandatory Anchors
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

def _get_sensory_imagery(mode_id: str, project_root: Path) -> dict[str, list[str]]:
    """Japanese Sensory Bank (Honest Grounding) / Atlas v2 (12k) Integrated."""
    atlas_path = project_root / "outputs" / "atlas_v2_trusted.json"
    atlas = {}
    if atlas_path.exists():
        try:
            with open(atlas_path, "r", encoding="utf-8") as f:
                atlas = json.load(f)
        except: pass
    
    # Body/Scene/Sound from Atlas v2 (12k Verified)
    body = atlas.get("body", ["体温", "喉", "息", "指先", "瞳", "鼓動"])
    scene = atlas.get("scene", ["ガラス", "夜", "影", "窓", "蛍光", "都会"])
    sound = atlas.get("sound", ["ノイズ", "残響", "静寂", "響き"])
    
    # Ensure minimum atom count for distribution
    def _get(lst, idx, default): return lst[idx % len(lst)] if lst else default

    # Mode-Specific distribution
    if mode_id == "dark_cute_breakdown":
        return {
            "intro": [_get(body, 0, "体温"), _get(scene, 0, "ガラス"), "甘いノイズ"],
            "verse_1": [_get(body, 1, "喉"), _get(scene, 1, "夜"), "視線"],
            "pre_chorus": [_get(body, 2, "息"), "鼓動", "めまい"],
            "chorus": ["毒", "熱", "笑顔", _get(body, 3, "指先")],
            "bridge": ["血", "ひび", "反射", _get(scene, 2, "影")],
            "chorus_final": ["落下", "火花", "叫び", "絶望"],
            "outro": ["余熱", "静電気", "残り香", _get(sound, 1, "残響")],
        }
    
    # Default: Use atlas atoms cyclically for high-fidelity grounding
    return {
        "intro": [_get(scene, 3, "窓"), _get(sound, 0, "ノイズ")],
        "verse_1": [_get(body, 4, "瞳"), "視線", _get(scene, 4, "蛍光")],
        "pre_chorus": ["鼓動", "息", _get(body, 5, "腕")],
        "chorus": ["熱", "痛み", _get(scene, 5, "都会"), "境界線"],
        "bridge": ["ひび", "血", _get(sound, 2, "静寂"), "再起動"],
        "chorus_final": ["叫び", "火花", "落下", "再会"],
        "outro": ["余熱", "静けさ", "残り香", _get(sound, 3, "響き")],
    }

def run_planner_stage(
    project_root: Path,
    artist_id: str,
    mode_id: str,
    title_seed: str = "",
) -> PlanResult:
    """Execute Stage F: Planner (Grounded Version)."""
    from src.akira_engine.production_policy import BASELINE_2026_03_31 as Policy
    
    track_id = f"{artist_id}_{mode_id}_{title_seed or 'demo'}"
    imagery_bank = _get_sensory_imagery(mode_id, project_root)
    
    sections = ["intro", "verse_1", "pre_chorus", "chorus", "bridge", "chorus_final", "outro"]
    cards = []
    
    # Baseline Freeze: Policy Driven Grounding
    for s in sections:
        focus = imagery_bank.get(s, ["体温", "視線"])
        cards.append(SectionCard(
            section=s,
            function="narrative" if "verse" in s else "release" if "chorus" in s else "setup",
            required_motifs=[], 
            imagery_focus=focus,
            # Mandatory anchors if policy enforced
            required_imagery=focus[:2] if Policy.MANDATORY_SENSORY_ANCHORS else [],
            line_target=4,
            abstraction_ceiling=0.15 if "chorus" in s else 0.25
        ))
        
    result = PlanResult(
        track_id=track_id,
        artist_id=artist_id,
        mode_id=mode_id,
        title_seed=title_seed,
        section_cards=cards,
        motif_roster=[{"motif_id": "core_sensory", "motifs": ["喉", "視線", "体温"]}],
        hook_blueprint={
            "core_text": title_seed or "...",
            "hook_density": "medium",
            "chorus_line_target": 4
        },
        status="planned"
    )
    return result
