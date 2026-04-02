from __future__ import annotations

from pathlib import Path
from typing import Any

from .manifest_tools import load_json
from .reporting import write_utf8_text


def build_producer_expansion_brief(project_root: Path, artist_id: str) -> dict[str, Any]:
    handoff = load_json(project_root / "data" / "_global" / "external_handoff" / artist_id / "producer_expansion" / "handoff_manifest.json")
    audit = load_json(project_root / "reports" / "quality" / "conditioning" / f"{artist_id}_producer_expansion_audit.json")

    audit_lookup = {
        str(item.get("track_id", "")).strip(): item
        for item in audit.get("records", [])
        if str(item.get("track_id", "")).strip()
    }

    tracks: list[dict[str, Any]] = []
    for item in handoff.get("tracks", []):
        track_id = str(item.get("track_id", "")).strip()
        audit_item = audit_lookup.get(track_id, {})
        score = int(audit_item.get("score", 0))
        priority = "high" if score < 50 else ("medium" if score < 75 else "low")
        blockers = [str(x).strip() for x in audit_item.get("blockers", []) if str(x).strip()]
        warnings = [str(x).strip() for x in audit_item.get("warnings", []) if str(x).strip()]
        tracks.append(
            {
                "track_id": track_id,
                "target_path": item.get("target_path", ""),
                "priority": priority,
                "score": score,
                "full_text_status": item.get("full_text_status", ""),
                "required_external_work": item.get("required_external_work", []),
                "blockers": blockers,
                "warnings": warnings,
            }
        )

    tracks.sort(key=lambda item: ({"high": 0, "medium": 1, "low": 2}.get(item["priority"], 9), item["score"], item["track_id"]))
    return {
        "artist_id": artist_id,
        "track_count": len(tracks),
        "tracks": tracks,
    }


def render_producer_expansion_brief(payload: dict[str, Any]) -> str:
    lines = [
        f"# Producer Expansion Delegation Brief: {payload['artist_id']}",
        "",
        "## Scope",
        "- Task type: conditioning promotion from scaffolded/weak to usable or gold candidate",
        "- Required work: full lyric grounding, provenance, hook extraction, section analysis, prompt conditioning completion, optional audio enrichment",
        "",
        "## Track Priority",
        "",
    ]
    for item in payload.get("tracks", []):
        lines.append(f"### {item['track_id']}")
        lines.append(f"- Priority: `{item['priority']}`")
        lines.append(f"- Current score: `{item['score']}`")
        lines.append(f"- Current full_text_status: `{item['full_text_status']}`")
        lines.append(f"- Target: `{item['target_path']}`")
        lines.append(f"- Required work: {', '.join(item.get('required_external_work', []))}")
        lines.append(f"- Blockers: {'; '.join(item.get('blockers', [])) if item.get('blockers') else 'none'}")
        lines.append(f"- Warnings: {'; '.join(item.get('warnings', [])) if item.get('warnings') else 'none'}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_producer_expansion_brief(project_root: Path, artist_id: str) -> Path:
    payload = build_producer_expansion_brief(project_root, artist_id)
    output_path = project_root / "data" / "_global" / "external_handoff" / artist_id / "producer_expansion" / "delegation_brief.md"
    write_utf8_text(output_path, render_producer_expansion_brief(payload))
    return output_path
