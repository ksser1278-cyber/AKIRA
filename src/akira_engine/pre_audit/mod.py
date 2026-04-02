from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class PreAuditResult:
    passed: bool
    severity: str           # warning | soft_fail | hard_fail
    diagnostics: list[str] = field(default_factory=list)
    imagery_coverage: float = 0.0
    structural_match: float = 0.0
    identity_match: bool = False

def run_pre_audit_stage(
    conditioning: Any, # ConditioningResult
    plan: Any          # PlanResult
) -> PreAuditResult:
    """Execute Stage E: Pre-Audit (Integrity Checker)."""
    
    diagnostics = []
    
    # 1. Identity Match (Hard Fail Criterion)
    # Check artist_id and mode_id compatibility
    plan_artist = getattr(plan, "artist_id", "")
    cond_artist = getattr(conditioning, "artist_id", "")
    plan_mode = getattr(plan, "mode_id", "")
    # Note: conditioning might not have mode_id at top level, check song_intent or separate field
    # For now, let's look at common artist_id consistency
    identity_match = (plan_artist == cond_artist)
    if not identity_match:
        diagnostics.append(f"Identity mismatch: Plan artist '{plan_artist}' vs Conditioning artist '{cond_artist}'")

    # 2. Imagery Coverage
    required_imagery = getattr(conditioning, "imagery_anchors", [])
    if not required_imagery and hasattr(conditioning, "prompt_conditioning"):
        required_imagery = conditioning.prompt_conditioning.get("imagery_anchors", [])
    
    plan_atoms = set()
    for card in getattr(plan, "section_cards", []):
        card_dict = card.__dict__ if hasattr(card, "__dict__") else card
        plan_atoms.update(card_dict.get("imagery_focus", []))
        plan_atoms.update(card_dict.get("required_motifs", []))
        plan_atoms.update(card_dict.get("required_imagery", []))
        
    unique_required = list(set(required_imagery))
    hits = [atom for atom in unique_required if atom in plan_atoms]
    imagery_coverage = round(len(hits) / len(unique_required), 2) if unique_required else 1.0
    
    if imagery_coverage < 1.0:
        diagnostics.append(f"Imagery coverage: {int(imagery_coverage * 100)}% ({len(hits)}/{len(unique_required)})")
        missing = [atom for atom in unique_required if atom not in plan_atoms]
        if missing:
            diagnostics.append(f"Missing required atoms: {', '.join(missing[:5])}")

    # 3. Structural Match
    cond_sections = getattr(conditioning, "normalized_sections", [])
    plan_cards = getattr(plan, "section_cards", [])
    
    matches = 0
    total = max(len(cond_sections), len(plan_cards))
    for i in range(min(len(cond_sections), len(plan_cards))):
        c_sec = cond_sections[i].get("section", "")
        p_sec = getattr(plan_cards[i], "section", "")
        if c_sec == p_sec:
            matches += 1
            
    structural_match = round(matches / total, 2) if total > 0 else 1.0
    if structural_match < 1.0:
        diagnostics.append(f"Structural match: {int(structural_match * 100)}% ({matches}/{total} sections)")

    # 4. Severity Verdict (Warning Mode for Phase 1)
    severity = "warning"
    passed = True # Phase 1 always passes but logs diagnostics
    
    if not identity_match or structural_match < 0.5:
        severity = "hard_fail"
        # In Hard Gate phase, passed would be False
    elif imagery_coverage < 0.4:
        severity = "soft_fail"
    elif imagery_coverage < 0.8 or structural_match < 0.9:
        severity = "warning"
    else:
        severity = "pass"

    return PreAuditResult(
        passed=passed,
        severity=severity,
        diagnostics=diagnostics,
        imagery_coverage=imagery_coverage,
        structural_match=structural_match,
        identity_match=identity_match
    )
