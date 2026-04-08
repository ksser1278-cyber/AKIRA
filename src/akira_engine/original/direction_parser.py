"""Direction Parser — 자유형식 입력을 CreativeDirection 객체로 파싱. (OpenAI API 버전)"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

import requests


# ──────────────────────────────────────────────
# 세계관 프리셋 정의 (아티스트 비종속)
# ──────────────────────────────────────────────
WORLD_PRESETS: dict[str, dict[str, Any]] = {
    "quiet_explosion": {
        "label": "静寂の爆発",
        "emotional_tone": "dark_and_tender",
        "energy_arc": "quiet_then_explosive",
        "imagery_hints": ["침묵", "균열", "빛"],
        "language_register": "poetic",
        "perspective_bias": "first_person",
    },
    "sweet_collapse": {
        "label": "甘い崩壊",
        "emotional_tone": "bittersweet",
        "energy_arc": "steady_medium",
        "imagery_hints": ["달콤함", "붕괴", "온기"],
        "language_register": "colloquial",
        "perspective_bias": "flexible",
    },
    "ironic_purity": {
        "label": "皮肉な純粋",
        "emotional_tone": "detached_ironic",
        "energy_arc": "fast_and_punchy",
        "imagery_hints": ["순수", "냉소", "날"],
        "language_register": "young_colloquial",
        "perspective_bias": "first_person",
    },
    "tender_defiance": {
        "label": "柔らかい反抗",
        "emotional_tone": "vulnerable_yet_defiant",
        "energy_arc": "slow_then_medium",
        "imagery_hints": ["취약함", "저항", "손"],
        "language_register": "mixed",
        "perspective_bias": "first_person",
    },
    "neon_solitude": {
        "label": "ネオンの孤独",
        "emotional_tone": "urban_lonely",
        "energy_arc": "medium_pop",
        "imagery_hints": ["도시", "네온", "고독"],
        "language_register": "pop",
        "perspective_bias": "flexible",
    },
}


@dataclass
class CreativeDirection:
    """파싱된 창작 방향."""
    raw_input: str
    theme_keywords: list[str] = field(default_factory=list)
    emotional_tone: str = "dark_and_tender"
    energy_arc: str = "quiet_then_explosive"
    imagery_hints: list[str] = field(default_factory=list)
    language_register: str = "colloquial"
    perspective: str = "first_person"
    structure_hints: dict[str, str] = field(default_factory=dict)
    climax_point: str = "final_chorus"
    english_insertion_level: str = "none"
    matched_preset: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _load_api_key(project_root: Path) -> str:
    for var in ("OPENAI_API_KEY",):
        val = os.getenv(var)
        if val:
            return val.strip()
    env_path = project_root / "config" / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                if k.strip() == "OPENAI_API_KEY":
                    return v.strip()
    raise ValueError("OPENAI_API_KEY not found.")


def _call_openai_json(
    system_prompt: str,
    user_prompt: str,
    *,
    api_key: str,
    model: str = "gpt-4o-mini",
    temperature: float = 0.3,
    max_tokens: int = 512,
) -> str:
    """OpenAI Chat Completions — JSON 응답 반환."""
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
        "max_completion_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }
    for attempt in range(3):
        try:
            resp = requests.post(url, headers=headers, json=body, timeout=60)
            if resp.status_code == 200:
                choices = resp.json().get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "").strip()
            time.sleep(2 ** attempt)
        except requests.RequestException:
            time.sleep(2 ** attempt)
    return ""


_PARSE_SYSTEM_PROMPT = """You are a creative direction analyzer for an original Japanese lyric engine.
Given a free-form input (in any language — Korean, Japanese, or English), extract the creative direction.

Return a JSON object with these fields:
- theme_keywords: list of 2-5 core theme keywords (in English, lowercase)
- emotional_tone: one of [dark_and_tender, bittersweet, detached_ironic, vulnerable_yet_defiant, urban_lonely, bright_uplift, rage_and_release, melancholic_drift]
- energy_arc: one of [quiet_then_explosive, steady_medium, fast_and_punchy, slow_then_medium, medium_pop, build_and_drop, flat_circular]
- imagery_hints: list of 2-4 concrete imagery keywords (in Japanese preferred)
- language_register: one of [poetic, colloquial, young_colloquial, mixed, pop, formal]
- perspective: one of [first_person, second_person, third_person, flexible]
- climax_point: one of [chorus, final_chorus, bridge, consistent]
- english_insertion_level: one of [none, low, medium]
- matched_preset: one of [quiet_explosion, sweet_collapse, ironic_purity, tender_defiance, neon_solitude, null]

Only return valid JSON."""


def parse_direction(raw_input: str, *, api_key: str) -> CreativeDirection:
    """자유형식 입력을 CreativeDirection으로 파싱."""
    raw_json = _call_openai_json(
        _PARSE_SYSTEM_PROMPT,
        f"Input: {raw_input}",
        api_key=api_key,
        model="gpt-5.4-mini",
        temperature=0.2,
        max_tokens=512,
    )

    try:
        data = json.loads(raw_json)
    except (json.JSONDecodeError, ValueError):
        preset = WORLD_PRESETS["quiet_explosion"]
        return CreativeDirection(
            raw_input=raw_input,
            theme_keywords=[raw_input[:40]],
            emotional_tone=preset["emotional_tone"],
            energy_arc=preset["energy_arc"],
            imagery_hints=preset["imagery_hints"],
            language_register=preset["language_register"],
            perspective=preset["perspective_bias"],
            matched_preset="quiet_explosion",
        )

    matched = data.get("matched_preset")
    if matched and matched in WORLD_PRESETS:
        preset = WORLD_PRESETS[matched]
    else:
        matched = None
        preset = {}

    return CreativeDirection(
        raw_input=raw_input,
        theme_keywords=data.get("theme_keywords", []),
        emotional_tone=data.get("emotional_tone", preset.get("emotional_tone", "dark_and_tender")),
        energy_arc=data.get("energy_arc", preset.get("energy_arc", "quiet_then_explosive")),
        imagery_hints=data.get("imagery_hints", preset.get("imagery_hints", [])),
        language_register=data.get("language_register", preset.get("language_register", "colloquial")),
        perspective=data.get("perspective", preset.get("perspective_bias", "first_person")),
        climax_point=data.get("climax_point", "final_chorus"),
        english_insertion_level=data.get("english_insertion_level", "none"),
        matched_preset=matched,
    )
