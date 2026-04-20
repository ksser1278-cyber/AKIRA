from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import (
    run_bootstrap_training_rights,
    run_build_derived_datasets,
    run_extract_lyric_technique_records,
    run_build_lyric_behavior_dataset,
    run_build_form_family_catalog,
    run_build_training_pilot,
    run_export_supervised_samples,
    run_export_vertex_supervised,
    run_build_vocaloid_metadata_review_queue,
    run_discover_vocadb_producers,
    run_auto_triage_vocaloid_metadata_queue,
    run_auto_accept_vocaloid_metadata_queue,
    run_build_vocaloid_metadata_canonical_corpus,
    run_report_vocaloid_metadata_coverage,
    run_audit_vocaloid_metadata_utf8,
    run_classify_corpus_value,
    run_build_track_generation_records,
    run_export_suno_prompt_assets,
    run_audit_generation_joinability,
    run_audit_generation_readiness,
    run_build_sound_profile_review_workspace,
    run_import_reviewed_sound_profiles,
    run_professional_quality_cycle,
    run_build_lyric_technique_acquisition_queue,
    run_build_vocadb_lyric_grounding_workspace,
    run_import_vocadb_grounded_technique_records,
    run_validate_vocadb_lyric_grounding_workspace,
    run_build_lyric_technique_pilot_batch,
    run_materialize_lyric_technique_pilot_workspace,
    run_lyric_technique_pilot_cycle,
    run_report_vocadb_lyric_grounding_status,
    run_auto_ground_vocadb_workspace_from_url_map,
    run_tier1_continuous_cycle,
    run_program_continuous_cycle,
    run_program_continuous_sweep,
    run_import_training_sources,
    run_review_vocaloid_metadata,
    run_seed_vocadb_metadata,
    run_seed_vocadb_bulk_metadata,
    run_enrich_vocaloid_metadata,
    run_report_baseline,
    run_report_engine_health,
    run_report_engine_state,
    run_report_sync_authoritative_wiki,
    run_report_sync_engine_surface,
    run_songwriter_demo,
)


def _run_pytest(root: Path, passthrough: list[str]) -> int:
    import subprocess

    command = [sys.executable, "-m", "pytest", *passthrough]
    return subprocess.call(command, cwd=str(root))


def cmd_status(root: Path, _: argparse.Namespace) -> int:
    print(f"AKIRA root: {root}")
    print("Active skeleton:")
    for name in ["src", "scripts", "schemas", "docs", "tests", "config"]:
        path = root / name
        print(f"- {name}: {'present' if path.exists() else 'missing'}")
    quarantine = root / "_quarantine"
    print(f"- _quarantine: {'present' if quarantine.exists() else 'missing'}")
    print("")
    print("Primary entrypoints:")
    print("- akira.py songwriter demo")
    print("- akira.py dataset build-derived")
    print("- akira.py dataset bootstrap-rights")
    print("- akira.py dataset export-supervised")
    print("- akira.py dataset import-training-sources")
    print("- akira.py report engine-health")
    print("- akira.py report engine-state")
    print("- akira.py report sync-authoritative-wiki")
    print("- akira.py report sync-engine-surface")
    print("- akira.py report baseline")
    print("- akira.py test")
    return 0


def cmd_songwriter_demo(root: Path, args: argparse.Namespace) -> int:
    manifest = run_songwriter_demo(
        project_root=args.project_root or root,
        artist_id=args.artist_id,
        mode_id=args.mode_id,
        intent=args.intent or "",
        title_seed=args.title_seed or "",
        output_dir=args.output_dir,
        candidate_count=args.candidate_count if args.candidate_count is not None else 4,
        generation_mode=args.generation_mode or "auto",
        model_provider=args.model_provider or "gpt",
        model_name=args.model_name,
    )
    print(f"Demo run manifest: {manifest['manifest_path']}")
    print(f"Selected lyric: {manifest['selected_lyric_path']}")
    print(f"Winning candidate: {manifest['selected_candidate_id']}")
    print(f"Winning score: {manifest['selected_score']}")
    print(f"Requested generation mode: {manifest.get('requested_generation_mode', 'auto')}")
    print(f"Resolved generation mode: {manifest.get('generation_mode', 'template')}")
    print(f"Source root: {manifest.get('source_root', args.project_root or root)}")
    return 0


def cmd_dataset_build_derived(root: Path, args: argparse.Namespace) -> int:
    summary = run_build_derived_datasets(
        project_root=args.project_root or root,
        audit_json=args.audit_json,
        minimum_recommendation=args.minimum_recommendation,
        output_dir=args.output_dir,
    )
    print(f"Training manifest: {summary['manifest_path']}")
    print(f"Track blueprints: {summary['counts']['track_blueprints']}")
    print(f"Artist style cards: {summary['counts']['artist_style_cards']}")
    return 0


def cmd_dataset_extract_technique(root: Path, args: argparse.Namespace) -> int:
    manifest = run_extract_lyric_technique_records(
        project_root=args.project_root or root,
        output_dir=args.output_dir,
        artists=args.artists,
        default_rights_status=args.default_rights_status,
        source_kind=args.source_kind,
    )
    print(f"Technique manifest: {manifest['manifest_path']}")
    print(f"Records: {manifest['counts']['records']}")
    print(f"Source root: {manifest['source_root']}")
    return 0


def cmd_dataset_build_lyric_behavior(root: Path, args: argparse.Namespace) -> int:
    manifest = run_build_lyric_behavior_dataset(
        project_root=args.project_root or root,
        artists=args.artists,
        output_root=args.output_root,
    )
    print(f"Lyric behavior manifest: {manifest['manifest_path']}")
    print(f"Line behavior records: {manifest['counts']['line_behavior_records']}")
    print(f"Phrase behavior records: {manifest['counts']['phrase_behavior_records']}")
    print(f"Chorus behavior records: {manifest['counts']['chorus_behavior_records']}")
    return 0


def cmd_dataset_build_form_family_catalog(root: Path, args: argparse.Namespace) -> int:
    manifest = run_build_form_family_catalog(
        project_root=args.project_root or root,
        artists=args.artists,
        behavior_root=args.behavior_root,
        output_root=args.output_root,
        catalog_name=args.catalog_name,
    )
    print(f"Form family manifest: {manifest['manifest_path']}")
    print(f"Track assignments: {manifest['counts']['track_assignments']}")
    print(f"Families: {manifest['counts']['families']}")
    print(f"Compressed hook: {manifest['counts']['compressed_hook']}")
    print(f"Expansive statement: {manifest['counts']['expansive_statement']}")
    print(f"Hybrid release: {manifest['counts']['hybrid_release']}")
    return 0


def cmd_dataset_bootstrap_rights(root: Path, args: argparse.Namespace) -> int:
    payload = run_bootstrap_training_rights(
        project_root=args.project_root or root,
        derived_jsonl=args.derived_jsonl,
        existing_map=args.existing_map,
        output_path=args.output_path,
    )
    print(f"Rights map: {payload['output_path']}")
    print(f"Records: {len(payload['records'])}")
    return 0


def cmd_dataset_export_supervised(root: Path, args: argparse.Namespace) -> int:
    manifest = run_export_supervised_samples(
        project_root=args.project_root or root,
        derived_jsonl=args.derived_jsonl,
        output_dir=args.output_dir,
        rights_map=args.rights_map,
        include_eval_only=args.include_eval_only,
        include_full_song=args.include_full_song,
    )
    print(f"Supervised manifest: {manifest['manifest_path']}")
    print(f"Samples: {manifest['counts']['samples']}")
    print(f"Skipped: {manifest['counts']['skipped']}")
    return 0


def cmd_dataset_import_training_sources(root: Path, args: argparse.Namespace) -> int:
    manifest = run_import_training_sources(
        project_root=args.project_root or root,
        pilot_root=args.pilot_root,
        rights_map=args.rights_map,
        output_dir=args.output_dir,
    )
    print(f"Import manifest: {manifest['manifest_path']}")
    print(f"Imported records: {manifest['counts']['imported_records']}")
    print(f"Samples: {manifest['counts']['samples']}")
    print(f"Skipped: {manifest['counts']['skipped']}")
    return 0


def cmd_dataset_build_training_pilot(root: Path, args: argparse.Namespace) -> int:
    manifest = run_build_training_pilot(
        project_root=args.project_root or root,
        source_jsonl=args.source_jsonl,
        output_dir=args.output_dir,
        pilot_name=args.pilot_name,
    )
    print(f"Pilot manifest: {manifest['manifest_path']}")
    print(f"Train: {manifest['counts']['train']}")
    print(f"Eval: {manifest['counts']['eval']}")
    return 0


def cmd_dataset_export_vertex_supervised(root: Path, args: argparse.Namespace) -> int:
    manifest = run_export_vertex_supervised(
        project_root=args.project_root or root,
        train_jsonl=args.train_jsonl,
        eval_jsonl=args.eval_jsonl,
        output_dir=args.output_dir,
        base_model=args.base_model,
    )
    print(f"Vertex export manifest: {manifest['manifest_path']}")
    print(f"Train samples: {manifest['counts']['train_samples']}")
    print(f"Eval samples: {manifest['counts']['eval_samples']}")
    return 0


def cmd_dataset_seed_vocadb_metadata(root: Path, args: argparse.Namespace) -> int:
    if not args.queries and not args.artist_ids and not args.artist_names and not args.artist_list and not args.artist_map:
        raise SystemExit("Provide at least one of: --queries, --artist-ids, --artist-names, --artist-list, --artist-map")
    manifest = run_seed_vocadb_metadata(
        project_root=args.project_root or root,
        queries=args.queries,
        artist_ids=args.artist_ids,
        artist_names=args.artist_names,
        artist_list_path=args.artist_list,
        artist_map_path=args.artist_map,
        output_dir=args.output_dir,
        max_entries=args.max_entries,
    )
    print(f"VocaDB seed manifest: {manifest['manifest_path']}")
    print(f"Written records: {manifest['counts']['written_records']}")
    print(f"Skipped items: {manifest['counts']['skipped_items']}")
    return 0


def cmd_dataset_seed_vocadb_bulk_metadata(root: Path, args: argparse.Namespace) -> int:
    manifest = run_seed_vocadb_bulk_metadata(
        project_root=args.project_root or root,
        output_dir=args.output_dir,
        page_count=args.page_count,
        page_size=args.page_size,
        start_offset=args.start_offset,
        sort=args.sort,
    )
    print(f"VocaDB bulk seed manifest: {manifest['manifest_path']}")
    print(f"Pages scanned: {manifest['counts']['pages_scanned']}")
    print(f"Written records: {manifest['counts']['written_records']}")
    print(f"Skipped items: {manifest['counts']['skipped_items']}")
    return 0


def cmd_dataset_discover_vocadb_producers(root: Path, args: argparse.Namespace) -> int:
    manifest = run_discover_vocadb_producers(
        project_root=args.project_root or root,
        intake_root=args.intake_root,
        output_root=args.output_root,
        page_count=args.page_count,
        page_size=args.page_size,
        sample_song_entries=args.sample_song_entries,
        min_synthetic_songs=args.min_synthetic_songs,
        max_candidates=args.max_candidates,
    )
    print(f"Producer discovery report: {manifest['manifest_path']}")
    print(f"Candidate map: {manifest['candidate_map_path']}")
    print(f"Selected candidates: {manifest['counts']['selected_candidates']}")
    return 0


def cmd_dataset_review_vocaloid_metadata(root: Path, args: argparse.Namespace) -> int:
    manifest = run_review_vocaloid_metadata(
        project_root=args.project_root or root,
        intake_dir=args.intake_dir,
        output_dir=args.output_dir,
    )
    print(f"Metadata review manifest: {manifest['manifest_path']}")
    print(f"Records: {manifest['counts']['records']}")
    print(f"Review candidate: {manifest['counts']['review_candidate']}")
    print(f"Needs manual review: {manifest['counts']['needs_manual_review']}")
    print(f"Low confidence: {manifest['counts']['low_confidence']}")
    return 0


def cmd_dataset_enrich_vocaloid_metadata(root: Path, args: argparse.Namespace) -> int:
    manifest = run_enrich_vocaloid_metadata(
        project_root=args.project_root or root,
        intake_dir=args.intake_dir,
    )
    print(f"Metadata enrichment manifest: {manifest['manifest_path']}")
    print(f"Enriched records: {manifest['counts']['enriched_records']}")
    print(f"Skipped records: {manifest['counts']['skipped_records']}")
    return 0


def cmd_dataset_build_vocaloid_metadata_review_queue(root: Path, args: argparse.Namespace) -> int:
    manifest = run_build_vocaloid_metadata_review_queue(
        project_root=args.project_root or root,
        review_manifest=args.review_manifest,
        output_dir=args.output_dir,
    )
    print(f"Review queue manifest: {manifest['manifest_path']}")
    print(f"Queued records: {manifest['counts']['queued_records']}")
    print(f"Review candidate: {manifest['counts']['review_candidate']}")
    print(f"Needs manual review: {manifest['counts']['needs_manual_review']}")
    print(f"Low confidence: {manifest['counts']['low_confidence']}")
    return 0


def cmd_dataset_auto_triage_vocaloid_metadata_queue(root: Path, args: argparse.Namespace) -> int:
    manifest = run_auto_triage_vocaloid_metadata_queue(
        project_root=args.project_root or root,
        queue_root=args.queue_root,
    )
    print(f"Queue triage manifest: {manifest['manifest_path']}")
    print(f"Rejected: {manifest['counts']['rejected']}")
    print(f"Needs patch: {manifest['counts']['needs_patch']}")
    print(f"Unchanged: {manifest['counts']['unchanged']}")
    return 0


def cmd_dataset_auto_accept_vocaloid_metadata_queue(root: Path, args: argparse.Namespace) -> int:
    manifest = run_auto_accept_vocaloid_metadata_queue(
        project_root=args.project_root or root,
        queue_root=args.queue_root,
    )
    print(f"Queue accept manifest: {manifest['manifest_path']}")
    print(f"Accepted: {manifest['counts']['accepted']}")
    print(f"Skipped: {manifest['counts']['skipped']}")
    return 0


def cmd_dataset_build_vocaloid_metadata_canonical_corpus(root: Path, args: argparse.Namespace) -> int:
    manifest = run_build_vocaloid_metadata_canonical_corpus(
        project_root=args.project_root or root,
        queue_root=args.queue_root,
        output_root=args.output_root,
    )
    print(f"Canonical manifest: {manifest['manifest_path']}")
    print(f"Accepted records: {manifest['counts']['accepted_records']}")
    return 0


def cmd_dataset_report_vocaloid_metadata_coverage(root: Path, args: argparse.Namespace) -> int:
    manifest = run_report_vocaloid_metadata_coverage(
        project_root=args.project_root or root,
        corpus_root=args.corpus_root,
        output_root=args.output_root,
    )
    print(f"Coverage report: {manifest['manifest_path']}")
    print(f"Records: {manifest['counts']['records']}")
    print(f"Unique producers: {manifest['counts']['unique_producers']}")
    print(f"Unique voicebanks: {manifest['counts']['unique_voicebanks']}")
    return 0


def cmd_dataset_audit_vocaloid_metadata_utf8(root: Path, args: argparse.Namespace) -> int:
    manifest = run_audit_vocaloid_metadata_utf8(
        project_root=args.project_root or root,
        corpus_root=args.corpus_root,
        output_root=args.output_root,
    )
    print(f"UTF-8 audit: {manifest['manifest_path']}")
    print(f"Records: {manifest['counts']['records']}")
    print(f"Clean records: {manifest['counts']['clean_records']}")
    print(f"Flagged records: {manifest['counts']['flagged_records']}")
    return 0


def cmd_dataset_classify_corpus_value(root: Path, args: argparse.Namespace) -> int:
    manifest = run_classify_corpus_value(
        project_root=args.project_root or root,
        corpus_root=args.corpus_root,
        output_root=args.output_root,
        write_back=args.write_back,
    )
    print(f"Corpus value classification: {manifest['manifest_path']}")
    print(f"Records: {manifest['counts']['records']}")
    print(f"Core: {manifest['counts']['core']}")
    print(f"Supporting: {manifest['counts']['supporting']}")
    print(f"Low-value retained: {manifest['counts']['low_value_retained']}")
    print(f"Deferred: {manifest['counts']['deferred']}")
    return 0


def cmd_dataset_build_track_generation_records(root: Path, args: argparse.Namespace) -> int:
    manifest = run_build_track_generation_records(
        project_root=args.project_root or root,
        corpus_root=args.corpus_root,
        output_root=args.output_root,
        lyric_technique_jsonl=args.lyric_technique_jsonl,
    )
    print(f"Track generation manifest: {manifest['manifest_path']}")
    print(f"Records: {manifest['counts']['records']}")
    print(f"Suno prompt ready: {manifest['counts']['suno_prompt_ready']}")
    print(f"Blocked: {manifest['counts']['blocked']}")
    print(f"Skipped: {manifest['counts']['skipped']}")
    return 0


def cmd_dataset_export_suno_prompt_assets(root: Path, args: argparse.Namespace) -> int:
    manifest = run_export_suno_prompt_assets(
        project_root=args.project_root or root,
        generation_root=args.generation_root,
        output_root=args.output_root,
        include_blocked=args.include_blocked,
    )
    print(f"Suno prompt asset manifest: {manifest['manifest_path']}")
    print(f"Assets: {manifest['counts']['assets']}")
    print(f"Skipped: {manifest['counts']['skipped']}")
    return 0


def cmd_dataset_audit_generation_joinability(root: Path, args: argparse.Namespace) -> int:
    manifest = run_audit_generation_joinability(
        project_root=args.project_root or root,
        generation_jsonl=args.generation_jsonl,
        technique_jsonl=args.technique_jsonl,
        output_root=args.output_root,
    )
    print(f"Generation joinability audit: {manifest['manifest_path']}")
    print(f"Generation tracks: {manifest['counts']['generation_tracks']}")
    print(f"Technique tracks: {manifest['counts']['technique_tracks']}")
    print(f"Overlap tracks: {manifest['counts']['overlap_tracks']}")
    print(f"Status: {manifest['joinability']['status']}")
    return 0


def cmd_dataset_audit_generation_readiness(root: Path, args: argparse.Namespace) -> int:
    manifest = run_audit_generation_readiness(
        project_root=args.project_root or root,
        generation_root=args.generation_root,
        output_root=args.output_root,
    )
    print(f"Generation readiness audit: {manifest['manifest_path']}")
    print(f"Records: {manifest['counts']['records']}")
    print(f"Joinable: {manifest['counts']['joinable']}")
    print(f"Prompt ready: {manifest['counts']['prompt_ready']}")
    print(f"Production candidate: {manifest['counts']['production_candidate']}")
    print(f"Professional target: {manifest['counts']['professional_target']}")
    return 0


def cmd_dataset_build_sound_profile_review_workspace(root: Path, args: argparse.Namespace) -> int:
    manifest = run_build_sound_profile_review_workspace(
        project_root=args.project_root or root,
        generation_root=args.generation_root,
        corpus_root=args.corpus_root,
        output_root=args.output_root,
        prompt_ready_only=not args.include_blocked,
    )
    print(f"Sound profile review workspace: {manifest['manifest_path']}")
    print(f"Selected tracks: {manifest['counts']['selected_tracks']}")
    print(f"Written incoming records: {manifest['counts']['written_incoming_records']}")
    print(f"Skipped records: {manifest['counts']['skipped_records']}")
    return 0


def cmd_dataset_import_reviewed_sound_profiles(root: Path, args: argparse.Namespace) -> int:
    manifest = run_import_reviewed_sound_profiles(
        project_root=args.project_root or root,
        generation_root=args.generation_root,
        workspace_root=args.workspace_root,
        output_root=args.output_root,
    )
    print(f"Sound profile review import: {manifest['manifest_path']}")
    print(f"Records: {manifest['counts']['records']}")
    print(f"Reviewed tracks applied: {manifest['counts']['reviewed_tracks_applied']}")
    print(f"Unchanged tracks: {manifest['counts']['unchanged_tracks']}")
    return 0


def cmd_dataset_run_professional_quality_cycle(root: Path, args: argparse.Namespace) -> int:
    manifest = run_professional_quality_cycle(
        project_root=args.project_root or root,
        generation_root=args.generation_root,
        sound_review_workspace=args.sound_review_workspace,
        reviewed_generation_root=args.reviewed_generation_root,
        readiness_output_root=args.readiness_output_root,
        prompt_asset_output_root=args.prompt_asset_output_root,
    )
    print(f"Professional quality cycle: {manifest['manifest_path']}")
    print(f"Reviewed tracks applied: {manifest['counts']['reviewed_tracks_applied']}")
    print(f"Joinable: {manifest['counts']['joinable']}")
    print(f"Prompt ready: {manifest['counts']['prompt_ready']}")
    print(f"Production candidate: {manifest['counts']['production_candidate']}")
    print(f"Professional target: {manifest['counts']['professional_target']}")
    print(f"Prompt assets: {manifest['counts']['prompt_assets']}")
    return 0


def cmd_dataset_run_tier1_continuous_cycle(root: Path, args: argparse.Namespace) -> int:
    manifest = run_tier1_continuous_cycle(
        project_root=args.project_root or root,
        corpus_root=args.corpus_root,
        pilot20_workspace=args.pilot20_workspace,
        pilot20_generation_root=args.pilot20_generation_root,
        pilot20_validation_root=args.pilot20_validation_root,
        pilot20_import_root=args.pilot20_import_root,
        pilot20_joinability_root=args.pilot20_joinability_root,
        pilot10_generation_root=args.pilot10_generation_root,
        sound_review_workspace=args.sound_review_workspace,
        sound_reviewed_generation_root=args.sound_reviewed_generation_root,
        sound_readiness_root=args.sound_readiness_root,
        sound_prompt_asset_root=args.sound_prompt_asset_root,
        grounding_status_root=args.grounding_status_root,
    )
    print(f"Tier1 continuous cycle: {manifest['manifest_path']}")
    print(f"Pilot20 valid: {manifest['counts']['pilot20_valid']}")
    print(f"Pilot20 invalid: {manifest['counts']['pilot20_invalid']}")
    print(f"Pilot20 imported: {manifest['counts']['pilot20_imported']}")
    print(f"Pilot20 overlap: {manifest['counts']['pilot20_overlap']}")
    print(f"Pilot10 joinable: {manifest['counts']['pilot10_joinable']}")
    print(f"Pilot10 production candidate: {manifest['counts']['pilot10_production_candidate']}")
    print(f"Pilot10 professional target: {manifest['counts']['pilot10_professional_target']}")
    print(f"Sound review applied: {manifest['counts']['sound_review_applied']}")
    print(f"Grounding total accepted: {manifest['counts']['grounding_total_accepted']}")
    return 0


def cmd_dataset_run_program_continuous_cycle(root: Path, args: argparse.Namespace) -> int:
    manifest = run_program_continuous_cycle(
        project_root=args.project_root or root,
        batch_tag=args.batch_tag,
        bulk_page_count=args.bulk_page_count,
        bulk_page_size=args.bulk_page_size,
        bulk_start_offset=args.bulk_start_offset,
        bulk_sort=args.bulk_sort,
        run_tier1_cycle=not args.skip_tier1_cycle,
    )
    print(f"Program continuous cycle: {manifest['manifest_path']}")
    print(f"Bulk seed written: {manifest['counts']['bulk_seed_written']}")
    print(f"Bulk enriched records: {manifest['counts']['bulk_enriched_records']}")
    print(f"Bulk review records: {manifest['counts']['bulk_review_records']}")
    print(f"Bulk queue records: {manifest['counts']['bulk_queue_records']}")
    print(f"Bulk needs patch: {manifest['counts']['bulk_needs_patch']}")
    print(f"Bulk auto accepted: {manifest['counts']['bulk_auto_accepted']}")
    print(f"Bulk canonical records: {manifest['counts']['bulk_canonical_records']}")
    print(f"Tier1 pilot20 invalid: {manifest['counts']['tier1_pilot20_invalid']}")
    print(f"Tier1 pilot20 overlap: {manifest['counts']['tier1_pilot20_overlap']}")
    print(f"Tier1 professional target: {manifest['counts']['tier1_pilot10_professional_target']}")
    print(f"Engine surface prompt-ready: {manifest['counts']['engine_surface_readiness_prompt_ready']}")
    print(f"Engine surface professional target: {manifest['counts']['engine_surface_readiness_professional_target']}")
    print(f"Engine state: {manifest['outputs']['engine_state_json_path']}")
    return 0


def cmd_dataset_run_program_continuous_sweep(root: Path, args: argparse.Namespace) -> int:
    manifest = run_program_continuous_sweep(
        project_root=args.project_root or root,
        batch_tag_prefix=args.batch_tag_prefix,
        batch_count=args.batch_count,
        bulk_page_count=args.bulk_page_count,
        bulk_page_size=args.bulk_page_size,
        bulk_start_offset=args.bulk_start_offset,
        bulk_offset_step=args.bulk_offset_step,
        bulk_sort=args.bulk_sort,
        run_tier1_once=not args.run_tier1_every_batch,
    )
    print(f"Program continuous sweep: {manifest['manifest_path']}")
    print(f"Runs: {manifest['counts']['runs']}")
    print(f"Bulk seed written: {manifest['counts']['bulk_seed_written']}")
    print(f"Bulk enriched records: {manifest['counts']['bulk_enriched_records']}")
    print(f"Bulk canonical records: {manifest['counts']['bulk_canonical_records']}")
    print(f"Bulk core: {manifest['counts']['bulk_core']}")
    print(f"Bulk low-value retained: {manifest['counts']['bulk_low_value_retained']}")
    print(f"Bulk needs patch: {manifest['counts']['bulk_needs_patch']}")
    print(f"Tier1 pilot20 invalid: {manifest['counts']['tier1_pilot20_invalid']}")
    print(f"Tier1 pilot20 overlap: {manifest['counts']['tier1_pilot20_overlap']}")
    print(f"Tier1 professional target: {manifest['counts']['tier1_pilot10_professional_target']}")
    print(f"Engine surface prompt-ready: {manifest['counts']['engine_surface_readiness_prompt_ready']}")
    print(f"Engine surface professional target: {manifest['counts']['engine_surface_readiness_professional_target']}")
    print(f"Engine state: {manifest['outputs'].get('engine_state_json_path', '')}")
    return 0


def cmd_dataset_build_lyric_technique_acquisition_queue(root: Path, args: argparse.Namespace) -> int:
    manifest = run_build_lyric_technique_acquisition_queue(
        project_root=args.project_root or root,
        corpus_root=args.corpus_root,
        output_root=args.output_root,
    )
    print(f"Lyric technique acquisition manifest: {manifest['manifest_path']}")
    print(f"Records: {manifest['counts']['records']}")
    print(f"Ready for lyric grounding: {manifest['counts']['ready_for_lyric_grounding']}")
    print(f"Patch first: {manifest['counts']['patch_first']}")
    print(f"Review first: {manifest['counts']['review_first']}")
    print(f"Skipped: {manifest['counts']['skipped']}")
    return 0


def cmd_dataset_build_vocadb_lyric_grounding_workspace(root: Path, args: argparse.Namespace) -> int:
    manifest = run_build_vocadb_lyric_grounding_workspace(
        project_root=args.project_root or root,
        queue_root=args.queue_root,
        workspace_root=args.workspace_root,
    )
    print(f"VocaDB lyric grounding workspace: {manifest['manifest_path']}")
    print(f"Written incoming records: {manifest['counts']['written_incoming_records']}")
    print(f"Skipped records: {manifest['counts']['skipped_records']}")
    return 0


def cmd_dataset_import_vocadb_grounded_technique(root: Path, args: argparse.Namespace) -> int:
    manifest = run_import_vocadb_grounded_technique_records(
        project_root=args.project_root or root,
        workspace_root=args.workspace_root,
        output_root=args.output_root,
    )
    print(f"Grounded technique import manifest: {manifest['manifest_path']}")
    print(f"Records: {manifest['counts']['records']}")
    print(f"Skipped: {manifest['counts']['skipped']}")
    return 0


def cmd_dataset_validate_vocadb_lyric_grounding_workspace(root: Path, args: argparse.Namespace) -> int:
    manifest = run_validate_vocadb_lyric_grounding_workspace(
        project_root=args.project_root or root,
        workspace_root=args.workspace_root,
        output_root=args.output_root,
    )
    print(f"VocaDB lyric grounding validation: {manifest['manifest_path']}")
    print(f"Records: {manifest['counts']['records']}")
    print(f"Valid: {manifest['counts']['valid']}")
    print(f"Invalid: {manifest['counts']['invalid']}")
    return 0


def cmd_dataset_build_lyric_technique_pilot_batch(root: Path, args: argparse.Namespace) -> int:
    manifest = run_build_lyric_technique_pilot_batch(
        project_root=args.project_root or root,
        queue_root=args.queue_root,
        output_root=args.output_root,
        batch_size=args.batch_size,
        exclude_track_ids=args.exclude_track_ids,
    )
    print(f"Lyric technique pilot batch: {manifest['manifest_path']}")
    print(f"Eligible candidates: {manifest['counts']['eligible_candidates']}")
    print(f"Selected: {manifest['counts']['selected']}")
    return 0


def cmd_dataset_materialize_lyric_technique_pilot_workspace(root: Path, args: argparse.Namespace) -> int:
    manifest = run_materialize_lyric_technique_pilot_workspace(
        project_root=args.project_root or root,
        source_workspace_root=args.source_workspace_root,
        pilot_manifest_path=args.pilot_manifest_path,
        output_root=args.output_root,
    )
    print(f"Lyric technique pilot workspace: {manifest['manifest_path']}")
    print(f"Selected tracks: {manifest['counts']['selected_tracks']}")
    print(f"Copied tracks: {manifest['counts']['copied_tracks']}")
    print(f"Skipped tracks: {manifest['counts']['skipped_tracks']}")
    return 0


def cmd_dataset_run_lyric_technique_pilot_cycle(root: Path, args: argparse.Namespace) -> int:
    manifest = run_lyric_technique_pilot_cycle(
        project_root=args.project_root or root,
        corpus_root=args.corpus_root,
        workspace_root=args.workspace_root,
        generation_output_root=args.generation_output_root,
        validation_output_root=args.validation_output_root,
        import_output_root=args.import_output_root,
        joinability_output_root=args.joinability_output_root,
    )
    print(f"Pilot workspace: {manifest['workspace_root']}")
    print(f"Generation records: {manifest['generation_manifest']['counts']['records']}")
    print(f"Validation invalid: {manifest['validation_manifest']['counts']['invalid']}")
    print(f"Imported technique records: {manifest['import_manifest']['counts']['records']}")
    print(f"Joinability overlap: {manifest['joinability_manifest']['counts']['overlap_tracks']}")
    print(f"Joinability status: {manifest['joinability_manifest']['joinability']['status']}")
    return 0


def cmd_dataset_report_vocadb_lyric_grounding_status(root: Path, args: argparse.Namespace) -> int:
    manifest = run_report_vocadb_lyric_grounding_status(
        project_root=args.project_root or root,
        workspaces_root=args.workspaces_root,
        output_root=args.output_root,
    )
    print(f"Grounding status report: {manifest['manifest_path']}")
    print(f"Workspaces: {manifest['counts']['workspaces']}")
    print(f"Total incoming: {manifest['counts']['total_incoming']}")
    print(f"Total accepted: {manifest['counts']['total_accepted']}")
    return 0


def cmd_dataset_auto_ground_vocadb_workspace_from_url_map(root: Path, args: argparse.Namespace) -> int:
    manifest = run_auto_ground_vocadb_workspace_from_url_map(
        project_root=args.project_root or root,
        workspace_root=args.workspace_root,
        url_map_path=args.url_map_path,
    )
    print(f"Auto grounding manifest: {manifest['manifest_path']}")
    print(f"Grounded: {manifest['counts']['grounded']}")
    print(f"Skipped: {manifest['counts']['skipped']}")
    return 0


def cmd_report_engine_health(root: Path, args: argparse.Namespace) -> int:
    result = run_report_engine_health(
        project_root=args.project_root or root,
        artists=args.artists,
        output_dir=args.output_dir,
    )
    print(result["json_path"])
    print(result["md_path"])
    print(f"Source root: {result['source_root']}")
    return 0


def cmd_report_baseline(root: Path, args: argparse.Namespace) -> int:
    result = run_report_baseline(
        project_root=args.project_root or root,
        output_root=args.output_root,
    )
    print(result["data_path"])
    print(result["json_path"])
    print(result["md_path"])
    print(f"Source root: {result['source_root']}")
    return 0


def cmd_report_engine_state(root: Path, args: argparse.Namespace) -> int:
    result = run_report_engine_state(
        project_root=args.project_root or root,
        output_root=args.output_root,
    )
    print(result["json_path"])
    print(result["md_path"])
    print(f"Status level: {result['status_level']}")
    return 0


def cmd_report_sync_authoritative_wiki(root: Path, args: argparse.Namespace) -> int:
    result = run_report_sync_authoritative_wiki(
        project_root=args.project_root or root,
        output_root=args.output_root,
    )
    print(result["wiki_manifest_path"])
    print(f"Wiki root: {result['wiki_root']}")
    print(f"Status level after: {result['status_level_after']}")
    return 0


def cmd_report_sync_engine_surface(root: Path, args: argparse.Namespace) -> int:
    result = run_report_sync_engine_surface(
        project_root=args.project_root or root,
        output_root=args.output_root,
    )
    print(result["manifest_path"])
    print(f"Status level after: {result['status_level_after']}")
    return 0


def cmd_test(root: Path, args: argparse.Namespace) -> int:
    return _run_pytest(root, args.pytest_args)


def build_parser(root: Path) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="akira.py",
        description="AKIRA single entrypoint for the reduced rebuild skeleton.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    status_parser = subparsers.add_parser("status", help="Show the current active skeleton and main entrypoints.")
    status_parser.set_defaults(func=lambda args: cmd_status(root, args))

    songwriter_parser = subparsers.add_parser("songwriter", help="Songwriter runtime commands.")
    songwriter_sub = songwriter_parser.add_subparsers(dest="songwriter_command", required=True)

    songwriter_demo = songwriter_sub.add_parser("demo", help="Run the demo songwriter entrypoint.")
    songwriter_demo.add_argument("--artist-id", required=True)
    songwriter_demo.add_argument("--mode-id")
    songwriter_demo.add_argument("--intent")
    songwriter_demo.add_argument("--title-seed")
    songwriter_demo.add_argument("--project-root", type=Path, default=root)
    songwriter_demo.add_argument("--output-dir", type=Path)
    songwriter_demo.add_argument("--candidate-count", type=int)
    songwriter_demo.add_argument("--generation-mode", choices=["auto", "template", "llm", "api"])
    songwriter_demo.add_argument("--model-provider", choices=["gemini", "gpt", "openai"])
    songwriter_demo.add_argument("--model-name")
    songwriter_demo.set_defaults(func=lambda args: cmd_songwriter_demo(root, args))

    dataset_parser = subparsers.add_parser("dataset", help="Dataset and training export commands.")
    dataset_sub = dataset_parser.add_subparsers(dest="dataset_command", required=True)

    build_derived = dataset_sub.add_parser("build-derived", help="Build derived training datasets.")
    build_derived.add_argument("--project-root", type=Path, default=root)
    build_derived.add_argument("--audit-json", type=Path)
    build_derived.add_argument("--minimum-recommendation", choices=["needs_review", "ready"], default="needs_review")
    build_derived.add_argument("--output-dir", type=Path)
    build_derived.set_defaults(func=lambda args: cmd_dataset_build_derived(root, args))

    extract_technique = dataset_sub.add_parser("extract-technique-records", help="Extract lyric technique records from normalized lyric corpora.")
    extract_technique.add_argument("--project-root", type=Path, default=root)
    extract_technique.add_argument("--output-dir", type=Path)
    extract_technique.add_argument("--artists", nargs="*")
    extract_technique.add_argument("--default-rights-status", default="unknown")
    extract_technique.add_argument("--source-kind", choices=["normalized_corpus", "owned_original_hook_pilot"], default="normalized_corpus")
    extract_technique.set_defaults(func=lambda args: cmd_dataset_extract_technique(root, args))

    build_lyric_behavior = dataset_sub.add_parser(
        "build-lyric-behavior",
        help="Extract line/phrase/chorus behavior records from conditioning corpora.",
    )
    build_lyric_behavior.add_argument("--project-root", type=Path, default=root)
    build_lyric_behavior.add_argument("--artists", nargs="*")
    build_lyric_behavior.add_argument("--output-root", type=Path)
    build_lyric_behavior.set_defaults(func=lambda args: cmd_dataset_build_lyric_behavior(root, args))

    build_form_families = dataset_sub.add_parser(
        "build-form-families",
        help="Cluster lyric behavior corpora into reusable chorus/form families.",
    )
    build_form_families.add_argument("--project-root", type=Path, default=root)
    build_form_families.add_argument("--artists", nargs="*")
    build_form_families.add_argument("--behavior-root", type=Path)
    build_form_families.add_argument("--output-root", type=Path)
    build_form_families.add_argument("--catalog-name", default="calibration_v1")
    build_form_families.set_defaults(func=lambda args: cmd_dataset_build_form_family_catalog(root, args))

    bootstrap_rights = dataset_sub.add_parser("bootstrap-rights", help="Bootstrap the training rights map from derived records.")
    bootstrap_rights.add_argument("--project-root", type=Path, default=root)
    bootstrap_rights.add_argument("--derived-jsonl", type=Path)
    bootstrap_rights.add_argument("--existing-map", type=Path)
    bootstrap_rights.add_argument("--output-path", type=Path)
    bootstrap_rights.set_defaults(func=lambda args: cmd_dataset_bootstrap_rights(root, args))

    export_supervised = dataset_sub.add_parser("export-supervised", help="Export supervised training samples from derived records.")
    export_supervised.add_argument("--project-root", type=Path, default=root)
    export_supervised.add_argument("--derived-jsonl", type=Path)
    export_supervised.add_argument("--output-dir", type=Path)
    export_supervised.add_argument("--rights-map", type=Path)
    export_supervised.add_argument("--include-eval-only", action="store_true")
    export_supervised.add_argument("--include-full-song", action="store_true")
    export_supervised.set_defaults(func=lambda args: cmd_dataset_export_supervised(root, args))

    import_training_sources = dataset_sub.add_parser(
        "import-training-sources",
        help="Import accepted rights-cleared training-source records into the rights map and supervised export path.",
    )
    import_training_sources.add_argument("--project-root", type=Path, default=root)
    import_training_sources.add_argument("--pilot-root", type=Path)
    import_training_sources.add_argument("--rights-map", type=Path)
    import_training_sources.add_argument("--output-dir", type=Path)
    import_training_sources.set_defaults(func=lambda args: cmd_dataset_import_training_sources(root, args))

    build_training_pilot = dataset_sub.add_parser(
        "build-training-pilot",
        help="Build a train/eval pilot bundle from a supervised sample export.",
    )
    build_training_pilot.add_argument("--project-root", type=Path, default=root)
    build_training_pilot.add_argument("--source-jsonl", type=Path)
    build_training_pilot.add_argument("--output-dir", type=Path)
    build_training_pilot.add_argument("--pilot-name", default="owned_original_hook_v1")
    build_training_pilot.set_defaults(func=lambda args: cmd_dataset_build_training_pilot(root, args))

    export_vertex_supervised = dataset_sub.add_parser(
        "export-vertex-supervised",
        help="Export a supervised pilot bundle to Vertex AI supervised tuning JSONL.",
    )
    export_vertex_supervised.add_argument("--project-root", type=Path, default=root)
    export_vertex_supervised.add_argument("--train-jsonl", type=Path)
    export_vertex_supervised.add_argument("--eval-jsonl", type=Path)
    export_vertex_supervised.add_argument("--output-dir", type=Path)
    export_vertex_supervised.add_argument("--base-model", default="gemini-2.5-flash")
    export_vertex_supervised.set_defaults(func=lambda args: cmd_dataset_export_vertex_supervised(root, args))

    seed_vocadb_metadata = dataset_sub.add_parser(
        "seed-vocadb-metadata",
        help="Seed Vocaloid metadata intake records from VocaDB search queries.",
    )
    seed_vocadb_metadata.add_argument("--project-root", type=Path, default=root)
    seed_vocadb_metadata.add_argument("--queries", nargs="+")
    seed_vocadb_metadata.add_argument("--artist-ids", nargs="+", type=int)
    seed_vocadb_metadata.add_argument("--artist-names", nargs="+")
    seed_vocadb_metadata.add_argument("--artist-list", type=Path)
    seed_vocadb_metadata.add_argument("--artist-map", type=Path)
    seed_vocadb_metadata.add_argument("--output-dir", type=Path)
    seed_vocadb_metadata.add_argument("--max-entries", type=int, default=50)
    seed_vocadb_metadata.set_defaults(func=lambda args: cmd_dataset_seed_vocadb_metadata(root, args))

    seed_vocadb_bulk_metadata = dataset_sub.add_parser(
        "seed-vocadb-bulk-metadata",
        help="Seed Vocaloid metadata directly from paged VocaDB song catalog results.",
    )
    seed_vocadb_bulk_metadata.add_argument("--project-root", type=Path, default=root)
    seed_vocadb_bulk_metadata.add_argument("--output-dir", type=Path)
    seed_vocadb_bulk_metadata.add_argument("--page-count", type=int, default=10)
    seed_vocadb_bulk_metadata.add_argument("--page-size", type=int, default=50)
    seed_vocadb_bulk_metadata.add_argument("--start-offset", type=int, default=0)
    seed_vocadb_bulk_metadata.add_argument("--sort", default="PublishDate")
    seed_vocadb_bulk_metadata.set_defaults(func=lambda args: cmd_dataset_seed_vocadb_bulk_metadata(root, args))

    discover_vocadb_producers = dataset_sub.add_parser(
        "discover-vocadb-producers",
        help="Discover new VocaDB producer candidates outside the current explicit seed maps.",
    )
    discover_vocadb_producers.add_argument("--project-root", type=Path, default=root)
    discover_vocadb_producers.add_argument("--intake-root", type=Path)
    discover_vocadb_producers.add_argument("--output-root", type=Path)
    discover_vocadb_producers.add_argument("--page-count", type=int, default=5)
    discover_vocadb_producers.add_argument("--page-size", type=int, default=50)
    discover_vocadb_producers.add_argument("--sample-song-entries", type=int, default=25)
    discover_vocadb_producers.add_argument("--min-synthetic-songs", type=int, default=3)
    discover_vocadb_producers.add_argument("--max-candidates", type=int, default=25)
    discover_vocadb_producers.set_defaults(func=lambda args: cmd_dataset_discover_vocadb_producers(root, args))

    review_vocaloid_metadata = dataset_sub.add_parser(
        "review-vocaloid-metadata",
        help="Run automatic canonical-review heuristics over seeded Vocaloid metadata records.",
    )
    review_vocaloid_metadata.add_argument("--project-root", type=Path, default=root)
    review_vocaloid_metadata.add_argument("--intake-dir", type=Path)
    review_vocaloid_metadata.add_argument("--output-dir", type=Path)
    review_vocaloid_metadata.set_defaults(func=lambda args: cmd_dataset_review_vocaloid_metadata(root, args))

    enrich_vocaloid_metadata = dataset_sub.add_parser(
        "enrich-vocaloid-metadata",
        help="Enrich seeded Vocaloid metadata records with official upload links from VocaDB detail.",
    )
    enrich_vocaloid_metadata.add_argument("--project-root", type=Path, default=root)
    enrich_vocaloid_metadata.add_argument("--intake-dir", type=Path)
    enrich_vocaloid_metadata.set_defaults(func=lambda args: cmd_dataset_enrich_vocaloid_metadata(root, args))

    build_review_queue = dataset_sub.add_parser(
        "build-vocaloid-review-queue",
        help="Build the manual review queue for seeded Vocaloid metadata records.",
    )
    build_review_queue.add_argument("--project-root", type=Path, default=root)
    build_review_queue.add_argument("--review-manifest", type=Path)
    build_review_queue.add_argument("--output-dir", type=Path)
    build_review_queue.set_defaults(func=lambda args: cmd_dataset_build_vocaloid_metadata_review_queue(root, args))

    auto_triage_queue = dataset_sub.add_parser(
        "auto-triage-vocaloid-queue",
        help="Auto-triage low-confidence and simple needs-patch Vocaloid metadata records.",
    )
    auto_triage_queue.add_argument("--project-root", type=Path, default=root)
    auto_triage_queue.add_argument("--queue-root", type=Path)
    auto_triage_queue.set_defaults(func=lambda args: cmd_dataset_auto_triage_vocaloid_metadata_queue(root, args))

    auto_accept_queue = dataset_sub.add_parser(
        "auto-accept-vocaloid-queue",
        help="Auto-accept clean zero-flag Vocaloid metadata review candidates into accepted/.",
    )
    auto_accept_queue.add_argument("--project-root", type=Path, default=root)
    auto_accept_queue.add_argument("--queue-root", type=Path)
    auto_accept_queue.set_defaults(func=lambda args: cmd_dataset_auto_accept_vocaloid_metadata_queue(root, args))

    build_canonical_corpus = dataset_sub.add_parser(
        "build-vocaloid-canonical-corpus",
        help="Materialize accepted Vocaloid metadata records into a stable canonical corpus root.",
    )
    build_canonical_corpus.add_argument("--project-root", type=Path, default=root)
    build_canonical_corpus.add_argument("--queue-root", type=Path)
    build_canonical_corpus.add_argument("--output-root", type=Path)
    build_canonical_corpus.set_defaults(func=lambda args: cmd_dataset_build_vocaloid_metadata_canonical_corpus(root, args))

    report_canonical_coverage = dataset_sub.add_parser(
        "report-vocaloid-metadata-coverage",
        help="Build a producer and voicebank coverage report from the canonical Vocaloid metadata corpus.",
    )
    report_canonical_coverage.add_argument("--project-root", type=Path, default=root)
    report_canonical_coverage.add_argument("--corpus-root", type=Path)
    report_canonical_coverage.add_argument("--output-root", type=Path)
    report_canonical_coverage.set_defaults(func=lambda args: cmd_dataset_report_vocaloid_metadata_coverage(root, args))

    audit_canonical_utf8 = dataset_sub.add_parser(
        "audit-vocaloid-metadata-utf8",
        help="Audit canonical Vocaloid metadata records for actual UTF-8 corruption signals.",
    )
    audit_canonical_utf8.add_argument("--project-root", type=Path, default=root)
    audit_canonical_utf8.add_argument("--corpus-root", type=Path)
    audit_canonical_utf8.add_argument("--output-root", type=Path)
    audit_canonical_utf8.set_defaults(func=lambda args: cmd_dataset_audit_vocaloid_metadata_utf8(root, args))

    classify_corpus_value = dataset_sub.add_parser(
        "classify-corpus-value",
        help="Classify retained canonical metadata records into core, supporting, low-value-retained, and deferred tiers.",
    )
    classify_corpus_value.add_argument("--project-root", type=Path, default=root)
    classify_corpus_value.add_argument("--corpus-root", type=Path)
    classify_corpus_value.add_argument("--output-root", type=Path)
    classify_corpus_value.add_argument("--write-back", action="store_true")
    classify_corpus_value.set_defaults(func=lambda args: cmd_dataset_classify_corpus_value(root, args))

    build_track_generation = dataset_sub.add_parser(
        "build-track-generation-records",
        help="Build track generation records from canonical Vocaloid metadata, optionally merging lyric technique records.",
    )
    build_track_generation.add_argument("--project-root", type=Path, default=root)
    build_track_generation.add_argument("--corpus-root", type=Path)
    build_track_generation.add_argument("--output-root", type=Path)
    build_track_generation.add_argument("--lyric-technique-jsonl", type=Path)
    build_track_generation.set_defaults(func=lambda args: cmd_dataset_build_track_generation_records(root, args))

    export_suno_prompt_assets = dataset_sub.add_parser(
        "export-suno-prompt-assets",
        help="Export Suno prompt assets from track generation records.",
    )
    export_suno_prompt_assets.add_argument("--project-root", type=Path, default=root)
    export_suno_prompt_assets.add_argument("--generation-root", type=Path)
    export_suno_prompt_assets.add_argument("--output-root", type=Path)
    export_suno_prompt_assets.add_argument("--include-blocked", action="store_true")
    export_suno_prompt_assets.set_defaults(func=lambda args: cmd_dataset_export_suno_prompt_assets(root, args))

    audit_generation_joinability = dataset_sub.add_parser(
        "audit-generation-joinability",
        help="Audit direct track_id overlap between generation profiles and lyric technique corpora.",
    )
    audit_generation_joinability.add_argument("--project-root", type=Path, default=root)
    audit_generation_joinability.add_argument("--generation-jsonl", type=Path)
    audit_generation_joinability.add_argument("--technique-jsonl", type=Path)
    audit_generation_joinability.add_argument("--output-root", type=Path)
    audit_generation_joinability.set_defaults(func=lambda args: cmd_dataset_audit_generation_joinability(root, args))

    audit_generation_readiness = dataset_sub.add_parser(
        "audit-generation-readiness",
        help="Audit track generation records against the professional-song quality target levels.",
    )
    audit_generation_readiness.add_argument("--project-root", type=Path, default=root)
    audit_generation_readiness.add_argument("--generation-root", type=Path)
    audit_generation_readiness.add_argument("--output-root", type=Path)
    audit_generation_readiness.set_defaults(func=lambda args: cmd_dataset_audit_generation_readiness(root, args))

    build_sound_profile_review_workspace = dataset_sub.add_parser(
        "build-sound-profile-review-workspace",
        help="Materialize a sound-profile review workspace for the current joined generation subset.",
    )
    build_sound_profile_review_workspace.add_argument("--project-root", type=Path, default=root)
    build_sound_profile_review_workspace.add_argument("--generation-root", type=Path)
    build_sound_profile_review_workspace.add_argument("--corpus-root", type=Path)
    build_sound_profile_review_workspace.add_argument("--output-root", type=Path)
    build_sound_profile_review_workspace.add_argument("--include-blocked", action="store_true")
    build_sound_profile_review_workspace.set_defaults(func=lambda args: cmd_dataset_build_sound_profile_review_workspace(root, args))

    import_reviewed_sound_profiles = dataset_sub.add_parser(
        "import-reviewed-sound-profiles",
        help="Overlay accepted sound-profile reviews onto generation records.",
    )
    import_reviewed_sound_profiles.add_argument("--project-root", type=Path, default=root)
    import_reviewed_sound_profiles.add_argument("--generation-root", type=Path)
    import_reviewed_sound_profiles.add_argument("--workspace-root", type=Path)
    import_reviewed_sound_profiles.add_argument("--output-root", type=Path)
    import_reviewed_sound_profiles.set_defaults(func=lambda args: cmd_dataset_import_reviewed_sound_profiles(root, args))

    run_professional_quality_cycle = dataset_sub.add_parser(
        "run-professional-quality-cycle",
        help="Apply accepted sound-profile reviews, rerun readiness audit, and refresh prompt assets in one pass.",
    )
    run_professional_quality_cycle.add_argument("--project-root", type=Path, default=root)
    run_professional_quality_cycle.add_argument("--generation-root", type=Path)
    run_professional_quality_cycle.add_argument("--sound-review-workspace", type=Path)
    run_professional_quality_cycle.add_argument("--reviewed-generation-root", type=Path)
    run_professional_quality_cycle.add_argument("--readiness-output-root", type=Path)
    run_professional_quality_cycle.add_argument("--prompt-asset-output-root", type=Path)
    run_professional_quality_cycle.set_defaults(func=lambda args: cmd_dataset_run_professional_quality_cycle(root, args))

    run_tier1_continuous_cycle = dataset_sub.add_parser(
        "run-tier1-continuous-cycle",
        help="Run the active Tier 1 grounding, joinability, sound review, and readiness loop in one pass.",
    )
    run_tier1_continuous_cycle.add_argument("--project-root", type=Path, default=root)
    run_tier1_continuous_cycle.add_argument("--corpus-root", type=Path)
    run_tier1_continuous_cycle.add_argument("--pilot20-workspace", type=Path)
    run_tier1_continuous_cycle.add_argument("--pilot20-generation-root", type=Path)
    run_tier1_continuous_cycle.add_argument("--pilot20-validation-root", type=Path)
    run_tier1_continuous_cycle.add_argument("--pilot20-import-root", type=Path)
    run_tier1_continuous_cycle.add_argument("--pilot20-joinability-root", type=Path)
    run_tier1_continuous_cycle.add_argument("--pilot10-generation-root", type=Path)
    run_tier1_continuous_cycle.add_argument("--sound-review-workspace", type=Path)
    run_tier1_continuous_cycle.add_argument("--sound-reviewed-generation-root", type=Path)
    run_tier1_continuous_cycle.add_argument("--sound-readiness-root", type=Path)
    run_tier1_continuous_cycle.add_argument("--sound-prompt-asset-root", type=Path)
    run_tier1_continuous_cycle.add_argument("--grounding-status-root", type=Path)
    run_tier1_continuous_cycle.set_defaults(func=lambda args: cmd_dataset_run_tier1_continuous_cycle(root, args))

    run_program_continuous_cycle = dataset_sub.add_parser(
        "run-program-continuous-cycle",
        help="Run bulk metadata expansion and the active Tier 1 lyric/generation loop in one pass.",
    )
    run_program_continuous_cycle.add_argument("--project-root", type=Path, default=root)
    run_program_continuous_cycle.add_argument("--batch-tag", required=True)
    run_program_continuous_cycle.add_argument("--bulk-page-count", type=int, default=3)
    run_program_continuous_cycle.add_argument("--bulk-page-size", type=int, default=50)
    run_program_continuous_cycle.add_argument("--bulk-start-offset", type=int, default=0)
    run_program_continuous_cycle.add_argument("--bulk-sort", default="PublishDate")
    run_program_continuous_cycle.add_argument("--skip-tier1-cycle", action="store_true")
    run_program_continuous_cycle.set_defaults(func=lambda args: cmd_dataset_run_program_continuous_cycle(root, args))

    run_program_continuous_sweep = dataset_sub.add_parser(
        "run-program-continuous-sweep",
        help="Run multiple bulk metadata expansion batches plus the active Tier 1 loop in sequence.",
    )
    run_program_continuous_sweep.add_argument("--project-root", type=Path, default=root)
    run_program_continuous_sweep.add_argument("--batch-tag-prefix", required=True)
    run_program_continuous_sweep.add_argument("--batch-count", type=int, required=True)
    run_program_continuous_sweep.add_argument("--bulk-page-count", type=int, default=3)
    run_program_continuous_sweep.add_argument("--bulk-page-size", type=int, default=50)
    run_program_continuous_sweep.add_argument("--bulk-start-offset", type=int, default=0)
    run_program_continuous_sweep.add_argument("--bulk-offset-step", type=int)
    run_program_continuous_sweep.add_argument("--bulk-sort", default="PublishDate")
    run_program_continuous_sweep.add_argument("--run-tier1-every-batch", action="store_true")
    run_program_continuous_sweep.set_defaults(func=lambda args: cmd_dataset_run_program_continuous_sweep(root, args))

    build_lyric_technique_queue = dataset_sub.add_parser(
        "build-lyric-technique-acquisition-queue",
        help="Build a vocadb track-id aligned acquisition queue for future lyric technique extraction.",
    )
    build_lyric_technique_queue.add_argument("--project-root", type=Path, default=root)
    build_lyric_technique_queue.add_argument("--corpus-root", type=Path)
    build_lyric_technique_queue.add_argument("--output-root", type=Path)
    build_lyric_technique_queue.set_defaults(func=lambda args: cmd_dataset_build_lyric_technique_acquisition_queue(root, args))

    build_vocadb_lyric_grounding_workspace = dataset_sub.add_parser(
        "build-vocadb-lyric-grounding-workspace",
        help="Seed an incoming grounded-lyric workspace from a vocadb track-id aligned technique acquisition queue.",
    )
    build_vocadb_lyric_grounding_workspace.add_argument("--project-root", type=Path, default=root)
    build_vocadb_lyric_grounding_workspace.add_argument("--queue-root", type=Path)
    build_vocadb_lyric_grounding_workspace.add_argument("--workspace-root", type=Path)
    build_vocadb_lyric_grounding_workspace.set_defaults(func=lambda args: cmd_dataset_build_vocadb_lyric_grounding_workspace(root, args))

    import_vocadb_grounded_technique = dataset_sub.add_parser(
        "import-vocadb-grounded-technique",
        help="Import accepted vocadb-aligned grounded lyric bundles into lyric_technique_record rows.",
    )
    import_vocadb_grounded_technique.add_argument("--project-root", type=Path, default=root)
    import_vocadb_grounded_technique.add_argument("--workspace-root", type=Path)
    import_vocadb_grounded_technique.add_argument("--output-root", type=Path)
    import_vocadb_grounded_technique.set_defaults(func=lambda args: cmd_dataset_import_vocadb_grounded_technique(root, args))

    validate_vocadb_grounding_workspace = dataset_sub.add_parser(
        "validate-vocadb-lyric-grounding-workspace",
        help="Validate grounded lyric bundles in a vocadb-aligned lyric grounding workspace.",
    )
    validate_vocadb_grounding_workspace.add_argument("--project-root", type=Path, default=root)
    validate_vocadb_grounding_workspace.add_argument("--workspace-root", type=Path)
    validate_vocadb_grounding_workspace.add_argument("--output-root", type=Path)
    validate_vocadb_grounding_workspace.set_defaults(func=lambda args: cmd_dataset_validate_vocadb_lyric_grounding_workspace(root, args))

    build_lyric_technique_pilot_batch = dataset_sub.add_parser(
        "build-lyric-technique-pilot-batch",
        help="Select a small high-priority lyric grounding pilot batch from a technique acquisition queue.",
    )
    build_lyric_technique_pilot_batch.add_argument("--project-root", type=Path, default=root)
    build_lyric_technique_pilot_batch.add_argument("--queue-root", type=Path)
    build_lyric_technique_pilot_batch.add_argument("--output-root", type=Path)
    build_lyric_technique_pilot_batch.add_argument("--batch-size", type=int, default=10)
    build_lyric_technique_pilot_batch.add_argument("--exclude-track-ids", nargs="*")
    build_lyric_technique_pilot_batch.set_defaults(func=lambda args: cmd_dataset_build_lyric_technique_pilot_batch(root, args))

    materialize_lyric_technique_pilot_workspace = dataset_sub.add_parser(
        "materialize-lyric-technique-pilot-workspace",
        help="Copy a selected lyric grounding pilot subset into a separate small workspace.",
    )
    materialize_lyric_technique_pilot_workspace.add_argument("--project-root", type=Path, default=root)
    materialize_lyric_technique_pilot_workspace.add_argument("--source-workspace-root", type=Path)
    materialize_lyric_technique_pilot_workspace.add_argument("--pilot-manifest-path", type=Path)
    materialize_lyric_technique_pilot_workspace.add_argument("--output-root", type=Path)
    materialize_lyric_technique_pilot_workspace.set_defaults(func=lambda args: cmd_dataset_materialize_lyric_technique_pilot_workspace(root, args))

    run_lyric_technique_pilot_cycle = dataset_sub.add_parser(
        "run-lyric-technique-pilot-cycle",
        help="Run generation-profile build, grounding validation, grounded import, and joinability audit for a lyric technique pilot workspace.",
    )
    run_lyric_technique_pilot_cycle.add_argument("--project-root", type=Path, default=root)
    run_lyric_technique_pilot_cycle.add_argument("--corpus-root", type=Path)
    run_lyric_technique_pilot_cycle.add_argument("--workspace-root", type=Path)
    run_lyric_technique_pilot_cycle.add_argument("--generation-output-root", type=Path)
    run_lyric_technique_pilot_cycle.add_argument("--validation-output-root", type=Path)
    run_lyric_technique_pilot_cycle.add_argument("--import-output-root", type=Path)
    run_lyric_technique_pilot_cycle.add_argument("--joinability-output-root", type=Path)
    run_lyric_technique_pilot_cycle.set_defaults(func=lambda args: cmd_dataset_run_lyric_technique_pilot_cycle(root, args))

    report_vocadb_lyric_grounding_status = dataset_sub.add_parser(
        "report-vocadb-lyric-grounding-status",
        help="Summarize incoming, accepted, needs_patch, and rejected counts across lyric grounding pilot workspaces.",
    )
    report_vocadb_lyric_grounding_status.add_argument("--project-root", type=Path, default=root)
    report_vocadb_lyric_grounding_status.add_argument("--workspaces-root", type=Path)
    report_vocadb_lyric_grounding_status.add_argument("--output-root", type=Path)
    report_vocadb_lyric_grounding_status.set_defaults(func=lambda args: cmd_dataset_report_vocadb_lyric_grounding_status(root, args))

    auto_ground_vocadb_workspace = dataset_sub.add_parser(
        "auto-ground-vocadb-workspace",
        help="Apply a trusted lyric URL map to a VocaDB grounding workspace and auto-promote matching records to accepted.",
    )
    auto_ground_vocadb_workspace.add_argument("--project-root", type=Path, default=root)
    auto_ground_vocadb_workspace.add_argument("--workspace-root", type=Path)
    auto_ground_vocadb_workspace.add_argument("--url-map-path", type=Path, required=True)
    auto_ground_vocadb_workspace.set_defaults(func=lambda args: cmd_dataset_auto_ground_vocadb_workspace_from_url_map(root, args))

    report_parser = subparsers.add_parser("report", help="Report commands.")
    report_sub = report_parser.add_subparsers(dest="report_command", required=True)

    report_engine = report_sub.add_parser("engine-health", help="Build engine health report.")
    report_engine.add_argument("--project-root", type=Path, default=root)
    report_engine.add_argument(
        "--artists",
        nargs="+",
        default=["pinocchiop", "deco27", "kanaria", "kairiki_bear", "maretu", "iyowa", "syudou", "neru"],
    )
    report_engine.add_argument("--output-dir", type=Path)
    report_engine.set_defaults(func=lambda args: cmd_report_engine_health(root, args))

    report_baseline = report_sub.add_parser("baseline", help="Build baseline snapshot report.")
    report_baseline.add_argument("--project-root", type=Path, default=root)
    report_baseline.add_argument("--output-root", type=Path)
    report_baseline.set_defaults(func=lambda args: cmd_report_baseline(root, args))

    report_engine_state = report_sub.add_parser("engine-state", help="Build authoritative engine state with stale/conflict detection.")
    report_engine_state.add_argument("--project-root", type=Path, default=root)
    report_engine_state.add_argument("--output-root", type=Path)
    report_engine_state.set_defaults(func=lambda args: cmd_report_engine_state(root, args))

    report_sync_authoritative_wiki = report_sub.add_parser(
        "sync-authoritative-wiki",
        help="Rebuild wiki outputs from the authoritative readiness audit and canonical corpus.",
    )
    report_sync_authoritative_wiki.add_argument("--project-root", type=Path, default=root)
    report_sync_authoritative_wiki.add_argument("--output-root", type=Path)
    report_sync_authoritative_wiki.set_defaults(func=lambda args: cmd_report_sync_authoritative_wiki(root, args))

    report_sync_engine_surface = report_sub.add_parser(
        "sync-engine-surface",
        help="Refresh baseline, authoritative wiki, and engine state in one step.",
    )
    report_sync_engine_surface.add_argument("--project-root", type=Path, default=root)
    report_sync_engine_surface.add_argument("--output-root", type=Path)
    report_sync_engine_surface.set_defaults(func=lambda args: cmd_report_sync_engine_surface(root, args))

    test_parser = subparsers.add_parser("test", help="Run pytest from the repository root.")
    test_parser.add_argument("pytest_args", nargs="*", help="Additional pytest arguments.")
    test_parser.set_defaults(func=lambda args: cmd_test(root, args))

    return parser


def main(root: Path) -> int:
    parser = build_parser(root)
    args = parser.parse_args()
    return args.func(args)
