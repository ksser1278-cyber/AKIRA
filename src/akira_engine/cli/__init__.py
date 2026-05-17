from __future__ import annotations

from pathlib import Path
from typing import Any


def run_build_derived_datasets(*, project_root: Path, audit_json: Path | None = None, minimum_recommendation: str = "needs_review", output_dir: Path | None = None) -> dict[str, Any]:
    from .dataset_commands import run_build_derived_datasets as _impl

    return _impl(
        project_root=project_root,
        audit_json=audit_json,
        minimum_recommendation=minimum_recommendation,
        output_dir=output_dir,
    )


def run_extract_lyric_technique_records(
    *,
    project_root: Path,
    output_dir: Path | None = None,
    artists: list[str] | None = None,
    default_rights_status: str = "unknown",
    source_kind: str = "normalized_corpus",
) -> dict[str, Any]:
    from .dataset_commands import run_extract_lyric_technique_records as _impl

    return _impl(
        project_root=project_root,
        output_dir=output_dir,
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
    from .dataset_commands import run_build_lyric_behavior_dataset as _impl

    return _impl(
        project_root=project_root,
        artists=artists,
        output_root=output_root,
    )


def run_build_form_family_catalog(
    *,
    project_root: Path,
    artists: list[str] | None = None,
    behavior_root: Path | None = None,
    output_root: Path | None = None,
    catalog_name: str = "calibration_v1",
) -> dict[str, Any]:
    from .dataset_commands import run_build_form_family_catalog as _impl

    return _impl(
        project_root=project_root,
        artists=artists,
        behavior_root=behavior_root,
        output_root=output_root,
        catalog_name=catalog_name,
    )


def run_bootstrap_training_rights(*, project_root: Path, derived_jsonl: Path | None = None, existing_map: Path | None = None, output_path: Path | None = None) -> dict[str, Any]:
    from .dataset_commands import run_bootstrap_training_rights as _impl

    return _impl(
        project_root=project_root,
        derived_jsonl=derived_jsonl,
        existing_map=existing_map,
        output_path=output_path,
    )


def run_export_supervised_samples(*, project_root: Path, derived_jsonl: Path | None = None, output_dir: Path | None = None, rights_map: Path | None = None, include_eval_only: bool = False, include_full_song: bool = False) -> dict[str, Any]:
    from .dataset_commands import run_export_supervised_samples as _impl

    return _impl(
        project_root=project_root,
        derived_jsonl=derived_jsonl,
        output_dir=output_dir,
        rights_map=rights_map,
        include_eval_only=include_eval_only,
        include_full_song=include_full_song,
    )


def run_import_training_sources(*, project_root: Path, pilot_root: Path | None = None, rights_map: Path | None = None, output_dir: Path | None = None) -> dict[str, Any]:
    from .dataset_commands import run_import_training_sources as _impl

    return _impl(
        project_root=project_root,
        pilot_root=pilot_root,
        rights_map=rights_map,
        output_dir=output_dir,
    )


def run_build_training_pilot(*, project_root: Path, source_jsonl: Path | None = None, output_dir: Path | None = None, pilot_name: str = "owned_original_hook_v1") -> dict[str, Any]:
    from .dataset_commands import run_build_training_pilot as _impl

    return _impl(
        project_root=project_root,
        source_jsonl=source_jsonl,
        output_dir=output_dir,
        pilot_name=pilot_name,
    )


def run_export_vertex_supervised(*, project_root: Path, train_jsonl: Path | None = None, eval_jsonl: Path | None = None, output_dir: Path | None = None, base_model: str = "gemini-2.5-flash") -> dict[str, Any]:
    from .dataset_commands import run_export_vertex_supervised as _impl

    return _impl(
        project_root=project_root,
        train_jsonl=train_jsonl,
        eval_jsonl=eval_jsonl,
        output_dir=output_dir,
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
    from .dataset_commands import run_seed_vocadb_metadata as _impl

    return _impl(
        project_root=project_root,
        queries=queries,
        artist_ids=artist_ids,
        artist_names=artist_names,
        artist_list_path=artist_list_path,
        artist_map_path=artist_map_path,
        output_dir=output_dir,
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
    from .dataset_commands import run_seed_vocadb_bulk_metadata as _impl

    return _impl(
        project_root=project_root,
        output_dir=output_dir,
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
    from .dataset_commands import run_discover_vocadb_producers as _impl

    return _impl(
        project_root=project_root,
        intake_root=intake_root,
        output_root=output_root,
        page_count=page_count,
        page_size=page_size,
        sample_song_entries=sample_song_entries,
        min_synthetic_songs=min_synthetic_songs,
        max_candidates=max_candidates,
    )


def run_review_vocaloid_metadata(*, project_root: Path, intake_dir: Path | None = None, output_dir: Path | None = None) -> dict[str, Any]:
    from .dataset_commands import run_review_vocaloid_metadata as _impl

    return _impl(
        project_root=project_root,
        intake_dir=intake_dir,
        output_dir=output_dir,
    )


def run_enrich_vocaloid_metadata(*, project_root: Path, intake_dir: Path | None = None) -> dict[str, Any]:
    from .dataset_commands import run_enrich_vocaloid_metadata as _impl

    return _impl(
        project_root=project_root,
        intake_dir=intake_dir,
    )


def run_build_vocaloid_metadata_review_queue(
    *,
    project_root: Path,
    review_manifest: Path | None = None,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    from .dataset_commands import run_build_vocaloid_metadata_review_queue as _impl

    return _impl(
        project_root=project_root,
        review_manifest=review_manifest,
        output_dir=output_dir,
    )


def run_auto_triage_vocaloid_metadata_queue(
    *,
    project_root: Path,
    queue_root: Path | None = None,
) -> dict[str, Any]:
    from .dataset_commands import run_auto_triage_vocaloid_metadata_queue as _impl

    return _impl(
        project_root=project_root,
        queue_root=queue_root,
    )


def run_auto_accept_vocaloid_metadata_queue(
    *,
    project_root: Path,
    queue_root: Path | None = None,
) -> dict[str, Any]:
    from .dataset_commands import run_auto_accept_vocaloid_metadata_queue as _impl

    return _impl(
        project_root=project_root,
        queue_root=queue_root,
    )


def run_build_vocaloid_metadata_canonical_corpus(
    *,
    project_root: Path,
    queue_root: Path | None = None,
    output_root: Path | None = None,
) -> dict[str, Any]:
    from .dataset_commands import run_build_vocaloid_metadata_canonical_corpus as _impl

    return _impl(
        project_root=project_root,
        queue_root=queue_root,
        output_root=output_root,
    )


def run_report_vocaloid_metadata_coverage(
    *,
    project_root: Path,
    corpus_root: Path | None = None,
    output_root: Path | None = None,
) -> dict[str, Any]:
    from .dataset_commands import run_report_vocaloid_metadata_coverage as _impl

    return _impl(
        project_root=project_root,
        corpus_root=corpus_root,
        output_root=output_root,
    )


def run_audit_vocaloid_metadata_utf8(
    *,
    project_root: Path,
    corpus_root: Path | None = None,
    output_root: Path | None = None,
) -> dict[str, Any]:
    from .dataset_commands import run_audit_vocaloid_metadata_utf8 as _impl

    return _impl(
        project_root=project_root,
        corpus_root=corpus_root,
        output_root=output_root,
    )


def run_classify_corpus_value(
    *,
    project_root: Path,
    corpus_root: Path | None = None,
    output_root: Path | None = None,
    write_back: bool = False,
) -> dict[str, Any]:
    from .dataset_commands import run_classify_corpus_value as _impl

    return _impl(
        project_root=project_root,
        corpus_root=corpus_root,
        output_root=output_root,
        write_back=write_back,
    )


def run_build_track_generation_records(
    *,
    project_root: Path,
    corpus_root: Path | None = None,
    output_root: Path | None = None,
    lyric_technique_jsonl: Path | None = None,
) -> dict[str, Any]:
    from .dataset_commands import run_build_track_generation_records as _impl

    return _impl(
        project_root=project_root,
        corpus_root=corpus_root,
        output_root=output_root,
        lyric_technique_jsonl=lyric_technique_jsonl,
    )


def run_export_suno_prompt_assets(
    *,
    project_root: Path,
    generation_root: Path | None = None,
    output_root: Path | None = None,
    include_blocked: bool = False,
) -> dict[str, Any]:
    from .dataset_commands import run_export_suno_prompt_assets as _impl

    return _impl(
        project_root=project_root,
        generation_root=generation_root,
        output_root=output_root,
        include_blocked=include_blocked,
    )


def run_audit_generation_joinability(
    *,
    project_root: Path,
    generation_jsonl: Path | None = None,
    technique_jsonl: Path | None = None,
    output_root: Path | None = None,
) -> dict[str, Any]:
    from .dataset_commands import run_audit_generation_joinability as _impl

    return _impl(
        project_root=project_root,
        generation_jsonl=generation_jsonl,
        technique_jsonl=technique_jsonl,
        output_root=output_root,
    )


def run_audit_generation_readiness(
    *,
    project_root: Path,
    generation_root: Path | None = None,
    output_root: Path | None = None,
) -> dict[str, Any]:
    from .dataset_commands import run_audit_generation_readiness as _impl

    return _impl(
        project_root=project_root,
        generation_root=generation_root,
        output_root=output_root,
    )


def run_build_sound_profile_review_workspace(
    *,
    project_root: Path,
    generation_root: Path | None = None,
    corpus_root: Path | None = None,
    output_root: Path | None = None,
    prompt_ready_only: bool = True,
) -> dict[str, Any]:
    from .dataset_commands import run_build_sound_profile_review_workspace as _impl

    return _impl(
        project_root=project_root,
        generation_root=generation_root,
        corpus_root=corpus_root,
        output_root=output_root,
        prompt_ready_only=prompt_ready_only,
    )


def run_import_reviewed_sound_profiles(
    *,
    project_root: Path,
    generation_root: Path | None = None,
    workspace_root: Path | None = None,
    output_root: Path | None = None,
) -> dict[str, Any]:
    from .dataset_commands import run_import_reviewed_sound_profiles as _impl

    return _impl(
        project_root=project_root,
        generation_root=generation_root,
        workspace_root=workspace_root,
        output_root=output_root,
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
    from .dataset_commands import run_professional_quality_cycle as _impl

    return _impl(
        project_root=project_root,
        generation_root=generation_root,
        sound_review_workspace=sound_review_workspace,
        reviewed_generation_root=reviewed_generation_root,
        readiness_output_root=readiness_output_root,
        prompt_asset_output_root=prompt_asset_output_root,
    )


def run_build_lyric_technique_acquisition_queue(
    *,
    project_root: Path,
    corpus_root: Path | None = None,
    output_root: Path | None = None,
) -> dict[str, Any]:
    from .dataset_commands import run_build_lyric_technique_acquisition_queue as _impl

    return _impl(
        project_root=project_root,
        corpus_root=corpus_root,
        output_root=output_root,
    )


def run_build_vocadb_lyric_grounding_workspace(
    *,
    project_root: Path,
    queue_root: Path | None = None,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    from .dataset_commands import run_build_vocadb_lyric_grounding_workspace as _impl

    return _impl(
        project_root=project_root,
        queue_root=queue_root,
        workspace_root=workspace_root,
    )


def run_import_vocadb_grounded_technique_records(
    *,
    project_root: Path,
    workspace_root: Path | None = None,
    output_root: Path | None = None,
) -> dict[str, Any]:
    from .dataset_commands import run_import_vocadb_grounded_technique_records as _impl

    return _impl(
        project_root=project_root,
        workspace_root=workspace_root,
        output_root=output_root,
    )


def run_validate_vocadb_lyric_grounding_workspace(
    *,
    project_root: Path,
    workspace_root: Path | None = None,
    output_root: Path | None = None,
) -> dict[str, Any]:
    from .dataset_commands import run_validate_vocadb_lyric_grounding_workspace as _impl

    return _impl(
        project_root=project_root,
        workspace_root=workspace_root,
        output_root=output_root,
    )


def run_build_lyric_technique_pilot_batch(
    *,
    project_root: Path,
    queue_root: Path | None = None,
    output_root: Path | None = None,
    batch_size: int = 10,
    exclude_track_ids: list[str] | None = None,
) -> dict[str, Any]:
    from .dataset_commands import run_build_lyric_technique_pilot_batch as _impl

    return _impl(
        project_root=project_root,
        queue_root=queue_root,
        output_root=output_root,
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
    from .dataset_commands import run_materialize_lyric_technique_pilot_workspace as _impl

    return _impl(
        project_root=project_root,
        source_workspace_root=source_workspace_root,
        pilot_manifest_path=pilot_manifest_path,
        output_root=output_root,
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
    from .dataset_commands import run_lyric_technique_pilot_cycle as _impl

    return _impl(
        project_root=project_root,
        corpus_root=corpus_root,
        workspace_root=workspace_root,
        generation_output_root=generation_output_root,
        validation_output_root=validation_output_root,
        import_output_root=import_output_root,
        joinability_output_root=joinability_output_root,
    )


def run_report_vocadb_lyric_grounding_status(
    *,
    project_root: Path,
    workspaces_root: Path | None = None,
    output_root: Path | None = None,
) -> dict[str, Any]:
    from .dataset_commands import run_report_vocadb_lyric_grounding_status as _impl

    return _impl(
        project_root=project_root,
        workspaces_root=workspaces_root,
        output_root=output_root,
    )


def run_auto_ground_vocadb_workspace_from_url_map(
    *,
    project_root: Path,
    workspace_root: Path | None = None,
    url_map_path: Path | None = None,
) -> dict[str, Any]:
    from .dataset_commands import run_auto_ground_vocadb_workspace_from_url_map as _impl

    return _impl(
        project_root=project_root,
        workspace_root=workspace_root,
        url_map_path=url_map_path,
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
    from .dataset_commands import run_tier1_continuous_cycle as _impl

    return _impl(
        project_root=project_root,
        corpus_root=corpus_root,
        pilot20_workspace=pilot20_workspace,
        pilot20_generation_root=pilot20_generation_root,
        pilot20_merged_generation_root=pilot20_merged_generation_root,
        pilot20_validation_root=pilot20_validation_root,
        pilot20_import_root=pilot20_import_root,
        pilot20_joinability_root=pilot20_joinability_root,
        pilot20_readiness_root=pilot20_readiness_root,
        pilot20_url_map_path=pilot20_url_map_path,
        pilot10_generation_root=pilot10_generation_root,
        sound_review_workspace=sound_review_workspace,
        sound_reviewed_generation_root=sound_reviewed_generation_root,
        sound_readiness_root=sound_readiness_root,
        sound_prompt_asset_root=sound_prompt_asset_root,
        grounding_status_root=grounding_status_root,
        tier1_queue_root=tier1_queue_root,
        tier1_source_workspace_root=tier1_source_workspace_root,
        tier1_rollover_planning_root=tier1_rollover_planning_root,
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
    from .dataset_commands import run_program_continuous_cycle as _impl

    return _impl(
        project_root=project_root,
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
    from .dataset_commands import run_program_continuous_sweep as _impl

    return _impl(
        project_root=project_root,
        batch_tag_prefix=batch_tag_prefix,
        batch_count=batch_count,
        bulk_page_count=bulk_page_count,
        bulk_page_size=bulk_page_size,
        bulk_start_offset=bulk_start_offset,
        bulk_offset_step=bulk_offset_step,
        bulk_sort=bulk_sort,
        run_tier1_once=run_tier1_once,
    )


def run_report_baseline(*, project_root: Path, output_root: Path | None = None) -> dict[str, Any]:
    from .report_commands import run_report_baseline as _impl

    return _impl(
        project_root=project_root,
        output_root=output_root,
    )


def run_report_engine_health(*, project_root: Path, artists: list[str], output_dir: Path | None = None) -> dict[str, Any]:
    from .report_commands import run_report_engine_health as _impl

    return _impl(
        project_root=project_root,
        artists=artists,
        output_dir=output_dir,
    )


def run_report_engine_state(*, project_root: Path, output_root: Path | None = None) -> dict[str, Any]:
    from .report_commands import run_report_engine_state as _impl

    return _impl(
        project_root=project_root,
        output_root=output_root,
    )


def run_report_sync_authoritative_wiki(*, project_root: Path, output_root: Path | None = None) -> dict[str, Any]:
    from .report_commands import run_report_sync_authoritative_wiki as _impl

    return _impl(
        project_root=project_root,
        output_root=output_root,
    )


def run_report_sync_engine_surface(*, project_root: Path, output_root: Path | None = None) -> dict[str, Any]:
    from .report_commands import run_report_sync_engine_surface as _impl

    return _impl(
        project_root=project_root,
        output_root=output_root,
    )


def run_validate_active_workflow(
    *,
    project_root: Path,
    config_path: Path | None = None,
    output_root: Path | None = None,
    write: bool = True,
) -> dict[str, Any]:
    from ..active_workflow import validate_active_workflow as _impl

    return _impl(
        project_root=project_root,
        config_path=config_path,
        output_root=output_root,
        write=write,
    )


def run_song_analysis_pipeline(*, input_dir: Path, output_dir: Path | None = None) -> dict[str, Any]:
    from ..song_analysis import run_song_analysis_pipeline as _impl

    return _impl(input_dir=input_dir, output_dir=output_dir)


def run_write_song_analysis_template(*, output_dir: Path, song_id: str = "sample_song") -> dict[str, Any]:
    from ..song_analysis import write_song_analysis_template as _impl

    return _impl(output_dir=output_dir, song_id=song_id)


def run_match_song_analysis_lyrics(
    *,
    metadata_dir: Path,
    lyrics_root: Path,
    output_root: Path,
    limit: int | None = None,
) -> dict[str, Any]:
    from ..song_analysis import match_song_analysis_lyrics as _impl

    return _impl(
        metadata_dir=metadata_dir,
        lyrics_root=lyrics_root,
        output_root=output_root,
        limit=limit,
    )


def run_materialize_song_analysis_inputs_from_metadata(
    *,
    metadata_dir: Path,
    output_root: Path,
    lyrics_root: Path | None = None,
    limit: int | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    from ..song_analysis import materialize_song_analysis_inputs_from_metadata as _impl

    return _impl(
        metadata_dir=metadata_dir,
        output_root=output_root,
        lyrics_root=lyrics_root,
        limit=limit,
        overwrite=overwrite,
    )


def run_scrape_vocadb_song_analysis_inputs(
    *,
    project_root: Path,
    output_root: Path,
    metadata_output_dir: Path,
    page_count: int = 1,
    page_size: int = 50,
    start_offset: int = 0,
    sort: str = "PublishDate",
    materialize_limit: int | None = None,
    lyrics_root: Path | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    from ..song_analysis import scrape_vocadb_song_analysis_inputs as _impl

    return _impl(
        project_root=project_root,
        output_root=output_root,
        metadata_output_dir=metadata_output_dir,
        page_count=page_count,
        page_size=page_size,
        start_offset=start_offset,
        sort=sort,
        materialize_limit=materialize_limit,
        lyrics_root=lyrics_root,
        overwrite=overwrite,
    )


def run_songwriter_demo(*, project_root: Path, artist_id: str, mode_id: str | None = None, intent: str = "", title_seed: str = "", output_dir: Path | None = None, candidate_count: int = 4, generation_mode: str = "auto", model_provider: str = "gpt", model_name: str | None = None) -> dict[str, Any]:
    from .songwriter_commands import run_songwriter_demo as _impl

    return _impl(
        project_root=project_root,
        artist_id=artist_id,
        mode_id=mode_id,
        intent=intent,
        title_seed=title_seed,
        output_dir=output_dir,
        candidate_count=candidate_count,
        generation_mode=generation_mode,
        model_provider=model_provider,
        model_name=model_name,
    )


def run_songwriter_ab_test(
    *,
    project_root: Path,
    intent: str,
    style: str,
    title_seed: str = "",
    language: str = "ja",
    analysis_dir: Path | None = None,
    output_dir: Path | None = None,
    model_name: str | None = None,
    execute_api: bool = False,
    direct_output_path: Path | None = None,
    assisted_output_path: Path | None = None,
    allow_ungrounded_assisted: bool = False,
) -> dict[str, Any]:
    from .songwriter_commands import run_songwriter_ab_test as _impl

    return _impl(
        project_root=project_root,
        intent=intent,
        style=style,
        title_seed=title_seed,
        language=language,
        analysis_dir=analysis_dir,
        output_dir=output_dir,
        model_name=model_name,
        execute_api=execute_api,
        direct_output_path=direct_output_path,
        assisted_output_path=assisted_output_path,
        allow_ungrounded_assisted=allow_ungrounded_assisted,
    )


__all__ = [
    "run_build_derived_datasets",
    "run_extract_lyric_technique_records",
    "run_build_lyric_behavior_dataset",
    "run_bootstrap_training_rights",
    "run_export_supervised_samples",
    "run_import_training_sources",
    "run_build_training_pilot",
    "run_export_vertex_supervised",
    "run_seed_vocadb_metadata",
    "run_seed_vocadb_bulk_metadata",
    "run_discover_vocadb_producers",
    "run_enrich_vocaloid_metadata",
    "run_review_vocaloid_metadata",
    "run_build_vocaloid_metadata_review_queue",
    "run_auto_triage_vocaloid_metadata_queue",
    "run_auto_accept_vocaloid_metadata_queue",
    "run_build_vocaloid_metadata_canonical_corpus",
    "run_report_vocaloid_metadata_coverage",
    "run_audit_vocaloid_metadata_utf8",
    "run_classify_corpus_value",
    "run_build_track_generation_records",
    "run_export_suno_prompt_assets",
    "run_audit_generation_joinability",
    "run_audit_generation_readiness",
    "run_build_sound_profile_review_workspace",
    "run_import_reviewed_sound_profiles",
    "run_professional_quality_cycle",
    "run_build_lyric_technique_acquisition_queue",
    "run_build_vocadb_lyric_grounding_workspace",
    "run_import_vocadb_grounded_technique_records",
    "run_validate_vocadb_lyric_grounding_workspace",
    "run_build_lyric_technique_pilot_batch",
    "run_materialize_lyric_technique_pilot_workspace",
    "run_lyric_technique_pilot_cycle",
    "run_report_vocadb_lyric_grounding_status",
    "run_auto_ground_vocadb_workspace_from_url_map",
    "run_tier1_continuous_cycle",
    "run_program_continuous_cycle",
    "run_program_continuous_sweep",
    "run_report_baseline",
    "run_report_engine_health",
    "run_report_engine_state",
    "run_report_sync_authoritative_wiki",
    "run_report_sync_engine_surface",
    "run_validate_active_workflow",
    "run_song_analysis_pipeline",
    "run_write_song_analysis_template",
    "run_match_song_analysis_lyrics",
    "run_materialize_song_analysis_inputs_from_metadata",
    "run_scrape_vocadb_song_analysis_inputs",
    "run_songwriter_demo",
    "run_songwriter_ab_test",
]
