from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .generation_joinability_audit import audit_generation_joinability
from .generation_readiness_audit import audit_generation_readiness
from .professional_quality_cycle import run_professional_quality_cycle
from .sound_profile_review import build_sound_profile_review_workspace
from .tier1_grounding_rollover import advance_tier1_grounding_lane
from .track_generation_profile import build_track_generation_records
from .training_data import write_json
from .vocadb_grounded_technique_import import import_vocadb_grounded_technique_records
from .vocadb_lyric_grounding_auto import auto_ground_vocadb_workspace_from_url_map
from .vocadb_lyric_grounding_discovery import discover_trusted_lyric_urls_for_workspace
from .vocadb_lyric_grounding_status import report_vocadb_lyric_grounding_status
from .vocadb_lyric_grounding_triage import (
    auto_triage_vocadb_lyric_grounding_workspace,
    defer_vocadb_lyric_grounding_records,
)
from .vocadb_lyric_grounding_validation import validate_vocadb_lyric_grounding_workspace


def run_tier1_continuous_cycle(
    *,
    corpus_root: Path,
    pilot20_workspace: Path,
    pilot20_generation_root: Path,
    pilot20_merged_generation_root: Path,
    pilot20_validation_root: Path,
    pilot20_import_root: Path,
    pilot20_joinability_root: Path,
    pilot20_readiness_root: Path,
    pilot20_url_map_path: Path | None,
    pilot10_generation_root: Path,
    sound_review_workspace: Path,
    sound_reviewed_generation_root: Path,
    sound_readiness_root: Path,
    sound_prompt_asset_root: Path,
    grounding_status_root: Path,
    tier1_queue_root: Path,
    tier1_source_workspace_root: Path,
    tier1_rollover_planning_root: Path,
) -> dict[str, Any]:
    corpus_root = corpus_root.resolve()
    pilot20_workspace = pilot20_workspace.resolve()
    pilot20_generation_root = pilot20_generation_root.resolve()
    pilot20_merged_generation_root = pilot20_merged_generation_root.resolve()
    pilot20_validation_root = pilot20_validation_root.resolve()
    pilot20_import_root = pilot20_import_root.resolve()
    pilot20_joinability_root = pilot20_joinability_root.resolve()
    pilot20_readiness_root = pilot20_readiness_root.resolve()
    pilot10_generation_root = pilot10_generation_root.resolve()
    sound_review_workspace = sound_review_workspace.resolve()
    sound_reviewed_generation_root = sound_reviewed_generation_root.resolve()
    sound_readiness_root = sound_readiness_root.resolve()
    sound_prompt_asset_root = sound_prompt_asset_root.resolve()
    grounding_status_root = grounding_status_root.resolve()
    tier1_queue_root = tier1_queue_root.resolve()
    tier1_source_workspace_root = tier1_source_workspace_root.resolve()
    tier1_rollover_planning_root = tier1_rollover_planning_root.resolve()

    auto_ground_manifest = None
    auto_triage_manifest = None
    auto_defer_manifest = None
    discovery_manifest = discover_trusted_lyric_urls_for_workspace(
        workspace_root=pilot20_workspace,
    )
    merged_url_map: dict[str, Any] = {}
    if pilot20_url_map_path is not None and pilot20_url_map_path.exists():
        merged_url_map.update(json.loads(pilot20_url_map_path.read_text(encoding="utf-8")))
    merged_url_map.update(discovery_manifest.get("discovered", {}))
    if merged_url_map:
        auto_ground_manifest = auto_ground_vocadb_workspace_from_url_map(
            workspace_root=pilot20_workspace,
            url_map=merged_url_map,
        )
    unmatched_track_ids = [
        item["track_id"]
        for item in discovery_manifest.get("skipped", [])
        if str(item.get("reason", "")).startswith("no_match:")
    ]
    if unmatched_track_ids:
        auto_defer_manifest = defer_vocadb_lyric_grounding_records(
            workspace_root=pilot20_workspace,
            track_ids=unmatched_track_ids,
            review_notes="Auto-deferred to needs_patch because trusted lyric source discovery found no reliable match.",
        )
    auto_triage_manifest = auto_triage_vocadb_lyric_grounding_workspace(
        workspace_root=pilot20_workspace,
    )

    pilot20_generation = build_track_generation_records(
        corpus_root=corpus_root,
        output_root=pilot20_generation_root,
        lyric_technique_jsonl=None,
    )
    pilot20_validation = validate_vocadb_lyric_grounding_workspace(
        workspace_root=pilot20_workspace,
        output_root=pilot20_validation_root,
    )
    pilot20_import = import_vocadb_grounded_technique_records(
        workspace_root=pilot20_workspace,
        output_root=pilot20_import_root,
    )
    pilot20_joinability = audit_generation_joinability(
        generation_jsonl=pilot20_generation_root / "track_generation_records.jsonl",
        technique_jsonl=pilot20_import_root / "lyric_technique_records.jsonl",
        output_root=pilot20_joinability_root,
    )
    pilot20_merged_generation = build_track_generation_records(
        corpus_root=corpus_root,
        output_root=pilot20_merged_generation_root,
        lyric_technique_jsonl=pilot20_import_root / "lyric_technique_records.jsonl",
    )
    pilot20_readiness = audit_generation_readiness(
        generation_root=pilot20_merged_generation_root,
        output_root=pilot20_readiness_root,
    )

    sound_review = build_sound_profile_review_workspace(
        generation_root=pilot10_generation_root,
        corpus_root=corpus_root,
        output_root=sound_review_workspace,
        prompt_ready_only=True,
    )
    professional_cycle = run_professional_quality_cycle(
        generation_root=pilot10_generation_root,
        sound_review_workspace=sound_review_workspace,
        reviewed_generation_root=sound_reviewed_generation_root,
        readiness_output_root=sound_readiness_root,
        prompt_asset_output_root=sound_prompt_asset_root,
    )
    pilot10_readiness = audit_generation_readiness(
        generation_root=sound_reviewed_generation_root,
        output_root=sound_readiness_root.parent / "tier1_map_seed_pilot10_merged_v10",
    )
    grounding_status = report_vocadb_lyric_grounding_status(
        workspaces_root=pilot20_workspace.parent,
        output_root=grounding_status_root,
    )
    rollover_manifest = advance_tier1_grounding_lane(
        queue_root=tier1_queue_root,
        source_workspace_root=tier1_source_workspace_root,
        workspaces_root=pilot20_workspace.parent,
        planning_root=tier1_rollover_planning_root,
        current_workspace_root=pilot20_workspace,
        batch_size=10,
    )

    manifest = {
        "schema_version": "1.0",
        "record_type": "tier1_continuous_cycle_manifest",
        "inputs": {
            "corpus_root": str(corpus_root),
            "pilot20_workspace": str(pilot20_workspace),
            "pilot10_generation_root": str(pilot10_generation_root),
            "sound_review_workspace": str(sound_review_workspace),
        },
        "counts": {
            "pilot20_valid": pilot20_validation["counts"]["valid"],
            "pilot20_invalid": pilot20_validation["counts"]["invalid"],
            "pilot20_imported": pilot20_import["counts"]["records"],
            "pilot20_overlap": pilot20_joinability["counts"]["overlap_tracks"],
            "pilot20_prompt_ready": pilot20_readiness["counts"]["prompt_ready"],
            "pilot20_production_candidate": pilot20_readiness["counts"]["production_candidate"],
            "pilot20_professional_target": pilot20_readiness["counts"]["professional_target"],
            "pilot10_joinable": pilot10_readiness["counts"]["joinable"],
            "pilot10_prompt_ready": pilot10_readiness["counts"]["prompt_ready"],
            "pilot10_production_candidate": pilot10_readiness["counts"]["production_candidate"],
            "pilot10_professional_target": pilot10_readiness["counts"]["professional_target"],
            "sound_review_templates": sound_review["counts"]["written_incoming_records"],
            "sound_review_applied": professional_cycle["counts"]["reviewed_tracks_applied"],
            "pilot20_auto_grounded": auto_ground_manifest["counts"]["grounded"] if auto_ground_manifest else 0,
            "pilot20_auto_discovered": discovery_manifest["counts"]["discovered"],
            "pilot20_auto_deferred": auto_defer_manifest["counts"]["deferred"] if auto_defer_manifest else 0,
            "pilot20_auto_rejected": auto_triage_manifest["counts"]["rejected"] if auto_triage_manifest else 0,
            "grounding_total_accepted": grounding_status["counts"]["total_accepted"],
            "rollover_selected_next_tracks": rollover_manifest["counts"]["selected_next_tracks"],
        },
        "outputs": {
            "pilot20_generation_manifest": pilot20_generation["manifest_path"],
            "pilot20_merged_generation_manifest": pilot20_merged_generation["manifest_path"],
            "pilot20_validation_manifest": pilot20_validation["manifest_path"],
            "pilot20_import_manifest": pilot20_import["manifest_path"],
            "pilot20_joinability_manifest": pilot20_joinability["manifest_path"],
            "pilot20_readiness_manifest": pilot20_readiness["manifest_path"],
            "sound_review_workspace_manifest": sound_review["manifest_path"],
            "professional_cycle_manifest": professional_cycle["manifest_path"],
            "pilot10_readiness_manifest": pilot10_readiness["manifest_path"],
            "grounding_status_manifest": grounding_status["manifest_path"],
            "pilot20_discovery_manifest": discovery_manifest["manifest_path"],
            "pilot20_auto_ground_manifest": auto_ground_manifest["manifest_path"] if auto_ground_manifest else "",
            "pilot20_auto_defer_manifest": auto_defer_manifest["manifest_path"] if auto_defer_manifest else "",
            "pilot20_auto_triage_manifest": auto_triage_manifest["manifest_path"] if auto_triage_manifest else "",
            "tier1_rollover_manifest": rollover_manifest["manifest_path"],
        },
    }
    manifest_path = write_json(pilot20_generation_root / "tier1_continuous_cycle_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest
