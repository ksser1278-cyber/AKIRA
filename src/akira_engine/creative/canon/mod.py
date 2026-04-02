# src/akira_engine/creative/canon/mod.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.akira_engine.creative.canon.admission import CanonAdmissionEngine
from src.akira_engine.creative.canon.policies import AdmissionStatus


def admit_to_canon(
    project_root: Path,
    track_id: str,
    lyrics: str,
    track_features: Optional[Dict[str, Any]] = None,
    critic_report: Optional[Dict[str, Any]] = None,
    grounding_intensity: float = 0.5,
    metadata: Optional[Dict[str, Any]] = None,
    # Legacy compat
    novelty_report: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Execute the Canon Admission workflow for a generated track.
    
    Uses the new 3-stage gate (Pass/Warn/Hold/Reject) with rejection reason codes.
    Maintains backward compatibility with old novelty_report-based callers.
    """
    engine = CanonAdmissionEngine(project_root)
    
    # Legacy compatibility: if called with novelty_report instead of track_features
    if track_features is None and novelty_report is not None:
        # Convert legacy format to new format
        track_features = {
            "motifs": [],
            "hooks": [],
            "imagery": [],
        }
        # Legacy callers pass composite_score etc. through novelty_report
        # We map to a synthetic craft score for compatibility
        legacy_composite = novelty_report.get("composite_score", 0.0)
        if critic_report is None:
            critic_report = {"total_score": legacy_composite}
    
    if track_features is None:
        track_features = {"motifs": [], "hooks": [], "imagery": []}
    
    # 1. Evaluate with new 3-stage policy
    status, reasons, metrics = engine.evaluate_admission(
        track_features, 
        critic_report=critic_report,
        grounding_intensity=grounding_intensity
    )
    
    # 2. Admit if PASS
    admission_info = {
        "status": status.value,
        "reasons": reasons,
        "metrics": track_features,
        "policy_metrics": metrics
    }
    
    if status == AdmissionStatus.PASS:
        engine.admit_track_data(track_id, lyrics, metadata or {}, admission_info)
        result_status = "admitted"
    elif status == AdmissionStatus.WARN:
        engine.admit_track_data(track_id, lyrics, metadata or {}, admission_info)
        result_status = "admitted_with_warnings"
    elif status == AdmissionStatus.HOLD:
        result_status = "held_for_review"
    else:
        result_status = "rejected"
        
    return {
        "track_id": track_id,
        "status": result_status,
        "admission_status": status.value,
        "reasons": reasons,
        "composite_score": metrics.get("craft_score", 0.0),
        "originality": metrics.get("composite_originality", 0.0),
        "diversity_bonus": metrics.get("diversity_bonus", 0.0)
    }


def sync_intelligence_from_canon(project_root: Path):
    """Placeholder for incremental intelligence updates from newly admitted canon tracks."""
    pass
