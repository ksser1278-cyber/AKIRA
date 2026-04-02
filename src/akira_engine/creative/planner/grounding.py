# src/akira_engine/creative/planner/grounding.py

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


class ImageryGroundingRegistry:
    """Registry for cluster-aware somatic and scenic imagery selection."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.atlas_path = project_root / "outputs" / "atlas_v2_trusted.json"
        self.cluster_path = project_root / "data" / "clusters" / "style_clusters_v1.json"
        
        self.body_pool: List[str] = []
        self.scene_pool: List[str] = []
        self.sound_pool: List[str] = []
        self.cluster_data: Dict[str, Any] = {}
        
        self._load_data()

    def _load_data(self):
        # 1. Load Atlas
        if self.atlas_path.exists():
            with open(self.atlas_path, "r", encoding="utf-8") as f:
                atlas = json.load(f)
                self.body_pool = atlas.get("body", [])
                self.scene_pool = atlas.get("scene", [])
                self.sound_pool = atlas.get("sound", [])

        # 2. Load Clusters
        if self.cluster_path.exists():
            with open(self.cluster_path, "r", encoding="utf-8") as f:
                self.cluster_data = json.load(f)

    def select_contextual_anchors(
        self,
        cluster_id: Optional[str] = None,
        count: int = 3,
        intensity: float = 0.5
    ) -> List[str]:
        """Select 3-5 anchors grounded in the target cluster's somatic/scenic style."""
        
        # 1. Default pool from atlas
        # High quality somatic atoms (body) and scenic (environment)
        somatic_pool = set(self.body_pool)
        scenic_pool = set(self.scene_pool)
        
        # 2. Cluster Resonant Atoms
        resonant_atoms = []
        if cluster_id and self.cluster_data:
            clusters = self.cluster_data.get("clusters", [])
            target = next((c for c in clusters if c["cluster_id"] == cluster_id), None)
            if target:
                dominant = target.get("dominant_atoms", [])
                # Filter for atoms that are likely somatic or scenic
                # (Intersection with atlas, or heuristic match)
                resonant_atoms = [a for a in dominant if a in somatic_pool or a in scenic_pool]

        # 3. Sampling
        anchors = []
        
        # Priority 1: Resonant atoms (Cluster specific)
        if resonant_atoms:
            anchors.extend(random.sample(resonant_atoms, min(len(resonant_atoms), count)))

        # Priority 2: Somatic Fillers
        if len(anchors) < count and self.body_pool:
            fill_count = count - len(anchors)
            available = [a for a in self.body_pool if a not in anchors]
            if available:
                anchors.extend(random.sample(available, min(len(available), fill_count)))

        # Priority 3: Scenic Fillers
        if len(anchors) < count and self.scene_pool:
            fill_count = count - len(anchors)
            available = [a for a in self.scene_pool if a not in anchors]
            if available:
                anchors.extend(random.sample(available, min(len(available), fill_count)))

        # Shuffling for variety
        random.shuffle(anchors)
        return anchors[:count]
