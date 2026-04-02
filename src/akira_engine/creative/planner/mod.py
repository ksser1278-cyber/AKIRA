# src/akira_engine/creative/planner/mod.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.akira_engine.creative.planner.schema import AbstractBlueprint
from src.akira_engine.creative.planner.engine import CreativePlannerEngine


def run_creative_planner(
    project_root: Path,
    artist_id: str,
    mode_id: str,
    title_seed: str = "",
    creativity_index: float = 0.5,
) -> AbstractBlueprint:
    """Execute Phase 2: Creative Design Stage.
    
    This replaces the old planner by using Motif Graphs, Style Clusters, 
    and Hook Grammar to design a song's abstract structure.
    """
    engine = CreativePlannerEngine(project_root)
    
    # 1. Generate autonomous blueprint
    blueprint = engine.design_blueprint(
        artist_id=artist_id,
        mode_id=mode_id,
        start_motif=title_seed or None,
        creativity_index=creativity_index
    )
    
    # 2. Add metadata for tracing
    blueprint.metadata["title_seed"] = title_seed
    blueprint.metadata["creation_method"] = "corpus_intelligence_v1"
    
    # 3. Finalize
    return blueprint


def convert_blueprint_to_legacy_plan(blueprint: AbstractBlueprint) -> Dict[str, Any]:
    """Provides backward compatibility with the existing production pipeline.
    
    Converts AbstractBlueprint to the older PlanResult format expected 
    by the generation stage.
    """
    from src.akira_engine.planner.mod import PlanResult, SectionCard
    
    legacy_cards = []
    for s in blueprint.sections:
        legacy_cards.append(SectionCard(
            section=s.section_name,
            function=s.function,
            required_motifs=[s.primary_motif] + s.secondary_motifs,
            imagery_focus=s.imagery_anchors,
            required_imagery=s.imagery_anchors[:2],
            line_target=4,
            cadence_target="medium",
            abstraction_ceiling=s.abstraction_ceiling
        ))
        
    return PlanResult(
        track_id=blueprint.track_id,
        artist_id=blueprint.target_artist_id,
        mode_id=blueprint.target_mode_id,
        title_seed=blueprint.metadata.get("title_seed", ""),
        section_cards=legacy_cards,
        motif_roster=[{"motif_id": "core_semantic", "motifs": [s.primary_motif for s in blueprint.sections]}],
        hook_blueprint={
            "chorus_line_target": 4,
            "syllables": [s.syllable_target for s in blueprint.sections if "chorus" in s.section_name]
        },
        status="planned"
    )
