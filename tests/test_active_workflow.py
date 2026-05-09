from __future__ import annotations

import json
from pathlib import Path

from src.akira_engine.active_workflow import validate_active_workflow


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_validate_active_workflow_minimal_ok(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# test\n", encoding="utf-8")
    config = {
        "schema_version": "1.0",
        "workflow_id": "test_workflow",
        "workflow_order": [{"stage": "validate"}],
        "required_paths": [
            {"path": "README.md", "type": "file"},
        ],
    }
    config_path = tmp_path / "config" / "active_workflow.json"
    write_json(config_path, config)

    result = validate_active_workflow(tmp_path, config_path=config_path, write=False)

    assert result["ok"] is True
    assert result["errors"] == []
    assert result["checked_path_count"] == 1


def test_validate_active_workflow_missing_required_path(tmp_path: Path) -> None:
    config = {
        "schema_version": "1.0",
        "workflow_id": "test_workflow",
        "workflow_order": [{"stage": "validate"}],
        "required_paths": [
            {"path": "missing.json", "type": "file"},
        ],
    }
    config_path = tmp_path / "config" / "active_workflow.json"
    write_json(config_path, config)

    result = validate_active_workflow(tmp_path, config_path=config_path, write=False)

    assert result["ok"] is False
    assert "missing path: missing.json" in result["errors"]
    assert result["remediation_backlog"][0]["priority"] == "P0"


def test_validate_active_workflow_builds_diversity_backlog(tmp_path: Path) -> None:
    config = {
        "schema_version": "1.0",
        "workflow_id": "test_workflow",
        "workflow_order": [{"stage": "validate"}],
        "active_engine": {
            "mode_ids": ["dark_cute_breakdown"],
            "form_families_current": ["compressed_hook"],
            "proposition_archetypes_current": ["obsessive_return"],
            "candidate_count_max_current": 2,
        },
        "diversity_targets": {
            "minimum_active_modes": 3,
            "minimum_form_families": 2,
            "minimum_proposition_families": 4,
            "minimum_candidate_count_max": 8,
        },
        "required_paths": [],
    }
    config_path = tmp_path / "config" / "active_workflow.json"
    write_json(config_path, config)

    result = validate_active_workflow(tmp_path, config_path=config_path, write=False)

    backlog_ids = {item["id"] for item in result["remediation_backlog"]}
    assert "expand_active_modes" in backlog_ids
    assert "expand_proposition_families" in backlog_ids
    assert "increase_candidate_search" in backlog_ids
