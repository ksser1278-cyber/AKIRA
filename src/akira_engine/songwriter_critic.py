from __future__ import annotations
import re
from collections import Counter
from typing import Any

from .lyric_utils import unique_preserve_order, extract_japanese_lexical_atoms, is_safe_lyric_term
from .japanese_lyric_features import build_markdown_japanese_profile
from .lyric_draft import extract_section_blocks, lyric_lines

def first_lines(markdown_text: str) -> list[str]:
    lines: list[str] = []
    for _, section_lines in extract_section_blocks(markdown_text):
        if section_lines:
            lines.append(section_lines[0])
    return lines

def motif_match_terms(motif: str) -> list[str]:
    cleaned = str(motif or "").strip()
    if not cleaned:
        return []
    terms = [cleaned]
    if "言葉はいらない" in cleaned and "キスをして" in cleaned:
        terms.extend(["言葉はいらない", "キス", "食らいつく", "噛みつく", "噛み砕いて"])
    elif "キスをして" in cleaned:
        terms.extend(["キス", "食らいつく", "噛みつく"])
    if "弾け飛んだ" in cleaned:
        terms.extend(["弾け飛んだ", "弾け", "飛んだ"])
    if "本音ばかり" in cleaned:
        terms.extend(["本音ばかり", "本音"])
    if "寄る" in cleaned:
        terms.extend(["寄る辺ない", "侘しさ"])
    if "新時代はこ" in cleaned:
        terms.extend(["新時代", "未来"])
    if cleaned.endswith("未来だ") or "この未来" in cleaned:
        terms.append("未来")
    if "世界中全部" in cleaned:
        terms.extend(["世界", "塗り替える"])
    if "変えてしま" in cleaned:
        terms.extend(["変える", "塗り替える"])
    if "果てしない音楽" in cleaned:
        terms.append("音楽")
    terms.extend(extract_japanese_lexical_atoms([cleaned], limit=4))
    return unique_preserve_order(term for term in terms if term and len(term) >= 2)

def motif_matches_text(motif: str, text: str) -> bool:
    return any(term in text for term in motif_match_terms(motif))

def motif_coverage_score(plan: dict[str, Any], markdown_text: str) -> float:
    body = markdown_text
    required = [motif for item in plan["motif_roster"] for motif in item.get("motifs", [])[:2]]
    required = unique_preserve_order(required)
    if not required:
        return 0.0
    hits = sum(1 for motif in required if motif_matches_text(motif, body))
    return round(min(1.0, hits / max(4, len(required) * 0.6)), 2)

def plan_alignment_score(plan: dict[str, Any], markdown_text: str) -> float:
    section_lookup = {section: lines for section, lines in extract_section_blocks(markdown_text)}
    hits = 0
    possible = 0
    for card in plan["section_cards"]:
        section = card["section"]
        if section not in section_lookup:
            continue
        possible += 1
        body = " ".join(section_lookup[section])
        required_motifs = [motif for motif in card.get("required_motifs", [])[:2] if motif]
        if not required_motifs:
            hits += 1
            continue
        if any(motif_matches_text(motif, body) for motif in required_motifs):
            hits += 1
    return round(hits / max(1, possible), 2)
