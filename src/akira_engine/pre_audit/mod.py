from __future__ import annotations
from dataclasses import dataclass, field
import re
from typing import Any

from src.akira_engine.normalize.mod import contains_bad_script, contains_japanese

@dataclass
class PreAuditResult:
    passed: bool
    severity: str           # warning | soft_fail | hard_fail
    diagnostics: list[str] = field(default_factory=list)
    imagery_coverage: float = 0.0
    structural_match: float = 0.0
    identity_match: bool = False


_ALLOWED_SURFACE = re.compile(r"^[\u3040-\u30ff\u3400-\u9fff々ー・、。！？「」『』（）\s]+$")
_WEAK_AUDIT_TOKENS = {
    "言い",
    "訳",
    "在り",
    "始まり",
    "始まりまし",
    "逃げ",
    "ニンゲン",
    "見下し",
    "物足り",
    "空振り",
    "理想論",
    "タカラモノ",
}
_WEAK_AUDIT_SUFFIXES = (
    "まし",
    "ですか",
    "でした",
    "する",
    "した",
    "して",
    "ます",
    "です",
    "ない",
    "たい",
    "よう",
    "られ",
    "れる",
    "せる",
    "とか",
    "だけ",
    "ほど",
    "より",
    "から",
)


_LOW_SIGNAL_AUDIT_TERMS = {
    "方",
    "感謝",
    "恩",
    "一生",
    "子供",
    "想い",
    "秘め",
    "愛言葉",
    "聴いてくれ",
    "世話になって",
    "誰と",
    "頂戴",
    "なくても",
    "僕は僕を見ない",
    "愛されない",
    "全部あげる",
    "知りたい",
    "好き",
    "大好き",
    "お別れ",
}


def _clean_term(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if not contains_japanese(text):
        return ""
    if contains_bad_script(text):
        return ""
    if not _ALLOWED_SURFACE.fullmatch(text):
        return ""
    compact = text.replace(" ", "").replace("　", "")
    if len(compact) < 2:
        return ""
    if compact in _WEAK_AUDIT_TOKENS:
        return ""
    if compact in _LOW_SIGNAL_AUDIT_TERMS:
        return ""
    if compact.endswith(_WEAK_AUDIT_SUFFIXES):
        return ""
    if re.search(r"[\u3400-\u9fff々][\u3040-\u309f]{2,}$", compact):
        return ""
    if re.fullmatch(r"[\u3040-\u309f]+", compact) and len(compact) <= 3:
        return ""
    return text


def _clean_terms(values: list[Any]) -> list[str]:
    out: list[str] = []
    for value in values:
        text = _clean_term(value)
        if text and text not in out:
            out.append(text)
    return out

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
    plan_required_imagery: list[Any] = []
    for card in getattr(plan, "section_cards", []):
        card_dict = card.__dict__ if hasattr(card, "__dict__") else card
        plan_required_imagery.extend(card_dict.get("required_imagery", []))
        plan_required_imagery.extend(card_dict.get("imagery_focus", []))
        scene = card_dict.get("scene")
        if scene:
            plan_required_imagery.append(scene)
    required_imagery = _clean_terms(plan_required_imagery)
    if not required_imagery:
        required_imagery = getattr(conditioning, "imagery_anchors", [])
        if not required_imagery and hasattr(conditioning, "prompt_conditioning"):
            required_imagery = conditioning.prompt_conditioning.get("imagery_anchors", [])
        required_imagery = _clean_terms(required_imagery if isinstance(required_imagery, list) else [])
    
    plan_atoms = set()
    for card in getattr(plan, "section_cards", []):
        card_dict = card.__dict__ if hasattr(card, "__dict__") else card
        plan_atoms.update(_clean_terms(card_dict.get("imagery_focus", [])))
        plan_atoms.update(_clean_terms(card_dict.get("required_motifs", [])))
        plan_atoms.update(_clean_terms(card_dict.get("required_imagery", [])))
        
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
    compared = min(len(cond_sections), len(plan_cards))
    for i in range(compared):
        c_sec = str(cond_sections[i].get("section", "")).strip()
        p_sec = getattr(plan_cards[i], "section", "")
        if c_sec == p_sec:
            matches += 1
    total = compared if compared > 0 else 0
    structural_match = round(matches / total, 2) if total > 0 else 1.0
    if structural_match < 1.0:
        diagnostics.append(f"Structural match: {int(structural_match * 100)}% ({matches}/{total} sections)")

    # 4. Severity Verdict
    severity = "warning"
    passed = True

    if not identity_match:
        severity = "hard_fail"
        passed = False
    elif unique_required and imagery_coverage < 0.4:
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
