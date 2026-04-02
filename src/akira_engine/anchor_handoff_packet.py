from __future__ import annotations

from pathlib import Path

from .manifest_tools import load_json
from .reporting import write_utf8_text


def build_anchor_handoff_packet(project_root: Path, artist_id: str) -> str:
    handoff_dir = project_root / "data" / "_global" / "external_handoff" / artist_id
    prompt_text = (handoff_dir / "delegation_prompt.txt").read_text(encoding="utf-8")
    handoff_md = (handoff_dir / "handoff_manifest.md").read_text(encoding="utf-8")
    audit = load_json(project_root / "reports" / "quality" / "conditioning" / f"{artist_id}_conditioning_audit_active.json")

    lines = [
        f"# Anchor Handoff Packet: {artist_id}",
        "",
        "## Purpose",
        "This packet is the single handoff unit for active anchor conditioning maintenance.",
        "",
        "## Delivery Prompt",
        "",
        "```text",
        prompt_text.rstrip(),
        "```",
        "",
        "## Current Audit Summary",
        "",
        f"- Records: `{audit.get('record_count', 0)}`",
        f"- Gold: `{audit.get('gold_count', 0)}`",
        f"- Usable: `{audit.get('usable_count', 0)}`",
        f"- Weak: `{audit.get('weak_count', 0)}`",
        f"- Average score: `{audit.get('average_score', 0.0)}`",
        "",
        "## Handoff Manifest",
        "",
        handoff_md.rstrip(),
        "",
        "## Incoming Directory",
        "",
        f"- `{handoff_dir / 'incoming'}`",
        "",
        "## After Return",
        "",
        "```powershell",
        f"python C:\\JPop_Songwriter\\AKIRA ENGINE\\scripts\\pipeline\\run_anchor_external_roundtrip.py --artist-id {artist_id} --input-dir \"{handoff_dir / 'incoming'}\" --project-root \"C:\\JPop_Songwriter\\AKIRA ENGINE\" --backup",
        "```",
        "",
    ]
    return "\n".join(lines)


def write_anchor_handoff_packet(project_root: Path, artist_id: str) -> Path:
    output_path = project_root / "data" / "_global" / "external_handoff" / artist_id / "packet.md"
    write_utf8_text(output_path, build_anchor_handoff_packet(project_root, artist_id))
    return output_path
