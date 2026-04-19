from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ..audit import load_json
from ..lyric_technique_extraction import extract_lyric_technique_records
from ..supervised_training_pilot import build_supervised_training_pilot_bundle
from ..vertex_supervised_export import export_vertex_supervised_jsonl
from ..owned_original_training_source import import_owned_original_hook_pilot
from ..supervised_training_export import export_supervised_training_samples
from ..training_data import build_training_datasets
from ..training_rights_map import bootstrap_training_rights_map
from ..vocaloid_metadata_intake import (
    load_artist_list,
    load_artist_seed_map,
    seed_vocadb_bulk_metadata_intake,
    seed_vocadb_metadata_intake,
)
from ..vocaloid_metadata_discovery import discover_vocadb_producers
from ..vocaloid_metadata_queue_triage import auto_triage_vocaloid_metadata_queue
from ..vocaloid_metadata_queue_accept import auto_accept_vocaloid_metadata_queue
from ..vocaloid_metadata_canonicalize import build_vocaloid_metadata_canonical_corpus
from ..vocaloid_metadata_coverage import build_vocaloid_metadata_coverage_report
from ..vocaloid_metadata_utf8_audit import audit_vocaloid_metadata_utf8
from ..corpus_value_classification import classify_corpus_value
from ..vocaloid_metadata_review import review_vocaloid_metadata_intake
from ..vocaloid_metadata_review_queue import build_vocaloid_metadata_review_queue
from ..vocaloid_metadata_enrichment import enrich_vocaloid_metadata_intake
from ..track_generation_profile import build_track_generation_records
from ..suno_prompt_asset_export import export_suno_prompt_assets
from ..generation_joinability_audit import audit_generation_joinability
from ..generation_readiness_audit import audit_generation_readiness
from ..sound_profile_review import build_sound_profile_review_workspace, import_reviewed_sound_profiles
from ..professional_quality_cycle import run_professional_quality_cycle as run_professional_quality_cycle_impl
from ..tier1_continuous_cycle import run_tier1_continuous_cycle as run_tier1_continuous_cycle_impl
from ..program_continuous_cycle import (
    run_program_continuous_cycle as run_program_continuous_cycle_impl,
    run_program_continuous_sweep as run_program_continuous_sweep_impl,
)
from ..lyric_technique_acquisition_queue import build_lyric_technique_acquisition_queue
from ..vocadb_lyric_grounding_workspace import build_vocadb_lyric_grounding_workspace
from ..vocadb_grounded_technique_import import import_vocadb_grounded_technique_records
from ..vocadb_lyric_grounding_validation import validate_vocadb_lyric_grounding_workspace
from ..vocadb_lyric_grounding_status import report_vocadb_lyric_grounding_status
from ..vocadb_lyric_grounding_auto import auto_ground_vocadb_workspace_from_url_map
from ..lyric_technique_pilot_batch import build_lyric_technique_pilot_batch
from ..lyric_technique_pilot_workspace import materialize_lyric_technique_pilot_workspace
from ..lyric_behavior_dataset import build_lyric_behavior_dataset
from ..form_family_catalog import build_form_family_catalog


def _archive_root(project_root: Path) -> Path:
    return project_root / "_quarantine" / "2026-04-03" / "archive"


def _resolve(project_root: Path, path: Path | None) -> Path | None:
    if path is None:
        return None
    return path if path.is_absolute() else (project_root / path).resolve()


def _has_training_inputs(project_root: Path) -> bool:
    return (
        (project_root / "artists").exists()
        and (project_root / "lyrics" / "normalized").exists()
        and (project_root / "lyrics" / "analyzed").exists()
    )


def _default_derived_jsonl(project_root: Path) -> Path:
    active = (project_root / "datasets" / "training" / "track_blueprints.jsonl").resolve()
    if active.exists():
        return active
    archived = (_archive_root(project_root) / "datasets" / "_global" / "track_blueprints.jsonl").resolve()
    return archived


def _default_rights_map(project_root: Path) -> Path:
    active = (project_root / "datasets" / "_global" / "training_rights_map.json").resolve()
    if active.exists():
        return active
    archived = (_archive_root(project_root) / "datasets" / "_global" / "training_rights_map.json").resolve()
    return archived


def _hydrate_derived_datasets(*, source_root: Path, output_dir: Path) -> dict[str, Any]:
    track_source = source_root / "datasets" / "_global" / "track_blueprints.jsonl"
    artist_source = source_root / "datasets" / "_global" / "artist_style_cards.jsonl"
    if not track_source.exists() or not artist_source.exists():
        raise SystemExit(
            f"Missing archived derived dataset inputs: {track_source} | {artist_source}"
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    track_output = output_dir / "track_blueprints.jsonl"
    artist_output = output_dir / "artist_style_cards.jsonl"
    track_output.write_text(track_source.read_text(encoding="utf-8"), encoding="utf-8")
    artist_output.write_text(artist_source.read_text(encoding="utf-8"), encoding="utf-8")

    track_count = sum(1 for line in track_output.read_text(encoding="utf-8").splitlines() if line.strip())
    artist_count = sum(1 for line in artist_output.read_text(encoding="utf-8").splitlines() if line.strip())
    manifest = {
        "schema_version": "1.0",
        "project_root": str(source_root),
        "minimum_recommendation": "hydrated_archive",
        "outputs": {
            "track_blueprints": str(track_output),
            "artist_style_cards": str(artist_output),
        },
        "counts": {
            "track_blueprints": track_count,
            "artist_style_cards": artist_count,
        },
        "artists_included": [],
        "skipped_artists": [],
        "hydrated_from_archive": True,
    }
    manifest_path = output_dir / "training_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def run_build_derived_datasets(
    *,
    project_root: Path,
    audit_json: Path | None = None,
    minimum_recommendation: str = "needs_review",
    output_dir: Path | None = None,
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    final_output_dir = _resolve(final_project_root, output_dir) or (final_project_root / "datasets" / "training").resolve()
    audit_payload = None
    if audit_json is not None:
        audit_path = _resolve(final_project_root, audit_json)
        if audit_path is None:
            raise SystemExit("Audit path resolution failed.")
        audit_payload = load_json(audit_path)
    if _has_training_inputs(final_project_root):
        return build_training_datasets(
            final_project_root,
            audit_payload=audit_payload,
            minimum_recommendation=minimum_recommendation,
            output_dir=final_output_dir,
        )
    archive_root = _archive_root(final_project_root)
    if archive_root.exists():
        return _hydrate_derived_datasets(
            source_root=archive_root,
            output_dir=final_output_dir,
        )
    return build_training_datasets(
        final_project_root,
        audit_payload=audit_payload,
        minimum_recommendation=minimum_recommendation,
        output_dir=final_output_dir,
    )


def run_extract_lyric_technique_records(
    *,
    project_root: Path,
    output_dir: Path | None = None,
    artists: list[str] | None = None,
    default_rights_status: str = "unknown",
    source_kind: str = "normalized_corpus",
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    final_output_dir = _resolve(final_project_root, output_dir) or (final_project_root / "datasets" / "training" / "technique").resolve()
    return extract_lyric_technique_records(
        project_root=final_project_root,
        output_dir=final_output_dir,
        artists=artists,
        default_rights_status=default_rights_status,
        source_kind=source_kind,
    )


def run_build_lyric_behavior_dataset(
    *,
    project_root: Path,
    artists: list[str] | None = None,
    output_root: Path | None = None,
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    final_output_root = _resolve(final_project_root, output_root) or (
        final_project_root / "datasets" / "training" / "lyric_behavior"
    ).resolve()
    return build_lyric_behavior_dataset(
        project_root=final_project_root,
        artists=artists,
        output_root=final_output_root,
    )


def run_build_form_family_catalog(
    *,
    project_root: Path,
    artists: list[str] | None = None,
    behavior_root: Path | None = None,
    output_root: Path | None = None,
    catalog_name: str = "calibration_v1",
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    final_behavior_root = _resolve(final_project_root, behavior_root)
    final_output_root = _resolve(final_project_root, output_root) or (
        final_project_root / "datasets" / "training" / "form_families"
    ).resolve()
    return build_form_family_catalog(
        final_project_root,
        artists=artists,
        behavior_root=final_behavior_root,
        output_root=final_output_root,
        catalog_name=catalog_name,
    )


def run_bootstrap_training_rights(
    *,
    project_root: Path,
    derived_jsonl: Path | None = None,
    existing_map: Path | None = None,
    output_path: Path | None = None,
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    final_derived_jsonl = _resolve(final_project_root, derived_jsonl) or _default_derived_jsonl(final_project_root)
    final_existing_map = _resolve(final_project_root, existing_map)
    final_output_path = _resolve(final_project_root, output_path) or (final_project_root / "datasets" / "_global" / "training_rights_map.json").resolve()

    payload = bootstrap_training_rights_map(
        derived_jsonl=final_derived_jsonl,
        existing_map_path=final_existing_map,
        updated_at=datetime.now().date().isoformat(),
    )
    final_output_path.parent.mkdir(parents=True, exist_ok=True)
    final_output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    payload["output_path"] = str(final_output_path)
    return payload


def run_export_supervised_samples(
    *,
    project_root: Path,
    derived_jsonl: Path | None = None,
    output_dir: Path | None = None,
    rights_map: Path | None = None,
    include_eval_only: bool = False,
    include_full_song: bool = False,
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    final_derived_jsonl = _resolve(final_project_root, derived_jsonl) or _default_derived_jsonl(final_project_root)
    final_output_dir = _resolve(final_project_root, output_dir) or (final_project_root / "datasets" / "training" / "supervised").resolve()
    final_rights_map = _resolve(final_project_root, rights_map) or _default_rights_map(final_project_root)
    return export_supervised_training_samples(
        project_root=final_project_root,
        derived_jsonl=final_derived_jsonl,
        output_dir=final_output_dir,
        rights_map_path=final_rights_map,
        include_eval_only=include_eval_only,
        include_full_song=include_full_song,
    )


def run_import_training_sources(
    *,
    project_root: Path,
    pilot_root: Path | None = None,
    rights_map: Path | None = None,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    final_pilot_root = _resolve(final_project_root, pilot_root) or (
        final_project_root / "datasets" / "_global" / "rights_cleared_corpus_acquisition" / "owned_original_hook_pilot"
    ).resolve()
    final_rights_map = _resolve(final_project_root, rights_map) or (
        final_project_root / "datasets" / "_global" / "training_rights_map.json"
    ).resolve()
    final_output_dir = _resolve(final_project_root, output_dir) or (
        final_project_root / "datasets" / "training" / "owned_original_supervised"
    ).resolve()
    return import_owned_original_hook_pilot(
        project_root=final_project_root,
        pilot_root=final_pilot_root,
        rights_map_path=final_rights_map,
        output_dir=final_output_dir,
    )


def run_build_training_pilot(
    *,
    project_root: Path,
    source_jsonl: Path | None = None,
    output_dir: Path | None = None,
    pilot_name: str = "owned_original_hook_v1",
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    final_source_jsonl = _resolve(final_project_root, source_jsonl) or (
        final_project_root / "datasets" / "training" / "owned_original_supervised" / "supervised_samples.jsonl"
    ).resolve()
    final_output_dir = _resolve(final_project_root, output_dir) or (
        final_project_root / "datasets" / "training" / "pilots" / pilot_name
    ).resolve()
    return build_supervised_training_pilot_bundle(
        project_root=final_project_root,
        source_jsonl=final_source_jsonl,
        output_dir=final_output_dir,
        pilot_name=pilot_name,
    )


def run_export_vertex_supervised(
    *,
    project_root: Path,
    train_jsonl: Path | None = None,
    eval_jsonl: Path | None = None,
    output_dir: Path | None = None,
    base_model: str = "gemini-2.5-flash",
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    final_train_jsonl = _resolve(final_project_root, train_jsonl) or (
        final_project_root / "datasets" / "training" / "pilots" / "owned_original_hook_v1" / "train.jsonl"
    ).resolve()
    final_eval_jsonl = _resolve(final_project_root, eval_jsonl) or (
        final_project_root / "datasets" / "training" / "pilots" / "owned_original_hook_v1" / "eval.jsonl"
    ).resolve()
    final_output_dir = _resolve(final_project_root, output_dir) or (
        final_project_root / "datasets" / "training" / "vertex" / "owned_original_hook_v1"
    ).resolve()
    return export_vertex_supervised_jsonl(
        project_root=final_project_root,
        train_jsonl=final_train_jsonl,
        eval_jsonl=final_eval_jsonl,
        output_dir=final_output_dir,
        base_model=base_model,
    )


def run_seed_vocadb_metadata(
    *,
    project_root: Path,
    queries: list[str] | None = None,
    artist_ids: list[int] | None = None,
    artist_names: list[str] | None = None,
    artist_list_path: Path | None = None,
    artist_map_path: Path | None = None,
    output_dir: Path | None = None,
    max_entries: int = 50,
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    final_output_dir = _resolve(final_project_root, output_dir) or (
        final_project_root / "datasets" / "_global" / "vocaloid_metadata_intake" / "incoming"
    ).resolve()
    final_artist_list_path = _resolve(final_project_root, artist_list_path)
    final_artist_map_path = _resolve(final_project_root, artist_map_path)
    merged_artist_names = list(artist_names or [])
    if final_artist_list_path is not None:
        merged_artist_names.extend(load_artist_list(final_artist_list_path))
    merged_artist_map = load_artist_seed_map(final_artist_map_path) if final_artist_map_path is not None else []
    return seed_vocadb_metadata_intake(
        project_root=final_project_root,
        queries=queries,
        artist_ids=artist_ids,
        artist_names=merged_artist_names,
        artist_map=merged_artist_map,
        output_dir=final_output_dir,
        max_entries=max_entries,
    )


def run_seed_vocadb_bulk_metadata(
    *,
    project_root: Path,
    output_dir: Path | None = None,
    page_count: int = 10,
    page_size: int = 50,
    start_offset: int = 0,
    sort: str = "PublishDate",
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    final_output_dir = _resolve(final_project_root, output_dir) or (
        final_project_root / "datasets" / "_global" / "vocaloid_metadata_intake" / "incoming_bulk"
    ).resolve()
    return seed_vocadb_bulk_metadata_intake(
        project_root=final_project_root,
        output_dir=final_output_dir,
        page_count=page_count,
        page_size=page_size,
        start_offset=start_offset,
        sort=sort,
    )


def run_discover_vocadb_producers(
    *,
    project_root: Path,
    intake_root: Path | None = None,
    output_root: Path | None = None,
    page_count: int = 5,
    page_size: int = 50,
    sample_song_entries: int = 25,
    min_synthetic_songs: int = 3,
    max_candidates: int = 25,
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    final_intake_root = _resolve(final_project_root, intake_root) or (
        final_project_root / "datasets" / "_global" / "vocaloid_metadata_intake"
    ).resolve()
    final_output_root = _resolve(final_project_root, output_root) or (
        final_project_root / "datasets" / "_global" / "vocaloid_metadata_intake" / "discovery"
    ).resolve()
    return discover_vocadb_producers(
        intake_root=final_intake_root,
        output_root=final_output_root,
        page_count=page_count,
        page_size=page_size,
        sample_song_entries=sample_song_entries,
        min_synthetic_songs=min_synthetic_songs,
        max_candidates=max_candidates,
    )


def run_review_vocaloid_metadata(
    *,
    project_root: Path,
    intake_dir: Path | None = None,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    final_intake_dir = _resolve(final_project_root, intake_dir) or (
        final_project_root / "datasets" / "_global" / "vocaloid_metadata_intake" / "incoming"
    ).resolve()
    final_output_dir = _resolve(final_project_root, output_dir) or (
        final_project_root / "reports" / "planning" / "vocaloid_metadata_review"
    ).resolve()
    return review_vocaloid_metadata_intake(
        intake_dir=final_intake_dir,
        output_dir=final_output_dir,
    )


def run_enrich_vocaloid_metadata(
    *,
    project_root: Path,
    intake_dir: Path | None = None,
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    final_intake_dir = _resolve(final_project_root, intake_dir) or (
        final_project_root / "datasets" / "_global" / "vocaloid_metadata_intake" / "incoming"
    ).resolve()
    return enrich_vocaloid_metadata_intake(
        intake_dir=final_intake_dir,
    )


def run_build_vocaloid_metadata_review_queue(
    *,
    project_root: Path,
    review_manifest: Path | None = None,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    final_review_manifest = _resolve(final_project_root, review_manifest) or (
        final_project_root / "reports" / "planning" / "vocaloid_metadata_review" / "vocaloid_metadata_review_manifest.json"
    ).resolve()
    final_output_dir = _resolve(final_project_root, output_dir) or (
        final_project_root / "datasets" / "_global" / "vocaloid_metadata_intake" / "manual_review_queue"
    ).resolve()
    return build_vocaloid_metadata_review_queue(
        review_manifest_path=final_review_manifest,
        output_root=final_output_dir,
    )


def run_auto_triage_vocaloid_metadata_queue(
    *,
    project_root: Path,
    queue_root: Path | None = None,
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    final_queue_root = _resolve(final_project_root, queue_root) or (
        final_project_root / "datasets" / "_global" / "vocaloid_metadata_intake" / "manual_review_queue"
    ).resolve()
    return auto_triage_vocaloid_metadata_queue(queue_root=final_queue_root)


def run_auto_accept_vocaloid_metadata_queue(
    *,
    project_root: Path,
    queue_root: Path | None = None,
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    final_queue_root = _resolve(final_project_root, queue_root) or (
        final_project_root / "datasets" / "_global" / "vocaloid_metadata_intake" / "manual_review_queue"
    ).resolve()
    return auto_accept_vocaloid_metadata_queue(queue_root=final_queue_root)


def run_build_vocaloid_metadata_canonical_corpus(
    *,
    project_root: Path,
    queue_root: Path | None = None,
    output_root: Path | None = None,
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    final_queue_root = _resolve(final_project_root, queue_root) or (
        final_project_root / "datasets" / "_global" / "vocaloid_metadata_intake" / "manual_review_queue"
    ).resolve()
    final_output_root = _resolve(final_project_root, output_root) or (
        final_project_root / "datasets" / "_global" / "vocaloid_metadata_canonical"
    ).resolve()
    return build_vocaloid_metadata_canonical_corpus(
        queue_root=final_queue_root,
        output_root=final_output_root,
    )


def run_report_vocaloid_metadata_coverage(
    *,
    project_root: Path,
    corpus_root: Path | None = None,
    output_root: Path | None = None,
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    final_corpus_root = _resolve(final_project_root, corpus_root) or (
        final_project_root / "datasets" / "_global" / "vocaloid_metadata_canonical"
    ).resolve()
    final_output_root = _resolve(final_project_root, output_root) or (
        final_project_root / "reports" / "planning" / "vocaloid_metadata_coverage"
    ).resolve()
    return build_vocaloid_metadata_coverage_report(
        corpus_root=final_corpus_root,
        output_root=final_output_root,
    )


def run_audit_vocaloid_metadata_utf8(
    *,
    project_root: Path,
    corpus_root: Path | None = None,
    output_root: Path | None = None,
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    final_corpus_root = _resolve(final_project_root, corpus_root) or (
        final_project_root / "datasets" / "_global" / "vocaloid_metadata_canonical"
    ).resolve()
    final_output_root = _resolve(final_project_root, output_root) or (
        final_project_root / "reports" / "planning" / "vocaloid_metadata_utf8_audit"
    ).resolve()
    return audit_vocaloid_metadata_utf8(
        corpus_root=final_corpus_root,
        output_root=final_output_root,
    )


def run_classify_corpus_value(
    *,
    project_root: Path,
    corpus_root: Path | None = None,
    output_root: Path | None = None,
    write_back: bool = False,
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    final_corpus_root = _resolve(final_project_root, corpus_root) or (
        final_project_root / "datasets" / "_global" / "vocaloid_metadata_canonical"
    ).resolve()
    final_output_root = _resolve(final_project_root, output_root) or (
        final_project_root / "reports" / "planning" / "corpus_value_classification"
    ).resolve()
    return classify_corpus_value(
        corpus_root=final_corpus_root,
        output_root=final_output_root,
        write_back=write_back,
    )


def run_build_track_generation_records(
    *,
    project_root: Path,
    corpus_root: Path | None = None,
    output_root: Path | None = None,
    lyric_technique_jsonl: Path | None = None,
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    final_corpus_root = _resolve(final_project_root, corpus_root) or (
        final_project_root / "datasets" / "_global" / "vocaloid_metadata_canonical"
    ).resolve()
    final_output_root = _resolve(final_project_root, output_root) or (
        final_project_root / "datasets" / "training" / "generation_profiles"
    ).resolve()
    final_lyric_technique_jsonl = _resolve(final_project_root, lyric_technique_jsonl)
    return build_track_generation_records(
        corpus_root=final_corpus_root,
        output_root=final_output_root,
        lyric_technique_jsonl=final_lyric_technique_jsonl,
    )


def run_export_suno_prompt_assets(
    *,
    project_root: Path,
    generation_root: Path | None = None,
    output_root: Path | None = None,
    include_blocked: bool = False,
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    final_generation_root = _resolve(final_project_root, generation_root) or (
        final_project_root / "datasets" / "training" / "generation_profiles"
    ).resolve()
    final_output_root = _resolve(final_project_root, output_root) or (
        final_project_root / "datasets" / "training" / "suno_prompt_assets"
    ).resolve()
    return export_suno_prompt_assets(
        generation_root=final_generation_root,
        output_root=final_output_root,
        include_blocked=include_blocked,
    )


def run_audit_generation_joinability(
    *,
    project_root: Path,
    generation_jsonl: Path | None = None,
    technique_jsonl: Path | None = None,
    output_root: Path | None = None,
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    final_generation_jsonl = _resolve(final_project_root, generation_jsonl) or (
        final_project_root / "datasets" / "training" / "generation_profiles" / "track_generation_records.jsonl"
    ).resolve()
    final_technique_jsonl = _resolve(final_project_root, technique_jsonl) or (
        final_project_root / "datasets" / "training" / "technique_probe_v3" / "lyric_technique_records.jsonl"
    ).resolve()
    final_output_root = _resolve(final_project_root, output_root) or (
        final_project_root / "reports" / "planning" / "generation_joinability_audit"
    ).resolve()
    return audit_generation_joinability(
        generation_jsonl=final_generation_jsonl,
        technique_jsonl=final_technique_jsonl,
        output_root=final_output_root,
    )


def run_audit_generation_readiness(
    *,
    project_root: Path,
    generation_root: Path | None = None,
    output_root: Path | None = None,
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    final_generation_root = _resolve(final_project_root, generation_root) or (
        final_project_root / "datasets" / "training" / "generation_profiles"
    ).resolve()
    final_output_root = _resolve(final_project_root, output_root) or (
        final_project_root / "reports" / "planning" / "generation_readiness_audit"
    ).resolve()
    return audit_generation_readiness(
        generation_root=final_generation_root,
        output_root=final_output_root,
    )


def run_build_sound_profile_review_workspace(
    *,
    project_root: Path,
    generation_root: Path | None = None,
    corpus_root: Path | None = None,
    output_root: Path | None = None,
    prompt_ready_only: bool = True,
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    final_generation_root = _resolve(final_project_root, generation_root) or (
        final_project_root / "datasets" / "training" / "generation_profiles"
    ).resolve()
    final_corpus_root = _resolve(final_project_root, corpus_root) or (
        final_project_root / "datasets" / "_global" / "vocaloid_metadata_canonical"
    ).resolve()
    final_output_root = _resolve(final_project_root, output_root) or (
        final_project_root / "datasets" / "_global" / "sound_profile_review"
    ).resolve()
    return build_sound_profile_review_workspace(
        generation_root=final_generation_root,
        corpus_root=final_corpus_root,
        output_root=final_output_root,
        prompt_ready_only=prompt_ready_only,
    )


def run_import_reviewed_sound_profiles(
    *,
    project_root: Path,
    generation_root: Path | None = None,
    workspace_root: Path | None = None,
    output_root: Path | None = None,
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    final_generation_root = _resolve(final_project_root, generation_root) or (
        final_project_root / "datasets" / "training" / "generation_profiles"
    ).resolve()
    final_workspace_root = _resolve(final_project_root, workspace_root) or (
        final_project_root / "datasets" / "_global" / "sound_profile_review"
    ).resolve()
    final_output_root = _resolve(final_project_root, output_root) or (
        final_project_root / "datasets" / "training" / "generation_profiles" / "sound_profile_reviewed"
    ).resolve()
    return import_reviewed_sound_profiles(
        generation_root=final_generation_root,
        workspace_root=final_workspace_root,
        output_root=final_output_root,
    )


def run_professional_quality_cycle(
    *,
    project_root: Path,
    generation_root: Path | None = None,
    sound_review_workspace: Path | None = None,
    reviewed_generation_root: Path | None = None,
    readiness_output_root: Path | None = None,
    prompt_asset_output_root: Path | None = None,
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    final_generation_root = _resolve(final_project_root, generation_root) or (
        final_project_root / "datasets" / "training" / "generation_profiles"
    ).resolve()
    final_sound_review_workspace = _resolve(final_project_root, sound_review_workspace) or (
        final_project_root / "datasets" / "_global" / "sound_profile_review"
    ).resolve()
    final_reviewed_generation_root = _resolve(final_project_root, reviewed_generation_root) or (
        final_project_root / "datasets" / "training" / "generation_profiles" / "sound_profile_reviewed"
    ).resolve()
    final_readiness_output_root = _resolve(final_project_root, readiness_output_root) or (
        final_project_root / "reports" / "planning" / "generation_readiness_audit" / "sound_profile_reviewed"
    ).resolve()
    final_prompt_asset_output_root = _resolve(final_project_root, prompt_asset_output_root) or (
        final_project_root / "datasets" / "training" / "suno_prompt_assets" / "sound_profile_reviewed"
    ).resolve()
    return run_professional_quality_cycle_impl(
        generation_root=final_generation_root,
        sound_review_workspace=final_sound_review_workspace,
        reviewed_generation_root=final_reviewed_generation_root,
        readiness_output_root=final_readiness_output_root,
        prompt_asset_output_root=final_prompt_asset_output_root,
    )


def run_build_lyric_technique_acquisition_queue(
    *,
    project_root: Path,
    corpus_root: Path | None = None,
    output_root: Path | None = None,
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    final_corpus_root = _resolve(final_project_root, corpus_root) or (
        final_project_root / "datasets" / "_global" / "vocaloid_metadata_canonical"
    ).resolve()
    final_output_root = _resolve(final_project_root, output_root) or (
        final_project_root / "datasets" / "training" / "lyric_technique_acquisition_queue"
    ).resolve()
    return build_lyric_technique_acquisition_queue(
        corpus_root=final_corpus_root,
        output_root=final_output_root,
    )


def run_build_vocadb_lyric_grounding_workspace(
    *,
    project_root: Path,
    queue_root: Path | None = None,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    final_queue_root = _resolve(final_project_root, queue_root) or (
        final_project_root / "datasets" / "training" / "lyric_technique_acquisition_queue"
    ).resolve()
    final_workspace_root = _resolve(final_project_root, workspace_root) or (
        final_project_root / "datasets" / "_global" / "vocadb_lyric_grounding_acquisition"
    ).resolve()
    return build_vocadb_lyric_grounding_workspace(
        queue_root=final_queue_root,
        workspace_root=final_workspace_root,
    )


def run_import_vocadb_grounded_technique_records(
    *,
    project_root: Path,
    workspace_root: Path | None = None,
    output_root: Path | None = None,
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    final_workspace_root = _resolve(final_project_root, workspace_root) or (
        final_project_root / "datasets" / "_global" / "vocadb_lyric_grounding_acquisition"
    ).resolve()
    final_output_root = _resolve(final_project_root, output_root) or (
        final_project_root / "datasets" / "training" / "vocadb_grounded_technique"
    ).resolve()
    return import_vocadb_grounded_technique_records(
        workspace_root=final_workspace_root,
        output_root=final_output_root,
    )


def run_validate_vocadb_lyric_grounding_workspace(
    *,
    project_root: Path,
    workspace_root: Path | None = None,
    output_root: Path | None = None,
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    final_workspace_root = _resolve(final_project_root, workspace_root) or (
        final_project_root / "datasets" / "_global" / "vocadb_lyric_grounding_acquisition"
    ).resolve()
    final_output_root = _resolve(final_project_root, output_root) or (
        final_project_root / "reports" / "planning" / "vocadb_lyric_grounding_validation"
    ).resolve()
    return validate_vocadb_lyric_grounding_workspace(
        workspace_root=final_workspace_root,
        output_root=final_output_root,
    )


def run_build_lyric_technique_pilot_batch(
    *,
    project_root: Path,
    queue_root: Path | None = None,
    output_root: Path | None = None,
    batch_size: int = 10,
    exclude_track_ids: list[str] | None = None,
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    final_queue_root = _resolve(final_project_root, queue_root) or (
        final_project_root / "datasets" / "training" / "lyric_technique_acquisition_queue"
    ).resolve()
    final_output_root = _resolve(final_project_root, output_root) or (
        final_project_root / "reports" / "planning" / "lyric_technique_pilot_batch"
    ).resolve()
    return build_lyric_technique_pilot_batch(
        queue_root=final_queue_root,
        output_root=final_output_root,
        batch_size=batch_size,
        exclude_track_ids=exclude_track_ids,
    )


def run_materialize_lyric_technique_pilot_workspace(
    *,
    project_root: Path,
    source_workspace_root: Path | None = None,
    pilot_manifest_path: Path | None = None,
    output_root: Path | None = None,
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    final_source_workspace_root = _resolve(final_project_root, source_workspace_root) or (
        final_project_root / "datasets" / "_global" / "vocadb_lyric_grounding_acquisition"
    ).resolve()
    final_pilot_manifest_path = _resolve(final_project_root, pilot_manifest_path) or (
        final_project_root / "reports" / "planning" / "lyric_technique_pilot_batch" / "lyric_technique_pilot_batch.json"
    ).resolve()
    final_output_root = _resolve(final_project_root, output_root) or (
        final_project_root / "datasets" / "_global" / "vocadb_lyric_grounding_acquisition_pilots"
    ).resolve()
    return materialize_lyric_technique_pilot_workspace(
        source_workspace_root=final_source_workspace_root,
        pilot_manifest_path=final_pilot_manifest_path,
        output_root=final_output_root,
    )


def run_lyric_technique_pilot_cycle(
    *,
    project_root: Path,
    corpus_root: Path | None = None,
    workspace_root: Path | None = None,
    generation_output_root: Path | None = None,
    validation_output_root: Path | None = None,
    import_output_root: Path | None = None,
    joinability_output_root: Path | None = None,
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    final_corpus_root = _resolve(final_project_root, corpus_root) or (
        final_project_root / "datasets" / "_global" / "vocaloid_metadata_canonical" / "tier1_map_seed"
    ).resolve()
    final_workspace_root = _resolve(final_project_root, workspace_root) or (
        final_project_root / "datasets" / "_global" / "vocadb_lyric_grounding_acquisition_pilots" / "tier1_map_seed_pilot10_v2"
    ).resolve()
    workspace_name = final_workspace_root.name
    final_generation_output_root = _resolve(final_project_root, generation_output_root) or (
        final_project_root / "datasets" / "training" / "generation_profiles" / workspace_name
    ).resolve()
    final_validation_output_root = _resolve(final_project_root, validation_output_root) or (
        final_project_root / "reports" / "planning" / "vocadb_lyric_grounding_validation" / workspace_name
    ).resolve()
    final_import_output_root = _resolve(final_project_root, import_output_root) or (
        final_project_root / "datasets" / "training" / "vocadb_grounded_technique" / workspace_name
    ).resolve()
    final_joinability_output_root = _resolve(final_project_root, joinability_output_root) or (
        final_project_root / "reports" / "planning" / "generation_joinability_audit" / workspace_name
    ).resolve()

    generation_manifest = run_build_track_generation_records(
        project_root=final_project_root,
        corpus_root=final_corpus_root,
        output_root=final_generation_output_root,
        lyric_technique_jsonl=None,
    )
    validation_manifest = run_validate_vocadb_lyric_grounding_workspace(
        project_root=final_project_root,
        workspace_root=final_workspace_root,
        output_root=final_validation_output_root,
    )
    import_manifest = run_import_vocadb_grounded_technique_records(
        project_root=final_project_root,
        workspace_root=final_workspace_root,
        output_root=final_import_output_root,
    )
    joinability_manifest = run_audit_generation_joinability(
        project_root=final_project_root,
        generation_jsonl=final_generation_output_root / "track_generation_records.jsonl",
        technique_jsonl=final_import_output_root / "lyric_technique_records.jsonl",
        output_root=final_joinability_output_root,
    )
    return {
        "schema_version": "1.0",
        "record_type": "lyric_technique_pilot_cycle_manifest",
        "workspace_root": str(final_workspace_root),
        "corpus_root": str(final_corpus_root),
        "generation_manifest": generation_manifest,
        "validation_manifest": validation_manifest,
        "import_manifest": import_manifest,
        "joinability_manifest": joinability_manifest,
    }


def run_report_vocadb_lyric_grounding_status(
    *,
    project_root: Path,
    workspaces_root: Path | None = None,
    output_root: Path | None = None,
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    final_workspaces_root = _resolve(final_project_root, workspaces_root) or (
        final_project_root / "datasets" / "_global" / "vocadb_lyric_grounding_acquisition_pilots"
    ).resolve()
    final_output_root = _resolve(final_project_root, output_root) or (
        final_project_root / "reports" / "planning" / "vocadb_lyric_grounding_status"
    ).resolve()
    return report_vocadb_lyric_grounding_status(
        workspaces_root=final_workspaces_root,
        output_root=final_output_root,
    )


def run_auto_ground_vocadb_workspace_from_url_map(
    *,
    project_root: Path,
    workspace_root: Path | None = None,
    url_map_path: Path | None = None,
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    final_workspace_root = _resolve(final_project_root, workspace_root) or (
        final_project_root / "datasets" / "_global" / "vocadb_lyric_grounding_acquisition_pilots" / "tier1_map_seed_pilot20_v1"
    ).resolve()
    final_url_map_path = _resolve(final_project_root, url_map_path)
    if final_url_map_path is None:
        raise ValueError("url_map_path is required")
    url_map_payload = load_json(final_url_map_path)
    return auto_ground_vocadb_workspace_from_url_map(
        workspace_root=final_workspace_root,
        url_map=url_map_payload,
    )


def run_tier1_continuous_cycle(
    *,
    project_root: Path,
    corpus_root: Path | None = None,
    pilot20_workspace: Path | None = None,
    pilot20_generation_root: Path | None = None,
    pilot20_merged_generation_root: Path | None = None,
    pilot20_validation_root: Path | None = None,
    pilot20_import_root: Path | None = None,
    pilot20_joinability_root: Path | None = None,
    pilot20_readiness_root: Path | None = None,
    pilot20_url_map_path: Path | None = None,
    pilot10_generation_root: Path | None = None,
    sound_review_workspace: Path | None = None,
    sound_reviewed_generation_root: Path | None = None,
    sound_readiness_root: Path | None = None,
    sound_prompt_asset_root: Path | None = None,
    grounding_status_root: Path | None = None,
    tier1_queue_root: Path | None = None,
    tier1_source_workspace_root: Path | None = None,
    tier1_rollover_planning_root: Path | None = None,
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    return run_tier1_continuous_cycle_impl(
        corpus_root=_resolve(final_project_root, corpus_root) or (final_project_root / "datasets" / "_global" / "vocaloid_metadata_canonical" / "tier1_map_seed").resolve(),
        pilot20_workspace=_resolve(final_project_root, pilot20_workspace) or (final_project_root / "datasets" / "_global" / "vocadb_lyric_grounding_acquisition_pilots" / "tier1_map_seed_pilot20_v1").resolve(),
        pilot20_generation_root=_resolve(final_project_root, pilot20_generation_root) or (final_project_root / "datasets" / "training" / "generation_profiles" / "tier1_map_seed_pilot20_v1").resolve(),
        pilot20_merged_generation_root=_resolve(final_project_root, pilot20_merged_generation_root) or (final_project_root / "datasets" / "training" / "generation_profiles" / "tier1_map_seed_pilot20_merged_v1").resolve(),
        pilot20_validation_root=_resolve(final_project_root, pilot20_validation_root) or (final_project_root / "reports" / "planning" / "vocadb_lyric_grounding_validation" / "tier1_map_seed_pilot20_v1").resolve(),
        pilot20_import_root=_resolve(final_project_root, pilot20_import_root) or (final_project_root / "datasets" / "training" / "vocadb_grounded_technique" / "tier1_map_seed_pilot20_v1").resolve(),
        pilot20_joinability_root=_resolve(final_project_root, pilot20_joinability_root) or (final_project_root / "reports" / "planning" / "generation_joinability_audit" / "tier1_map_seed_pilot20_v1").resolve(),
        pilot20_readiness_root=_resolve(final_project_root, pilot20_readiness_root) or (final_project_root / "reports" / "planning" / "generation_readiness_audit" / "tier1_map_seed_pilot20_merged_v1").resolve(),
        pilot20_url_map_path=_resolve(final_project_root, pilot20_url_map_path) or (final_project_root / "datasets" / "_global" / "vocadb_lyric_grounding_acquisition_pilots" / "tier1_map_seed_pilot20_v1" / "trusted_lyric_url_map.json").resolve(),
        pilot10_generation_root=_resolve(final_project_root, pilot10_generation_root) or (final_project_root / "datasets" / "training" / "generation_profiles" / "tier1_map_seed_pilot10_merged_v10").resolve(),
        sound_review_workspace=_resolve(final_project_root, sound_review_workspace) or (final_project_root / "datasets" / "_global" / "sound_profile_review" / "tier1_map_seed_pilot10_v1").resolve(),
        sound_reviewed_generation_root=_resolve(final_project_root, sound_reviewed_generation_root) or (final_project_root / "datasets" / "training" / "generation_profiles" / "tier1_map_seed_pilot10_sound_reviewed_v2").resolve(),
        sound_readiness_root=_resolve(final_project_root, sound_readiness_root) or (final_project_root / "reports" / "planning" / "generation_readiness_audit" / "tier1_map_seed_pilot10_sound_reviewed_v2").resolve(),
        sound_prompt_asset_root=_resolve(final_project_root, sound_prompt_asset_root) or (final_project_root / "datasets" / "training" / "suno_prompt_assets" / "tier1_map_seed_pilot10_sound_reviewed_v2").resolve(),
        grounding_status_root=_resolve(final_project_root, grounding_status_root) or (final_project_root / "reports" / "planning" / "vocadb_lyric_grounding_status").resolve(),
        tier1_queue_root=_resolve(final_project_root, tier1_queue_root) or (final_project_root / "datasets" / "training" / "lyric_technique_acquisition_queue" / "tier1_map_seed_v1").resolve(),
        tier1_source_workspace_root=_resolve(final_project_root, tier1_source_workspace_root) or (final_project_root / "datasets" / "_global" / "vocadb_lyric_grounding_acquisition" / "tier1_map_seed_v1").resolve(),
        tier1_rollover_planning_root=_resolve(final_project_root, tier1_rollover_planning_root) or (final_project_root / "reports" / "planning" / "lyric_technique_pilot_batch" / "tier1_rollover").resolve(),
    )


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
    final_project_root = project_root.resolve()
    return run_program_continuous_cycle_impl(
        project_root=final_project_root,
        batch_tag=batch_tag,
        bulk_page_count=bulk_page_count,
        bulk_page_size=bulk_page_size,
        bulk_start_offset=bulk_start_offset,
        bulk_sort=bulk_sort,
        run_tier1_cycle=run_tier1_cycle,
    )


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
    final_project_root = project_root.resolve()
    return run_program_continuous_sweep_impl(
        project_root=final_project_root,
        batch_tag_prefix=batch_tag_prefix,
        batch_count=batch_count,
        bulk_page_count=bulk_page_count,
        bulk_page_size=bulk_page_size,
        bulk_start_offset=bulk_start_offset,
        bulk_offset_step=bulk_offset_step,
        bulk_sort=bulk_sort,
        run_tier1_once=run_tier1_once,
    )
