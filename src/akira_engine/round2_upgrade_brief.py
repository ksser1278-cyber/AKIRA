from __future__ import annotations

from pathlib import Path

from .manifest_tools import load_json
from .reporting import write_utf8_text


def build_round2_upgrade_brief(project_root: Path, artist_id: str) -> str:
    queue_path = project_root / "data" / artist_id / "reference_tracks" / "round2_queue.json"
    audit_path = project_root / "reports" / "quality" / "round2_expansion_audit" / f"{artist_id}_round2_audit.json"
    queue = load_json(queue_path)
    audit = load_json(audit_path)
    weak_records = {
        str(item.get("track_id", "")).strip(): item
        for item in audit.get("records", [])
        if str(item.get("grade", "")).strip() == "weak"
    }

    lines = [
        f"# Round2 Upgrade Brief: {artist_id}",
        "",
        "## Goal",
        "Upgrade scaffolded round2 conditioning records from weak to usable or gold without changing their intended mode or track identity.",
        "",
        "## Required Fixes",
        "",
        "- Add lyric_sources and metadata_sources with confirmed/cross_checked status.",
        "- Upgrade partial lyric grounding to full when possible.",
        "- Fill song_intent.contrast_device.",
        "- Expand section evidence enough to justify ready_for_prompting = true.",
        "- Keep title, likely_mode, and seed direction aligned with the existing scaffold.",
        "",
        "## Target Tracks",
        "",
    ]
    for item in queue.get("queue", []):
        if str(item.get("status", "")).strip() != "scaffolded":
            continue
        track_id = str(item.get("track_id", "")).strip()
        audit_item = weak_records.get(track_id, {})
        blockers = "; ".join(str(value).strip() for value in audit_item.get("blockers", []) if str(value).strip()) or "none"
        lines.extend(
            [
                f"### {track_id}",
                f"- likely_mode: `{item.get('likely_mode', '')}`",
                f"- priority: `{item.get('priority_label', '')}`",
                f"- blockers: {blockers}",
                "",
            ]
        )
    return "\n".join(lines)


def write_round2_upgrade_brief(project_root: Path, artist_id: str) -> Path:
    out_dir = project_root / "data" / "_global" / "round2_expansion" / artist_id
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "upgrade_brief.md"
    write_utf8_text(path, build_round2_upgrade_brief(project_root, artist_id))
    return path
