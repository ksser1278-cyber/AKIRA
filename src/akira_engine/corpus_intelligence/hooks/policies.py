# src/akira_engine/corpus_intelligence/hooks/policies.py
"""Hook Grammar Safety Policies (Day 7).

Prevents the hook grammar bank from becoming a copy-paste template.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Set


class HookGrammarPolicy:
    """Safety constraints on hook grammar usage."""

    # Maximum consecutive uses of the same syllable pattern
    MAX_CONSECUTIVE_SAME_PATTERN = 3
    
    # Maximum percentage of recent tracks using the same top pattern
    MAX_PATTERN_SATURATION = 0.4
    
    # Exclamation density threshold (e.g., "(Ah-hah)", "Hey!", etc.)
    MAX_EXCLAMATION_RATIO = 0.15  # 15% of total tokens
    
    # Title ignition grammar (title repeated in hook) max ratio
    MAX_TITLE_IGNITION_RATIO = 0.6  # 60% of recent hooks


def check_hook_safety(
    proposed_hook: Dict[str, Any],
    recent_hooks: List[Dict[str, Any]],
    max_recent: int = 20
) -> Dict[str, Any]:
    """Check if a proposed hook violates safety policies.
    
    Returns {'safe': bool, 'violations': list, 'penalties': dict}
    """
    policy = HookGrammarPolicy()
    violations = []
    penalties = {}
    
    pool = recent_hooks[:max_recent]
    proposed_pattern = proposed_hook.get("pattern", "")
    proposed_excl = proposed_hook.get("exclamation_count", 0)
    proposed_tokens = max(1, proposed_hook.get("token_count", 1))
    proposed_title_ignition = proposed_hook.get("title_ignition", False)
    
    # 1. Consecutive pattern check
    consecutive = 0
    for h in pool:
        if h.get("pattern") == proposed_pattern:
            consecutive += 1
        else:
            break
    
    if consecutive >= policy.MAX_CONSECUTIVE_SAME_PATTERN:
        violations.append("hook_pattern_consecutive_limit")
        penalties["pattern_penalty"] = -0.2
    
    # 2. Pattern saturation check
    if pool:
        pattern_counts = Counter(h.get("pattern") for h in pool)
        saturation = pattern_counts.get(proposed_pattern, 0) / len(pool)
        if saturation >= policy.MAX_PATTERN_SATURATION:
            violations.append("hook_pattern_saturated")
            penalties["saturation_penalty"] = -0.15
    
    # 3. Exclamation density check
    excl_ratio = proposed_excl / proposed_tokens
    if excl_ratio > policy.MAX_EXCLAMATION_RATIO:
        violations.append("hook_exclamation_overuse")
        penalties["exclamation_penalty"] = -0.1
    
    # 4. Title ignition overuse check
    if proposed_title_ignition and pool:
        ignition_count = sum(1 for h in pool if h.get("title_ignition"))
        ignition_ratio = ignition_count / len(pool)
        if ignition_ratio >= policy.MAX_TITLE_IGNITION_RATIO:
            violations.append("title_ignition_overuse")
            penalties["ignition_penalty"] = -0.1
    
    return {
        "safe": len(violations) == 0,
        "violations": violations,
        "penalties": penalties,
        "total_penalty": sum(penalties.values())
    }


def apply_hook_penalty_to_score(base_score: float, hook_check: Dict[str, Any]) -> float:
    """Applies hook safety penalties to a candidate's score."""
    return max(0.0, base_score + (hook_check.get("total_penalty", 0.0) * 100))
