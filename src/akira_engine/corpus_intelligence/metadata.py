# src/akira_engine/corpus_intelligence/metadata.py
"""Common metadata helper for all intelligence artifacts (Day 9).

Ensures every intelligence artifact (novelty_index, style_clusters,
motif_transition_graph, hook_grammar_bank) carries reproducible metadata.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Current schema version for all intelligence artifacts
SCHEMA_VERSION = "2.0"
BUILD_VERSION = "sprint_stabilization_w2"


def create_artifact_metadata(
    artifact_type: str,
    record_count: int,
    source_paths: List[str] = None,
    feature_flags: Dict[str, bool] = None,
    extra: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Creates a standard metadata block for an intelligence artifact.
    
    Fields:
    - schema_version: Version of the metadata schema
    - build_version: Build identifier of the engine that generated this
    - source_manifest_hash: SHA256 of sorted source file list
    - feature_flags: Active features during generation
    - build_timestamp: ISO8601 timestamp
    - record_count: Number of records in the artifact
    """
    source_paths = source_paths or []
    feature_flags = feature_flags or {}
    
    # Hash source list for reproducibility
    manifest_str = "\n".join(sorted(source_paths))
    manifest_hash = hashlib.sha256(manifest_str.encode("utf-8")).hexdigest()[:16]
    
    metadata = {
        "schema_version": SCHEMA_VERSION,
        "build_version": BUILD_VERSION,
        "source_manifest_hash": manifest_hash,
        "feature_flags": feature_flags,
        "build_timestamp": datetime.now(timezone.utc).isoformat(),
        "record_count": record_count,
        "artifact_type": artifact_type,
    }
    
    if extra:
        metadata.update(extra)
    
    return metadata


def inject_metadata_into_artifact(
    artifact_path: Path,
    metadata: Dict[str, Any]
) -> None:
    """Injects metadata block into an existing JSON artifact file."""
    with open(artifact_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    data["_metadata"] = metadata
    
    with open(artifact_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def read_artifact_metadata(artifact_path: Path) -> Optional[Dict[str, Any]]:
    """Reads the metadata block from an intelligence artifact."""
    try:
        with open(artifact_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("_metadata")
    except:
        return None
