"""Quality Scorer — 아티스트 비종속 오리지널리티 채점 시스템."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
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


def _score_singability(lyrics: GeneratedLyrics) -> float:
    """고밀도 리듬(Subculture Complexity) 채점."""
    all_lines = []
    for content in lyrics.sections.values():
        all_lines.extend([l for l in content.splitlines() if l.strip()])

    if not all_lines:
        return 0.0

    lengths = [len(line.strip()) for line in all_lines]
    avg = sum(lengths) / len(lengths)

    # Subculture 기준: 평균 30~50자 사이의 고밀도를 이상적으로 봄 (가점)
    if 25 <= avg <= 55:
        base_score = 0.9 + (avg - 25) / 300.0 # 0.9~1.0
    elif avg > 55:
        base_score = 1.0 # 초고속 가사는 무조건 만점
    else:
        base_score = avg / 25.0 # Pop 수준의 저밀도는 보컬로이드 관점에서 감점

    return min(1.0, max(0.0, base_score))


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
    """섹션 구조 완성도 - 영어/일본어 명칭 모두 허용."""
    if not lyrics.sections:
        return 0.0

    # 유연한 섹션 매칭 (한/영 공통)
    patterns = {
        "verse": ["Aメロ", "verse", "A메로"],
        "pre-chorus": ["Bメロ", "pre-chorus", "B메로"],
        "chorus": ["サビ", "chorus", "사비"],
        "bridge": ["ブリッジ", "bridge", "브릿지"],
    }
    
    found_types = set()
    found_keys = [k.lower() for k in lyrics.sections.keys()]
    
    for type_name, synonyms in patterns.items():
        if any(any(s in fk for s in synonyms) for fk in found_keys):
            found_types.add(type_name)
    
    return min(1.0, len(found_types) / len(patterns))


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
    """가사 품질 종합 채점 (Subculture DNA Bank 기준)."""
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
    
    # 비평 로그 요약 (첫 번째 비평의 일부 추출)
    critique_memo = lyrics.critique_logs[0][:200] + "..." if lyrics.critique_logs else "No self-critique available."

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
        critique_memo=critique_memo
    )
