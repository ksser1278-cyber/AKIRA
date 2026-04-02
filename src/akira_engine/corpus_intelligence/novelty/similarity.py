"""Novelty Index — Text Similarity & Nearest-Neighbor Search.

Provides cost-effective similarity computation using SequenceMatcher + atom overlap.
Designed to work without heavy ML dependencies (pure Python / stdlib).
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any

from src.akira_engine.corpus_intelligence.novelty.schema import NeighborHit


# ─── Constants ───────────────────────────────────────────────────────────────

# Minimum text length to consider for similarity (skip empty/trivial)
_MIN_TEXT_LENGTH = 20

# Section markers to strip before comparison
_SECTION_PATTERN = re.compile(r"^\[.*?\]$", re.MULTILINE)
_METADATA_PATTERN = re.compile(r"^(###?\s|genre:|vocal:|bpm:|style:).*$", re.MULTILINE | re.IGNORECASE)


# ─── Text Preprocessing ─────────────────────────────────────────────────────

def _clean_lyric_text(text: str) -> str:
    """Strip section markers, metadata, whitespace for clean comparison."""
    cleaned = _SECTION_PATTERN.sub("", text)
    cleaned = _METADATA_PATTERN.sub("", cleaned)
    # Collapse whitespace
    cleaned = re.sub(r"\n{2,}", "\n", cleaned)
    return cleaned.strip()


def _extract_lines(text: str) -> list[str]:
    """Extract non-empty, non-metadata lines for line-level comparison."""
    cleaned = _clean_lyric_text(text)
    return [line.strip() for line in cleaned.splitlines() if line.strip()]


# ─── Similarity Functions ────────────────────────────────────────────────────

def compute_text_similarity(text_a: str, text_b: str) -> float:
    """Compute text-level similarity using SequenceMatcher + line overlap.

    Returns 0.0 (completely different) — 1.0 (identical).
    Uses a blended approach:
      - 60% weight: SequenceMatcher ratio on cleaned full text
      - 40% weight: Line-level Jaccard overlap (exact line match)

    This is deliberately fast and dependency-free.
    """
    clean_a = _clean_lyric_text(text_a)
    clean_b = _clean_lyric_text(text_b)

    if len(clean_a) < _MIN_TEXT_LENGTH or len(clean_b) < _MIN_TEXT_LENGTH:
        return 0.0

    # Full-text sequence ratio (character-level)
    seq_ratio = SequenceMatcher(None, clean_a, clean_b).ratio()

    # Line-level Jaccard
    lines_a = set(_extract_lines(text_a))
    lines_b = set(_extract_lines(text_b))
    if not lines_a or not lines_b:
        return round(seq_ratio, 4)

    intersection = lines_a & lines_b
    union = lines_a | lines_b
    line_jaccard = len(intersection) / len(union) if union else 0.0

    # Blended
    blended = seq_ratio * 0.6 + line_jaccard * 0.4
    return round(blended, 4)


def compute_atom_jaccard(atoms_a: list[str], atoms_b: list[str]) -> float:
    """Compute Jaccard similarity at the feature-atom level.

    Args:
        atoms_a: List of lexical atoms (motif, body, scene, sound) from candidate.
        atoms_b: List of lexical atoms from reference track.

    Returns 0.0 (no overlap) — 1.0 (identical atom sets).
    """
    if not atoms_a or not atoms_b:
        return 0.0

    set_a = set(atoms_a)
    set_b = set(atoms_b)
    intersection = set_a & set_b
    union = set_a | set_b
    return round(len(intersection) / len(union), 4) if union else 0.0


def find_nearest_neighbor(
    candidate_text: str,
    candidate_atoms: list[str],
    corpus: list[dict[str, Any]],
    top_k: int = 5,
    exclude_track_id: str = "",
) -> list[NeighborHit]:
    """Search entire corpus for nearest neighbors to the candidate.

    Args:
        candidate_text: Cleaned lyric text of the candidate.
        candidate_atoms: Feature atoms extracted from the candidate.
        corpus: List of dicts with keys: track_id, artist_id, text, atoms.
        top_k: Number of top matches to return.
        exclude_track_id: Optional track_id to exclude (self-match prevention).

    Returns:
        List of NeighborHit sorted by similarity (descending), length <= top_k.
    """
    results: list[NeighborHit] = []

    for entry in corpus:
        entry_track_id = str(entry.get("track_id", ""))
        if entry_track_id == exclude_track_id:
            continue

        entry_text = str(entry.get("text", ""))
        entry_atoms = entry.get("atoms", [])

        # Blended similarity: text (70%) + atom Jaccard (30%)
        text_sim = compute_text_similarity(candidate_text, entry_text)
        atom_sim = compute_atom_jaccard(candidate_atoms, entry_atoms)
        blended = text_sim * 0.7 + atom_sim * 0.3

        results.append(NeighborHit(
            track_id=entry_track_id,
            artist_id=str(entry.get("artist_id", "")),
            similarity=round(blended, 4),
            atom_jaccard=atom_sim,
        ))

    # Sort descending by similarity
    results.sort(key=lambda h: h.similarity, reverse=True)
    return results[:top_k]
