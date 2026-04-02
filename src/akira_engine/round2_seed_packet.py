from __future__ import annotations

from pathlib import Path

from .manifest_tools import load_json
from .reporting import write_utf8_text


def build_round2_seed_packet(project_root: Path, artist_id: str) -> str:
    queue_path = project_root / "data" / artist_id / "reference_tracks" / "round2_queue.json"
    queue = load_json(queue_path)
    round2_dir = project_root / "data" / "_global" / "round2_expansion" / artist_id
    incoming_dir = round2_dir / "seed_incoming"
    incoming_dir.mkdir(parents=True, exist_ok=True)

    candidate_only = [
        item
        for item in queue.get("queue", [])
        if str(item.get("status", "")).strip() == "candidate_only"
    ]

    lines = [
        f"# Round2 Seed Packet: {artist_id}",
        "",
        "## Purpose",
        "This packet is for the remaining round2 candidate-only tracks that still need draft seeds before scaffold generation.",
        "",
        "## Required Output",
        "",
        "- Submit draft seed JSON only, not full conditioning JSON.",
        "- Keep `track_id`, `likely_mode`, and candidate direction intact.",
        "- Target file: `expansion_round2_draft_seeds.json`-compatible per-track payloads.",
        "",
        "## Candidate-Only Queue",
        "",
    ]

    for item in candidate_only:
        secondary = ", ".join(item.get("secondary_modes", [])) or "none"
        why = "; ".join(item.get("why_it_matters", [])) or "none"
        lines.extend(
            [
                f"- `{item['track_id']}` / priority `{item['priority_label']}` / likely `{item['likely_mode']}` / secondary `{secondary}`",
                f"  why: {why}",
            ]
        )

    lines.extend(
        [
            "",
            "## Draft Seed Fields",
            "",
            "- artist_id",
            "- track_id",
            "- title",
            "- likely_mode",
            "- title_pattern",
            "- hook_behavior",
            "- section_flow_guess",
            "- imagery_classes",
            "- emotional_arc",
            "- leakage_watchouts",
            "- prompt_seed_terms",
            "- grounding_status",
            "",
            "## Incoming Directory",
            "",
            f"- `{incoming_dir}`",
            "",
            "## Notes",
            "",
            "- Prefer high-priority candidates first.",
            "- Do not output full conditioning in this step.",
            "- This step exists only to unlock scaffold generation for the remaining round2 queue.",
            "",
        ]
    )
    return "\n".join(lines)


def write_round2_seed_packet(project_root: Path, artist_id: str) -> Path:
    round2_dir = project_root / "data" / "_global" / "round2_expansion" / artist_id
    round2_dir.mkdir(parents=True, exist_ok=True)
    output_path = round2_dir / "seed_packet.md"
    write_utf8_text(output_path, build_round2_seed_packet(project_root, artist_id))
    return output_path
