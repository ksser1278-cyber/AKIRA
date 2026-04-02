"""Style Clusters — Auto-Labeling & Recombination Discovery.

Generates human-readable labels for clusters based on dominant atoms
and category profiles, and discovers distant cluster pairs suitable
for creative cross-pollination.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from src.akira_engine.features.mod import (
    BODY_KEYWORDS, SCENE_KEYWORDS, SOUND_KEYWORDS,
)
from src.akira_engine.corpus_intelligence.clusters.schema import StyleCluster


# ─── Emotional Lexicon ───────────────────────────────────────────────────────
# Maps common motif atoms to emotional labels for auto-profiling.

_EMOTIONAL_LEXICON: dict[str, str] = {
    # Dark / Intense
    "痛み": "dark", "叫び": "intense", "血": "dark", "毒": "dark",
    "壊れ": "dark", "狂": "chaotic", "闇": "dark", "絶望": "despair",
    "殺": "violent", "死": "dark",
    # Tender / Warm
    "愛": "tender", "優しい": "tender", "温": "warm", "光": "hopeful",
    "笑顔": "warm", "桜": "nostalgic", "花": "gentle", "守": "protective",
    "大切な": "tender", "想い": "tender",
    # Melancholic / Nostalgic
    "夢": "melancholic", "涙": "melancholic", "雨": "melancholic",
    "消え": "melancholic", "忘れ": "nostalgic", "過去": "nostalgic",
    "思い出": "nostalgic", "別れ": "melancholic",
    # Energetic / Chaotic
    "叫び": "energetic", "爆": "explosive", "走": "energetic",
    "衝動": "explosive", "熱": "passionate",
    # Abstract / Philosophical
    "世界": "philosophical", "運命": "philosophical", "永遠": "philosophical",
    "真実": "philosophical", "心": "introspective",
    # Sensory
    "甘い": "sweet", "苦い": "bitter", "冷たい": "cold",
}

# Category-based label prefixes
_CATEGORY_LABELS: dict[str, str] = {
    "body_heavy": "somatic",     # High body atom ratio
    "scene_heavy": "scenic",      # High scene atom ratio
    "sound_heavy": "sonic",       # High sound atom ratio
    "abstract_heavy": "abstract", # High abstract ratio
    "dense": "dense",             # High atom count
    "sparse": "minimal",          # Low atom count
}


# ─── Labeling ────────────────────────────────────────────────────────────────

def label_cluster(
    cluster_atoms: list[str],
    category_ratios: dict[str, float],
    abstract_ratio: float = 0.0,
    atom_count_mean: float = 20.0,
) -> tuple[str, list[str]]:
    """Generate a human-readable label and emotional profile for a cluster.

    Args:
        cluster_atoms: Most frequent atoms in the cluster (top N).
        category_ratios: Dict with keys body, scene, sound, motif and float ratios.
        abstract_ratio: Mean abstract ratio across cluster members.
        atom_count_mean: Mean atom count across cluster members.

    Returns:
        Tuple of (label_string, emotional_tags).
    """
    parts: list[str] = []
    emotional_tags: list[str] = []

    # 1. Category-based prefix
    body_r = category_ratios.get("body", 0.0)
    scene_r = category_ratios.get("scene", 0.0)
    sound_r = category_ratios.get("sound", 0.0)

    if body_r > 0.15:
        parts.append("somatic")
    elif scene_r > 0.15:
        parts.append("scenic")
    elif sound_r > 0.15:
        parts.append("sonic")

    if abstract_ratio > 0.3:
        parts.append("abstract")
    elif abstract_ratio < 0.05:
        parts.append("concrete")

    if atom_count_mean > 35:
        parts.append("dense")
    elif atom_count_mean < 12:
        parts.append("minimal")

    # 2. Emotional profiling from dominant atoms
    emotion_counter: Counter = Counter()
    for atom in cluster_atoms[:20]:
        # Check partial match
        for keyword, emotion in _EMOTIONAL_LEXICON.items():
            if keyword in atom:
                emotion_counter[emotion] += 1
                break

    top_emotions = [e for e, _ in emotion_counter.most_common(3)]
    emotional_tags = top_emotions if top_emotions else ["neutral"]

    # Add top emotion as label part
    if top_emotions:
        parts.append(top_emotions[0])
    else:
        parts.append("neutral")

    # 3. Build label string
    label = "_".join(parts) if parts else "unclassified"
    return label, emotional_tags


def find_distant_cluster_pairs(
    clusters: list[StyleCluster],
    centroids: list[list[float]],
    top_n: int = 5,
) -> list[tuple[str, str, float]]:
    """Find the most distant cluster pairs for creative recombination.

    Distant clusters have the most different stylistic profiles, making them
    ideal candidates for novel cross-pollination.

    Args:
        clusters: List of StyleCluster objects.
        centroids: Corresponding centroid vectors.
        top_n: Number of distant pairs to return.

    Returns:
        List of (cluster_id_a, cluster_id_b, distance) sorted by distance desc.
    """
    if len(clusters) < 2:
        return []

    import math
    pairs: list[tuple[str, str, float]] = []

    for i in range(len(clusters)):
        for j in range(i + 1, len(clusters)):
            if i < len(centroids) and j < len(centroids):
                dist = math.sqrt(
                    sum((a - b) ** 2 for a, b in zip(centroids[i], centroids[j]))
                )
                pairs.append((
                    clusters[i].cluster_id,
                    clusters[j].cluster_id,
                    round(dist, 4),
                ))

    pairs.sort(key=lambda p: p[2], reverse=True)
    return pairs[:top_n]


def build_atom_cluster_map(
    clusters: list[StyleCluster],
) -> dict[str, str]:
    """Build a mapping from atom → primary cluster_id.

    For atoms that appear in multiple clusters, assigns to the cluster
    where the atom is most dominant (appears first in dominant_atoms).

    Returns:
        Dict mapping atom string to cluster_id.
    """
    atom_map: dict[str, str] = {}
    # Process clusters in order; first claim wins (dominant_atoms are sorted by freq)
    for cluster in clusters:
        for atom in cluster.dominant_atoms:
            if atom not in atom_map:
                atom_map[atom] = cluster.cluster_id

    return atom_map
