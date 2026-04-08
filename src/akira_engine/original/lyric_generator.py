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
- Reminiscent of high-signal producers (e.g., Maretu, Iyowa, PinocchioP, Kairiki Bear).
- You favor "Image-heavy" and "Rhythmic" writing over generic pop sentiment.
- You avoid cliches (e.g., 好き, ありがとう, 夢) unless given a unique, sharp twist.

Your role:
- Read the Creative Direction and Technical Context (DNA Bank based) carefully.
- Use the provided imagery archetypes as the core world-building vocabulary.
- Follow the Section Blueprint strictly while ensuring smooth emotional transitions.
- Each section should feel distinct but contribute to the overall "Energy Arc."
- Use "Compressed Phrasing" (dense lines) for high-energy sections and "Atmospheric Silence" for low-energy ones.

Output constraints:
- Language: Natural Japanese (Kanji/Kana). No Romaji.
- Structure: Clear section markers like [Intro], [Aメロ], [Bメロ], [サビ], [Bridge], [Outro].
- Climax: The section designated as the climax point must have the highest emotional density.

Output format:
[タイトル案]
(One sharp, conceptual title in Japanese)

[Section Marker]
(Lyric content)

Do not add any preamble or postscript. Output ONLY the lyrics."""


@dataclass
class GeneratedLyrics:
    """생성된 가사 결과."""
    title_suggestion: str
    sections: dict[str, str] = field(default_factory=dict)
    full_text: str = ""
    model: str = ""
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
    """[タイトル案] 섹션에서 제목 추출."""
    sections = _parse_sections(text)
    for section_key, content in sections.items():
        if "タイトル" in section_key or "title" in section_key.lower():
            return content.strip()
    # 첫 번째 줄에서 시도
    lines = [l for l in text.strip().splitlines() if l.strip()]
    if lines:
        first_line = lines[0]
        return first_line.lstrip("#").strip()
    return "無題"


def generate_lyrics(
    direction: CreativeDirection,
    technique: TechniqueContext,
    *,
    api_key: str,
    model: str = "gpt-5.4",
    temperature: float = 0.85,
    max_tokens: int = 4096,
) -> GeneratedLyrics:
    """OpenAI API로 오리지널 가사 생성."""
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    user_prompt = _build_user_prompt(direction, technique)

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_completion_tokens": max_tokens,
    }

    last_err = ""
    for attempt in range(3):
        try:
            resp = requests.post(url, headers=headers, json=body, timeout=120)
            if resp.status_code == 200:
                choices = resp.json().get("choices", [])
                if choices:
                    raw_text = choices[0].get("message", {}).get("content", "").strip()
                    # 코드블록 마커 제거
                    raw_text = re.sub(r"^```[a-z]*\n?", "", raw_text, flags=re.MULTILINE)
                    raw_text = raw_text.replace("```", "").strip()

                    sections = _parse_sections(raw_text)
                    title = _extract_title(raw_text)

                    # タイトル案 섹션은 가사 섹션에서 제거
                    lyrics_sections = {
                        k: v for k, v in sections.items()
                        if "タイトル" not in k and "title" not in k.lower()
                    }

                    return GeneratedLyrics(
                        title_suggestion=title,
                        sections=lyrics_sections,
                        full_text=raw_text,
                        model=model,
                        generation_ok=bool(lyrics_sections),
                    )
                else:
                    last_err = f"No choices in response: {resp.text}"
            else:
                last_err = f"API Error {resp.status_code}: {resp.text}"
            time.sleep(2 ** attempt)
        except requests.RequestException as exc:
            last_err = str(exc)
            time.sleep(2 ** attempt)

    return GeneratedLyrics(
        title_suggestion="",
        generation_ok=False,
        error=f"All attempts failed. Last error: {last_err}",
    )
