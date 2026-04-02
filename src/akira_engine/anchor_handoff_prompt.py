from __future__ import annotations

from pathlib import Path

from .manifest_tools import load_json
from .reporting import write_utf8_text


def build_anchor_handoff_prompt(project_root: Path, artist_id: str) -> str:
    handoff = load_json(project_root / "data" / "_global" / "external_handoff" / artist_id / "handoff_manifest.json")
    audit = load_json(project_root / "reports" / "quality" / "conditioning" / f"{artist_id}_conditioning_audit_active.json")
    audit_lookup = {
        str(item.get("track_id", "")).strip(): item
        for item in audit.get("records", [])
        if str(item.get("track_id", "")).strip()
    }

    lines = [
        f"This is an anchor conditioning maintenance task for `{artist_id}`.",
        "",
        "Goal:",
        "- Keep active anchor conditioning records at gold quality.",
        "- Strengthen provenance, section detail, and audio-linked notes without changing the existing schema.",
        "- This is dataset maintenance, not songwriting.",
        "",
        "Rules:",
        "- Keep `lyric_ground_truth.full_text_status` at `full` when justified by the returned data.",
        "- Preserve the existing track identity and track_id.",
        "- Distinguish `confirmed`, `cross_checked`, `estimated`, and `inferred`.",
        "- Do not weaken provenance or remove existing grounded sections.",
        "- Return JSON only.",
        "",
        "Output directory:",
        f"- `C:\\JPop_Songwriter\\AKIRA ENGINE\\data\\_global\\external_handoff\\{artist_id}\\incoming`",
        "",
        "Target tracks:",
    ]

    for item in handoff.get("tracks", []):
        track_id = str(item.get("track_id", "")).strip()
        audit_item = audit_lookup.get(track_id, {})
        warnings = [str(x).strip() for x in audit_item.get("warnings", []) if str(x).strip()]
        lines.append(f"- `{track_id}`")
        lines.append(f"  current score: `{audit_item.get('score', 0)}`")
        lines.append(f"  current full_text_status: `{item.get('full_text_status', '')}`")
        lines.append(f"  target file: `{item.get('target_path', '')}`")
        lines.append(f"  required work: {', '.join(item.get('required_external_work', []))}")
        lines.append(f"  warnings: {'; '.join(warnings) if warnings else 'none'}")
        lines.append("")

    lines.extend(
        [
            "Required output format:",
            "- One JSON file per track",
            "- Include `track_identity.track_id`",
            "- Return either a complete replacement JSON or a merge-friendly JSON payload",
            "",
        ]
    )
    return "\n".join(lines)


def write_anchor_handoff_prompt(project_root: Path, artist_id: str) -> Path:
    prompt = build_anchor_handoff_prompt(project_root, artist_id)
    output_path = project_root / "data" / "_global" / "external_handoff" / artist_id / "delegation_prompt.txt"
    write_utf8_text(output_path, prompt)
    return output_path
