from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

@dataclass
class FeatureProfile:
    track_id: str
    motif_atoms: list[str] = field(default_factory=list)
    scene_atoms: list[str] = field(default_factory=list)
    body_atoms: list[str] = field(default_factory=list)
    sound_atoms: list[str] = field(default_factory=list)
    abstract_ratio: float = 0.0
    repeat_density: float = 0.0
    status: str = "pending"

# Patterns for Japanese text analysis
# Allows: Katakana(2+), Kanji+Hiragana combo, or Kanji(1-5)
JAPANESE_ATOM_PATTERN = re.compile(r"[ァ-ヶー]{2,}|[一-龯々]{1,3}[ぁ-ん]{1,4}|[一-龯々]{1,5}")

# Stopwords and trim suffixes for lexical atom extraction
GENERIC_ATOM_STOPWORDS = {
    "こと", "もの", "それ", "これ", "あれ", "ため", "よう", "まま", "ほど", "どこ", "なに", "全部", "一切",
    "君", "僕", "俺", "私", "あなた", "僕ら", "君ら", "誰", "どこか", "いつか", "の", "に", "を", "は", "が", "へ", "と", "も", "で",
}

ATOM_TRIM_SUFFIXES_JP = (
    "だ", "です", "ます", "た", "る", "ない", "たい", "ながら", "けれど", "の", "に", "を", "は", "が", "へ", "と", "も", "で",
    "まで", "から", "より", "ほど", "くらい", "ばかり", "とか", "たり", "だり", "なら", "たら", "れば",
)

# Japanese Sensory Categories (Seed Data)
BODY_KEYWORDS = {"喉", "指先", "視線", "脈", "爪", "鼓動", "体温", "息", "聲", "瞳", "胸", "肌", "腕", "足音"}
SCENE_KEYWORDS = {"蛍光", "教室", "窓", "雨", "影", "公園", "階段", "ガラス", "路地", "空", "月", "太陽", "夜", "都会"}
SOUND_KEYWORDS = {"ノイズ", "ざわめき", "響き", "静寂", "叫び", "歌", "残響", "音", "リズム", "メロディ"}

def extract_atoms(text: str) -> list[str]:
    """Basic lexical atom extraction logic."""
    output: list[str] = []
    seen: set[str] = set()
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
        # Length check: allow 1-char only if it is a Kanji
        is_kanji = bool(re.match(r"[一-龯々]", atom))
        if (not is_kanji and len(atom) < 2) or (is_kanji and len(atom) < 1):
            continue
        if atom in GENERIC_ATOM_STOPWORDS:
            continue
        if atom not in seen:
            seen.add(atom)
            output.append(atom)
    return output

def categorize_atoms(atoms: list[str]) -> tuple[list[str], list[str], list[str], list[str]]:
    """Categorize atoms into sensory groups."""
    body, scene, sound, motif = [], [], [], []
    for a in atoms:
        if a in BODY_KEYWORDS: body.append(a)
        elif a in SCENE_KEYWORDS: scene.append(a)
        elif a in SOUND_KEYWORDS: sound.append(a)
        else: motif.append(a)
    return body, scene, sound, motif

def calculate_abstract_ratio(text: str) -> float:
    """Heuristic for abstract phrasing (e.g., emotional labels)."""
    abstract_markers = ["愛", "希望", "絶望", "運命", "永遠", "幸福", "悲哀", "孤独"]
    total_tokens = len(text.split())
    if total_tokens == 0: return 0.0
    hits = sum(1 for m in abstract_markers if m in text)
    return round(hits / max(1, total_tokens / 10), 2)

def run_features_stage(track_id: str, normalized_text: str) -> FeatureProfile:
    """Execute Stage C: Feature & Atom Extraction."""
    profile = FeatureProfile(track_id=track_id)
    
    atoms = extract_atoms(normalized_text)
    body, scene, sound, motif = categorize_atoms(atoms)
    
    profile.body_atoms = body
    profile.scene_atoms = scene
    profile.sound_atoms = sound
    profile.motif_atoms = motif
    
    profile.abstract_ratio = calculate_abstract_ratio(normalized_text)
    
    # Simple repeat density based on line-level overlap
    lines = [l.strip() for l in normalized_text.splitlines() if l.strip()]
    if lines:
        unique_lines = set(lines)
        profile.repeat_density = round(1.0 - (len(unique_lines) / len(lines)), 3)
        
    profile.status = "extracted"
    return profile
