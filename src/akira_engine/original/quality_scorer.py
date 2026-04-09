"""Quality Scorer — 아티스트 비종속 오리지널리티 채점 시스템."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .section_names import (
    normalize_sections,
    structural_completeness,
    VERSE_1, PRE_CHORUS, CHORUS, BRIDGE, FINAL_CHORUS,
)

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
    """서브컬처 DNA 기반 품질 채점 결과."""
    imagery_specificity: float       # 0.0–1.0: 고해상도 어휘 사용 밀도
    singability: float               # 0.0–1.0: 리듬 밀도 (Subculture에서는 고밀도 가점)
    emotional_coherence: float       # 0.0–1.0: 감정 아크 및 서사 긴장감
    structural_integrity: float      # 0.0–1.0: 섹션 구조 및 리듬 그리드 준수
    japanese_quality: float          # 0.0–1.0: 일본어 고해상도 한자 밀도

    cliche_hits: list[str]
    artist_trace_detected: bool
    section_count: int
    avg_line_length: float
    total_lines: int
    critique_memo: str = ""          # 자가 진화 비평 메모

    @property
    def composite_score(self) -> float:
        """Subculture Density Index (SDI) - 0-100."""
        # 서브컬처 가사에서는 Singability(밀도)와 Imagery(고해상도 어휘)에 70% 가중치 부여
        raw = (
            self.imagery_specificity * 0.35
            + self.singability * 0.35
            + self.emotional_coherence * 0.10
            + self.structural_integrity * 0.10
            + self.japanese_quality * 0.10
        )
        score = raw * 100
        # 클리셰 패널티는 유지하되, 고밀도 가사에서는 클리셰가 희석되므로 영향 최소화
        score -= len(self.cliche_hits) * 2
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
        if self.imagery_specificity < 0.4:
            alerts.append("Imagery too sparse - missing high-fidelity subculture keywords")
        if self.singability < 0.4:
            alerts.append("Density mismatch - rhythm may be too generic for subculture")
        if self.structural_integrity < 0.5:
            alerts.append("Structural weakness - blueprint adherence failed")
        if self.artist_trace_detected:
            alerts.append("Artist anchor detected - review for originality")
        if self.cliche_hits:
            alerts.append(f"Cliche phrases found: {', '.join(self.cliche_hits)}")
        return alerts


def _score_imagery_specificity(lyrics: GeneratedLyrics) -> float:
    """11만 건 기반 고해상도 어휘 밀도 측정."""
    if not lyrics.sections:
        return 0.0

    # 11만 건 추출 어휘 라이브러리 로드
    lib_path = Path(__file__).resolve().parent.parent.parent / "data" / "technique_library" / "subculture_lexicon.json"
    if lib_path.exists():
        with lib_path.open(encoding="utf-8") as f:
            lexicon = json.load(f).get("words", [])
    else:
        lexicon = ["心臓", "回路", "世界", "嘘", "影", "夜"] # 폴백

    all_text = "\n".join(lyrics.sections.values())
    total_chars = len(all_text.replace("\n", ""))
    if total_chars == 0:
        return 0.0

    # 유니크한 고해상도 단어 수 측정
    hits = sum(1 for word in lexicon if word in all_text)
    
    # 고밀도 어휘가 5개만 있어도 보컬로이드 씬에서는 충분한 신호로 간주 (가중치 상향)
    score = (hits / (total_chars / 500 + 1)) / 5.0 
    return min(1.0, score)


def _count_mora(text: str) -> int:
    """일본어 텍스트의 모라 수를 카운트.

    히라가나/카타카나 1문자 = 1모라 (단, 촉음·장음은 별도 모라).
    한자는 평균 2모라로 추정.
    """
    mora = 0
    for ch in text:
        if '\u3040' <= ch <= '\u309F':    # 히라가나
            mora += 1
        elif '\u30A0' <= ch <= '\u30FF':  # 카타카나
            mora += 1
        elif '\u4E00' <= ch <= '\u9FFF':  # 한자 (평균 2모라)
            mora += 2
        # ASCII, 기호 등은 무시
    return mora


def _score_singability(lyrics: GeneratedLyrics) -> float:
    """모라 기반 가창성 채점.

    - 이상적 범위: 라인당 15-35 모라 (보컬로이드 서브컬처 기준)
    - 범위 내 라인 비율이 높을수록 고득점
    - 극단적 고밀도(40+모라)는 가창성 감점 (밀도 점수는 별도)
    """
    all_lines = []
    for content in lyrics.sections.values():
        all_lines.extend([l for l in content.splitlines() if l.strip()])

    if not all_lines:
        return 0.0

    mora_counts = [_count_mora(line.strip()) for line in all_lines]
    if not mora_counts:
        return 0.0

    avg_mora = sum(mora_counts) / len(mora_counts)

    # 이상적 범위(15-35 모라) 내 라인 비율
    in_range = sum(1 for m in mora_counts if 15 <= m <= 35)
    range_ratio = in_range / len(mora_counts)

    # 기본 점수: 이상적 범위 비율 (0.0-0.7)
    base = range_ratio * 0.7

    # 평균 모라 보정 (0.0-0.3)
    if 18 <= avg_mora <= 30:
        avg_bonus = 0.3  # 이상적 평균
    elif 12 <= avg_mora <= 40:
        avg_bonus = 0.2  # 허용 범위
    elif avg_mora > 40:
        avg_bonus = 0.05  # 극고밀도 — 부르기 어려움
    else:
        avg_bonus = avg_mora / 12.0 * 0.15  # 저밀도

    return min(1.0, max(0.0, base + avg_bonus))


def _score_emotional_coherence(lyrics: GeneratedLyrics, direction: CreativeDirection) -> float:
    """감정 아크 일관성 — 정규화된 섹션 기반 구조 분석."""
    canonical = normalize_sections(lyrics.sections)
    if not canonical:
        return 0.0

    score = 0.0

    # 필수 섹션 존재 여부 (정규화된 키 기반)
    has_verse = VERSE_1 in canonical
    has_chorus = CHORUS in canonical
    has_final = FINAL_CHORUS in canonical
    has_bridge = BRIDGE in canonical

    if has_verse:
        score += 0.25
    if has_chorus:
        score += 0.3
    if has_final:
        score += 0.25
    if has_bridge:
        score += 0.1

    # 최종 사비가 가장 긴지 확인 (에너지 아크 상승)
    if has_final and has_chorus:
        final_len = len(canonical.get(FINAL_CHORUS, ""))
        chorus_len = len(canonical.get(CHORUS, ""))
        if final_len >= chorus_len:
            score += 0.1

    return min(1.0, score)


def _score_structural_integrity(lyrics: GeneratedLyrics) -> float:
    """섹션 구조 완성도 — 정규화된 canonical 키 기반."""
    if not lyrics.sections:
        return 0.0
    canonical = normalize_sections(lyrics.sections)
    return structural_completeness(canonical)


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
    """가사 품질 종합 채점 (Subculture DNA Bank 기준).

    모든 섹션명을 canonical 형식으로 정규화한 뒤 채점합니다.
    """
    # 섹션 정규화 (채점 전에 한 번만 수행)
    canonical = normalize_sections(lyrics.sections)
    # 정규화된 섹션으로 임시 래핑
    original_sections = lyrics.sections
    lyrics.sections = canonical

    try:
        # 클리셰 감지
        all_text = "\n".join(canonical.values())
        cliche_hits = [phrase for phrase in _CLICHE_PHRASES if phrase in all_text]

        # 아티스트 흔적 감지
        artist_trace = bool(_ARTIST_NAME_PATTERN.search(all_text + lyrics.full_text))

        # 라인 통계
        all_lines = []
        for content in canonical.values():
            all_lines.extend([l for l in content.splitlines() if l.strip()])
        avg_line_len = (
            sum(len(l.strip()) for l in all_lines) / len(all_lines) if all_lines else 0.0
        )

        # 비평 로그 요약
        critique_memo = lyrics.critique_logs[0][:200] + "..." if lyrics.critique_logs else "No self-critique available."

        return QualityReport(
            imagery_specificity=_score_imagery_specificity(lyrics),
            singability=_score_singability(lyrics),
            emotional_coherence=_score_emotional_coherence(lyrics, direction),
            structural_integrity=_score_structural_integrity(lyrics),
            japanese_quality=_score_japanese_quality(lyrics, direction),
            cliche_hits=cliche_hits,
            artist_trace_detected=artist_trace,
            section_count=len(canonical),
            avg_line_length=avg_line_len,
            total_lines=len(all_lines),
            critique_memo=critique_memo
        )
    finally:
        # 원본 섹션 복원 (side-effect 방지)
        lyrics.sections = original_sections
