# src/akira_engine/creative/planner/engine.py

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.akira_engine.creative.planner.schema import CreativeSection, AbstractBlueprint
from src.akira_engine.creative.planner.grounding import ImageryGroundingRegistry
from src.akira_engine.corpus_intelligence.clusters.mod import assign_cluster_membership_for_candidate
from src.akira_engine.corpus_intelligence.motifs.graph import sample_transition_chain, MotifGraph, MotifTransition
from src.akira_engine.corpus_intelligence.hooks.mod import generate_hook_blueprint


class CreativePlannerEngine:
    """The autonomous creative brain that design songs based on corpus intelligence.
    
    This engine leverages:
    - Motif Transition Graph: For thematic flow.
    - Style Clusters: For stylistic grounding.
    - Hook Grammar Bank: For structural hook design.
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.motif_graph_path = project_root / "data" / "motifs" / "motif_transition_graph_v1.json"
        self.cluster_map_path = project_root / "data" / "clusters" / "style_clusters_v1.json"
        self.hook_bank_path = project_root / "data" / "hooks" / "hook_grammar_bank_v1.json"
        self.atlas_path = project_root / "outputs" / "atlas_v2_trusted.json"
        self.dampener_path = project_root / "data" / "config" / "narrative_dampener_v1.json"
        
        self.grounding = ImageryGroundingRegistry(project_root)
        self.dampened_transitions: Set[Tuple[str, str]] = self._load_dampeners()

    def _load_motif_graph(self) -> Optional[MotifGraph]:
        if not self.motif_graph_path.exists():
            return None
        with open(self.motif_graph_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Simple reconstruction
        transitions = {k: [MotifTransition(**item) for item in v] for k, v in data.get("transitions", {}).items()}
        return MotifGraph(
            version=data['version'],
            node_count=data['node_count'],
            edge_count=data['edge_count'],
            transitions=transitions,
            motif_stats={},
            sampling_index=data['sampling_index']
        )

    def _load_dampeners(self) -> Set[Tuple[str, str]]:
        if not self.dampener_path.exists():
            return set()
        try:
            with open(self.dampener_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Format: [[src, dst], ...]
                return {tuple(pair) for pair in data.get("blacklist", [])}
        except:
            return set()

    def _sample_target_transition(
        self,
        graph: MotifGraph,
        current_motif: str,
        target_types: Set[str],
        fallback_types: Set[str] = {"sustain", "unknown"}
    ) -> Dict[str, Any]:
        """Sample a transition from current_motif that matches target_types."""
        edges = graph.transitions.get(current_motif, [])
        if not edges:
            return {"src_motif": current_motif, "dst_motif": current_motif, "transition_type": "sustain"}
            
        # 1. Try target types (intensify, release, etc.)
        candidates = [
            e for e in edges 
            if e.transition_type in target_types 
            and (current_motif, e.dst_motif) not in self.dampened_transitions
        ]
        if candidates:
            picked = random.choice(candidates)
            return {"src_motif": current_motif, "dst_motif": picked.dst_motif, "transition_type": picked.transition_type}
            
        # 2. Try fallback types
        candidates = [e for e in edges if e.transition_type in fallback_types]
        if candidates:
            picked = random.choice(candidates)
            return {"src_motif": current_motif, "dst_motif": picked.dst_motif, "transition_type": picked.transition_type}
            
        # 3. Final random fallback
        picked = random.choice(edges)
        return {"src_motif": current_motif, "dst_motif": picked.dst_motif, "transition_type": picked.transition_type}

    def design_blueprint(
        self,
        artist_id: str,
        mode_id: str,
        start_motif: Optional[str] = None,
        creativity_index: float = 0.5
    ) -> AbstractBlueprint:
        """Main design logic to build a song blueprint with narrative progression."""
        
        # 1. Select Start Motif
        graph = self._load_motif_graph()
        if not start_motif and graph:
            all_motifs = list(graph.transitions.keys())
            start_motif = random.choice(all_motifs) if all_motifs else "革命"
        elif not start_motif:
            start_motif = "革命"

        # 2. Identify Target Cluster
        target_cluster_id = None
        if self.grounding.cluster_data:
            clusters = self.grounding.cluster_data.get("clusters", [])
            for c in clusters:
                if any(artist_id in track for track in c.get("member_track_ids", [])):
                    target_cluster_id = c["cluster_id"]
                    break

        # 3. Setup Sections Structure
        sections_config = [
            ("intro", "setup", "setup", {"unknown", "sustain"}),
            ("verse_1", "narrative", "setup", {"sustain", "unknown"}),
            ("pre_chorus", "build", "build", {"intensify"}),
            ("chorus", "release", "climax", {"release", "intensify"}),
            ("verse_2", "narrative", "build", {"sustain"}),
            ("bridge", "twist", "twist", {"distort", "invert"}),
            ("chorus_final", "release", "climax", {"release", "intensify"}),
            ("outro", "resolution", "resolution", {"sustain", "release"}),
        ]
        
        # 4. Integrate Hook Grammar
        hook_bp = generate_hook_blueprint(self.hook_bank_path)
        
        creative_sections = []
        theme_chain = []
        current_motif = start_motif
        
        # 5. Distribute motifs and imagery based on narrative intent
        for s_name, func, intent, target_types in sections_config:
            
            # Narrative sampling if graph exists
            if graph:
                trans = self._sample_target_transition(graph, current_motif, target_types)
                motif = trans["dst_motif"]
                theme_chain.append(trans)
                # Only progress motif on key sections (chorus, bridge) or by chance
                if intent in ["climax", "twist"] or random.random() > 0.4:
                    current_motif = motif
            else:
                motif = start_motif
            
            # Grounding
            intensity = 0.8 if intent == "climax" else 0.5
            anchors = self.grounding.select_contextual_anchors(
                cluster_id=target_cluster_id, count=3, intensity=intensity
            )
            
            # Hooks
            syllables = hook_bp.get("syllables", []) if "chorus" in s_name else []
            rhyme = hook_bp.get("rhyme_vowel", "a") if "chorus" in s_name else None
            
            # Abstraction Control
            # Verse is concrete (0.15), Chorus is concept (0.35)
            ceiling = 0.35 if intent == "climax" else 0.15 if intent == "setup" else 0.25
            
            creative_sections.append(CreativeSection(
                section_name=s_name,
                function=func,
                primary_motif=motif,
                imagery_anchors=anchors,
                syllable_target=syllables,
                rhyme_vowel=rhyme,
                abstraction_ceiling=ceiling,
                grounding_intensity=intensity,
                narrative_intent=intent
            ))

        return AbstractBlueprint(
            track_id=f"{artist_id}_{mode_id}_{random.randint(1000, 9999)}",
            target_artist_id=artist_id,
            target_mode_id=mode_id,
            primary_cluster=target_cluster_id or "unknown",
            thematic_chain=theme_chain,
            sections=creative_sections,
            creativity_index=creativity_index
        )
