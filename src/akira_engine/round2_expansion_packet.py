from __future__ import annotations

from pathlib import Path

from .manifest_tools import load_json
from .reporting import write_utf8_text


def build_round2_packet(project_root: Path, artist_id: str) -> str:
    round2_dir = project_root / "data" / "_global" / "round2_expansion"
    queue_path = project_root / "data" / artist_id / "reference_tracks" / "round2_queue.json"
    audit_path = project_root / "reports" / "quality" / "round2_expansion_audit" / f"{artist_id}_round2_audit.json"
    seed_dir = project_root / "data" / artist_id / "reference_tracks" / "round2_seed_scaffolds"
    incoming_dir = round2_dir / artist_id / "incoming"
    incoming_dir.mkdir(parents=True, exist_ok=True)

    queue = load_json(queue_path)
    audit = load_json(audit_path) if audit_path.exists() else {}
    audit_lookup = {
        str(item.get("track_id", "")).strip(): item
        for item in audit.get("records", [])
        if str(item.get("track_id", "")).strip()
    }

    validated = [
        item for item in queue.get("queue", []) if str(item.get("status", "")).strip() == "validated"
    ]
    scaffolded = [
        item for item in queue.get("queue", []) if str(item.get("status", "")).strip() == "scaffolded"
    ]

    lines = [
        f"# Round2 Expansion Packet: {artist_id}",
        "",
        "## Purpose",
        "This packet is the handoff unit for upgrading round2 scaffold records into fully grounded usable records.",
        "",
        "## Queue Summary",
        "",
        f"- validated `{len(validated)}`",
        f"- scaffolded `{len(scaffolded)}`",
        "",
        "## Current Queue Snapshot",
        "",
    ]
    for item in queue.get("queue", []):
        lines.append(
            f"- `{item['track_id']}` / status `{item['status']}` / priority `{item['priority_label']}` / mode `{item['likely_mode']}`"
        )
    lines.extend(
        [
            "",
            "## Current Audit Summary",
            "",
            f"- Records: `{audit.get('record_count', 0)}`",
            f"- Gold: `{audit.get('gold_count', 0)}`",
            f"- Usable: `{audit.get('usable_count', 0)}`",
            f"- Weak: `{audit.get('weak_count', 0)}`",
            f"- Average score: `{audit.get('average_score', 0.0)}`",
            "",
            "## Weak Track Upgrade Targets",
            "",
        ]
    )

    weak_records = [item for item in audit.get("records", []) if str(item.get("grade", "")).strip() == "weak"]
    if weak_records:
        for item in weak_records:
            blockers = [str(value).strip() for value in item.get("blockers", []) if str(value).strip()]
            warnings = [str(value).strip() for value in item.get("warnings", []) if str(value).strip()]
            metrics = item.get("metrics", {})
            lines.extend(
                [
                    f"### {item['track_id']}",
                    f"- Score: `{item['score']}`",
                    f"- full_text_status: `{metrics.get('full_text_status', '')}`",
                    f"- trusted_ratio: `{metrics.get('trusted_ratio', 0.0)}`",
                    f"- hook_lines: `{metrics.get('hook_line_count', 0)}`",
                    f"- prompt anchors: `{metrics.get('prompt_anchor_count', 0)}`",
                    f"- Blockers: {'; '.join(blockers) if blockers else 'none'}",
                    f"- Warnings: {'; '.join(warnings) if warnings else 'none'}",
                    "",
                ]
            )
    else:
        lines.extend(
            [
                "- none",
                "",
            ]
        )

    lines.extend(
        [
            "## Required Upgrades",
            "",
            "- Add lyric_sources and metadata_sources with confirmed/cross_checked status.",
            "- Upgrade partial lyric grounding to full where possible.",
            "- Fill song_intent.contrast_device.",
            "- Raise quality_control.ready_for_prompting only when grounding is sufficient.",
            "- Keep track_id, likely_mode, and seed direction intact.",
            "",
            "## Seed Directory",
            "",
            f"- `{seed_dir}`",
            "",
            "## Validated Tracks",
            "",
        ]
    )
    if validated:
        for item in validated:
            record = audit_lookup.get(str(item.get("track_id", "")).strip(), {})
            lines.append(
                f"- `{item['track_id']}` / score `{record.get('score', 'n/a')}` / keep as benchmarked round2 winner"
            )
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Incoming Directory",
            "",
            f"- `{incoming_dir}`",
            "",
        ]
    )
    return "\n".join(lines)


def write_round2_packet(project_root: Path, artist_id: str) -> Path:
    round2_dir = project_root / "data" / "_global" / "round2_expansion" / artist_id
    round2_dir.mkdir(parents=True, exist_ok=True)
    output_path = round2_dir / "packet.md"
    write_utf8_text(output_path, build_round2_packet(project_root, artist_id))
    return output_path
