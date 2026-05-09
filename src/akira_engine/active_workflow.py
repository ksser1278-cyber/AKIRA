from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0"
DEFAULT_CONFIG_PATH = Path("config") / "active_workflow.json"
DEFAULT_OUTPUT_ROOT = Path("reports") / "planning" / "active_workflow_validation"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")
    return path


def _resolve(project_root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (project_root / path).resolve()


def _validate_path_entry(project_root: Path, entry: dict[str, Any]) -> tuple[list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []
    path_value = str(entry.get("path", "")).strip()
    expected_type = str(entry.get("type", "any")).strip().lower() or "any"
    required = bool(entry.get("required", True))
    resolved = _resolve(project_root, path_value) if path_value else project_root

    if not path_value:
        errors.append("required_paths entry is missing path")
    elif not resolved.exists():
        message = f"missing path: {path_value}"
        if required:
            errors.append(message)
        else:
            warnings.append(message)
    elif expected_type == "file" and not resolved.is_file():
        errors.append(f"path is not a file: {path_value}")
    elif expected_type == "dir" and not resolved.is_dir():
        errors.append(f"path is not a directory: {path_value}")
    elif expected_type not in {"any", "file", "dir"}:
        warnings.append(f"unknown path type '{expected_type}' for {path_value}")

    return errors, warnings, {
        "path": path_value,
        "resolved_path": str(resolved),
        "type": expected_type,
        "required": required,
        "exists": resolved.exists(),
    }


def _collect_state_warnings(project_root: Path, workflow: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    warnings: list[str] = []
    snapshot: dict[str, Any] = {}
    targets = workflow.get("quality_targets", {}) if isinstance(workflow.get("quality_targets"), dict) else {}

    artifacts = workflow.get("authoritative_artifacts", {})
    engine_state_path = artifacts.get("engine_state")
    if engine_state_path:
        resolved = _resolve(project_root, str(engine_state_path))
        if resolved.exists():
            state = _load_json(resolved)
            counts = state.get("counts", {}) if isinstance(state.get("counts"), dict) else {}
            snapshot["engine_state_counts"] = counts
            prompt_ready = int(counts.get("readiness_prompt_ready", 0) or 0)
            min_prompt_ready = int(targets.get("minimum_prompt_ready_tracks", 0) or 0)
            if min_prompt_ready and prompt_ready < min_prompt_ready:
                warnings.append(
                    f"prompt-ready track count is {prompt_ready}, below target {min_prompt_ready}"
                )

            accepted = int(counts.get("grounding_total_accepted", 0) or 0)
            min_grounded = int(targets.get("minimum_grounded_accepted_tracks", 0) or 0)
            if min_grounded and accepted < min_grounded:
                warnings.append(
                    f"grounded accepted track count is {accepted}, below target {min_grounded}"
                )

            stale = state.get("stale_or_conflicting_state", [])
            if stale:
                warnings.append(f"engine state reports stale/conflicting entries: {len(stale)}")

    history_path = artifacts.get("recent_winner_history")
    if history_path:
        resolved = _resolve(project_root, str(history_path))
        if resolved.exists():
            history = _load_json(resolved)
            entries = [entry for entry in history.get("entries", []) if isinstance(entry, dict)]
            snapshot["recent_winner_count"] = len(entries)
            if entries:
                latest = entries[0]
                latest_score = float(latest.get("selected_score", 0.0) or 0.0)
                snapshot["latest_winner"] = {
                    "artist_id": latest.get("artist_id"),
                    "mode_id": latest.get("mode_id"),
                    "proposition_id": latest.get("proposition_id"),
                    "core_phrase": latest.get("core_phrase"),
                    "form_family_id": latest.get("form_family_id"),
                    "selected_score": latest_score,
                }
                min_demo_score = float(targets.get("minimum_demo_blended_total", 0.0) or 0.0)
                if min_demo_score and latest_score < min_demo_score:
                    warnings.append(
                        f"latest winner score is {latest_score}, below target {min_demo_score}"
                    )

                window_size = int(targets.get("recent_winner_repeat_window", 20) or 20)
                max_ratio = float(targets.get("maximum_recent_winner_signature_ratio", 0.0) or 0.0)
                window = entries[:window_size]
                signatures = [
                    "|".join(
                        str(entry.get(key, "") or "")
                        for key in ("artist_id", "mode_id", "proposition_id", "core_phrase", "form_family_id")
                    )
                    for entry in window
                ]
                counts = Counter(signature for signature in signatures if signature.strip("|"))
                if counts and max_ratio:
                    signature, count = counts.most_common(1)[0]
                    ratio = count / len(window)
                    snapshot["recent_winner_repeat"] = {
                        "signature": signature,
                        "count": count,
                        "window_size": len(window),
                        "ratio": round(ratio, 3),
                    }
                    if ratio > max_ratio:
                        warnings.append(
                            f"recent winner repeat ratio is {ratio:.2f}, above target {max_ratio:.2f}"
                        )

    return warnings, snapshot


def _collect_diversity_warnings(workflow: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    active_engine = workflow.get("active_engine", {}) if isinstance(workflow.get("active_engine"), dict) else {}
    targets = workflow.get("diversity_targets", {}) if isinstance(workflow.get("diversity_targets"), dict) else {}

    mode_ids = list(active_engine.get("mode_ids", []))
    form_families = list(active_engine.get("form_families_current", []))
    proposition_families = list(active_engine.get("proposition_archetypes_current", []))
    candidate_max = int(active_engine.get("candidate_count_max_current", 0) or 0)

    min_modes = int(targets.get("minimum_active_modes", 0) or 0)
    min_forms = int(targets.get("minimum_form_families", 0) or 0)
    min_props = int(targets.get("minimum_proposition_families", 0) or 0)
    min_candidates = int(targets.get("minimum_candidate_count_max", 0) or 0)

    if min_modes and len(mode_ids) < min_modes:
        warnings.append(f"active mode count is {len(mode_ids)}, below target {min_modes}")
    if min_forms and len(form_families) < min_forms:
        warnings.append(f"active form family count is {len(form_families)}, below target {min_forms}")
    if min_props and len(proposition_families) < min_props:
        warnings.append(f"active proposition family count is {len(proposition_families)}, below target {min_props}")
    if min_candidates and candidate_max < min_candidates:
        warnings.append(f"candidate max is {candidate_max}, below target {min_candidates}")

    return warnings


def _render_validation_report(result: dict[str, Any]) -> str:
    lines = [
        "# Active Workflow Validation",
        "",
        f"- Workflow: `{result.get('workflow_id', '')}`",
        f"- OK: `{result.get('ok')}`",
        f"- Config: `{result.get('config_path', '')}`",
        f"- Checked paths: `{result.get('checked_path_count', 0)}`",
        f"- Errors: `{len(result.get('errors', []))}`",
        f"- Warnings: `{len(result.get('warnings', []))}`",
        "",
        "## Errors",
    ]
    errors = result.get("errors", [])
    lines.extend([f"- {item}" for item in errors] if errors else ["- none"])
    lines.extend(["", "## Warnings"])
    warnings = result.get("warnings", [])
    lines.extend([f"- {item}" for item in warnings] if warnings else ["- none"])
    lines.extend(["", "## Remediation Backlog"])
    backlog = result.get("remediation_backlog", [])
    if backlog:
        for item in backlog:
            lines.extend(
                [
                    f"### {item.get('priority', '')} {item.get('id', '')}",
                    f"- Area: `{item.get('area', '')}`",
                    f"- Problem: {item.get('problem', '')}",
                    f"- Next action: {item.get('next_action', '')}",
                    "",
                ]
            )
    else:
        lines.append("- none")
    lines.extend(["", "## Interpretation"])
    lines.append(
        "A clean validation means the active workflow contract is internally reachable. "
        "Warnings mark quality-loop weaknesses that can still make generations repetitive or underdeveloped."
    )
    return "\n".join(lines)


def _backlog_item(item_id: str, priority: str, area: str, problem: str, next_action: str) -> dict[str, str]:
    return {
        "id": item_id,
        "priority": priority,
        "area": area,
        "problem": problem,
        "next_action": next_action,
    }


def _build_remediation_backlog(errors: list[str], warnings: list[str]) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []

    for error in errors:
        items.append(
            _backlog_item(
                "workflow_contract_error",
                "P0",
                "workflow",
                error,
                "Fix the active workflow config or required file path before running generation work.",
            )
        )

    warning_rules: list[tuple[str, dict[str, str]]] = [
        (
            "active mode count",
            _backlog_item(
                "expand_active_modes",
                "P0",
                "generation_diversity",
                "The active engine is effectively routing through too few mode profiles.",
                "Wire at least two more mode profiles into the proposition engine and add validation fixtures for each.",
            ),
        ),
        (
            "active form family count",
            _backlog_item(
                "expand_form_families",
                "P0",
                "song_form",
                "The active form set is too narrow to avoid repeated song shapes.",
                "Add at least two form families with distinct section order, line targets, pressure transitions, and regression examples.",
            ),
        ),
        (
            "active proposition family count",
            _backlog_item(
                "expand_proposition_families",
                "P0",
                "song_concept",
                "The proposition set is too small, so topics and hooks converge.",
                "Expand proposition archetypes to at least eight and derive their selection from corpus signal clusters, not fixed order only.",
            ),
        ),
        (
            "candidate max",
            _backlog_item(
                "increase_candidate_search",
                "P1",
                "selection",
                "The candidate search space is too small for meaningful novelty pressure.",
                "Raise candidate max after adding dedupe and repeat-pressure gates so the engine explores more without selecting near-clones.",
            ),
        ),
        (
            "prompt-ready track count",
            _backlog_item(
                "increase_prompt_ready_lane",
                "P1",
                "data_quality",
                "The prompt-ready quality lane is too small compared with corpus scale.",
                "Promote enough joined generation records to reach the prompt-ready target before treating corpus scale as useful signal.",
            ),
        ),
        (
            "grounded accepted track count",
            _backlog_item(
                "increase_grounded_accepts",
                "P1",
                "data_grounding",
                "Grounded accepted lyric-technique records are below the active target.",
                "Accept or patch the smallest high-value grounding batch needed to cross the target, then rerun readiness.",
            ),
        ),
        (
            "latest winner score",
            _backlog_item(
                "block_low_scoring_winners",
                "P0",
                "quality_gate",
                "The latest selected winner is below the quality target.",
                "Treat the run as non-promotable and inspect its critic diagnostics before changing renderer behavior.",
            ),
        ),
        (
            "recent winner repeat ratio",
            _backlog_item(
                "stop_winner_convergence",
                "P0",
                "anti_convergence",
                "Recent winners repeat the same artist/mode/proposition/core/form signature too often.",
                "Add stronger repeat penalties or a hard stop when the recent winner signature ratio exceeds the threshold.",
            ),
        ),
    ]

    seen_ids: set[str] = set()
    for warning in warnings:
        for marker, item in warning_rules:
            if marker in warning and item["id"] not in seen_ids:
                items.append(item)
                seen_ids.add(item["id"])

    priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    return sorted(items, key=lambda item: (priority_order.get(item["priority"], 9), item["id"]))


def validate_active_workflow(
    project_root: Path,
    *,
    config_path: Path | None = None,
    output_root: Path | None = None,
    write: bool = True,
) -> dict[str, Any]:
    final_root = project_root.resolve()
    final_config_path = _resolve(final_root, config_path or DEFAULT_CONFIG_PATH)
    final_output_root = _resolve(final_root, output_root or DEFAULT_OUTPUT_ROOT)

    errors: list[str] = []
    warnings: list[str] = []
    checked_paths: list[dict[str, Any]] = []

    if not final_config_path.exists():
        result = {
            "schema_version": SCHEMA_VERSION,
            "workflow_id": "",
            "ok": False,
            "project_root": str(final_root),
            "config_path": str(final_config_path),
            "checked_path_count": 0,
            "checked_paths": [],
            "errors": [f"active workflow config not found: {final_config_path}"],
            "warnings": [],
            "state_snapshot": {},
        }
        return result

    workflow = _load_json(final_config_path)
    workflow_id = str(workflow.get("workflow_id", "")).strip()
    if workflow.get("schema_version") != SCHEMA_VERSION:
        warnings.append(
            f"schema_version is {workflow.get('schema_version')!r}, expected {SCHEMA_VERSION!r}"
        )
    if not workflow_id:
        errors.append("workflow_id is required")
    if not workflow.get("workflow_order"):
        errors.append("workflow_order must not be empty")

    for entry in workflow.get("required_paths", []):
        if not isinstance(entry, dict):
            errors.append("required_paths entries must be objects")
            continue
        entry_errors, entry_warnings, checked = _validate_path_entry(final_root, entry)
        errors.extend(entry_errors)
        warnings.extend(entry_warnings)
        checked_paths.append(checked)

    warnings.extend(_collect_diversity_warnings(workflow))
    state_warnings, state_snapshot = _collect_state_warnings(final_root, workflow)
    warnings.extend(state_warnings)
    remediation_backlog = _build_remediation_backlog(errors, warnings)

    result = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "active_workflow_validation",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "workflow_id": workflow_id,
        "ok": not errors,
        "project_root": str(final_root),
        "config_path": str(final_config_path),
        "output_root": str(final_output_root),
        "checked_path_count": len(checked_paths),
        "checked_paths": checked_paths,
        "errors": errors,
        "warnings": warnings,
        "remediation_backlog": remediation_backlog,
        "state_snapshot": state_snapshot,
    }

    if write:
        json_path = _write_json(final_output_root / "active_workflow_validation.json", result)
        md_path = _write_text(final_output_root / "active_workflow_validation.md", _render_validation_report(result))
        result["json_path"] = str(json_path)
        result["md_path"] = str(md_path)

    return result
