from __future__ import annotations

from pathlib import Path

from .mode_support import load_json
from .reporting import write_utf8_text


def build_mode_support_brief(project_root: Path, mode_id: str) -> str:
    queue = load_json(project_root / "data" / "_global" / "mode_support" / mode_id / "queue.json")
    gold_anchor = load_json(project_root / "data" / "anchor_sets" / "gold_anchor_set.json")
    producer_expansion = load_json(project_root / "data" / "anchor_sets" / "producer_expansion_set.json")

    excluded_track_ids: list[str] = []
    for block in gold_anchor.get("artists", []):
        excluded_track_ids.extend(str(track_id).strip() for track_id in block.get("track_ids", []) if str(track_id).strip())
    for block in producer_expansion.get("artists", []):
        excluded_track_ids.extend(str(track_id).strip() for track_id in block.get("track_ids", []) if str(track_id).strip())

    lines = [
        f"# Mode Support Brief: {mode_id}",
        "",
        "## Objective",
        "Curate cross-producer support tracks that strengthen this mode without duplicating anchor or producer-expansion coverage.",
        "",
        "## Mode Constraints",
        f"- Mode id: `{mode_id}`",
        f"- Target total count: `{queue.get('target_count', 0)}`",
        f"- Support artists: `{', '.join(queue.get('support_artists', []))}`",
        "",
        "## Curation Rules",
        "- Prefer tracks that diversify hook shape, section geometry, and phrase energy.",
        "- Avoid near-duplicates of current gold anchors.",
        "- Avoid active producer-expansion tracks already queued for grounding.",
        "- Return only support candidates, not conditioning JSON.",
        "",
        "## Excluded Track IDs",
        "",
    ]
    for track_id in excluded_track_ids:
        lines.append(f"- `{track_id}`")

    lines.extend(["", "## Artist Targets", ""])
    for item in queue.get("queue", []):
        lines.append(
            f"- `{item['artist_id']}` / target `{item['target_track_count']}` / status `{item['status']}`"
        )
    lines.append("")
    return "\n".join(lines)


def write_mode_support_brief(project_root: Path, mode_id: str) -> Path:
    handoff_dir = project_root / "data" / "_global" / "mode_support" / mode_id / "external_handoff"
    handoff_dir.mkdir(parents=True, exist_ok=True)
    output_path = handoff_dir / "delegation_brief.md"
    write_utf8_text(output_path, build_mode_support_brief(project_root, mode_id))
    return output_path
