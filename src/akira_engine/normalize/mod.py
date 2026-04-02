from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

@dataclass
class NormalizeResult:
    track_id: str
    original_text: str
    normalized_text: str = ""
    japanese_char_ratio: float = 0.0
    latin_token_ratio: float = 0.0
    suspicious_token_count: int = 0
    has_bad_script: bool = False
    section_guess: dict[str, int] = field(default_factory=dict)
    status: str = "pending"
    errors: list[str] = field(default_factory=list)

def contains_japanese(text: str) -> bool:
    """Check if the text contains any Japanese characters (Hiragana, Katakana, or Kanji)."""
    return any(("\u3040" <= ch <= "\u30ff") or ("\u4e00" <= ch <= "\u9fff") for ch in text)

def contains_bad_script(text: str) -> bool:
    """Check for Hangul or corrupted characters in the context of AKIRA ENGINE Japanese focus."""
    # Expanded Hangul ranges: Syllables (AC00-D7AF), Jamo (1100-11FF), Compatibility Jamo (3130-318F)
    hangul_pattern = re.compile(r'[\uac00-\ud7af\u1100-\u11ff\u3130-\u318f]')
    return bool(hangul_pattern.search(text)) or "\ufffd" in text

def calculate_script_ratios(text: str) -> tuple[float, float]:
    """Calculate Japanese character ratio and Latin token ratio."""
    if not text:
        return 0.0, 0.0
    
    total_chars = len(text)
    jp_chars = sum(1 for ch in text if ("\u3040" <= ch <= "\u30ff") or ("\u4e00" <= ch <= "\u9fff"))
    jp_ratio = jp_chars / total_chars if total_chars > 0 else 0.0
    
    tokens = text.split()
    if not tokens:
        return jp_ratio, 0.0
        
    latin_tokens = sum(1 for t in tokens if re.search(r"[a-zA-Z]", t))
    latin_ratio = latin_tokens / len(tokens)
    
    return round(jp_ratio, 3), round(latin_ratio, 3)

def normalize_text(text: str) -> str:
    """Apply basic Japanese-specific normalization."""
    # Normalize full-width spaces and specific punctuation
    text = text.replace("　", " ").replace("〜", "~").replace("！", "!").replace("？", "?")
    # Remove excessive newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def guess_sections(text: str) -> dict[str, int]:
    """Guess section counts based on bracket notation [Section]."""
    counts = {}
    for match in re.finditer(r"\[([^\]]+)\]", text):
        section = match.group(1).lower().strip()
        # Normalize common names
        if "verse" in section: section = "verse"
        if "chorus" in section or "sabi" in section: section = "chorus"
        if "pre" in section: section = "pre_chorus"
        counts[section] = counts.get(section, 0) + 1
    return counts

def run_normalize_stage(track_id: str, raw_text: str) -> NormalizeResult:
    """Execute Stage B: Normalize / Validate."""
    result = NormalizeResult(track_id=track_id, original_text=raw_text)
    
    if not raw_text.strip():
        result.status = "failed"
        result.errors.append("empty_source_text")
        return result
        
    # 1. Bad Script Check (Strict Hard Gate)
    if contains_bad_script(raw_text):
        result.has_bad_script = True
        # In vNext, we might still proceed to record the failure diagnostics
        result.errors.append("bad_script_detected")

    # 2. Ratios
    jp_ratio, latin_ratio = calculate_script_ratios(raw_text)
    result.japanese_char_ratio = jp_ratio
    result.latin_token_ratio = latin_ratio
    
    # 3. Normalization
    result.normalized_text = normalize_text(raw_text)
    
    # 4. Section Guessing
    result.section_guess = guess_sections(result.normalized_text)
    
    result.status = "normalized"
    return result
