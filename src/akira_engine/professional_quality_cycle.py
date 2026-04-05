from __future__ import annotations

from pathlib import Path
from typing import Any

from .generation_readiness_audit import audit_generation_readiness
from .sound_profile_review import auto_accept_inferred_sound_profiles, import_reviewed_sound_profiles
from .suno_prompt_asset_export import export_suno_prompt_assets
from .training_data import write_json


def run_professional_quality_cycle(
    *,
    generation_root: Path,
    sound_review_workspace: Path,
    reviewed_generation_root: Path,
    readiness_output_root: Path,
    prompt_asset_output_root: Path,
) -> dict[str, Any]:
    generation_root = generation_root.resolve()
    sound_review_workspace = sound_review_workspace.resolve()
    reviewed_generation_root = reviewed_generation_root.resolve()
    readiness_output_root = readiness_output_root.resolve()
    prompt_asset_output_root = prompt_asset_output_root.resolve()

    bootstrap_manifest = auto_accept_inferred_sound_profiles(
        workspace_root=sound_review_workspace,
    )
    import_manifest = import_reviewed_sound_profiles(
        generation_root=generation_root,
        workspace_root=sound_review_workspace,
        output_root=reviewed_generation_root,
    )
    readiness_manifest = audit_generation_readiness(
        generation_root=reviewed_generation_root,
        output_root=readiness_output_root,
    )
    prompt_asset_manifest = export_suno_prompt_assets(
        generation_root=reviewed_generation_root,
        output_root=prompt_asset_output_root,
        include_blocked=True,
    )

    manifest = {
        "schema_version": "1.0",
        "record_type": "professional_quality_cycle_manifest",
        "generation_root": str(generation_root),
        "sound_review_workspace": str(sound_review_workspace),
        "reviewed_generation_root": str(reviewed_generation_root),
        "readiness_output_root": str(readiness_output_root),
        "prompt_asset_output_root": str(prompt_asset_output_root),
        "counts": {
            "bootstrapped_reviews": bootstrap_manifest["counts"]["accepted"],
            "reviewed_tracks_applied": import_manifest["counts"]["reviewed_tracks_applied"],
            "joinable": readiness_manifest["counts"]["joinable"],
            "prompt_ready": readiness_manifest["counts"]["prompt_ready"],
            "production_candidate": readiness_manifest["counts"]["production_candidate"],
            "professional_target": readiness_manifest["counts"]["professional_target"],
            "prompt_assets": prompt_asset_manifest["counts"]["assets"],
        },
        "outputs": {
            "bootstrap_manifest": bootstrap_manifest["manifest_path"],
            "import_manifest": import_manifest["manifest_path"],
            "readiness_manifest": readiness_manifest["manifest_path"],
            "prompt_asset_manifest": prompt_asset_manifest["manifest_path"],
        },
    }
    manifest_path = write_json(reviewed_generation_root / "professional_quality_cycle_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest
