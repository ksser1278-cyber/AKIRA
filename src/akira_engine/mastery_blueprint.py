from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class MasteryConstraints:
    """
    Universal J-Pop Songwriting Mechanics (v1.0)
    Derived from Alexandria 60k Mastery Analysis (Elite vs. Control).
    """
    # Structural
    min_sectional_repetition: float = 0.027  # Repetition Index
    target_mora_variance: float = 3.3       # Rhythmic Tension
    max_hook_latency_lines: int = 9         # Speed to Chorus
    
    # Phonetic
    target_chorus_mora: float = 15.0        # Density Peak
    vowel_priority: List[str] = field(default_factory=lambda: ["a", "i"]) # Brilliance
    max_phonetic_impact: float = 0.16       # Smoothness (avoiding harshness)
    
    # Validation Thresholds
    min_line_count_per_section: int = 4
    max_line_count_per_verse: int = 8
    
    # Universal Templates
    universal_section_order: List[str] = field(default_factory=lambda: [
        "intro", "verse_1", "pre_chorus", "chorus", 
        "verse_2", "pre_chorus_2", "chorus", "bridge", 
        "chorus_final", "outro"
    ])

def get_universal_blueprint() -> MasteryConstraints:
    return MasteryConstraints()

def load_approved_calibration(mode_id: str) -> Dict[str, float]:
    """
    Loads human-approved stylistic calibrations from data/mastery/calibration_approved.json.
    """
    import json
    from pathlib import Path
    cal_file = Path("data/mastery/calibration_approved.json")
    if not cal_file.exists():
        return {}
        
    try:
        data = json.loads(cal_file.read_text(encoding="utf-8"))
        # Return mode-specific calibration or empty dict
        return data.get("modes", {}).get(mode_id, {})
    except Exception:
        return {}

def get_blueprint_for_mode(mode_id: str) -> MasteryConstraints:
    """
    Returns stylistic constraints for specific J-Pop sub-genres.
    Merges static Base constraints with human-approved Calibrations (Overlay).
    """
    m = str(mode_id).lower()
    
    # 1. Start with the Base constraints (Hardcoded GROUND TRUTH)
    base = MasteryConstraints()
    
    if any(k in m for k in ["dark", "cute", "yami", "kawaii"]):
        base = MasteryConstraints(
            min_sectional_repetition=0.45,
            target_mora_variance=4.5,
            target_chorus_mora=18.0,
            max_line_count_per_verse=6,
        )
    elif any(k in m for k in ["anthem", "cinematic", "power", "hero"]):
        base = MasteryConstraints(
            min_sectional_repetition=0.15,
            target_mora_variance=2.5,
            target_chorus_mora=12.0,
            vowel_priority=["a", "i", "o"],
            max_phonetic_impact=0.12,
        )
    elif any(k in m for k in ["glitch", "hyper", "technical", "experimental"]):
        base = MasteryConstraints(
            min_sectional_repetition=0.60,
            target_mora_variance=6.0,
            target_chorus_mora=22.0,
            max_hook_latency_lines=4,
        )
    
    # 2. Apply the Approved Calibration Overlay
    calibration = load_approved_calibration(mode_id)
    if calibration:
        # Proposed Mora Adjustment (Damped Step)
        if "proposed_mora_offset" in calibration:
            base.target_chorus_mora += calibration["proposed_mora_offset"]
            
        # Add other calibration merges here as needed (rep, variance, etc.)
        
    return base

def validate_against_blueprint(lines: List[str], section_type: str = "Verse", mode_id: str = "universal") -> Dict[str, float]:
    """
    Scores a block of lyrics against the Universal or Genre-Specific Blueprint.
    """
    import statistics
    from .japanese_lyric_features import mora_unit_estimate
    from .phonetic_engine import analyze_phonetic_profile
    
    if not lines:
        return {"score": 0.0}
        
    mora_counts = [mora_unit_estimate(l) for l in lines]
    avg_mora = sum(mora_counts) / len(mora_counts)
    variance = statistics.stdev(mora_counts) if len(mora_counts) > 1 else 0
    
    # Repetition Index
    unique_lines = len(set(lines))
    rep_idx = 1 - (unique_lines / len(lines))
    
    # Selection of Blueprint
    blueprint = get_blueprint_for_mode(mode_id)
    
    scores = {}
    
    # Mora Density (Weight 0.3)
    if "Chorus" in section_type or "sabi" in section_type.lower():
        density_score = 1.0 - (abs(avg_mora - blueprint.target_chorus_mora) / 10.0)
    else:
        # Verses should be less dense than chorus peak
        target_verse_mora = blueprint.target_chorus_mora * 0.75
        density_score = 1.0 - (abs(avg_mora - target_verse_mora) / 10.0)
    scores["density"] = max(0, min(1, density_score))
    
    # Variance (Weight 0.3)
    var_score = variance / blueprint.target_mora_variance
    scores["tension"] = max(0, min(1, var_score))
    
    # Repetition (Weight 0.4)
    rep_score = 1.0 if rep_idx >= blueprint.min_sectional_repetition else (rep_idx / blueprint.min_sectional_repetition)
    scores["hooking"] = max(0, min(1, rep_score))
    
    # Phonetic Precision (Weight 0.2)
    profile = analyze_phonetic_profile(" ".join(lines))
    scores["brilliance"] = profile.brilliance_score
    scores["impact"] = profile.plosive_ratio
    
    # Final Weighted Score
    scores["total_mastery_score"] = (
        scores["density"] * 0.25 + 
        scores["tension"] * 0.25 + 
        scores["hooking"] * 0.3 + 
        scores["brilliance"] * 0.1 +
        scores["impact"] * 0.1
    )
    
    return scores
