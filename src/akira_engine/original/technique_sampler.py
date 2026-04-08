"""Technique Sampler — Technique Library에서 CreativeDirection에 맞는 기법 컨텍스트 샘플링."""
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

from .direction_parser import CreativeDirection


def _load_library(lib_root: Path) -> dict[str, Any]:
    """5개 JSON 파일을 로드해 통합 라이브러리 반환."""
    library: dict[str, Any] = {}
    for name in [
        "hook_patterns",
        "imagery_archetypes",
        "emotional_arc_templates",
        "structural_templates",
        "syllable_profiles",
    ]:
        path = lib_root / f"{name}.json"
        if path.exists():
            with path.open(encoding="utf-8") as f:
                library[name] = json.load(f)
        else:
            library[name] = {}
    return library


def _match_emotional_arc(direction: CreativeDirection, templates: dict) -> dict:
    """energy_arc에 맞는 감정 아크 템플릿 선택."""
    arcs = templates.get("arcs", [])
    for arc in arcs:
        if arc.get("arc_id") == direction.energy_arc:
            return arc
    # 기본값: build_and_drop
    for arc in arcs:
        if arc.get("arc_id") == "build_and_drop":
            return arc
    return arcs[0] if arcs else {}


def _sample_hook_pattern(direction: CreativeDirection, patterns: dict) -> dict:
    """emotional_tone 및 인덱싱된 통계에 맞는 훅 패턴 샘플링."""
    dist = patterns.get("force_distribution", {})
    if not dist:
        return {"hook_density": "high", "repeat_style": "default"}

    # 조향(climax_point)에 따른 가중치 조정
    target_force = "high"
    if direction.climax_point == "none":
        target_force = "low"
    elif direction.climax_point == "final_chorus":
        target_force = "high"
    else:
        choices = list(dist.keys())
        weights = [float(dist[k]) for k in choices]
        target_force = random.choices(choices, weights=weights, k=1)[0]

    return {
        "hook_density": target_force,
        "repeat_style": "dynamic_sampling_based_on_dna"
    }


def _sample_imagery(direction: CreativeDirection, archetypes: dict) -> list[str]:
    """imagery_hints와 통계 기반 클러스터에서 이미지리 뱅크 구성."""
    bank: set[str] = set(direction.imagery_hints)
    clusters = archetypes.get("clusters", {})
    
    # 조향 키워드가 클러스터 이름과 겹치면 해당 단어들 추가
    for hint in direction.theme_keywords:
        hint_lower = hint.lower()
        if hint_lower in clusters:
            bank.update(random.sample(clusters[hint_lower], min(3, len(clusters[hint_lower]))))

    tone_cluster_map = {
        "dark_and_tender": ["dread", "body_horror"],
        "bittersweet": ["abstract"],
        "detached_ironic": ["cyber"],
        "vulnerable_yet_defiant": ["dread"],
        "urban_lonely": ["cyber"],
        "bright_uplift": ["abstract"],
        "rage_and_release": ["dread", "body_horror"],
        "melancholic_drift": ["abstract"],
    }
    for cluster_key in tone_cluster_map.get(direction.emotional_tone, []):
        if cluster_key in clusters:
            words = clusters[cluster_key]
            bank.update(random.sample(words, min(3, len(words))))

    return list(bank)[:10]


def _select_structure(direction: CreativeDirection, templates: dict) -> list[dict]:
    """11만 건 데이터에서 추출된 템플릿 중 빈도 기반 가중 샘플링."""
    items = templates.get("templates", [])
    if not items:
        return [
            {"section": "Aメロ", "goal": "시점 확립"},
            {"section": "Bメロ", "goal": "긴장 구축"},
            {"section": "サビ", "goal": "감정 해방"},
        ]

    # 빈도수 기반 가중치 추출
    freqs = [float(it.get("observed_frequency", 1)) for it in items]
    selected = random.choices(items, weights=freqs, k=1)[0]
    
    raw_sections = selected.get("sections", [])
    sections = []
    for i, s in enumerate(raw_sections):
        goal = "보컬로이드 문법에 따른 섹션 전개"
        if "chorus" in s or "sabi" in s: goal = "핵심 감정 폭발 및 훅 전달"
        elif "verse" in s: goal = "풍경 묘사 및 화자의 독백"
        elif "intro" in s: goal = "짧고 강렬한 슬로건 또는 분위기 셋업"
        sections.append({"section": s.capitalize(), "goal": goal})
    
    return sections


class TechniqueContext:
    """샘플링된 기법 컨텍스트."""

    def __init__(
        self,
        *,
        hook_pattern: dict,
        imagery_bank: list[str],
        arc_template: dict,
        section_structure: list[dict],
        syllable_profile: dict,
    ) -> None:
        self.hook_pattern = hook_pattern
        self.imagery_bank = imagery_bank
        self.arc_template = arc_template
        self.section_structure = section_structure
        self.syllable_profile = syllable_profile

    def to_prompt_fragment(self) -> str:
        """생성 프롬프트에 삽입될 기법 컨텍스트 텍스트."""
        lines = ["## Technique Context (Subculture DNA Bank Based)"]

        if self.imagery_bank:
            lines.append(f"\n### Imagery Archetypes\n{', '.join(self.imagery_bank)}")

        if self.hook_pattern:
            hd = self.hook_pattern.get("hook_density", "high")
            lines.append(f"\n### Hook Strategy\n- Density: {hd}")

        if self.arc_template:
            arc_desc = self.arc_template.get("description", "")
            if arc_desc:
                lines.append(f"\n### Emotional Arc Template\n{arc_desc}")

        lines.append("\n### Section Blueprint")
        for sec in self.section_structure:
            name = sec.get("section", "")
            goal = sec.get("goal", "")
            lines.append(f"- **{name}**: {goal}")

        if self.syllable_profile:
            avg = self.syllable_profile.get("avg_chars_per_line", 12)
            lines.append(f"\n### Phrasing Intensity\n~{avg} characters per line average (target density)")

        return "\n".join(lines)


def sample_technique_context(
    direction: CreativeDirection,
    *,
    lib_root: Path,
) -> TechniqueContext:
    """CreativeDirection에 맞는 TechniqueContext 샘플링."""
    library = _load_library(lib_root)

    hook_pattern = _sample_hook_pattern(direction, library.get("hook_patterns", {}))
    imagery_bank = _sample_imagery(direction, library.get("imagery_archetypes", {}))
    arc_template = _match_emotional_arc(direction, library.get("emotional_arc_templates", {}))
    section_structure = _select_structure(direction, library.get("structural_templates", {}))

    # 음절 프로파일: language_register 기반 선택
    syllable_profiles = library.get("syllable_profiles", {})
    register = direction.language_register
    syllable_profile = syllable_profiles.get(register) or syllable_profiles.get("colloquial") or {}

    return TechniqueContext(
        hook_pattern=hook_pattern,
        imagery_bank=imagery_bank,
        arc_template=arc_template,
        section_structure=section_structure,
        syllable_profile=syllable_profile,
    )
