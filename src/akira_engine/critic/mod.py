from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from src.akira_engine.lexical_family_bank import score_demo_cliche_density, score_family_diversity
from src.akira_engine.normalize.mod import calculate_script_ratios, contains_bad_script

@dataclass
class HardGate:
    passed: bool
    reasons: list[str] = field(default_factory=list)

@dataclass
class CriticResult:
    candidate_id: str
    hard_gate: HardGate
    scores: dict[str, float] = field(default_factory=dict)
    diagnostics: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    honest_metrics_active: bool = False

def _lyric_lines(text: str) -> list[str]:
    lines = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or (line.startswith("[") and line.endswith("]")):
            continue
        # vNext: Filter out metadata-heavy common labels
        if ":" in line and not any(q in line for q in ["「", "」", "『", "』"]):
            continue
        lines.append(line)
    return lines

def _extract_pure_lyric_body(text: str) -> str:
    """Extraction logic for script ratio calculations (excludes metadata/brackets)."""
    pure_lines = []
    is_metadata_block = False
    for raw in text.splitlines():
        line = raw.strip()
        if not line: continue
        
        # Detect metadata blocks
        if line.lower().startswith("### style") or line.lower().startswith("# metadata") or line.lower().startswith("genre:") or line.lower().startswith("vocal:"):
            is_metadata_block = True
            continue
            
        # Detect end of metadata (usually a section bracket or first non-colon line)
        if is_metadata_block and line.startswith("["):
            is_metadata_block = False
            
        if is_metadata_block: continue
        
        # Skip section markers and headers for ratio purposes
        if line.startswith("[") and line.endswith("]"): continue
        if line.startswith("#"): continue
        
        pure_lines.append(line)
    return "\n".join(pure_lines)

def _calculate_honest_latin_ratio(text: str) -> float:
    """Calculates Latin ratio while exempting allowlisted ad-libs."""
    tokens = text.split()
    if not tokens: return 0.0
    
    allowlist = {"(ah)", "(uh)", "(oh)", "(hey)", "(ah-hah)", "(ha)", "(nee)"}
    latin_tokens = 0
    for t in tokens:
        clean_t = t.lower().strip(".,!?")
        if clean_t in allowlist:
            continue # Exempt
        if re.search(r"[a-zA-Z]", t):
            latin_tokens += 1
            
    return round(latin_tokens / len(tokens), 3)

def _parse_sections(text: str) -> dict[str, list[str]]:
    sections = {}
    current = ""
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1]
            sections.setdefault(current, [])
            continue
        sections.setdefault(current or "body", []).append(line)
    return sections

def _title_binding_score(title: str, lines: list[str]) -> float:
    if not title or not lines: return 0.0
    title_clean = title.replace(" ", "").lower()
    joined = "".join(lines).lower()
    if title_clean in joined:
        hits = sum(1 for line in lines if title_clean in line.lower())
        if hits >= 3: return 1.0
        if hits >= 2: return 0.8
        return 0.6
    return 0.2

def _singability_score(lines: list[str]) -> float:
    if not lines: return 0.0
    long_lines = sum(1 for line in lines if len(line.replace(" ", "")) > 24)
    ratio = long_lines / len(lines)
    return round(max(0.0, 1.0 - ratio * 1.5), 2)


def _normalized_line_signature(line: str, title: str) -> str:
    normalized = re.sub(r"\s+", "", line)
    if title:
        normalized = normalized.replace(re.sub(r"\s+", "", title), "<TITLE>")
    return normalized


def _line_variety_score(lines: list[str], title: str) -> float:
    if not lines:
        return 0.0
    signatures = [_normalized_line_signature(line, title) for line in lines]
    unique_ratio = len(set(signatures)) / len(signatures)
    adjacent_duplicates = sum(1 for i in range(1, len(signatures)) if signatures[i] == signatures[i - 1])
    duplicate_ratio = adjacent_duplicates / max(len(signatures) - 1, 1)
    score = unique_ratio - (duplicate_ratio * 0.35)
    return round(max(0.0, min(1.0, score)), 2)


def _hook_restraint_score(title: str, lines: list[str]) -> float:
    if not title or not lines:
        return 0.0
    title_clean = re.sub(r"\s+", "", title)
    if not title_clean:
        return 0.0
    mention_count = sum(_normalized_line_signature(line, "").count(title_clean) for line in lines)
    mention_ratio = mention_count / len(lines)
    if 0.15 <= mention_ratio <= 0.75:
        return 1.0
    if mention_ratio <= 1.0:
        return 0.8
    if mention_ratio <= 1.35:
        return 0.6
    return 0.35


def _evidence_atoms(card: dict[str, Any]) -> list[str]:
    atoms: list[str] = []
    values = (
        list(card.get("required_imagery", []))
        + [card.get("scene", "")]
        + list(card.get("imagery_focus", []))[:2]
        + list(card.get("required_motifs", []))[:2]
    )
    for value in values:
        text = str(value or "").strip()
        if not text:
            continue
        if len(text.replace(" ", "")) > 14:
            continue
        if text in {"誰に", "場所", "見え", "心を", "色に", "色で", "あと", "少し", "全部"}:
            continue
        if not any(("\u3040" <= ch <= "\u30ff") or ("\u4e00" <= ch <= "\u9fff") for ch in text):
            continue
        if contains_bad_script(text):
            continue
        if text not in atoms:
            atoms.append(text)
    return atoms[:4]


def _title_policy_score(policy: str, title: str, section_lines: list[str]) -> float:
    title_clean = re.sub(r"\s+", "", title)
    if not title_clean:
        return 1.0
    signatures = [_normalized_line_signature(line, "") for line in section_lines]
    mentions = sum(sig.count(title_clean) for sig in signatures)
    first_line_has = bool(signatures and title_clean in signatures[0])

    if policy == "withhold":
        return 1.0 if mentions == 0 else max(0.0, 0.55 - ((mentions - 1) * 0.15))
    if policy == "sparse":
        if mentions <= 1:
            return 1.0
        if mentions == 2:
            return 0.75
        return 0.4
    if policy == "anchor":
        if mentions >= 1 and first_line_has:
            return 1.0
        if mentions >= 1:
            return 0.8
        return 0.2
    if policy == "primary":
        if mentions >= 2 and first_line_has:
            return 1.0
        if mentions >= 1:
            return 0.7
        return 0.2
    return 1.0


def _evidence_utilization_score(plan: dict[str, Any], title: str, markdown: str) -> tuple[float, dict[str, Any]]:
    parsed = _parse_sections(markdown)
    section_scores: dict[str, Any] = {}
    scores: list[float] = []

    for card in plan.get("section_cards", []):
        section = str(card.get("section", "")).strip()
        if not section:
            continue
        section_lines = parsed.get(section, [])
        joined = "".join(section_lines)
        atoms = _evidence_atoms(card)
        atom_hits = [atom for atom in atoms if atom in joined]
        atom_score = len(atom_hits) / len(atoms) if atoms else 1.0
        title_policy = str(card.get("title_drop_policy", "")).strip()
        title_score = _title_policy_score(title_policy, title, section_lines)
        if card.get("evidence_track_ids"):
            section_score = atom_score * 0.7 + title_score * 0.3
        else:
            section_score = atom_score * 0.55 + title_score * 0.45
        scores.append(section_score)
        section_scores[section] = {
            "atoms": atoms,
            "atom_hits": atom_hits,
            "atom_score": round(atom_score, 2),
            "title_drop_policy": title_policy,
            "title_policy_score": round(title_score, 2),
            "evidence_track_count": len(card.get("evidence_track_ids", [])),
            "line_count": len(section_lines),
            "section_score": round(section_score, 2),
        }

    if not scores:
        return 0.0, {"per_section": {}, "section_count": 0}
    return round(sum(scores) / len(scores), 2), {
        "per_section": section_scores,
        "section_count": len(scores),
    }


def _structure_score(plan: dict[str, Any], text: str) -> tuple[float, dict[str, Any]]:
    parsed = _parse_sections(text)
    present_sections = [section for section in parsed.keys() if section and section != "body"]
    expected_sections = [
        str(section).strip()
        for section in plan.get("form_profile", {}).get("section_order", [])
        if str(section).strip()
    ]

    if not expected_sections:
        return 0.5, {
            "expected_sections": [],
            "present_sections": present_sections,
            "missing_sections": [],
            "coverage_ratio": 0.0,
            "order_ratio": 0.0,
            "escalation_ok": False,
        }

    missing_sections = [section for section in expected_sections if section not in present_sections]
    coverage_ratio = (len(expected_sections) - len(missing_sections)) / len(expected_sections)

    filtered_present = [section for section in present_sections if section in expected_sections]
    expected_iter = iter(expected_sections)
    next_expected = next(expected_iter, None)
    ordered_hits = 0
    for section in filtered_present:
        while next_expected is not None and next_expected != section:
            next_expected = next(expected_iter, None)
        if next_expected == section:
            ordered_hits += 1
            next_expected = next(expected_iter, None)
    order_ratio = ordered_hits / len(expected_sections)

    chorus_len = len(parsed.get("chorus", []))
    final_len = len(parsed.get("chorus_final", []))
    escalation_ok = final_len >= max(chorus_len + 1, 5) if chorus_len else final_len >= 5

    pre_chorus_expected = any(section.startswith("pre_chorus") for section in expected_sections)
    pre_chorus_present = any(section.startswith("pre_chorus") for section in present_sections)
    bridge_present = "bridge" in present_sections
    transition_score = 1.0
    if pre_chorus_expected and not pre_chorus_present:
        transition_score -= 0.35
    if not bridge_present:
        transition_score -= 0.2
    transition_score = max(0.0, transition_score)

    score = (
        coverage_ratio * 0.4
        + order_ratio * 0.2
        + (1.0 if escalation_ok else 0.45) * 0.25
        + transition_score * 0.15
    )
    return round(max(0.0, min(1.0, score)), 2), {
        "expected_sections": expected_sections,
        "present_sections": present_sections,
        "missing_sections": missing_sections,
        "coverage_ratio": round(coverage_ratio, 2),
        "order_ratio": round(order_ratio, 2),
        "escalation_ok": escalation_ok,
        "transition_score": round(transition_score, 2),
        "chorus_line_count": chorus_len,
        "chorus_final_line_count": final_len,
    }

def _calculate_imagery_coverage(plan: dict[str, Any], pure_body: str) -> tuple[float, list[str]]:
    """Evaluates how many mandatory imagery anchors from the plan appear in the PURE lyrics (excluding metadata)."""
    all_required = []
    # vNext: Use section cards if available
    for card in plan.get("section_cards", []):
        all_required.extend(card.get("required_imagery", []))
    
    # Compatibility: Use motif_roster or keywords if no section cards
    if not all_required:
        roster = plan.get("motif_roster", [])
        for item in roster:
            if isinstance(item, dict):
                # Extract motifs list from dictionary if present
                all_required.extend(item.get("motifs", []))
                if "text" in item: all_required.append(item["text"])
            elif isinstance(item, str):
                all_required.append(item)
        all_required.extend(plan.get("keywords", []))
    
    # Ensure all items are strings and unique
    clean_required = []
    for item in all_required:
        if isinstance(item, str):
            clean_required.append(item)
        elif isinstance(item, (list, tuple)):
            clean_required.extend([str(x) for x in item if isinstance(x, (str, int, float))])
            
    unique_required = sorted(list(set(clean_required)))
    if not unique_required: return 1.0, []
    
    hits = [atom for atom in unique_required if atom in pure_body]
    coverage = len(hits) / len(unique_required)
    return round(coverage, 2), hits

def run_critic_stage(
    plan: dict[str, Any],
    candidate: dict[str, Any],
    base_total: float = 0.0,
) -> CriticResult:
    """Execute Stage I: Critic (Honest Version)."""
    from src.akira_engine.production_policy import BASELINE_2026_03_31 as Policy
    
    candidate_id = str(candidate.get("candidate_id", "unknown"))
    markdown = str(candidate.get("markdown", ""))
    title = str(candidate.get("title", "")).strip()
    
    # 1. Honest Extraction Pre-Audit
    pure_body = _extract_pure_lyric_body(markdown)
    lines = _lyric_lines(pure_body) # Now derived from pure body
    
    # 1. Hard Gate (Absolute Rules - Policy Driven)
    jp_ratio, _ = calculate_script_ratios(pure_body)
    latin_ratio = _calculate_honest_latin_ratio(pure_body)
    has_bad_script = contains_bad_script(pure_body)
    
    reasons = []
    # Baseline Freeze: Policy Enforced
    if jp_ratio < 0.7: reasons.append("japanese_ratio_critical_low")
    if latin_ratio > Policy.LATIN_TOKEN_RATIO_MAX * 2.5: reasons.append("latin_leakage_extreme")
    if has_bad_script: reasons.append("script_contamination_detected")
    
    gate = HardGate(passed=len(reasons) == 0, reasons=reasons)
    
    # 2. Quality Scores (Baseline Threshold: Japanese >= Policy.JAPANESE_RATIO_MIN)
    scaffold_mode = candidate.get("scaffold_mode", False)
    
    # Dual Policy: Production is strict, Scaffold is loose
    if scaffold_mode:
        surface_score = round(max(0.4, 1.0 - (latin_ratio * 1.2) - (0.75 - jp_ratio if jp_ratio < 0.75 else 0)), 2)
    else:
        # Production Strict (Frozen)
        surface_score = round(max(0.0, 1.0 - (latin_ratio * 2.5) - (Policy.JAPANESE_RATIO_MIN - jp_ratio if jp_ratio < Policy.JAPANESE_RATIO_MIN else 0)), 2)
        
    singability = _singability_score(lines)
    binding = _title_binding_score(title, lines)
    imagery_cov, imagery_hits = _calculate_imagery_coverage(plan, pure_body)
    line_variety = _line_variety_score(lines, title)
    hook_restraint = _hook_restraint_score(title, lines)
    structure_score, structure_diag = _structure_score(plan, markdown)
    evidence_utilization, evidence_diag = _evidence_utilization_score(plan, title, markdown)
    family_diversity, family_diag = score_family_diversity(pure_body)
    cliche_density, cliche_diag = score_demo_cliche_density(pure_body)
    cliche_control = round(max(0.0, 1.0 - cliche_density), 2)
    
    # 3. Diagnostics
    template_markers = ["(Ah-hah)", "Ready-dy-dy", "Ga-ga-giga", "B-B-BPM"]
    detected_templates = [m for m in template_markers if m in pure_body]
    
    result = CriticResult(
        candidate_id=candidate_id,
        hard_gate=gate,
        scores={
            "total": round(
                surface_score * 16
                + singability * 10
                + binding * 8
                + imagery_cov * 12
                + line_variety * 8
                + hook_restraint * 6
                + structure_score * 12
                + evidence_utilization * 14
                + family_diversity * 6
                + cliche_control * 8,
                2,
            ),
            "japanese_char_ratio": jp_ratio,
            "latin_token_ratio": latin_ratio,
            "surface_score": surface_score,
            "singability": singability,
            "title_binding": binding,
            "imagery_coverage": imagery_cov,
            "line_variety": line_variety,
            "hook_restraint": hook_restraint,
            "structure_score": structure_score,
            "evidence_utilization": evidence_utilization,
            "family_diversity": family_diversity,
            "cliche_density": cliche_density,
            "cliche_control": cliche_control,
        },
        diagnostics={
            "template_hits": detected_templates,
            "imagery_hits": imagery_hits,
            "has_bad_script": has_bad_script,
            "line_count": len(lines),
            "scaffold_mode": scaffold_mode,
            "pure_body_length": len(pure_body),
            "structure": structure_diag,
            "evidence": evidence_diag,
            "family_profile": family_diag,
            "cliche_profile": cliche_diag,
        },
        honest_metrics_active=True
    )
    
    if not gate.passed: result.notes.append(f"Hard gate failed: {', '.join(reasons)}")
    if latin_ratio > Policy.LATIN_TOKEN_RATIO_MAX and not scaffold_mode: 
        result.notes.append("Linguistic leakage detected (Production Strict)")
        
    if imagery_cov <= Policy.IMAGERY_COVERAGE_HARD_FAIL_THRESHOLD and not scaffold_mode:
        result.notes.append("CRITICAL: Imagery coverage hard fail (Grounding Bridge broken)")
    if structure_score < 0.8:
        result.notes.append("Structure under target: section coverage or escalation is weak")
    if evidence_utilization < 0.68:
        result.notes.append("Evidence utilization under target: section atoms or title policy are weak")
    if cliche_density > 0.34:
        result.notes.append("Cliche density under review: overused mode vocabulary is dominating")
    if family_diversity < 0.5:
        result.notes.append("Family diversity under target: lexical field mix is too narrow")
        
    return result
