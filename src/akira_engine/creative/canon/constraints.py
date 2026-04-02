# src/akira_engine/creative/canon/constraints.py

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Optional


def check_diversity_constraints(
    current_features: Dict[str, Any],
    recent_tracks: List[Dict[str, Any]],
    quota_limit: float = 0.25,
    max_recent_check: int = 100
) -> Dict[str, Any]:
    """Checks diversity constraints for a candidate track against recent canon.
    
    Returns a dict with 'passed' and 'reasons'.
    """
    reasons = []
    
    if not recent_tracks:
        return {"passed": True, "reasons": []}

    # Slice to recent N
    check_pool = recent_tracks[:max_recent_check]
    pool_size = len(check_pool)

    # 1. Cluster Quota (Hard Cap: 25%)
    curr_cluster = current_features.get("cluster_id")
    if curr_cluster and curr_cluster != "unknown":
        cluster_counts = Counter(t.get("cluster_id") for t in check_pool)
        usage_ratio = cluster_counts[curr_cluster] / pool_size
        if usage_ratio >= quota_limit and pool_size >= 20: # Wait for enough samples
            reasons.append("cluster_quota_exceeded")

    # 2. Hook Grammar Continuity (Max 3 consecutive)
    curr_hook_grammars = set(current_track_hooks := current_features.get("hooks", []))
    if curr_hook_grammars:
        # Check last 3 tracks
        consecutive_matches = 0
        for other in recent_tracks[:3]:
            other_hooks = set(other.get("hooks", []))
            if curr_hook_grammars.intersection(other_hooks):
                consecutive_matches += 1
            else:
                break
        
        if consecutive_matches >= 3:
            reasons.append("hook_grammar_continuity_limit")

    # 3. Recency Distance (Min similarity for most recent N)
    # Check if TOO similar to the last 5 tracks (even if acceptable overall originality)
    for i, other in enumerate(recent_tracks[:5]):
        # Reuse set-based overlap logic or local simple overlap
        curr_motifs = set(current_features.get("motifs", []))
        other_motifs = set(other.get("motifs", []))
        if len(curr_motifs.intersection(other_motifs)) / max(1, len(curr_motifs)) > 0.8:
            reasons.append("recent_canon_too_close")
            break

    return {
        "passed": len(reasons) == 0,
        "reasons": reasons,
        "diagnostics": {
            "cluster_usage_ratio": usage_ratio if 'usage_ratio' in locals() else 0.0,
            "pool_size": pool_size
        }
    }


def apply_underrepresented_bonus(
    current_features: Dict[str, Any],
    recent_tracks: List[Dict[str, Any]]
) -> float:
    """Provides a boost to tracks from clusters that are rare in the recent canon."""
    if not recent_tracks:
        return 0.0
        
    curr_cluster = current_features.get("cluster_id")
    if not curr_cluster or curr_cluster == "unknown":
        return 0.0
        
    check_pool = recent_tracks[:100]
    cluster_counts = Counter(t.get("cluster_id") for t in check_pool)
    
    # If this cluster is < 5% of recent canon, give a small bonus
    usage_ratio = cluster_counts[curr_cluster] / len(check_pool)
    if usage_ratio < 0.05:
        return 5.0 # +5 points to craft_score or similar
    return 0.0
