# src/akira_engine/creative/canon/policies.py

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from src.akira_engine.creative.config import CreativeConfig


class AdmissionStatus(Enum):
    REJECT = "reject"
    HOLD = "hold"
    WARN = "warn"
    PASS = "pass"

class AdmissionPolicy:
    """Policies for admitting tracks into the internal creative canon.
    
    Uses a 3-stage gate (warn / hold / reject) for better explainability.
    """
    
    # Rejection Reason Codes
    REASONS = {
        "CRAFT_LOW": "low_craft_score",
        "GROUNDING_LOW": "low_grounding_intensity",
        "ORIGINALITY_LOW": "low_originality",
        "CLICHE_HIGH": "high_cliche_density",
        "IMITATION_HIGH": "high_imitation_risk",
        "QUOTA_EXCEEDED": "cluster_quota_exceeded",
        "RECENT_CLOSE": "recent_canon_too_close",
        "HOOK_CONTINUITY": "hook_grammar_continuity_limit"
    }

    def __init__(self, config: Optional[CreativeConfig] = None):
        self.config = config or CreativeConfig.load_canonical(Path.cwd())

    def evaluate(self, metrics: Dict[str, Any]) -> Tuple[AdmissionStatus, List[str]]:
        """Evaluates metrics against policies and returns status and reasons."""
        reasons = []
        status = AdmissionStatus.PASS
        
        # 1. Craft Check
        craft = metrics.get("craft_score", 0.0)
        min_craft = self.config.get("min_craft_score")
        warn_craft = self.config.get("warn_craft_score")
        
        if craft < min_craft:
            reasons.append(self.REASONS["CRAFT_LOW"])
            status = AdmissionStatus.REJECT if craft < warn_craft else AdmissionStatus.HOLD
            
        # 2. Grounding Check
        grounding = metrics.get("grounding_intensity", 0.0)
        min_grounding = self.config.get("min_grounding_intensity")
        warn_grounding = self.config.get("warn_grounding_intensity")
        
        if grounding < min_grounding:
            reasons.append(self.REASONS["GROUNDING_LOW"])
            if status != AdmissionStatus.REJECT:
                status = AdmissionStatus.HOLD if grounding < warn_grounding else AdmissionStatus.WARN

        # 3. Originality Check
        originality = metrics.get("composite_originality", 1.0)
        min_orig = self.config.get("min_originality_composite")
        warn_orig = self.config.get("warn_originality_composite")
        
        if originality < min_orig:
            reasons.append(self.REASONS["ORIGINALITY_LOW"])
            if status != AdmissionStatus.REJECT:
                status = AdmissionStatus.REJECT if originality < warn_orig else AdmissionStatus.HOLD
                
        # 4. Cliché Check
        cliche = metrics.get("cliche_density", 0.0)
        max_cliche = self.config.get("max_cliche_density")
        if cliche > max_cliche:
            reasons.append(self.REASONS["CLICHE_HIGH"])
            if status != AdmissionStatus.REJECT:
                status = AdmissionStatus.WARN

        return status, sorted(list(set(reasons)))
