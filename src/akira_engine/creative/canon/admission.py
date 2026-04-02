# src/akira_engine/creative/canon/admission.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


from src.akira_engine.critic.originality import calculate_originality_metrics
from src.akira_engine.creative.canon.policies import AdmissionPolicy, AdmissionStatus
from src.akira_engine.creative.config import CreativeConfig
from src.akira_engine.creative.canon.constraints import check_diversity_constraints, apply_underrepresented_bonus


class CanonAdmissionEngine:
    """Evaluates and admits high-quality generated tracks into the internal canon."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.config = CreativeConfig.load_canonical(project_root)
        self.policy = AdmissionPolicy(self.config)
        self.novelty_index_path = project_root / "data" / "novelty" / "novelty_index_v1.json"
        self.canon_dir = project_root / "data" / "canon_tracks"
        self.canon_dir.mkdir(parents=True, exist_ok=True)

    def _load_comparison_tracks(self) -> List[Dict[str, Any]]:
        """Loads existing canon tracks for similarity comparison. 
        Sorted by timestamp (newest first).
        """
        tracks = []
        for p in sorted(self.canon_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    info = data.get("admission_info", {})
                    metrics = info.get("metrics", info)
                    if "track_id" not in metrics:
                        metrics["track_id"] = data.get("track_id", p.stem)
                    tracks.append(metrics)
            except: continue
        return tracks

    def evaluate_admission(
        self, 
        track_features: Dict[str, Any], 
        critic_report: Optional[Dict[str, Any]] = None,
        grounding_intensity: float = 0.5
    ) -> Tuple[AdmissionStatus, List[str], Dict[str, Any]]:
        """Determines if a track is 'Elite' enough to join the internal canon.
        
        Uses 3-stage logic (Originality, Craft, Policy, Diversity) with Rejection Reasons.
        """
        # 1. Load comparison set (Recency sorted)
        comparison_tracks = self._load_comparison_tracks()
        
        # 2. Calculate Originality Metrics (Day 1: Motif focus)
        originality = calculate_originality_metrics(track_features, comparison_tracks)
        
        # 3. Check Diversity Constraints (Day 2)
        diversity = check_diversity_constraints(track_features, comparison_tracks)
        
        # 4. Calculate Consolidate Metrics (with underrepresented bonus)
        # Fix: critic_report uses 'total', not 'total_score'
        craft_score = (critic_report or {}).get("total", 0.0)
        # Fix: imagery coverage is grounding in this context
        grounding_score = (critic_report or {}).get("imagery_coverage", grounding_intensity)
        
        bonus = apply_underrepresented_bonus(track_features, comparison_tracks)
        effective_craft = craft_score + bonus
        
        combined_metrics = {
            "craft_score": effective_craft,
            "raw_craft_score": craft_score,
            "grounding_intensity": grounding_score,
            "diversity_bonus": bonus,
            **originality
        }
        
        # 5. Evaluate Policy
        status, reasons = self.policy.evaluate(combined_metrics)
        
        # 6. Inject Diversity Reasons if any
        if not diversity["passed"]:
            reasons.extend(diversity["reasons"])
            # Diversity failures on recent 100 are REJECT (Hard Cap)
            status = AdmissionStatus.REJECT
            
        return status, sorted(list(set(reasons))), combined_metrics

    def admit_track_data(self, track_id: str, lyrics: str, metadata: Dict[str, Any], admission_info: Dict[str, Any]) -> bool:
        """Saves the admitted track's data to the internal creative corpus."""
        
        save_path = self.canon_dir / f"{track_id}.json"
        data = {
            "track_id": track_id,
            "lyrics": lyrics,
            "metadata": metadata,
            "admission_info": admission_info,
            "admission_timestamp": metadata.get("timestamp", "unknown")
        }
        
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return True
