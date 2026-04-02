from __future__ import annotations

from pathlib import Path

from .mode_support_brief import build_mode_support_brief, write_mode_support_brief
from .mode_support import load_json
from .reporting import write_utf8_text


def build_mode_support_prompt(project_root: Path, mode_id: str) -> str:
    queue_path = project_root / "data" / "_global" / "mode_support" / mode_id / "queue.json"
    queue = load_json(queue_path)
    lines = [
        f"This is a mode support curation task for `{mode_id}`.",
        "",
        "Goal:",
        "- Curate support tracks for each listed artist that match this mode.",
        "- Do not create conditioning JSON yet.",
        "- Return only candidate track ids, titles, and short justification atoms.",
        "",
        "Rules:",
        "- Avoid duplicating current gold anchors and active producer expansion tracks.",
        "- Prefer tracks that diversify hook shape, section behavior, and lyrical framing.",
        "- Keep the output structured and mode-focused.",
        "",
        "Per-artist targets:",
    ]
    for item in queue.get("queue", []):
        lines.append(f"- `{item['artist_id']}` / target `{item['target_track_count']}`")
    lines.extend(
        [
            "",
            "Required output format:",
            "- One JSON file per mode",
            "- Include `mode_id` and an `artist_candidates` array",
            "- Each artist entry should include `artist_id`, `candidate_track_ids`, `candidate_titles`, and `notes`",
            "",
        ]
    )
    return "\n".join(lines)


def build_mode_support_packet(project_root: Path, mode_id: str) -> str:
    queue_path = project_root / "data" / "_global" / "mode_support" / mode_id / "queue.json"
    queue = load_json(queue_path)
    prompt = build_mode_support_prompt(project_root, mode_id)
    brief = build_mode_support_brief(project_root, mode_id)
    lines = [
        f"# Mode Support Packet: {mode_id}",
        "",
        "## Purpose",
        "This packet is the single handoff unit for cross-producer mode support curation.",
        "",
        "## Delivery Prompt",
        "",
        "```text",
        prompt.rstrip(),
        "```",
        "",
        "## Working Notes",
        "",
        brief.rstrip(),
        "",
        "## Current Queue",
        "",
        f"- Target count: `{queue.get('target_count', 0)}`",
        f"- Support artists: `{', '.join(queue.get('support_artists', []))}`",
        "",
    ]
    for item in queue.get("queue", []):
        lines.append(f"- `{item['artist_id']}` / status `{item['status']}` / target `{item['target_track_count']}`")
    lines.extend(
        [
            "",
            "## Incoming Directory",
            "",
            f"- `{project_root / 'data' / '_global' / 'mode_support' / mode_id / 'external_handoff' / 'incoming'}`",
            "",
        ]
    )
    return "\n".join(lines)


def write_mode_support_packet(project_root: Path, mode_id: str) -> tuple[Path, Path]:
    handoff_dir = project_root / "data" / "_global" / "mode_support" / mode_id / "external_handoff"
    handoff_dir.mkdir(parents=True, exist_ok=True)
    incoming_dir = handoff_dir / "incoming"
    incoming_dir.mkdir(parents=True, exist_ok=True)

    write_mode_support_brief(project_root, mode_id)
    prompt_path = handoff_dir / "delegation_prompt.txt"
    packet_path = handoff_dir / "packet.md"
    write_utf8_text(prompt_path, build_mode_support_prompt(project_root, mode_id))
    write_utf8_text(packet_path, build_mode_support_packet(project_root, mode_id))
    return prompt_path, packet_path
