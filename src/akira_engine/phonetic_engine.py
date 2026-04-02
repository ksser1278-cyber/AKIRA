from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple
from dataclasses import dataclass

# Phonetic classification for Japanese
VOWELS = {"a", "i", "u", "e", "o"}
CONSONANTS = {
    "k", "s", "t", "n", "h", "m", "y", "r", "w", "g", "z", "d", "b", "p", 
    "ky", "sy", "ty", "ny", "hy", "my", "ry", "gy", "zy", "dy", "by", "py"
}

# Consonant types for impact analysis
PLOSIVES = {"k", "t", "p", "g", "d", "b"} # Explosive, high impact
FRICATIVES = {"s", "z", "sh", "h"} # Smooth, high clarity
NASALS = {"n", "m"} # Resonant, singing-friendly

# Romaji mapping for phonetic analysis (simplistic)
ROMAJI_MAP = {
    "あ": "a", "い": "i", "う": "u", "え": "e", "お": "o",
    "か": "ka", "き": "ki", "く": "ku", "け": "ke", "こ": "ko",
    "さ": "sa", "し": "shi", "す": "su", "せ": "se", "そ": "so",
    "た": "ta", "ち": "chi", "つ": "tsu", "て": "te", "と": "to",
    "な": "na", "に": "ni", "ぬ": "nu", "ね": "ne", "の": "no",
    "は": "ha", "ひ": "hi", "ふ": "fu", "へ": "he", "ほ": "ho",
    "ま": "ma", "み": "mi", "む": "mu", "め": "me", "も": "mo",
    "や": "ya", "ゆ": "yu", "よ": "yo",
    "ら": "ra", "り": "ri", "る": "ru", "れ": "re", "ろ": "ro",
    "わ": "wa", "を": "wo", "ん": "n",
    "が": "ga", "ぎ": "gi", "ぐ": "gu", "げ": "ge", "ご": "go",
    "ざ": "za", "じ": "ji", "ず": "zu", "ぜ": "ze", "ぞ": "zo",
    "だ": "da", "ぢ": "ji", "づ": "zu", "で": "de", "ど": "do",
    "ば": "ba", "び": "bi", "ぶ": "bu", "べ": "be", "ぼ": "bo",
    "ぱ": "pa", "ぴ": "pi", "ぷ": "pu", "ぺ": "pe", "ぽ": "po",
    "きゃ": "kya", "きゅ": "kyu", "きょ": "kyo",
    "しゃ": "sha", "しゅ": "shu", "しょ": "sho",
    "ちゃ": "cha", "ちゅ": "chu", "ちょ": "cho",
    "にゃ": "nya", "にゅ": "nyu", "にょ": "nyo",
    "ひゃ": "hya", "ひゅ": "hyu", "ひょ": "hyo",
    "みゃ": "mya", "みゅ": "myu", "みょ": "myo",
    "りゃ": "rya", "りゅ": "ryu", "りょ": "ryo",
    "ぎゃ": "gya", "ぎゅ": "gyu", "ぎょ": "gyo",
    "じゃ": "ja", "じゅ": "ju", "じょ": "jo",
    "びゃ": "bya", "びゅ": "byu", "びょ": "byo",
    "ぴゃ": "pya", "ぴゅ": "pyu", "ぴょ": "pyo",
    "ー": "-", "っ": "q",
}

@dataclass
class PhoneticProfile:
    vowel_dist: Dict[str, float]
    plosive_ratio: float
    fricative_ratio: float
    nasal_ratio: float
    brilliance_score: float # High 'a', 'i' content

def text_to_phonetic_units(text: str) -> List[str]:
    """
    Decomposes Japanese text into phonetic units (Romaji-like).
    """
    units = []
    # Handle multi-character units first (yoon)
    i = 0
    while i < len(text):
        if i + 1 < len(text) and text[i:i+2] in ROMAJI_MAP:
            units.append(ROMAJI_MAP[text[i:i+2]])
            i += 2
        elif text[i] in ROMAJI_MAP:
            units.append(ROMAJI_MAP[text[i]])
            i += 1
        else:
            # Skip non-japanese or unknown
            i += 1
    return units

def analyze_phonetic_profile(text: str) -> PhoneticProfile:
    units = text_to_phonetic_units(text)
    if not units:
        return PhoneticProfile({v: 0.0 for v in VOWELS}, 0, 0, 0, 0)
    
    vowels = []
    consonants = []
    
    for unit in units:
        # Extract last char as vowel (e.g., 'ka' -> 'a')
        if any(unit.endswith(v) for v in VOWELS):
            vowels.append(unit[-1])
            if len(unit) > 1:
                consonants.append(unit[:-1])
        elif unit in VOWELS:
            vowels.append(unit)
    
    v_dist = {v: (vowels.count(v) / len(vowels)) if vowels else 0.0 for v in VOWELS}
    
    # Brilliance (Elite tracks show high 'a'/'i' ratio for clarity/perceived brightness)
    brilliance = (v_dist.get("a", 0) + v_dist.get("i", 0)) / max(0.001, sum(v_dist.values()))
    
    plosive_count = sum(1 for c in consonants if c in PLOSIVES)
    fricative_count = sum(1 for c in consonants if c in FRICATIVES)
    nasal_count = sum(1 for c in consonants if c in NASALS)
    
    total_c = max(1, len(consonants))
    
    return PhoneticProfile(
        vowel_dist=v_dist,
        plosive_ratio=plosive_count / total_c,
        fricative_ratio=fricative_count / total_c,
        nasal_ratio=nasal_count / total_c,
        brilliance_score=brilliance
    )

def apply_stutter_glitch(line: str, style: str = "explosive", intensity: float = 0.2) -> str:
    """
    Injects rhythmic stutters based on phonetic structure.
    More aggressive version that splits text into smaller chunks for higher hit-rate.
    """
    import random
    if not line or intensity <= 0:
        return line

    # Split by spaces FIRST to preserve overall structure
    parts = line.split(" ")
    glitched_parts = []
    
    for part in parts:
        # For each whitespace-separated part, find Japanese islands
        # We split by Kanji vs Kana transition to get more "word-like" boundaries
        tokens = re.findall(r"[\u4e00-\u9fff]+|[\u3041-\u3096\u30a1-\u30fa\u30fc]+", part)
        if not tokens:
            glitched_parts.append(part)
            continue
            
        new_part = part
        for token in tokens:
            if random.random() > intensity:
                continue
                
            # Find the best kana for the glitch in THIS token
            target_char = None
            for char in token:
                if char in ROMAJI_MAP and char not in {"ー", "っ"}:
                    target_char = char
                    break
            
            if not target_char:
                # If no specific kana found, and intensity is high, we can still repeat the token
                # but only if it's short (1-2 chars)
                if intensity > 0.5 and len(token) <= 2:
                    glitch = f"{token}-{token}"
                    new_part = new_part.replace(token, glitch, 1)
                continue
                
            romaji = ROMAJI_MAP.get(target_char)
            if style == "explosive":
                # [k-k-kako]
                if romaji and any(romaji.startswith(p) for p in PLOSIVES):
                    prefix = romaji[0]
                    glitch = f"{prefix}-{prefix}-{token}"
                    new_part = new_part.replace(token, glitch, 1)
                elif intensity > 0.4:
                    # Identity Fallback for explosive: [過-過-過去]
                    prefix = token[0]
                    glitch = f"{prefix}-{prefix}-{token}"
                    new_part = new_part.replace(token, glitch, 1)
            elif style == "melodic":
                # [a-a-ai]
                if romaji:
                    vowel = romaji[-1]
                    if vowel in VOWELS:
                        glitch = f"{vowel}-{vowel}-{token}"
                        new_part = new_part.replace(token, glitch, 1)
                elif intensity > 0.4:
                    # Identity Fallback for melodic: [過-過-過去]
                    prefix = token[0]
                    glitch = f"{prefix}-{prefix}-{token}"
                    new_part = new_part.replace(token, glitch, 1)
        
        glitched_parts.append(new_part)
        
    return " ".join(glitched_parts)

def optimize_for_suno_phonetics(text: str) -> str:
    """
    Slightly adjust text to ensure Suno handles high-speed mora correctly.
    E.g., adding explicit small 'tsu' or spaces for breathing.
    """
    # Heuristic: if a line is too dense, add a soft break [!] or space
    # This is a placeholder for more advanced Suno v6 tagging
    return text.replace(" ", "  ") # Extra spacing often helps AI focus
