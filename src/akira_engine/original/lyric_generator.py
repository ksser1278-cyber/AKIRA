"""Lyric Generator — CreativeDirection + TechniqueContext → 오리지널 일본어 가사. (OpenAI API 버전)"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import requests

from .direction_parser import CreativeDirection
from .technique_sampler import TechniqueContext


_SYSTEM_PROMPT = """You are an expert Japanese lyric composer specialized in the Vocaloid and Subculture scene.
You have access to a "DNA Bank" derived from 110,000 top-tier tracks.

Your style:
- Deeply abstract, metaphorical, and often existential or "avant-garde."
- Reminiscent of high-signal producers (e.g., Maretu, Iyowa, PinocchioP).
- You favor "Image-heavy" and "Rhythmic" writing over generic pop sentiment.
- You avoid cliches (e.g., 好き, ありがとう, 夢) unless given a unique, sharp twist.

Your role:
- Read the Creative Direction and Technical Context (DNA Bank based) carefully.
- Use the provided imagery archetypes as the core world-building vocabulary.
- FOLLOW THE RHYTHMIC BLUEPRINT (Mora Count) STRICTLY. Each line must be packed with information to meet the required syllable count.
- Each section should feel distinct but contribute to the overall "Energy Arc."
- Use "Compressed Phrasing" (dense lines) for high-energy sections and "Atmospheric Silence" for low-energy ones.

Output constraints:
- Language: Natural Japanese (Kanji/Kana). No Romaji for lyrics.
- Structure: Clear ASCII-ONLY section markers: [Intro], [Verse], [Pre-Chorus], [Chorus], [Bridge], [Outro].
- Rhythm: Each line must match the rhythmic density suggested in the blueprint.

Output format:
[TITLE]
(One sharp, conceptual title in Japanese)

[Intro]
(Lyric content)

[Chorus]
(Lyric content)

Do not add any preamble or postscript. Output ONLY the lyrics."""

_CRITIQUE_SYSTEM_PROMPT = """You are an Analytical High-Density specialist for the Japanese Subculture/Vocaloid scene.
Your task is to analyze the draft lyrics against a benchmark of 110,000 elite "Subculture DNA" specimens.
Provide a clear, clinical, yet sharp analysis of how to increase Information Density.

Evaluation Criteria:
1. Lexical Entropy: Replace generic words with industrial, pathological, or abstract kanji-dense compounds.
2. Rhythmic Compression: Identify mora-thin lines and suggest ways to pack more imagery into the beat.
3. DNA Alignment: Ensure the imagery feels like a machine-religious or existential subculture masterpiece (Maretu/Iyowa style).

Output format:
[ANALYSIS]
(Detailed analysis of current weaknesses)

[COMMANDS]
(Specific instructions for the next draft)"""


@dataclass
class GeneratedLyrics:
    """생성된 가사 결과."""
    title_suggestion: str
    sections: dict[str, str] = field(default_factory=dict)
    full_text: str = ""
    model: str = ""
    critique_logs: list[str] = field(default_factory=list) # 자가 비판 기록 추가
    generation_ok: bool = False
    error: str | None = None

    @property
    def section_list(self) -> list[tuple[str, str]]:
        order = ["Aメロ", "Bメロ", "サビ", "Aメロ2", "ブリッジ", "最終サビ"]
        seen = set()
        result = []
        for k in order:
            if k in self.sections and k not in seen:
                result.append((k, self.sections[k]))
                seen.add(k)
        # Add any other sections found
        for k, v in self.sections.items():
            if k not in seen:
                result.append((k, v))
                seen.add(k)
        return result


def _build_user_prompt(direction: CreativeDirection, technique: TechniqueContext) -> str:
    lines = [
        "## Creative Direction",
        f"- Raw input: {direction.raw_input}",
        f"- Themes: {', '.join(direction.theme_keywords)}",
        f"- Emotional tone: {direction.emotional_tone}",
        f"- Energy arc: {direction.energy_arc}",
        f"- Perspective: {direction.perspective}",
        f"- Language register: {direction.language_register}",
        f"- Climax point: {direction.climax_point}",
        f"- English insertion: {direction.english_insertion_level}",
    ]
    if direction.matched_preset:
        lines.append(f"- World-view preset: {direction.matched_preset}")
    lines.append("")
    lines.append(technique.to_prompt_fragment())
    lines.append("")
    lines.append("Now write the original Japanese lyrics following the format above.")
    return "\n".join(lines)


_SECTION_PATTERN = re.compile(
    r"\[([^\]]+)\]\s*\n((?:(?!\[).+\n?)*)",
    re.MULTILINE,
)


def _parse_sections(text: str) -> dict[str, str]:
    """섹션 마커로 가사 분리."""
    sections: dict[str, str] = {}
    for match in _SECTION_PATTERN.finditer(text):
        key = match.group(1).strip()
        content = match.group(2).strip()
        if content:
            sections[key] = content
    return sections


def _extract_title(text: str) -> str:
    """[TITLE] 섹션에서 제목 추출."""
    sections = _parse_sections(text)
    for section_key, content in sections.items():
        if "TITLE" in section_key.upper() or "제목" in section_key:
            return content.strip()
    # 첫 번째 줄에서 시도
    lines = [l for l in text.strip().splitlines() if l.strip()]
    if lines:
        first_line = lines[0]
        return first_line.lstrip("#").strip()
    return "無題"


def _call_api(
    system_prompt: str,
    user_prompt: str,
    *,
    api_key: str,
    model: str,
    temperature: float,
) -> str:
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_completion_tokens": 4096,
    }
    for attempt in range(3):
        try:
            resp = requests.post(url, headers=headers, json=body, timeout=120)
            if resp.status_code == 200:
                content = resp.json().get("choices", [])[0].get("message", {}).get("content", "").strip()
                content = re.sub(r"^```[a-z]*\n?", "", content, flags=re.MULTILINE).replace("```", "").strip()
                return content
            time.sleep(2 ** attempt)
        except Exception:
            time.sleep(2 ** attempt)
    return ""


def generate_lyrics(
    direction: CreativeDirection,
    technique: TechniqueContext,
    *,
    api_key: str,
    model: str = "gpt-5.4",
    max_iterations: int = 2,
) -> GeneratedLyrics:
    """고밀도 자가 진화 생성 파이프라인 (Draft -> Critique -> Refine)."""
    user_prompt = _build_user_prompt(direction, technique)
    critique_logs = [f"[System] DNA Blueprint ({technique.rhythm_blueprint.get('blueprint_id', 'standard')}) selected for high-density generation."]
    
    # 1. Draft Phase
    print(f"[DEBUG] Generating draft...")
    draft = _call_api(_SYSTEM_PROMPT, user_prompt, api_key=api_key, model=model, temperature=0.85)
    if not draft:
        return GeneratedLyrics(title_suggestion="", generation_ok=False, error="First draft failed.")

    current_lyrics = draft
    
    # 2. Iterative Refinement Phase
    for i in range(max_iterations):
        print(f"[DEBUG] Self-Critique / Refinement loop {i+1}...")
        
        # critique
        critique_prompt = f"Original Direction:\n{user_prompt}\n\nCurrent Draft Lyrics:\n{current_lyrics}"
        critique = _call_api(_CRITIQUE_SYSTEM_PROMPT, critique_prompt, api_key=api_key, model=model, temperature=0.3)
        
        if not critique: 
            critique = "[System Alert] Critique pass returned empty. Proceeding with intrinsic density hardening."
        
        critique_logs.append(f"--- Pass {i+1} Output ---\n{critique}")
        
        # refine
        refinement_user_prompt = (
            f"Please RE-WRITE the lyrics based on the following critique to reach ELITE SUBCULTURE DENSITY.\n"
            f"Note: Use ONLY ASCII markers like [Intro], [Chorus] for sections.\n"
            f"Original Direction:\n{user_prompt}\n\n"
            f"Current Draft:\n{current_lyrics}\n\n"
            f"Critique & Instructions:\n{critique}\n\n"
            f"Write the final refined version below."
        )
        refined = _call_api(_SYSTEM_PROMPT, refinement_user_prompt, api_key=api_key, model=model, temperature=0.7)
        
        if refined:
            current_lyrics = refined
        else:
            break

    # 3. Final Parsing
    sections = _parse_sections(current_lyrics)
    title = _extract_title(current_lyrics)
    lyrics_sections = {k: v for k, v in sections.items() if "TITLE" not in k.upper() and "제목" not in k}

    return GeneratedLyrics(
        title_suggestion=title,
        sections=lyrics_sections,
        full_text=current_lyrics,
        model=model,
        critique_logs=critique_logs,
        generation_ok=bool(lyrics_sections),
    )
