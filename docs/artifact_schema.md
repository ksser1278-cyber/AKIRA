# Artifact Metadata Schema

## Version: 2.0

All intelligence artifacts must include a `_metadata` block with the following fields:

## Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | string | Version of the metadata schema (currently `"2.0"`) |
| `build_version` | string | Engine build identifier (e.g., `"sprint_stabilization_w2"`) |
| `source_manifest_hash` | string | SHA256 prefix of sorted source file list |
| `feature_flags` | object | Active features during generation |
| `build_timestamp` | string | ISO8601 UTC timestamp |
| `record_count` | integer | Number of records in the artifact |
| `artifact_type` | string | One of: `motif_graph`, `style_clusters`, `hook_grammar`, `novelty_index` |

## Example

```json
{
  "_metadata": {
    "schema_version": "2.0",
    "build_version": "sprint_stabilization_w2",
    "source_manifest_hash": "a1b2c3d4e5f6g7h8",
    "feature_flags": {
      "pruning_enabled": true,
      "unknown_cap": true
    },
    "build_timestamp": "2026-04-01T15:00:00+00:00",
    "record_count": 165,
    "artifact_type": "motif_graph"
  }
}
```

## Usage

```python
from src.akira_engine.corpus_intelligence.metadata import (
    create_artifact_metadata,
    inject_metadata_into_artifact,
    read_artifact_metadata
)

# Create
meta = create_artifact_metadata("motif_graph", record_count=165)

# Inject into existing file
inject_metadata_into_artifact(Path("data/motifs/motif_transition_graph_v1.json"), meta)

# Read
meta = read_artifact_metadata(Path("data/motifs/motif_transition_graph_v1.json"))
```

## Affected Artifacts

- `data/novelty/novelty_index_v1.json`
- `data/clusters/style_clusters_v1.json`
- `data/motifs/motif_transition_graph_v1.json`
- `data/hooks/hook_grammar_bank_v1.json`
