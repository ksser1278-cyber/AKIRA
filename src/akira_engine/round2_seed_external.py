from __future__ import annotations

from typing import Any


def validate_round2_seed_payload(payload: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    artist_id = str(payload.get("artist_id", "")).strip()
    track_id = str(payload.get("track_id", "")).strip()
    title = str(payload.get("title", "")).strip()
    likely_mode = str(payload.get("likely_mode", "")).strip()
    title_pattern = str(payload.get("title_pattern", "")).strip()
    hook_behavior = payload.get("hook_behavior", [])
    section_flow_guess = payload.get("section_flow_guess", [])
    imagery_classes = payload.get("imagery_classes", [])
    emotional_arc = payload.get("emotional_arc", [])
    leakage_watchouts = payload.get("leakage_watchouts", [])
    prompt_seed_terms = payload.get("prompt_seed_terms", [])
    grounding_status = str(payload.get("grounding_status", "")).strip()

    if not artist_id:
        issues.append("artist_id missing")
    if not track_id:
        issues.append("track_id missing")
    if not title:
        issues.append("title missing")
    if not likely_mode:
        issues.append("likely_mode missing")
    if not title_pattern:
        issues.append("title_pattern missing")
    if not isinstance(hook_behavior, list) or len([x for x in hook_behavior if str(x).strip()]) < 1:
        issues.append("hook_behavior must be a non-empty list")
    if not isinstance(section_flow_guess, list) or len([x for x in section_flow_guess if str(x).strip()]) < 3:
        issues.append("section_flow_guess must have at least 3 entries")
    if not isinstance(imagery_classes, list) or len([x for x in imagery_classes if str(x).strip()]) < 2:
        issues.append("imagery_classes must have at least 2 entries")
    if not isinstance(emotional_arc, list) or len([x for x in emotional_arc if str(x).strip()]) < 2:
        issues.append("emotional_arc must have at least 2 entries")
    if not isinstance(leakage_watchouts, list):
        issues.append("leakage_watchouts must be a list")
    if not isinstance(prompt_seed_terms, list) or len([x for x in prompt_seed_terms if str(x).strip()]) < 2:
        issues.append("prompt_seed_terms must have at least 2 entries")
    if not grounding_status:
        issues.append("grounding_status missing")

    return issues
