"""Section Names — 전체 엔진에서 사용하는 섹션 네이밍 정규화 유틸리티.

모든 모듈이 이 파일의 함수를 통해 섹션명을 처리해야 합니다.
Generator가 어떤 형식으로 출력해도, Quality Scorer와 Suno Formatter가
일관되게 이해할 수 있도록 보장합니다.
"""
from __future__ import annotations

import re
from typing import Any


# ──────────────────────────────────────────────────────────────
# Canonical Section IDs
# ──────────────────────────────────────────────────────────────
# 내부적으로 모든 섹션은 이 ID로 통일됩니다.
INTRO = "intro"
VERSE_1 = "verse_1"
VERSE_2 = "verse_2"
PRE_CHORUS = "pre_chorus"
PRE_CHORUS_2 = "pre_chorus_2"
CHORUS = "chorus"
CHORUS_2 = "chorus_2"
BRIDGE = "bridge"
FINAL_CHORUS = "final_chorus"
OUTRO = "outro"

# 표준 섹션 순서 (에너지 아크 기준)
CANONICAL_ORDER: list[str] = [
    INTRO,
    VERSE_1,
    PRE_CHORUS,
    CHORUS,
    VERSE_2,
    PRE_CHORUS_2,
    CHORUS_2,
    BRIDGE,
    FINAL_CHORUS,
    OUTRO,
]

# ──────────────────────────────────────────────────────────────
# Alias → Canonical 매핑 테이블
# ──────────────────────────────────────────────────────────────
# 키: 소문자 정규화된 별칭, 값: canonical ID
_ALIAS_MAP: dict[str, str] = {
    # --- Intro ---
    "intro": INTRO,
    "イントロ": INTRO,
    "인트로": INTRO,

    # --- Verse 1 ---
    "verse": VERSE_1,
    "verse 1": VERSE_1,
    "verse1": VERSE_1,
    "aメロ": VERSE_1,
    "a메로": VERSE_1,
    "a_melo": VERSE_1,
    "a melo": VERSE_1,

    # --- Verse 2 ---
    "verse 2": VERSE_2,
    "verse2": VERSE_2,
    "aメロ2": VERSE_2,
    "aメロ 2": VERSE_2,
    "a메로2": VERSE_2,
    "a_melo_2": VERSE_2,

    # --- Pre-Chorus ---
    "pre-chorus": PRE_CHORUS,
    "pre chorus": PRE_CHORUS,
    "prechorus": PRE_CHORUS,
    "bメロ": PRE_CHORUS,
    "b메로": PRE_CHORUS,
    "b_melo": PRE_CHORUS,
    "b melo": PRE_CHORUS,

    # --- Pre-Chorus 2 ---
    "pre-chorus 2": PRE_CHORUS_2,
    "pre chorus 2": PRE_CHORUS_2,
    "prechorus 2": PRE_CHORUS_2,
    "bメロ2": PRE_CHORUS_2,
    "bメロ 2": PRE_CHORUS_2,
    "b메로2": PRE_CHORUS_2,

    # --- Chorus ---
    "chorus": CHORUS,
    "chorus 1": CHORUS,
    "chorus1": CHORUS,
    "サビ": CHORUS,
    "사비": CHORUS,
    "sabi": CHORUS,

    # --- Chorus 2 ---
    "chorus 2": CHORUS_2,
    "chorus2": CHORUS_2,
    "サビ2": CHORUS_2,
    "サビ 2": CHORUS_2,
    "사비2": CHORUS_2,

    # --- Bridge ---
    "bridge": BRIDGE,
    "ブリッジ": BRIDGE,
    "브릿지": BRIDGE,
    "c_melo": BRIDGE,
    "cメロ": BRIDGE,
    "c메로": BRIDGE,

    # --- Final Chorus ---
    "final chorus": FINAL_CHORUS,
    "final_chorus": FINAL_CHORUS,
    "last chorus": FINAL_CHORUS,
    "最終サビ": FINAL_CHORUS,
    "最終사비": FINAL_CHORUS,
    "大サビ": FINAL_CHORUS,
    "dai_sabi": FINAL_CHORUS,

    # --- Outro ---
    "outro": OUTRO,
    "アウトロ": OUTRO,
    "아웃트로": OUTRO,
}


def normalize_section_name(raw_name: str) -> str:
    """어떤 형식의 섹션명이든 canonical ID로 변환.

    >>> normalize_section_name("[Verse]")
    'verse_1'
    >>> normalize_section_name("Aメロ")
    'verse_1'
    >>> normalize_section_name("サビ")
    'chorus'
    >>> normalize_section_name("Pre-Chorus")
    'pre_chorus'
    >>> normalize_section_name("最終サビ")
    'final_chorus'
    """
    # 대괄호·공백 정리
    cleaned = raw_name.strip().strip("[]【】「」").strip()
    # 소문자 변환 (일본어/한국어는 영향 없음)
    lowered = cleaned.lower()

    # 직접 매칭
    if lowered in _ALIAS_MAP:
        return _ALIAS_MAP[lowered]

    # 대소문자 무관 일본어 매칭 (원본 그대로 시도)
    if cleaned in _ALIAS_MAP:
        return _ALIAS_MAP[cleaned]

    # 부분 매칭 (예: "Verse 1 (Expanded)" → "verse 1")
    for alias, canonical in sorted(_ALIAS_MAP.items(), key=lambda x: -len(x[0])):
        if alias in lowered:
            return canonical

    # 매칭 실패 시 원본 반환 (소문자, 공백→언더스코어)
    return re.sub(r"\s+", "_", lowered)


def normalize_sections(sections: dict[str, str]) -> dict[str, str]:
    """섹션 딕셔너리의 모든 키를 canonical 이름으로 변환.

    중복 키가 발생하면 뒤에 나오는 것이 우선 (Final Chorus가 Chorus를 덮지 않도록).
    """
    result: dict[str, str] = {}
    for raw_name, content in sections.items():
        canonical = normalize_section_name(raw_name)
        # 이미 같은 canonical 키가 있고, 새 키가 "final" 계열이 아니면 건너뜀
        if canonical in result and canonical != FINAL_CHORUS:
            # 두 번째 chorus는 chorus_2로
            if canonical == CHORUS:
                result[CHORUS_2] = content
                continue
            elif canonical == VERSE_1:
                result[VERSE_2] = content
                continue
            elif canonical == PRE_CHORUS:
                result[PRE_CHORUS_2] = content
                continue
        result[canonical] = content
    return result


def to_display_name(canonical: str, *, style: str = "jp") -> str:
    """Canonical ID를 표시용 이름으로 변환.

    style:
        "jp" — 일본어 (Aメロ, サビ, ...)
        "en" — 영어 (Verse, Chorus, ...)
        "suno" — Suno 포맷 ([Verse], [Chorus], ...)
    """
    jp_map = {
        INTRO: "イントロ",
        VERSE_1: "Aメロ",
        VERSE_2: "Aメロ2",
        PRE_CHORUS: "Bメロ",
        PRE_CHORUS_2: "Bメロ2",
        CHORUS: "サビ",
        CHORUS_2: "サビ2",
        BRIDGE: "ブリッジ",
        FINAL_CHORUS: "最終サビ",
        OUTRO: "アウトロ",
    }
    en_map = {
        INTRO: "Intro",
        VERSE_1: "Verse 1",
        VERSE_2: "Verse 2",
        PRE_CHORUS: "Pre-Chorus",
        PRE_CHORUS_2: "Pre-Chorus 2",
        CHORUS: "Chorus",
        CHORUS_2: "Chorus 2",
        BRIDGE: "Bridge",
        FINAL_CHORUS: "Final Chorus",
        OUTRO: "Outro",
    }
    suno_map = {
        INTRO: "[Intro]",
        VERSE_1: "[Verse]",
        VERSE_2: "[Verse 2]",
        PRE_CHORUS: "[Pre-Chorus]",
        PRE_CHORUS_2: "[Pre-Chorus 2]",
        CHORUS: "[Chorus]",
        CHORUS_2: "[Chorus 2]",
        BRIDGE: "[Bridge]",
        FINAL_CHORUS: "[Chorus]",
        OUTRO: "[Outro]",
    }

    style_maps = {"jp": jp_map, "en": en_map, "suno": suno_map}
    chosen = style_maps.get(style, en_map)
    return chosen.get(canonical, canonical)


def ordered_sections(sections: dict[str, str]) -> list[tuple[str, str]]:
    """섹션을 CANONICAL_ORDER 순서로 정렬하여 반환."""
    result: list[tuple[str, str]] = []
    seen: set[str] = set()

    for canonical in CANONICAL_ORDER:
        if canonical in sections and canonical not in seen:
            result.append((canonical, sections[canonical]))
            seen.add(canonical)

    # 표준 순서에 없는 나머지 섹션 추가
    for key, content in sections.items():
        if key not in seen:
            result.append((key, content))

    return result


# ──────────────────────────────────────────────────────────────
# 구조 완성도 검증
# ──────────────────────────────────────────────────────────────
# 최소 필수 섹션 (이 중 3개 이상 있으면 합격)
REQUIRED_SECTIONS = {VERSE_1, PRE_CHORUS, CHORUS, BRIDGE}
# 강화 섹션 (있으면 가점)
BONUS_SECTIONS = {INTRO, VERSE_2, FINAL_CHORUS, OUTRO}


def structural_completeness(sections: dict[str, str]) -> float:
    """정규화된 섹션 딕셔너리의 구조 완성도 (0.0-1.0)."""
    canonical_keys = set(sections.keys())
    required_hits = len(REQUIRED_SECTIONS & canonical_keys)
    bonus_hits = len(BONUS_SECTIONS & canonical_keys)

    # 필수 4개 중 몇 개 존재하는지 (0.0-0.8)
    base = (required_hits / len(REQUIRED_SECTIONS)) * 0.8
    # 보너스 (0.0-0.2)
    bonus = (bonus_hits / len(BONUS_SECTIONS)) * 0.2

    return min(1.0, base + bonus)
"""Section Names module — canonical section naming for AKIRA ENGINE."""
