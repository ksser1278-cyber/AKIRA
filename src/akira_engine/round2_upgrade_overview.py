from __future__ import annotations

from pathlib import Path
from typing import Any

from .manifest_tools import load_json


def build_round2_upgrade_overview(project_root: Path) -> dict[str, Any]:
    registry = load_json(project_root / "data" / "_global" / "round2_expansion" / "registry.json")
    rows: list[dict[str, Any]] = []
    for artist in registry.get("artists", []):
        artist_id = str(artist.get("artist_id", "")).strip()
        if not artist_id:
            continue
        queue = load_json(project_root / "data" / artist_id / "reference_tracks" / "round2_queue.json")
        audit_path = project_root / "reports" / "quality" / "round2_expansion_audit" / f"{artist_id}_round2_audit.json"
        audit = load_json(audit_path) if audit_path.exists() else {}
        audit_lookup = {
            str(item.get("track_id", "")).strip(): item
            for item in audit.get("records", [])
            if str(item.get("track_id", "")).strip()
        }
        for item in queue.get("queue", []):
            status = str(item.get("status", "")).strip()
            if status != "scaffolded":
                continue
            track_id = str(item.get("track_id", "")).strip()
            audit_item = audit_lookup.get(track_id, {})
            metrics = audit_item.get("metrics", {})
            blockers = [str(value).strip() for value in audit_item.get("blockers", []) if str(value).strip()]
            warnings = [str(value).strip() for value in audit_item.get("warnings", []) if str(value).strip()]
            priority_label = str(item.get("priority_label", "")).strip() or "medium"
            priority_rank = {"high": 0, "medium": 1, "low": 2}.get(priority_label, 3)
            rows.append(
                {
                    "artist_id": artist_id,
                    "track_id": track_id,
                    "likely_mode": str(item.get("likely_mode", "")).strip(),
                    "priority_label": priority_label,
                    "priority_rank": priority_rank,
                    "score": float(audit_item.get("score", 0.0) or 0.0),
                    "full_text_status": str(metrics.get("full_text_status", "")).strip(),
                    "trusted_ratio": float(metrics.get("trusted_ratio", 0.0) or 0.0),
                    "hook_line_count": int(metrics.get("hook_line_count", 0) or 0),
                    "prompt_anchor_count": int(metrics.get("prompt_anchor_count", 0) or 0),
                    "blockers": blockers,
                    "warnings": warnings,
                }
            )
    rows.sort(
        key=lambda item: (
            item["priority_rank"],
            item["trusted_ratio"],
            item["score"],
            item["artist_id"],
            item["track_id"],
        )
    )
    return {
        "schema_version": "1.0",
        "record_type": "round2_upgrade_overview",
        "weak_track_count": len(rows),
        "artists": sorted({row["artist_id"] for row in rows}),
        "tracks": rows,
    }


def render_round2_upgrade_overview_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Round2 Upgrade Overview",
        "",
        f"- weak scaffold tracks `{payload.get('weak_track_count', 0)}`",
        f"- artists `{len(payload.get('artists', []))}`",
        "",
        "## Priority Queue",
        "",
    ]
    for item in payload.get("tracks", []):
        blockers = "; ".join(item.get("blockers", [])) or "none"
        warnings = "; ".join(item.get("warnings", [])) or "none"
        lines.extend(
            [
                f"### {item['track_id']}",
                f"- artist `{item['artist_id']}` / mode `{item['likely_mode']}` / priority `{item['priority_label']}`",
                f"- score `{item['score']}` / full_text_status `{item['full_text_status']}` / trusted_ratio `{item['trusted_ratio']}`",
                f"- hook_lines `{item['hook_line_count']}` / prompt anchors `{item['prompt_anchor_count']}`",
                f"- blockers: {blockers}",
                f"- warnings: {warnings}",
                "",
            ]
        )
    return "\n".join(lines)
