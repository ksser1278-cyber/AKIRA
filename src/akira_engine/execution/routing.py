# src/akira_engine/execution/routing.py
"""Production Router — Parameter selection only (Day 6 refactor).

Delegates prompt assembly to prompt_builder.py.
Delegates scoring to critic.
Delegates admission to canon.
"""

from __future__ import annotations

from typing import Any, Dict, List
from src.akira_engine.creative.planner.schema import AbstractBlueprint
from src.akira_engine.execution.constraints import TechnicalConstraintManager
from src.akira_engine.execution.prompt_builder import assemble_prompt_package


class ProductionRouter:
    """Bridges Creative Design and Production Engine.
    
    Responsibility: parameter selection and delegation. 
    Does NOT score, judge, or admit.
    """
    
    MODE_PARAMS = {
        "dark_cute_breakdown": {
            "temperature": 0.8,
            "top_p": 0.95,
            "presence_penalty": 0.4,
            "style_prompt": "Glitchy, dissonant, somatic, emotional breakdown.",
            "grounding_intensity": 0.9
        },
        "energetic_pop": {
            "temperature": 0.6,
            "top_p": 0.9,
            "presence_penalty": 0.2,
            "style_prompt": "Bright, rhythmic, repetitive, high energy.",
            "grounding_intensity": 0.4
        },
        "default": {
            "temperature": 0.7,
            "top_p": 0.9,
            "presence_penalty": 0.3,
            "style_prompt": "Strategic, balanced, high fidelity.",
            "grounding_intensity": 0.5
        }
    }
    
    def __init__(self):
        self.constraints = TechnicalConstraintManager()

    def get_mode_params(self, mode_id: str) -> Dict[str, Any]:
        return self.MODE_PARAMS.get(mode_id, self.MODE_PARAMS["default"])

    def create_prompt_package(self, blueprint: AbstractBlueprint) -> Dict[str, Any]:
        """Route a blueprint through parameter selection and prompt assembly."""
        
        mode_params = self.get_mode_params(blueprint.target_mode_id)
        base_temp = mode_params.get("temperature", 0.7)
        
        # Compute per-section technical parameters
        section_params = []
        density_guides = []
        for s in blueprint.sections:
            section_params.append(
                self.constraints.get_section_parameters(s.narrative_intent, base_temp)
            )
            density_guides.append(
                self.constraints.get_density_guidance(s.token_density_target)
            )

        # Delegate assembly
        return assemble_prompt_package(blueprint, mode_params, section_params, density_guides)
