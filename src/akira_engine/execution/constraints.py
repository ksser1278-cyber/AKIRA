# src/akira_engine/execution/constraints.py

from __future__ import annotations

from typing import Any, Dict, List, Optional


class TechnicalConstraintManager:
    """Manages dynamic sampling parameters and token density controls."""

    # Base density profiles
    DENSITY_PROFILES = {
        "airy": {
            "mora_per_line": "8-12",
            "instruction": "Keep lines short and breathable. Use silence (pacing)."
        },
        "dense": {
            "mora_per_line": "14-22",
            "instruction": "Rapid fire delivery. High information density."
        },
        "staccato": {
            "mora_per_line": "4-8",
            "instruction": "Short, punchy fragments. Glitchy rhythm."
        }
    }

    def __init__(self):
        pass

    def get_section_parameters(self, intent: str, base_temp: float = 0.7) -> Dict[str, Any]:
        """Calculates dynamic temperature and sampling parameters based on narrative intent."""
        
        # Scale temperature by dramatic tension
        if intent == "climax":
            temp = base_temp + 0.1 # More expressive
        elif intent == "twist":
            temp = base_temp + 0.2 # High unpredictability
        elif intent == "setup":
            temp = base_temp - 0.1 # Clear and grounded
        else:
            temp = base_temp

        return {
            "temperature": round(min(max(temp, 0.2), 1.2), 2),
            "top_p": 0.95 if intent == "twist" else 0.9,
            "presence_penalty": 0.4 if intent == "climax" else 0.3
        }

    def get_density_guidance(self, target: str) -> Dict[str, str]:
        """Returns rhythmic guidance based on token density profile."""
        return self.DENSITY_PROFILES.get(target, self.DENSITY_PROFILES["airy"])
