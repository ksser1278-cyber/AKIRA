from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from src.akira_engine.lexical_family_bank import score_demo_cliche_density, score_family_diversity
from src.akira_engine.normalize.mod import calculate_script_ratios, contains_bad_script

_LOW_SIGNAL_ALIGNMENT_TERMS = {
    "ちゅっ",
    "いないいないばあっ",
    "痛い痛い痛い",
    "鏡よ鏡",
    "真っ赤な",
    "痛い",
}

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


def _is_low_signal_alignment_term(text: str) -> bool:
    return str(text or "").strip() in _LOW_SIGNAL_ALIGNMENT_TERMS

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




def _title_policy_score(policy: str, title: str, section_lines: list[str]) -> float:
    return _title_policy_score_impl(policy, title, section_lines)




def _title_policy_score_impl(policy: str, title: str, section_lines: list[str]) -> float:
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
    return _evidence_utilization_score_impl(plan, title, markdown)


def _evidence_atoms(card: dict[str, Any]) -> list[str]:
    atoms: list[str] = []
    # Include conditioning_atoms as primary evidence source
    values = (
        list(card.get("conditioning_atoms", []))[:4]
        + list(card.get("required_imagery", []))
        + [card.get("scene", "")]
        + list(card.get("imagery_focus", []))[:3]
        + list(card.get("required_motifs", []))[:4]
    )
    blocked_terms = {
        "\u65b9",
        "\u611f\u8b1d",
        "\u6069",
        "\u4e00\u751f",
        "\u5b50\u4f9b",
        "\u60f3\u3044",
        "\u79d8\u3081",
        "\u611b\u8a00\u8449",
    }
    for value in values:
        text = str(value or "").strip()
        if not text:
            continue
        compact = text.replace(" ", "")
        if len(compact) > 18:
            continue
        if text in blocked_terms:
            continue
        if _is_low_signal_alignment_term(text):
            continue
        if not any(("\u3040" <= ch <= "\u30ff") or ("\u4e00" <= ch <= "\u9fff") for ch in text):
            continue
        if contains_bad_script(text):
            continue
        if text not in atoms:
            atoms.append(text)
    return atoms[:6]


def _evidence_utilization_score_impl(plan: dict[str, Any], title: str, markdown: str) -> tuple[float, dict[str, Any]]:
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

def _atom_matches_body(atom: str, body: str) -> bool:
    """Check if atom appears in body, with partial matching for longer atoms."""
    if atom in body:
        return True
    # Partial match: if atom is 3+ chars, check core substring (first 2 kanji/kana)
    compact = atom.replace(" ", "")
    jp_chars = [ch for ch in compact if ("\u3040" <= ch <= "\u30ff") or ("\u4e00" <= ch <= "\u9fff") or ("\u30a0" <= ch <= "\u30ff")]
    if len(jp_chars) >= 3:
        core = "".join(jp_chars[:2])
        if core in body:
            return True
    return False


def _calculate_imagery_coverage(plan: dict[str, Any], pure_body: str) -> tuple[float, list[str]]:
    """Evaluates how many imagery anchors from each section card appear in the lyrics."""
    parsed = _parse_sections(pure_body)
    section_scores: list[float] = []
    all_hits: list[str] = []
    
    for card in plan.get("section_cards", []):
        section = str(card.get("section", "")).strip()
        section_lines = parsed.get(section, [])
        section_body = "".join(section_lines)
        
        atoms: list[str] = []
        for value in (
            list(card.get("conditioning_atoms", []))[:4]
            + list(card.get("required_imagery", []))
            + list(card.get("imagery_focus", []))[:2]
        ):
            text = str(value or "").strip()
            if text and text not in atoms and not _is_low_signal_alignment_term(text):
                atoms.append(text)
        
        if not atoms:
            section_scores.append(1.0)
            continue
        
        # Check in section body first, then fall back to full body
        hits = [atom for atom in atoms[:4] if _atom_matches_body(atom, section_body) or _atom_matches_body(atom, pure_body)]
        all_hits.extend(hits)
        section_scores.append(len(hits) / len(atoms[:4]) if atoms[:4] else 1.0)
    
    if not section_scores:
        # Compatibility fallback for plans without section cards
        all_required = list(plan.get("keywords", []))
        roster = plan.get("motif_roster", [])
        for item in roster:
            if isinstance(item, dict):
                all_required.extend(item.get("motifs", []))
            elif isinstance(item, str):
                all_required.append(item)
        clean_required = list(set(str(x) for x in all_required if isinstance(x, str)))
        if not clean_required:
            return 1.0, []
        hits = [atom for atom in clean_required if _atom_matches_body(atom, pure_body)]
        return round(len(hits) / len(clean_required), 2), hits
    
    return round(sum(section_scores) / len(section_scores), 2), list(set(all_hits))

def _section_lines(parsed: dict[str, list[str]], expected_sections: list[str]) -> list[tuple[str, list[str]]]:
    ordered: list[tuple[str, list[str]]] = []
    seen: set[str] = set()
    for section in expected_sections:
        if section in seen:
            continue
        lines = parsed.get(section, [])
        if lines:
            ordered.append((section, lines))
            seen.add(section)
    if ordered:
        return ordered
    for section, lines in parsed.items():
        if section and section != "body" and lines:
            ordered.append((section, lines))
    return ordered

def _mean_line_length(lines: list[str]) -> float:
    if not lines:
        return 0.0
    lengths = [len(re.sub(r"\s+", "", line)) for line in lines if line.strip()]
    if not lengths:
        return 0.0
    return sum(lengths) / len(lengths)

def _prosodic_flow_score(lines: list[str], parsed: dict[str, list[str]], expected_sections: list[str], singability: float) -> float:
    if not lines:
        return 0.0
    lengths = [len(re.sub(r"\s+", "", line)) for line in lines if line.strip()]
    if len(lengths) < 2:
        return round(max(0.0, min(1.0, singability)), 2)

    jumps = [abs(lengths[i] - lengths[i - 1]) for i in range(1, len(lengths))]
    avg_jump = sum(jumps) / len(jumps)
    smoothness = max(0.0, 1.0 - min(avg_jump / 14.0, 1.0))

    section_groups = _section_lines(parsed, expected_sections)
    section_means = [_mean_line_length(section_lines) for _, section_lines in section_groups if section_lines]
    if len(section_means) >= 2:
        section_jumps = [abs(section_means[i] - section_means[i - 1]) for i in range(1, len(section_means))]
        avg_section_jump = sum(section_jumps) / len(section_jumps)
        section_flow = max(0.0, 1.0 - min(avg_section_jump / 10.0, 1.0))
    else:
        section_flow = 0.5

    score = (singability * 0.45) + (smoothness * 0.35) + (section_flow * 0.20)
    return round(max(0.0, min(1.0, score)), 2)

def _hook_memorability_score(title: str, parsed: dict[str, list[str]]) -> float:
    chorus_lines = list(parsed.get("chorus", [])) + list(parsed.get("chorus_final", []))
    target_lines = chorus_lines or [line for section, lines in parsed.items() if section and section != "body" for line in lines]
    if not title or not target_lines:
        return 0.0
    title_clean = re.sub(r"\s+", "", title)
    if not title_clean:
        return 0.0
    mentions = sum(1 for line in target_lines if title_clean in re.sub(r"\s+", "", line))
    title_binding = _title_binding_score(title, target_lines)
    density = min(1.0, mentions / max(1.0, len(target_lines) / 2.0))
    first_line_bonus = 1.0 if title_clean in re.sub(r"\s+", "", target_lines[0]) else 0.0
    score = (title_binding * 0.45) + (density * 0.35) + (first_line_bonus * 0.20)
    return round(max(0.0, min(1.0, score)), 2)

def _repetition_payoff_score(title: str, parsed: dict[str, list[str]]) -> float:
    chorus_lines = list(parsed.get("chorus", [])) + list(parsed.get("chorus_final", []))
    if not chorus_lines:
        return 0.35
    title_clean = re.sub(r"\s+", "", title)
    normalized = [re.sub(r"\s+", "", line) for line in chorus_lines]
    repeated_line_hits = sum(1 for i in range(1, len(normalized)) if normalized[i] == normalized[i - 1])
    repeated_line_ratio = repeated_line_hits / max(1, len(normalized) - 1)
    title_mentions = sum(1 for line in normalized if title_clean and title_clean in line)
    title_ratio = title_mentions / len(normalized)
    chorus_return_bonus = 0.25 if title_mentions >= 2 else 0.0
    score = (repeated_line_ratio * 0.35) + (min(1.0, title_ratio * 2.0) * 0.45) + chorus_return_bonus
    return round(max(0.0, min(1.0, score)), 2)

def _section_contrast_score(parsed: dict[str, list[str]], expected_sections: list[str]) -> float:
    section_groups = _section_lines(parsed, expected_sections)
    if len(section_groups) < 2:
        return 0.5

    section_means = [(section, _mean_line_length(lines)) for section, lines in section_groups if lines]
    if len(section_means) < 2:
        return 0.5

    jumps = [abs(section_means[i][1] - section_means[i - 1][1]) for i in range(1, len(section_means))]
    avg_jump = sum(jumps) / len(jumps)
    base = min(1.0, avg_jump / 6.0)

    section_map = {section: mean for section, mean in section_means}
    verse_sections = [section_map[s] for s in section_map if s.startswith("verse")]
    verse_mean = sum(verse_sections) / len(verse_sections) if verse_sections else 0.0
    chorus_mean = section_map.get("chorus", section_map.get("chorus_final", verse_mean))
    bridge_mean = section_map.get("bridge", verse_mean)
    verse_chorus_gap = min(0.2, abs(verse_mean - chorus_mean) / 30.0)
    bridge_gap = min(0.1, abs(bridge_mean - verse_mean) / 40.0)

    score = base + verse_chorus_gap + bridge_gap
    return round(max(0.0, min(1.0, score)), 2)

def _oral_friction_score(lines: list[str], singability: float) -> float:
    if not lines:
        return 0.0
    lengths = [len(re.sub(r"\s+", "", line)) for line in lines if line.strip()]
    if not lengths:
        return 0.0
    long_ratio = sum(1 for length in lengths if length > 24) / len(lengths)
    short_ratio = sum(1 for length in lengths if length < 6) / len(lengths)
    friction = (long_ratio * 0.65) + ((1.0 - singability) * 0.55) + (short_ratio * 0.1)
    return round(max(0.0, min(1.0, friction)), 2)

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

    parsed_sections = _parse_sections(markdown)
    expected_sections = [
        str(section).strip()
        for section in plan.get("form_profile", {}).get("section_order", [])
        if str(section).strip()
    ]
    prosodic_flow = _prosodic_flow_score(lines, parsed_sections, expected_sections, singability)
    hook_memorability = _hook_memorability_score(title, parsed_sections)
    repetition_payoff = _repetition_payoff_score(title, parsed_sections)
    section_contrast = _section_contrast_score(parsed_sections, expected_sections)
    oral_friction = _oral_friction_score(lines, singability)
    musical_scores = {
        "prosodic_flow": prosodic_flow,
        "hook_memorability": hook_memorability,
        "repetition_payoff": repetition_payoff,
        "section_contrast": section_contrast,
        "oral_friction": oral_friction,
    }
    legacy_total = round(
        surface_score * 16
        + singability * 10
        + binding * 8
        + imagery_cov * 10
        + line_variety * 8
        + hook_restraint * 6
        + structure_score * 8
        + evidence_utilization * 14
        + family_diversity * 6
        + cliche_control * 4
        + section_contrast * 4
        + hook_memorability * 2,
        2,
    )
    musical_total = round(
        prosodic_flow * 24
        + hook_memorability * 24
        + repetition_payoff * 20
        + section_contrast * 18
        + (1.0 - oral_friction) * 14,
        2,
    )
    blended_total = round((legacy_total * 0.4) + (musical_total * 0.6), 2)
    
    # 3. Diagnostics
    template_markers = ["(Ah-hah)", "Ready-dy-dy", "Ga-ga-giga", "B-B-BPM"]
    detected_templates = [m for m in template_markers if m in pure_body]
    
    result = CriticResult(
        candidate_id=candidate_id,
        hard_gate=gate,
        scores={
            "total": legacy_total,
            "legacy_total": legacy_total,
            "musical_total": musical_total,
            "blended_total": blended_total,
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
            "musical_scores": musical_scores,
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
            "musical_scores": musical_scores,
            "legacy_total": legacy_total,
            "musical_total": musical_total,
            "blended_total": blended_total,
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
