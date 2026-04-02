# src/akira_engine/creative/config.py
"""Centralized configuration for the creative pipeline.

Supports dynamic calibration of thresholds based on RC results.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional


class CreativeConfig:
    """Dynamic configuration for creative policies/thresholds."""
    
    DEFAULT_THRESHOLDS = {
        "min_craft_score": 70.0,
        "warn_craft_score": 60.0,
        "min_grounding_intensity": 0.5,
        "warn_grounding_intensity": 0.4,
        "min_originality_composite": 0.4,
        "warn_originality_composite": 0.3,
        "max_cliche_density": 0.2,
        "cluster_quota": 0.25,
        "hook_continuity_limit": 3
    }
    
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.data = self._load()
        
    def _load(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            return self.DEFAULT_THRESHOLDS.copy()
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return self.DEFAULT_THRESHOLDS.copy()
            
    def save(self):
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
            
    def get(self, key: str) -> Any:
        return self.data.get(key, self.DEFAULT_THRESHOLDS.get(key))
        
    def set(self, key: str, value: Any):
        self.data[key] = value
        self.save()

    @classmethod
    def load_canonical(cls, project_root: Path) -> CreativeConfig:
        return cls(project_root / "data" / "config" / "creative_policy_v2.json")
