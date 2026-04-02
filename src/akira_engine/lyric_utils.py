from __future__ import annotations

import re
from typing import Any

# Patterns for Japanese text analysis
JAPANESE_ATOM_PATTERN = re.compile(r"[ァ-ヶー]{2,}|[一-龯々]{1,3}[ぁ-ん]{1,4}|[一-龯々]{2,5}")
SAFE_PROMPT_TERM_PATTERN = re.compile(r"[A-Za-z0-9ぁ-んァ-ヶー一-龯々]")

# Stopwords and trim suffixes for lexical atom extraction
GENERIC_ATOM_STOPWORDS = {
    "こと", "もの", "それ", "これ", "あれ", "ため", "よう", "まま", "だけ", "ほど", "どこ", "なに", "全部", "一切",
}

ATOM_TRIM_SUFFIXES_JP = (
    "という", "とは", "とか", "だって", "される", "され", "する", "してる", "して", "した", "したら",
    "だもの", "だよ", "まで", "だけ", "さえ", "ほど", "より", "から", "たり", "だっ", "です", "ます",
    "ない", "たい", "とい", "の", "は", "が", "へ", "と", "も", "で", "か", "よ", "た",
)

def contains_japanese(text: str) -> bool:
    """Check if the text contains any Japanese characters (Hiragana, Katakana, or Kanji)."""
    return any(("\u3040" <= ch <= "\u30ff") or ("\u4e00" <= ch <= "\u9fff") for ch in text)

def contains_bad_script(text: str) -> bool:
    """Check for Hangul or corrupted characters in the context of AKIRA ENGINE Japanese focus."""
    # Expanded Hangul ranges: Syllables (AC00-D7AF), Jamo (1100-11FF), Compatibility Jamo (3130-318F)
    hangul_pattern = re.compile(r'[\uac00-\ud7af\u1100-\u11ff\u3130-\u318f]')
    return bool(hangul_pattern.search(text)) or "\ufffd" in text

def safe_text(value: Any, fallback: str = "") -> str:
    """Safely convert any value to a stripped string, with an optional fallback."""
    text = str(value or "").strip()
    return text or fallback

def unique_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        cleaned = str(item).strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            output.append(cleaned)
    return output

def is_safe_prompt_term(term: str) -> bool:
    cleaned = str(term).strip()
    if not cleaned:
        return False
    visible = cleaned.replace(" ", "")
    matches = SAFE_PROMPT_TERM_PATTERN.findall(visible)
    if not matches:
        return False
    return len(matches) / max(1, len(visible)) >= 0.45

def is_safe_lyric_term(term: str) -> bool:
    cleaned = str(term).strip()
    if not is_safe_prompt_term(cleaned):
        return False
    return bool(re.search(r"[\u3041-\u3096\u30a1-\u30fa\u30fc\u4e00-\u9fff]", cleaned))

def looks_corrupted_text(value: Any) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    if "?" in text:
        return True
    visible = re.sub(r"\s+", "", text)
    if not visible:
        return False
    # Detect Hangul contamination (Korean characters in Japanese engine)
    if contains_bad_script(visible):
        return True
    return False

def extract_japanese_lexical_atoms(values: list[Any], *, limit: int | None = None) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value or "").strip()
        if not text:
            continue
        cleaned = re.sub(r"[「」『』\[\]!?？！…。、,./]", " ", text)
        for match in JAPANESE_ATOM_PATTERN.finditer(cleaned):
            atom = match.group(0).strip()
            changed = True
            while changed:
                changed = False
                for suffix in ATOM_TRIM_SUFFIXES_JP:
                    if atom.endswith(suffix) and len(atom) - len(suffix) >= 1:
                        atom = atom[: -len(suffix)]
                        changed = True
                        break
            if len(atom) < 2:
                continue
            if atom in GENERIC_ATOM_STOPWORDS:
                continue
            if atom not in seen:
                seen.add(atom)
                output.append(atom)
                if limit is not None and len(output) >= limit:
                    return output
    return output
