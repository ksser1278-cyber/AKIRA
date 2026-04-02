# src/akira_engine/critic/originality.py

from __future__ import annotations

import math
from typing import Any, Dict, List, Set


def calculate_set_cosine_similarity(set_a: Set[str], set_b: Set[str]) -> float:
    """Calculates cosine similarity between two sets (binary vectors)."""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a.intersection(set_b))
    return intersection / math.sqrt(len(set_a) * len(set_b))


def calculate_originality_metrics(
    current_track: Dict[str, Any],
    comparison_tracks: List[Dict[str, Any]],
    base_cliche_bank: Set[str] = None
) -> Dict[str, Any]:
    """Calculates deep originality metrics for a candidate track.
    
    Weights:
    - 0.6: Motif vector overlap
    - 0.2: Hook grammar similarity
    - 0.1: Section progression similarity
    - 0.1: Imagery axis overlap
    """
    if not comparison_tracks:
        return {
            "composite_originality": 1.0,
            "nearest_neighbor_similarity": 0.0,
            "cliche_density": 0.0,
            "recombinative_novelty": 0.8  # Default high for first track
        }

    # Extract current features
    curr_motifs = set(current_track.get("motifs", []))
    curr_hooks = set(current_track.get("hooks", []))
    curr_sections = tuple(current_track.get("section_names", []))
    curr_imagery = set(current_track.get("imagery", []))

    max_sim = 0.0
    nearest_id = ""

    for other in comparison_tracks:
        other_motifs = set(other.get("motifs", []))
        other_hooks = set(other.get("hooks", []))
        other_sections = tuple(other.get("section_names", []))
        other_imagery = set(other.get("imagery", []))

        # 1. Motif Similarity (0.6)
        motif_sim = calculate_set_cosine_similarity(curr_motifs, other_motifs)
        
        # 2. Hook Similarity (0.2)
        hook_sim = calculate_set_cosine_similarity(curr_hooks, other_hooks)
        
        # 3. Section Similarity (0.1)
        # Use Jaccard or Sequence similarity? User said 'progression similarity'.
        # For Day 1, we use set-based overlap as a proxy, or ordered overlap.
        section_sim = calculate_set_cosine_similarity(set(curr_sections), set(other_sections))
        
        # 4. Imagery Similarity (0.1)
        imagery_sim = calculate_set_cosine_similarity(curr_imagery, other_imagery)

        # Composite Result for THIS neighbor
        composite = (motif_sim * 0.6) + (hook_sim * 0.2) + (section_sim * 0.1) + (imagery_sim * 0.1)
        
        if composite > max_sim:
            max_sim = composite
            nearest_id = other.get("track_id", "unknown")

    # Cliché Density
    cliche_hits = 0
    if base_cliche_bank and curr_motifs:
        cliche_hits = len(curr_motifs.intersection(base_cliche_bank))
        cliche_density = cliche_hits / len(curr_motifs)
    else:
        cliche_density = 0.0

    return {
        "composite_originality": round(1.0 - max_sim, 4),
        "nearest_neighbor_similarity": round(max_sim, 4),
        "nearest_neighbor_id": nearest_id,
        "cliche_density": round(cliche_density, 4),
        "motif_overlap_ratio": round(len(curr_motifs.intersection(set(curr_motifs))) / max(1, len(curr_motifs)), 4)
    }
