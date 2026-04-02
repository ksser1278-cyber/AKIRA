# src/akira_engine/creative/runner.py
"""Orchestration layer for the AKIRA ENGINE creative pipeline.

Handles I/O, logging, artifact persistence, and coordination between 
the pure-logic modules (planner, admission, routing). 

The engine.py module remains side-effect-free for unit testing.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.akira_engine.creative.planner.engine import CreativePlannerEngine
from src.akira_engine.creative.planner.schema import AbstractBlueprint, CreativeSection
from src.akira_engine.creative.canon.admission import CanonAdmissionEngine
from src.akira_engine.creative.canon.policies import AdmissionStatus
from src.akira_engine.execution.mod import run_production_loop
from src.akira_engine.demo_runtime import _resolve_generation_backend, _generate_llm_candidate

logger = logging.getLogger("akira.runner")


class CreativeRunner:
    """Orchestrates the full creative pipeline with I/O management.
    
    Sequence:
    1. Load intelligence artifacts (motif graph, clusters, hooks)
    2. Invoke CreativePlannerEngine (pure logic)
    3. Persist blueprint to disk
    4. (Optional) Evaluate and admit to canon
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.output_dir = project_root / "outputs" / "blueprints"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.planner = CreativePlannerEngine(project_root)
        self.canon = CanonAdmissionEngine(project_root)

    def design_and_save(
        self,
        artist_id: str,
        mode_id: str,
        start_motif: Optional[str] = None,
        creativity_index: float = 0.5
    ) -> Dict[str, Any]:
        """Design a blueprint and persist it to disk."""
        
        # 1. Pure logic: design
        blueprint = self.planner.design_blueprint(
            artist_id=artist_id,
            mode_id=mode_id,
            start_motif=start_motif,
            creativity_index=creativity_index
        )
        
        # 2. I/O: save
        bp_path = self.output_dir / f"{blueprint.track_id}.json"
        self._save_blueprint(blueprint, bp_path)
        logger.info(f"Blueprint saved: {bp_path}")
        
        return {
            "blueprint": blueprint,
            "path": str(bp_path),
            "track_id": blueprint.track_id
        }

    def run_full_cycle(
        self,
        artist_id: str,
        mode_id: str,
        candidate_count: int = 3,
        model_provider: str = "gpt",
        model_name: Optional[str] = None,
        creativity_index: float = 0.5
    ) -> Dict[str, Any]:
        """
        Executes the full AKIRA ENGINE creative cycle:
        Design -> Route -> Generate -> Critique -> Admit.
        """
        # 1. Design Blueprint
        design_result = self.design_and_save(artist_id, mode_id, creativity_index=creativity_index)
        blueprint = design_result["blueprint"]
        
        # 2. Resolve Backend
        backend = _resolve_generation_backend(
            self.project_root, 
            requested_generation_mode="llm", 
            model_provider=model_provider, 
            model_name=model_name
        )
        
        # 3. Create Generation Callback
        def _candidate_generator_cb(plan_legacy, prompt_package, index, rng):
            return _generate_llm_candidate(
                plan_legacy, 
                prompt_package, 
                index=index, 
                api_key=backend["api_key"], 
                model_provider=model_provider, 
                active_model=backend["active_model"], 
                artist_id=artist_id, 
                rng=rng
            )

        # 4. Production Loop (Stage L)
        execution_result = run_production_loop(
            self.project_root,
            blueprint,
            candidate_generator_fn=_candidate_generator_cb,
            max_candidates=candidate_count
        )
        
        winner = execution_result["selected_candidate"]
        critic_score = execution_result["critic"]
        promotion = execution_result["promotion"]
        
        # 5. Evaluate and Admit
        critic_metrics = critic_score.scores
        # Map critic score map to what AdmissionEngine expects
        combined_metrics = {
            "craft_score": critic_metrics.get("total", 0.0),
            "grounding_intensity": critic_metrics.get("imagery_coverage", 0.0), # Direct grounding match
            "composite_originality": admission_result_tmp_was_here if False else 1.0, # Placeholder: will be computed by Engine
            "cliche_density": critic_metrics.get("cliche_density", 0.0),
        }

        admission_result = self.evaluate_and_admit(
            track_id=blueprint.track_id,
            lyrics=winner["markdown"],
            track_features={
                "cluster_id": blueprint.target_mode_id,
                "motifs": [s.primary_motif for s in blueprint.sections],
                "hooks": [s.primary_motif for s in blueprint.sections if "hook" in s.section_name.lower()],
                "imagery": [anchor for s in blueprint.sections for anchor in s.imagery_anchors],
            },
            critic_report=critic_metrics,
            grounding_intensity=critic_metrics.get("imagery_coverage", 0.0)
        )
        
        return {
            "track_id": blueprint.track_id,
            "blueprint": blueprint,
            "execution": execution_result,
            "admission": admission_result,
            "grade": promotion.grade.upper()
        }

    def evaluate_and_admit(
        self,
        track_id: str,
        lyrics: str,
        track_features: Dict[str, Any],
        critic_report: Optional[Dict[str, Any]] = None,
        grounding_intensity: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Evaluate a track for canon admission and persist results."""
        
        # 1. Pure logic: evaluate 
        status, reasons, metrics = self.canon.evaluate_admission(
            track_features,
            critic_report=critic_report,
            grounding_intensity=grounding_intensity
        )
        
        admission_info = {
            "status": status.value,
            "reasons": reasons,
            "metrics": track_features,
            "policy_metrics": metrics
        }
        
        # 2. I/O: persist if admitted
        if status in (AdmissionStatus.PASS, AdmissionStatus.WARN):
            self.canon.admit_track_data(track_id, lyrics, metadata or {}, admission_info)
            logger.info(f"Track admitted: {track_id} ({status.value})")
        else:
            logger.info(f"Track blocked: {track_id} ({status.value}) — {reasons}")
        
        # 3. I/O: save evaluation log
        log_path = self.project_root / "outputs" / "admission_log.jsonl"
        self._append_log(log_path, {
            "track_id": track_id,
            "status": status.value,
            "reasons": reasons,
            "craft_score": metrics.get("craft_score", 0.0),
            "originality": metrics.get("composite_originality", 0.0)
        })
        
        return {
            "status": status,
            "reasons": reasons,
            "metrics": metrics
        }

    def _save_blueprint(self, blueprint: AbstractBlueprint, path: Path):
        """Serialize blueprint to JSON."""
        from dataclasses import asdict
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(blueprint), f, ensure_ascii=False, indent=2)

    def _append_log(self, path: Path, entry: Dict[str, Any]):
        """Append a JSONL entry to the admission log."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
