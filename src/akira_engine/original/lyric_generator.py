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

_CRITIQUE_SYSTEM_PROMPT = """You are a Structured Quality Evaluator for original Japanese lyrics in the Vocaloid/Subculture scene.

Your task: Analyze draft lyrics and return EXACTLY a JSON object with structured improvement commands.
Do NOT write free-form analysis. Return ONLY valid JSON.

Evaluation Axes (BALANCED — do not over-optimize any single axis):
1. DENSITY: Information density per line (kanji compound richness, imagery layering)
2. SINGABILITY: Can a vocalist actually perform this? (15-35 mora per line is ideal; 40+ is a penalty)
3. EMOTIONAL_ARC: Does the energy build across sections? (Verse→Pre-Chorus→Chorus→Bridge→Final)
4. ORIGINALITY: Avoidance of cliché; unique compound-word creation
5. STRUCTURAL: Section completeness and hook memorability

Return this EXACT JSON structure:
{
  "overall_score_estimate": 72,
  "weakest_axis": "singability",
  "strongest_axis": "density",
  "actions": [
    {
      "priority": 1,
      "target_section": "Pre-Chorus",
      "axis": "singability",
      "action": "Split compound lines into 2 shorter lines (target: 20-25 mora each)",
      "example_before": "歯車咽頭、懺悔漏電、君規格祭壇へ自壊縫合、供犠起動",
      "example_after": "歯車咽頭、懺悔漏電\\n君規格祭壇へ 自壊縫合"
    }
  ],
  "hook_assessment": "壊愛実行 is strong — keep as central hook",
  "lines_over_40_mora": 5,
  "sections_missing": []
}

CRITICAL RULES:
- Maximum 5 actions in the "actions" array
- Each action must target a SPECIFIC section
- Balance density WITH singability — do NOT push density at the cost of performability
- Return ONLY the JSON object, no markdown, no explanation"""


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
    
    # 2. Iterative Refinement Phase (Harness-style structured loop)
    for i in range(max_iterations):
        print(f"[DEBUG] Self-Critique / Refinement loop {i+1}...")
        
        # critique — request JSON structured evaluation
        critique_prompt = f"Original Direction:\n{user_prompt}\n\nCurrent Draft Lyrics:\n{current_lyrics}"
        critique_raw = _call_api(_CRITIQUE_SYSTEM_PROMPT, critique_prompt, api_key=api_key, model=model, temperature=0.3)
        
        if not critique_raw: 
            critique_logs.append(f"--- Pass {i+1}: Critique returned empty, skipping ---")
            break
        
        # Parse structured critique (Harness: machine control, not prose)
        critique_data = None
        try:
            # Strip markdown code fences if present
            cleaned = re.sub(r"^```(?:json)?\n?", "", critique_raw.strip(), flags=re.MULTILINE)
            cleaned = cleaned.replace("```", "").strip()
            critique_data = json.loads(cleaned)
        except (json.JSONDecodeError, ValueError):
            # Fallback: treat as unstructured (legacy behavior)
            critique_logs.append(f"--- Pass {i+1} (unstructured fallback) ---\n{critique_raw[:500]}...")
        
        if critique_data:
            # Extract only the top 5 actions (Harness: Context budget control)
            actions = critique_data.get("actions", [])[:5]
            score_est = critique_data.get("overall_score_estimate", "?")
            weakest = critique_data.get("weakest_axis", "unknown")
            hook_note = critique_data.get("hook_assessment", "")
            missing = critique_data.get("sections_missing", [])
            
            # Build compact critique log
            action_summary = "\n".join(
                f"  [{a.get('priority', '?')}] {a.get('target_section', '?')}: {a.get('action', '')}"
                for a in actions
            )
            critique_logs.append(
                f"--- Pass {i+1} (Structured) ---\n"
                f"Score: {score_est}/100 | Weakest: {weakest}\n"
                f"Hook: {hook_note}\n"
                f"Actions:\n{action_summary}"
            )
            
            # Build TARGETED refinement prompt (Harness: minimal, actionable commands only)
            action_instructions = "\n".join(
                f"{j+1}. [{a.get('target_section', 'ALL')}] {a.get('action', '')}"
                + (f"\n   Before: {a['example_before']}\n   After: {a['example_after']}" 
                   if a.get("example_before") else "")
                for j, a in enumerate(actions)
            )
            
            missing_note = f"\nMissing sections to add: {', '.join(missing)}" if missing else ""
            
            refinement_user_prompt = (
                f"RE-WRITE the lyrics applying EXACTLY these {len(actions)} fixes:\n\n"
                f"{action_instructions}\n"
                f"{missing_note}\n\n"
                f"KEEP the hook: {hook_note}\n"
                f"Use ONLY ASCII markers: [Intro], [Verse], [Pre-Chorus], [Chorus], [Bridge], [Outro]\n\n"
                f"Current Draft:\n{current_lyrics}\n\n"
                f"Write the refined version below."
            )
        else:
            # Fallback: use raw critique (legacy path)
            refinement_user_prompt = (
                f"Please RE-WRITE the lyrics based on the following critique.\n"
                f"Note: Use ONLY ASCII markers like [Intro], [Chorus] for sections.\n"
                f"Current Draft:\n{current_lyrics}\n\n"
                f"Critique:\n{critique_raw[:1500]}\n\n"
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
