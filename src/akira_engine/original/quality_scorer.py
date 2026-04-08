"""Quality Scorer — 아티스트 비종속 오리지널리티 채점 시스템."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .lyric_generator import GeneratedLyrics
from .direction_parser import CreativeDirection


# 너무 일반적인 클리셰 표현 목록 (감점 대상)
_CLICHE_PHRASES = [
    "君のことが好き",
    "夢を追いかけ",
    "頑張れ",
    "永遠に",
    "輝いて",
    "諦めないで",
    "大丈夫",
    "笑顔",
]

# 아티스트명 감지 패턴 (오리지널리티 검증)
_ARTIST_NAME_PATTERN = re.compile(
    r"(pinocchio|deco27|kanaria|kairiki|maretu|iyowa|syudou|neru|vocaloid)",
    re.IGNORECASE,
)

# 라틴 문자 비율 (일본어 퀄리티)
_ASCII_CHAR_PATTERN = re.compile(r"[a-zA-Z]")
_JAPANESE_CHAR_PATTERN = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff]")


@dataclass
class QualityReport:
    """품질 채점 결과."""
    imagery_specificity: float       # 0.0–1.0: 이미지의 구체성
    singability: float               # 0.0–1.0: 라인 길이 및 음절 적절성
    emotional_coherence: float       # 0.0–1.0: 감정 아크 일관성
    structural_integrity: float      # 0.0–1.0: 섹션 구조 완성도
    japanese_quality: float          # 0.0–1.0: 일본어 자연스러움

    cliche_hits: list[str]
    artist_trace_detected: bool
    section_count: int
    avg_line_length: float
    total_lines: int

    @property
    def composite_score(self) -> float:
        """가중 종합 점수 (0–100)."""
        raw = (
            self.imagery_specificity * 0.25
            + self.singability * 0.25
            + self.emotional_coherence * 0.20
            + self.structural_integrity * 0.15
            + self.japanese_quality * 0.15
        )
        score = raw * 100
        # 아티스트 흔적 감지 시 패널티
        if self.artist_trace_detected:
            score -= 15
        # 클리셰 패널티 (개당 -3점)
        score -= len(self.cliche_hits) * 3
        return max(0.0, min(100.0, score))

    @property
    def passes_threshold(self) -> bool:
        return self.composite_score >= 72.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "composite_score": round(self.composite_score, 2),
            "passes_threshold": self.passes_threshold,
            "imagery_specificity": round(self.imagery_specificity, 3),
            "singability": round(self.singability, 3),
            "emotional_coherence": round(self.emotional_coherence, 3),
            "structural_integrity": round(self.structural_integrity, 3),
            "japanese_quality": round(self.japanese_quality, 3),
            "cliche_hits": self.cliche_hits,
            "artist_trace_detected": self.artist_trace_detected,
            "section_count": self.section_count,
            "avg_line_length": round(self.avg_line_length, 1),
            "total_lines": self.total_lines,
            "alerts": self._build_alerts(),
        }

    def _build_alerts(self) -> list[str]:
        alerts = []
        if self.imagery_specificity < 0.5:
            alerts.append("imagery too abstract — add concrete objects or sensory details")
        if self.singability < 0.5:
            alerts.append("singability risk — some lines may be too long or too short")
        if self.emotional_coherence < 0.5:
            alerts.append("emotional coherence weak — arc may feel disconnected")
        if self.structural_integrity < 0.6:
            alerts.append("structural integrity low — key sections may be missing")
        if self.japanese_quality < 0.6:
            alerts.append("japanese quality concern — too much latin script")
        if self.artist_trace_detected:
            alerts.append("ARTIST TRACE DETECTED — review output for style anchoring")
        if self.cliche_hits:
            alerts.append(f"cliche phrases found: {', '.join(self.cliche_hits)}")
        return alerts


def _score_imagery_specificity(lyrics: GeneratedLyrics) -> float:
    """구체적 명사/이미지 밀도 측정."""
    if not lyrics.sections:
        return 0.0

    # 구체적 이미지 신호 단어 (감각적, 물리적)
    concrete_signals = [
        # 신체
        "手", "指", "目", "声", "息", "血", "胸", "骨",
        # 환경
        "雨", "雪", "窓", "夜", "朝", "道", "橋", "部屋",
        # 감각
        "冷たい", "熱い", "白い", "暗い", "重い", "軽い",
        # 사물
        "鍵", "電話", "時計", "鏡", "花", "火", "水",
    ]

    all_text = "\n".join(lyrics.sections.values())
    total_chars = len(all_text.replace("\n", ""))
    if total_chars == 0:
        return 0.0

    hit_count = sum(all_text.count(sig) for sig in concrete_signals)
    # 100자당 2개 이상이면 높은 점수
    ratio = (hit_count / max(total_chars, 1)) * 100
    return min(1.0, ratio / 4.0)


def _score_singability(lyrics: GeneratedLyrics) -> float:
    """음절 밀도 및 라인 길이 채점."""
    all_lines = []
    for content in lyrics.sections.values():
        all_lines.extend([l for l in content.splitlines() if l.strip()])

    if not all_lines:
        return 0.0

    lengths = [len(line.strip()) for line in all_lines]
    avg = sum(lengths) / len(lengths)

    # 8–22자 범위가 이상적
    ideal_count = sum(1 for l in lengths if 6 <= l <= 24)
    too_long = sum(1 for l in lengths if l > 30)
    too_short = sum(1 for l in lengths if l < 4)

    ideal_ratio = ideal_count / len(lengths)
    penalty = (too_long + too_short) / len(lengths)

    return min(1.0, max(0.0, ideal_ratio - penalty * 0.5))


def _score_emotional_coherence(lyrics: GeneratedLyrics, direction: CreativeDirection) -> float:
    """감정 아크 일관성 — 섹션 존재 + climax 구조."""
    if not lyrics.sections:
        return 0.0

    score = 0.0
    sections = set(lyrics.sections.keys())

    # 필수 섹션 존재 여부
    has_verse = any("Aメロ" in s or "verse" in s.lower() for s in sections)
    has_chorus = any("サビ" in s or "chorus" in s.lower() for s in sections)
    has_final = any("最終" in s or "final" in s.lower() for s in sections)
    has_bridge = any("ブリッジ" in s or "bridge" in s.lower() for s in sections)

    if has_verse:
        score += 0.25
    if has_chorus:
        score += 0.3
    if has_final:
        score += 0.25
    if has_bridge:
        score += 0.1

    # 최종 사비가 가장 긴지 확인 (강도 상승)
    if has_final and has_chorus:
        final_len = max(
            (len(v) for k, v in lyrics.sections.items() if "最終" in k or "final" in k.lower()),
            default=0,
        )
        chorus_len = max(
            (len(v) for k, v in lyrics.sections.items() if k in ("サビ", "chorus")),
            default=0,
        )
        if final_len >= chorus_len:
            score += 0.1

    return min(1.0, score)


def _score_structural_integrity(lyrics: GeneratedLyrics) -> float:
    """섹션 구조 완성도."""
    if not lyrics.sections:
        return 0.0

    expected = {"Aメロ", "Bメロ", "サビ", "ブリッジ", "最終サビ"}
    found = set(lyrics.sections.keys())
    overlap = sum(1 for e in expected for f in found if e in f)
    return min(1.0, overlap / len(expected))


def _score_japanese_quality(lyrics: GeneratedLyrics, direction: CreativeDirection) -> float:
    """일본어 비율 및 자연스러움."""
    all_text = "\n".join(lyrics.sections.values())
    if not all_text:
        return 0.0

    jp_chars = len(_JAPANESE_CHAR_PATTERN.findall(all_text))
    ascii_chars = len(_ASCII_CHAR_PATTERN.findall(all_text))
    total = jp_chars + ascii_chars

    if total == 0:
        return 0.5

    jp_ratio = jp_chars / total

    # english_insertion_level에 따라 기준 조정
    if direction.english_insertion_level == "none":
        return min(1.0, jp_ratio / 0.95)
    elif direction.english_insertion_level == "low":
        return min(1.0, jp_ratio / 0.80)
    else:
        return min(1.0, jp_ratio / 0.60)


def score_lyrics(
    lyrics: GeneratedLyrics,
    direction: CreativeDirection,
) -> QualityReport:
    """가사 품질 종합 채점."""
    # 클리셰 감지
    all_text = "\n".join(lyrics.sections.values())
    cliche_hits = [phrase for phrase in _CLICHE_PHRASES if phrase in all_text]

    # 아티스트 흔적 감지
    artist_trace = bool(_ARTIST_NAME_PATTERN.search(all_text + lyrics.full_text))

    # 라인 통계
    all_lines = []
    for content in lyrics.sections.values():
        all_lines.extend([l for l in content.splitlines() if l.strip()])
    avg_line_len = (
        sum(len(l.strip()) for l in all_lines) / len(all_lines) if all_lines else 0.0
    )

    return QualityReport(
        imagery_specificity=_score_imagery_specificity(lyrics),
        singability=_score_singability(lyrics),
        emotional_coherence=_score_emotional_coherence(lyrics, direction),
        structural_integrity=_score_structural_integrity(lyrics),
        japanese_quality=_score_japanese_quality(lyrics, direction),
        cliche_hits=cliche_hits,
        artist_trace_detected=artist_trace,
        section_count=len(lyrics.sections),
        avg_line_length=avg_line_len,
        total_lines=len(all_lines),
    )
