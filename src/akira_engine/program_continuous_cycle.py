from __future__ import annotations

from pathlib import Path
from typing import Any

from .corpus_value_classification import classify_corpus_value
from .tier1_continuous_cycle import run_tier1_continuous_cycle
from .training_data import write_json
from .vocaloid_metadata_canonicalize import build_vocaloid_metadata_canonical_corpus
from .vocaloid_metadata_coverage import build_vocaloid_metadata_coverage_report
from .vocaloid_metadata_enrichment import enrich_vocaloid_metadata_intake
from .vocaloid_metadata_intake import seed_vocadb_bulk_metadata_intake
from .vocaloid_metadata_queue_accept import auto_accept_vocaloid_metadata_queue
from .vocaloid_metadata_queue_triage import auto_triage_vocaloid_metadata_queue
from .vocaloid_metadata_review import review_vocaloid_metadata_intake
from .vocaloid_metadata_review_queue import build_vocaloid_metadata_review_queue
from .vocaloid_metadata_utf8_audit import audit_vocaloid_metadata_utf8


def _select_active_tier1_workspace(workspaces_root: Path) -> Path | None:
    candidates: list[tuple[float, Path]] = []
    for workspace in workspaces_root.glob("tier1_map_seed_pilot*"):
        if not workspace.is_dir():
            continue
        incoming_dir = workspace / "incoming"
        if not incoming_dir.exists():
            continue
        incoming_count = len(list(incoming_dir.glob("vocadb_*.json")))
        if incoming_count <= 0:
            continue
        marker = workspace / "workspace_manifest.json"
        timestamp = marker.stat().st_mtime if marker.exists() else workspace.stat().st_mtime
        candidates.append((timestamp, workspace))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def run_program_continuous_cycle(
    *,
    project_root: Path,
    batch_tag: str,
    bulk_page_count: int = 3,
    bulk_page_size: int = 50,
    bulk_start_offset: int = 0,
    bulk_sort: str = "PublishDate",
    run_tier1_cycle: bool = True,
) -> dict[str, Any]:
    project_root = project_root.resolve()

    intake_root = project_root / "datasets" / "_global" / "vocaloid_metadata_intake"
    incoming_root = intake_root / f"incoming_bulk_{batch_tag}"
    review_root = project_root / "reports" / "planning" / f"vocaloid_metadata_review_bulk_{batch_tag}"
    queue_root = intake_root / f"manual_review_queue_bulk_{batch_tag}"
    canonical_root = project_root / "datasets" / "_global" / "vocaloid_metadata_canonical" / f"bulk_{batch_tag}"
    coverage_root = project_root / "reports" / "planning" / "vocaloid_metadata_coverage" / f"bulk_{batch_tag}"
    utf8_root = project_root / "reports" / "planning" / "vocaloid_metadata_utf8_audit" / f"bulk_{batch_tag}"
    value_root = project_root / "reports" / "planning" / "corpus_value_classification" / f"bulk_{batch_tag}"

    bulk_seed = seed_vocadb_bulk_metadata_intake(
        project_root=project_root,
        output_dir=incoming_root,
        page_count=bulk_page_count,
        page_size=bulk_page_size,
        start_offset=bulk_start_offset,
        sort=bulk_sort,
    )
    bulk_enrichment = enrich_vocaloid_metadata_intake(
        intake_dir=incoming_root,
    )
    bulk_review = review_vocaloid_metadata_intake(
        intake_dir=incoming_root,
        output_dir=review_root,
    )
    bulk_queue = build_vocaloid_metadata_review_queue(
        review_manifest_path=review_root / "vocaloid_metadata_review_manifest.json",
        output_root=queue_root,
    )
    bulk_triage = auto_triage_vocaloid_metadata_queue(
        queue_root=queue_root,
    )
    bulk_accept = auto_accept_vocaloid_metadata_queue(
        queue_root=queue_root,
    )
    bulk_canonical = build_vocaloid_metadata_canonical_corpus(
        queue_root=queue_root,
        output_root=canonical_root,
    )
    bulk_coverage = build_vocaloid_metadata_coverage_report(
        corpus_root=canonical_root,
        output_root=coverage_root,
    )
    bulk_utf8 = audit_vocaloid_metadata_utf8(
        corpus_root=canonical_root,
        output_root=utf8_root,
    )
    bulk_value = classify_corpus_value(
        corpus_root=canonical_root,
        output_root=value_root,
        write_back=True,
    )

    if run_tier1_cycle:
        tier1_workspaces_root = project_root / "datasets" / "_global" / "vocadb_lyric_grounding_acquisition_pilots"
        active_workspace = _select_active_tier1_workspace(tier1_workspaces_root) or (
            tier1_workspaces_root / "tier1_map_seed_pilot20_v1"
        )
        active_name = active_workspace.name
        tier1_cycle = run_tier1_continuous_cycle(
            corpus_root=project_root / "datasets" / "_global" / "vocaloid_metadata_canonical" / "tier1_map_seed",
            pilot20_workspace=active_workspace,
            pilot20_generation_root=project_root / "datasets" / "training" / "generation_profiles" / active_name,
            pilot20_merged_generation_root=project_root / "datasets" / "training" / "generation_profiles" / f"{active_name}_merged",
            pilot20_validation_root=project_root / "reports" / "planning" / "vocadb_lyric_grounding_validation" / active_name,
            pilot20_import_root=project_root / "datasets" / "training" / "vocadb_grounded_technique" / active_name,
            pilot20_joinability_root=project_root / "reports" / "planning" / "generation_joinability_audit" / active_name,
            pilot20_readiness_root=project_root / "reports" / "planning" / "generation_readiness_audit" / f"{active_name}_merged",
            pilot20_url_map_path=active_workspace / "trusted_lyric_url_map.json",
            pilot10_generation_root=project_root / "datasets" / "training" / "generation_profiles" / "tier1_map_seed_pilot10_merged_v10",
            sound_review_workspace=project_root / "datasets" / "_global" / "sound_profile_review" / "tier1_map_seed_pilot10_v1",
            sound_reviewed_generation_root=project_root / "datasets" / "training" / "generation_profiles" / "tier1_map_seed_pilot10_sound_reviewed_v2",
            sound_readiness_root=project_root / "reports" / "planning" / "generation_readiness_audit" / "tier1_map_seed_pilot10_sound_reviewed_v2",
            sound_prompt_asset_root=project_root / "datasets" / "training" / "suno_prompt_assets" / "tier1_map_seed_pilot10_sound_reviewed_v2",
            grounding_status_root=project_root / "reports" / "planning" / "vocadb_lyric_grounding_status",
            tier1_queue_root=project_root / "datasets" / "training" / "lyric_technique_acquisition_queue" / "tier1_map_seed_v1",
            tier1_source_workspace_root=project_root / "datasets" / "_global" / "vocadb_lyric_grounding_acquisition" / "tier1_map_seed_v1",
            tier1_rollover_planning_root=project_root / "reports" / "planning" / "lyric_technique_pilot_batch" / "tier1_rollover",
        )
    else:
        tier1_cycle = {
            "counts": {
                "pilot20_invalid": 0,
                "pilot20_overlap": 0,
                "pilot10_production_candidate": 0,
                "pilot10_professional_target": 0,
            },
            "manifest_path": "",
        }

    manifest = {
        "schema_version": "1.0",
        "record_type": "program_continuous_cycle_manifest",
        "project_root": str(project_root),
        "batch_tag": batch_tag,
        "bulk_inputs": {
            "page_count": bulk_page_count,
            "page_size": bulk_page_size,
            "start_offset": bulk_start_offset,
            "sort": bulk_sort,
            "run_tier1_cycle": run_tier1_cycle,
        },
        "counts": {
            "bulk_seed_written": bulk_seed["counts"]["written_records"],
            "bulk_enriched_records": bulk_enrichment["counts"]["enriched_records"],
            "bulk_review_records": bulk_review["counts"]["records"],
            "bulk_queue_records": bulk_queue["counts"]["queued_records"],
            "bulk_needs_patch": bulk_triage["counts"]["needs_patch"],
            "bulk_auto_accepted": bulk_accept["counts"]["accepted"],
            "bulk_canonical_records": bulk_canonical["counts"]["accepted_records"],
            "bulk_core": bulk_value["counts"]["core"],
            "bulk_low_value_retained": bulk_value["counts"]["low_value_retained"],
            "tier1_pilot20_invalid": tier1_cycle["counts"]["pilot20_invalid"],
            "tier1_pilot20_overlap": tier1_cycle["counts"]["pilot20_overlap"],
            "tier1_pilot10_production_candidate": tier1_cycle["counts"]["pilot10_production_candidate"],
            "tier1_pilot10_professional_target": tier1_cycle["counts"]["pilot10_professional_target"],
        },
        "outputs": {
            "bulk_seed_manifest": bulk_seed["manifest_path"],
            "bulk_enrichment_manifest": bulk_enrichment["manifest_path"],
            "bulk_review_manifest": bulk_review["manifest_path"],
            "bulk_queue_manifest": bulk_queue["manifest_path"],
            "bulk_triage_manifest": bulk_triage["manifest_path"],
            "bulk_accept_manifest": bulk_accept["manifest_path"],
            "bulk_canonical_manifest": bulk_canonical["manifest_path"],
            "bulk_coverage_manifest": bulk_coverage["manifest_path"],
            "bulk_utf8_manifest": bulk_utf8["manifest_path"],
            "bulk_value_manifest": bulk_value["manifest_path"],
            "tier1_cycle_manifest": tier1_cycle["manifest_path"],
        },
    }
    manifest_path = write_json(
        project_root / "reports" / "planning" / f"program_continuous_cycle_{batch_tag}.json",
        manifest,
    )
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def run_program_continuous_sweep(
    *,
    project_root: Path,
    batch_tag_prefix: str,
    batch_count: int,
    bulk_page_count: int = 3,
    bulk_page_size: int = 50,
    bulk_start_offset: int = 0,
    bulk_offset_step: int | None = None,
    bulk_sort: str = "PublishDate",
    run_tier1_once: bool = True,
) -> dict[str, Any]:
    project_root = project_root.resolve()
    offset_step = bulk_offset_step or (bulk_page_count * bulk_page_size)

    runs: list[dict[str, Any]] = []
    totals = {
        "bulk_seed_written": 0,
        "bulk_enriched_records": 0,
        "bulk_review_records": 0,
        "bulk_queue_records": 0,
        "bulk_needs_patch": 0,
        "bulk_auto_accepted": 0,
        "bulk_canonical_records": 0,
        "bulk_core": 0,
        "bulk_low_value_retained": 0,
    }

    last_tier1_counts: dict[str, Any] = {}
    for index in range(batch_count):
        start_offset = bulk_start_offset + (index * offset_step)
        batch_tag = f"{batch_tag_prefix}_{index + 1:02d}"
        manifest = run_program_continuous_cycle(
            project_root=project_root,
            batch_tag=batch_tag,
            bulk_page_count=bulk_page_count,
            bulk_page_size=bulk_page_size,
            bulk_start_offset=start_offset,
            bulk_sort=bulk_sort,
            run_tier1_cycle=(not run_tier1_once) or index == (batch_count - 1),
        )
        counts = manifest["counts"]
        for key in totals:
            totals[key] += int(counts.get(key, 0) or 0)
        last_tier1_counts = {
            "tier1_pilot20_invalid": counts.get("tier1_pilot20_invalid", 0),
            "tier1_pilot20_overlap": counts.get("tier1_pilot20_overlap", 0),
            "tier1_pilot10_production_candidate": counts.get("tier1_pilot10_production_candidate", 0),
            "tier1_pilot10_professional_target": counts.get("tier1_pilot10_professional_target", 0),
        }
        runs.append(
            {
                "batch_tag": batch_tag,
                "bulk_start_offset": start_offset,
                "manifest_path": manifest["manifest_path"],
                "counts": counts,
            }
        )

    sweep_manifest = {
        "schema_version": "1.0",
        "record_type": "program_continuous_sweep_manifest",
        "project_root": str(project_root),
        "batch_tag_prefix": batch_tag_prefix,
        "inputs": {
            "batch_count": batch_count,
            "bulk_page_count": bulk_page_count,
            "bulk_page_size": bulk_page_size,
            "bulk_start_offset": bulk_start_offset,
            "bulk_offset_step": offset_step,
            "bulk_sort": bulk_sort,
            "run_tier1_once": run_tier1_once,
        },
        "counts": {
            **totals,
            **last_tier1_counts,
            "runs": len(runs),
        },
        "runs": runs,
    }
    manifest_path = write_json(
        project_root / "reports" / "planning" / f"program_continuous_sweep_{batch_tag_prefix}.json",
        sweep_manifest,
    )
    sweep_manifest["manifest_path"] = str(manifest_path)
    return sweep_manifest
