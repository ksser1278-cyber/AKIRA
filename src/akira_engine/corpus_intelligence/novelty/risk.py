"""Novelty Index — Risk Scoring.

Evaluates originality risks: artist imitation, cliché density, and recombinative novelty.
These scores feed into the NoveltyProfile composite.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any


# ─── Cliché Patterns ────────────────────────────────────────────────────────
# High-frequency patterns in J-Pop that indicate low originality.
# These are common lyrical tropes that the engine should learn to avoid or minimize.

JPOP_CLICHE_PATTERNS: list[str] = [
    # Emotional abstractions (overused without grounding)
    "永遠に", "世界の果て", "約束した", "君がいない", "涙が", "夢の中",
    "時が止まる", "最後の", "何もない", "消えたい", "壊れた",
    # Relational tropes
    "二人だけの", "手を繋いで", "振り返らない", "出会いと別れ",
    # Repetitive fillers
    "ああ", "ねえ", "もう一度",
]

# Compiled for efficient line scanning
_CLICHE_RE = re.compile("|".join(re.escape(p) for p in JPOP_CLICHE_PATTERNS))


# ─── Artist Imitation Risk ──────────────────────────────────────────────────

def score_artist_imitation_risk(
    candidate_text: str,
    candidate_atoms: list[str],
    artist_corpus: list[dict[str, Any]],
) -> float:
    """Score how much a candidate concentrates on a single artist's lyrical DNA.

    Measures two axes:
      1. Text overlap: How similar the candidate is to the artist's most similar track.
      2. Atom concentration: What fraction of the candidate's atoms appear in the artist's vocabulary.

    Args:
        candidate_text: Cleaned lyric text.
        candidate_atoms: Atoms extracted from candidate.
        artist_corpus: List of dicts with keys: text, atoms (all from one artist).

    Returns:
        0.0 (no risk) — 1.0 (near-direct copy from this artist).
    """
    if not artist_corpus or not candidate_text:
        return 0.0

    from src.akira_engine.corpus_intelligence.novelty.similarity import (
        compute_text_similarity, compute_atom_jaccard,
    )

    # 1. Max text similarity to any track by this artist
    max_text_sim = 0.0
    for entry in artist_corpus:
        sim = compute_text_similarity(candidate_text, str(entry.get("text", "")))
        if sim > max_text_sim:
            max_text_sim = sim

    # 2. Atom vocabulary concentration
    artist_vocab: set[str] = set()
    for entry in artist_corpus:
        artist_vocab.update(entry.get("atoms", []))

    if candidate_atoms and artist_vocab:
        candidate_set = set(candidate_atoms)
        overlap = candidate_set & artist_vocab
        atom_concentration = len(overlap) / len(candidate_set) if candidate_set else 0.0
    else:
        atom_concentration = 0.0

    # Blended: text similarity (60%) + atom concentration (40%)
    risk = max_text_sim * 0.6 + atom_concentration * 0.4
    return round(min(1.0, risk), 4)


def score_cliche_density(text: str) -> float:
    """Score the proportion of lines containing high-frequency cliché patterns.

    Returns 0.0 (no clichés) — 1.0 (every line contains clichés).
    """
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if not lines:
        return 0.0

    # Filter out section markers and metadata
    lyric_lines = [
        l for l in lines
        if not (l.startswith("[") and l.endswith("]"))
        and not l.startswith("#")
        and ":" not in l[:10]  # Skip metadata-like lines
    ]

    if not lyric_lines:
        return 0.0

    cliche_lines = sum(1 for line in lyric_lines if _CLICHE_RE.search(line))
    return round(cliche_lines / len(lyric_lines), 4)


# ─── Recombinative Novelty ──────────────────────────────────────────────────

def score_recombinative_novelty(
    candidate_atoms: list[str],
    cluster_memberships: list[str] | None = None,
    atom_cluster_map: dict[str, str] | None = None,
) -> float:
    """Score how many different stylistic cluster axes the candidate combines.

    Higher score = more creative cross-pollination. An atom set that draws from
    a single cluster is not recombinative; one that mixes 4+ clusters is novel.

    Args:
        candidate_atoms: List of feature atoms from the candidate.
        cluster_memberships: Explicit cluster labels assigned to the candidate.
            (Available after Week 2 clusters are built.)
        atom_cluster_map: Dict mapping atom -> cluster_id.
            (Available after Week 2 clusters are built.)

    Returns:
        0.0 (single source) — 1.0 (high cross-cluster mixing).
    """
    if not candidate_atoms:
        return 0.0

    # Phase 1 fallback: Use atom category diversity as proxy
    # (Full cluster-based scoring activates after Week 2)
    if atom_cluster_map:
        # Map atoms to clusters
        clusters_hit: set[str] = set()
        for atom in candidate_atoms:
            if atom in atom_cluster_map:
                clusters_hit.add(atom_cluster_map[atom])

        if not clusters_hit:
            return 0.3  # Unknown atoms = moderate novelty

        # Scale: 1 cluster = 0.1, 2 = 0.3, 3 = 0.5, 4 = 0.7, 5+ = 0.9
        n = len(clusters_hit)
        if n >= 5:
            return 0.9
        elif n >= 4:
            return 0.7
        elif n >= 3:
            return 0.5
        elif n >= 2:
            return 0.3
        else:
            return 0.1

    elif cluster_memberships:
        unique = set(cluster_memberships)
        n = len(unique)
        if n >= 4:
            return 0.9
        elif n >= 3:
            return 0.6
        elif n >= 2:
            return 0.4
        return 0.15

    else:
        # Pre-clustering fallback: Use atom category diversity
        # Category heuristic based on features/mod.py
        from src.akira_engine.features.mod import (
            BODY_KEYWORDS, SCENE_KEYWORDS, SOUND_KEYWORDS,
        )

        categories_hit: set[str] = set()
        for atom in candidate_atoms:
            if atom in BODY_KEYWORDS:
                categories_hit.add("body")
            elif atom in SCENE_KEYWORDS:
                categories_hit.add("scene")
            elif atom in SOUND_KEYWORDS:
                categories_hit.add("sound")
            else:
                categories_hit.add("motif")

        n = len(categories_hit)
        # 1 cat = 0.1, 2 = 0.3, 3 = 0.5, 4 = 0.7
        return round(min(1.0, n * 0.2 - 0.1), 2) if n > 0 else 0.0
