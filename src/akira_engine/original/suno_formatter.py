"""Suno Formatter — 생성된 가사를 Suno 즉시 사용 가능한 프롬프트로 변환."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .direction_parser import CreativeDirection
from .lyric_generator import GeneratedLyrics
from .quality_scorer import QualityReport
from .section_names import (
    normalize_sections,
    ordered_sections,
    to_display_name,
    CANONICAL_ORDER,
)


# energy_arc → BPM 범위 매핑
_ARC_BPM_MAP: dict[str, tuple[int, int]] = {
    "quiet_then_explosive":   (80,  130),
    "steady_medium":          (110, 135),
    "fast_and_punchy":        (140, 175),
    "slow_then_medium":       (70,  120),
    "medium_pop":             (115, 140),
    "build_and_drop":         (90,  135),
    "flat_circular":          (95,  125),
}

# emotional_tone → 장르/분위기 태그
_TONE_STYLE_MAP: dict[str, list[str]] = {
    "dark_and_tender":      ["emotional J-pop", "introspective", "melodic", "minor key"],
    "bittersweet":          ["J-pop", "bittersweet", "piano ballad", "emotional"],
    "detached_ironic":      ["indie J-pop", "ironic", "quirky", "synth-driven"],
    "vulnerable_yet_defiant": ["pop rock", "emotional", "powerful vocals", "dramatic"],
    "urban_lonely":         ["city pop", "lo-fi", "urban", "melancholic"],
    "bright_uplift":        ["upbeat J-pop", "bright", "anthemic", "energetic"],
    "rage_and_release":     ["rock", "powerful", "cathartic", "distorted guitars"],
    "melancholic_drift":    ["ambient pop", "melancholic", "dreamy", "slow"],
}

# language_register → 보컬 스타일
_REGISTER_VOCAL_MAP: dict[str, list[str]] = {
    "poetic":          ["breathy vocals", "expressive", "controlled vibrato"],
    "colloquial":      ["natural vocals", "conversational tone", "emotionally raw"],
    "young_colloquial": ["youthful vocals", "energetic delivery", "punchy"],
    "mixed":           ["dynamic range", "soft verses sharp chorus"],
    "pop":             ["clean vocals", "catchy delivery", "radio-ready"],
    "formal":          ["theatrical vocals", "dramatic", "classical influence"],
}

# NOTE: Suno 섹션 태그 매핑은 이제 section_names.to_display_name(canonical, style="suno")를 사용합니다.


@dataclass
class SunoPrompt:
    """Suno 완전 포맷 프롬프트."""
    title: str
    style_tags: list[str]
    bpm_range: tuple[int, int]
    vocal_style: list[str]
    structure_notes: list[str]
    suno_lyrics: str          # [Verse]/[Chorus] 포맷
    raw_sections: dict[str, str]
    quality_score: float
    critique_logs: list[str] = field(default_factory=list) # 추가

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "style_prompt": ", ".join(self.style_tags + self.vocal_style),
            "style_tags": self.style_tags,
            "vocal_style": self.vocal_style,
            "bpm_range": {"min": self.bpm_range[0], "max": self.bpm_range[1]},
            "bpm_suggestion": (self.bpm_range[0] + self.bpm_range[1]) // 2,
            "structure_notes": self.structure_notes,
            "quality_score": self.quality_score,
            "suno_lyrics": self.suno_lyrics,
            "raw_sections": self.raw_sections,
        }

    def to_markdown(self) -> str:
        """사람이 읽기 좋은 마크다운 형식."""
        lines = [
            f"# {self.title}",
            "",
            "## Suno Style Prompt",
            f"> {', '.join(self.style_tags + self.vocal_style)}",
            "",
            f"**BPM**: {self.bpm_range[0]}–{self.bpm_range[1]} "
            f"(추천: {(self.bpm_range[0] + self.bpm_range[1]) // 2})",
            "",
        ]
        if self.structure_notes:
            lines += ["## Structure Notes", ""]
            for note in self.structure_notes:
                lines.append(f"- {note}")
            lines.append("")

        lines += [
            f"## Quality Score: {self.quality_score:.1f}/100",
            "",
            "---",
            "",
            "## Lyrics (Suno Format)",
            "",
            self.suno_lyrics,
            "",
            "---",
            "",
            "## Evolution Insight (Self-Critique Logs)",
            "",
        ]
        
        if self.critique_logs:
            for i, log in enumerate(self.critique_logs):
                lines.append(f"### Log {i+1}")
                lines.append(log)
                lines.append("")
        else:
            lines.append("*No specific critique logs recorded for this session.*")

        return "\n".join(lines)


def _build_suno_lyrics(sections: dict[str, str]) -> str:
    """섹션 딕셔너리 → Suno [Tag] 포맷 변환.

    정규화된 canonical 키를 사용하여 Suno 태그로 변환합니다.
    """
    canonical = normalize_sections(sections)
    parts: list[str] = []

    for canonical_key, content in ordered_sections(canonical):
        suno_tag = to_display_name(canonical_key, style="suno")
        parts.append(f"{suno_tag}\n{content}")

    return "\n\n".join(parts)


def _build_structure_notes(
    direction: CreativeDirection,
    lyrics: GeneratedLyrics,
    report: QualityReport,
) -> list[str]:
    """Suno 생성 시 참고할 구조 노트."""
    notes: list[str] = []

    arc = direction.energy_arc
    if arc == "quiet_then_explosive":
        notes.append("Start soft and sparse — build intensity toward final chorus")
    elif arc == "fast_and_punchy":
        notes.append("Drive the tempo from the first bar — keep energy constant")
    elif arc == "slow_then_medium":
        notes.append("Begin with minimal instrumentation — add layers in verse 2")
    elif arc == "build_and_drop":
        notes.append("Classic build-and-drop structure — drop hits at [Chorus]")

    if direction.climax_point == "final_chorus":
        notes.append("Final chorus is the emotional peak — max instrumentation here")

    if report.singability < 0.7:
        notes.append("⚠ Some lines are long — vocalist may need to adjust phrasing")

    return notes


def format_suno_prompt(
    lyrics: GeneratedLyrics,
    direction: CreativeDirection,
    report: QualityReport,
) -> SunoPrompt:
    """GeneratedLyrics → SunoPrompt 변환."""
    # 스타일 태그 조합
    style_tags = _TONE_STYLE_MAP.get(direction.emotional_tone, ["J-pop", "emotional"])
    vocal_style = _REGISTER_VOCAL_MAP.get(direction.language_register, ["natural vocals"])

    # BPM
    bpm_range = _ARC_BPM_MAP.get(direction.energy_arc, (100, 130))

    # Suno 가사 변환
    suno_lyrics = _build_suno_lyrics(lyrics.sections)

    # 구조 노트
    structure_notes = _build_structure_notes(direction, lyrics, report)

    return SunoPrompt(
        title=lyrics.title_suggestion or "無題",
        style_tags=style_tags,
        bpm_range=bpm_range,
        vocal_style=vocal_style,
        structure_notes=structure_notes,
        suno_lyrics=suno_lyrics,
        raw_sections=lyrics.sections,
        quality_score=report.composite_score,
        critique_logs=lyrics.critique_logs,
    )
