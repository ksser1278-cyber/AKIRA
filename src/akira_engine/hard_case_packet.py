from __future__ import annotations

from pathlib import Path

from .hard_case import load_json
from .reporting import write_utf8_text


def build_hard_case_packet(project_root: Path, artist_id: str) -> str:
    registry = load_json(project_root / "data" / "_global" / "hard_case_registry.json")
    artist_block = next((item for item in registry.get("artists", []) if str(item.get("artist_id", "")).strip() == artist_id), {})
    tracks = artist_block.get("tracks", [])
    lines = [
        f"# Hard Case Packet: {artist_id}",
        "",
        "## Purpose",
        "Track-specific hard cases that still block clean benchmark quality.",
        "",
        "## Focus",
        "- Diagnose why current candidates still miss the target.",
        "- Keep fixes narrow and avoid broad bank rewrites that break the baseline.",
        "",
        "## Tracks",
        "",
    ]
    for item in tracks:
        lines.append(
            f"- `{item['track_id']}` / score `{item['score']}` / issues: {'; '.join(item.get('issues', []))}"
        )
    lines.append("")
    return "\n".join(lines)


def write_hard_case_packet(project_root: Path, artist_id: str) -> Path:
    handoff_dir = project_root / "data" / "_global" / "hard_case" / artist_id
    handoff_dir.mkdir(parents=True, exist_ok=True)
    packet_path = handoff_dir / "packet.md"
    write_utf8_text(packet_path, build_hard_case_packet(project_root, artist_id))
    return packet_path
