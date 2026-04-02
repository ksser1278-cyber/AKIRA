from __future__ import annotations

from pathlib import Path
from typing import Any

from .manifest_tools import load_json


def build_external_handoff_index(project_root: Path) -> dict[str, Any]:
    backlog = load_json(project_root / "reports" / "planning" / "execution_backlog.json")
    handoff_root = project_root / "data" / "_global" / "external_handoff"
    mode_support_root = project_root / "data" / "_global" / "mode_support"
    hard_case_root = project_root / "data" / "_global" / "hard_case"
    round2_root = project_root / "data" / "_global" / "round2_expansion"
    generation_safety_root = project_root / "data" / "_global" / "generation_safety_invalid"
    generation_safety_promotion_root = project_root / "data" / "_global" / "generation_safety_promotion"
    generation_safety_grounding_root = project_root / "data" / "_global" / "generation_safety_grounding_upgrade"
    generation_safety_lyric_grounding_root = (
        project_root / "data" / "_global" / "generation_safety_lyric_grounding_source_acquisition"
    )
    generation_safety_remaining_source_root = (
        project_root / "data" / "_global" / "generation_safety_remaining_source_acquisition"
    )

    external_by_artist: dict[str, list[dict[str, Any]]] = {}
    for task in backlog.get("external_tasks", []):
        artist_id = str(task.get("artist_id", "")).strip()
        if not artist_id:
            continue
        external_by_artist.setdefault(artist_id, []).append(task)

    artists: list[dict[str, Any]] = []
    for artist_dir in sorted(path for path in handoff_root.iterdir() if path.is_dir()):
        artist_id = artist_dir.name
        anchor_incoming = artist_dir / "incoming"
        expansion_dir = artist_dir / "producer_expansion"
        expansion_incoming = expansion_dir / "incoming"

        artist_payload = {
            "artist_id": artist_id,
            "anchor": {
                "manifest_json": str(artist_dir / "handoff_manifest.json"),
                "manifest_md": str(artist_dir / "handoff_manifest.md"),
                "prompt_txt": str(artist_dir / "delegation_prompt.txt"),
                "packet_md": str(artist_dir / "packet.md"),
                "incoming_dir": str(anchor_incoming),
                "incoming_count": len(list(anchor_incoming.glob("*.json"))) if anchor_incoming.exists() else 0,
            },
            "producer_expansion": {
                "manifest_json": str(expansion_dir / "handoff_manifest.json"),
                "manifest_md": str(expansion_dir / "handoff_manifest.md"),
                "brief_md": str(expansion_dir / "delegation_brief.md"),
                "prompt_txt": str(expansion_dir / "delegation_prompt.txt"),
                "packet_md": str(expansion_dir / "packet.md"),
                "incoming_dir": str(expansion_incoming),
                "incoming_count": len(list(expansion_incoming.glob("*.json"))) if expansion_incoming.exists() else 0,
            },
            "external_backlog": external_by_artist.get(artist_id, []),
        }
        artists.append(artist_payload)

    mode_support: list[dict[str, Any]] = []
    if mode_support_root.exists():
        for mode_dir in sorted(path for path in mode_support_root.iterdir() if path.is_dir()):
            handoff_dir = mode_dir / "external_handoff"
            incoming_dir = handoff_dir / "incoming"
            mode_support.append(
                {
                    "mode_id": mode_dir.name,
                    "queue_json": str(mode_dir / "queue.json"),
                    "brief_md": str(handoff_dir / "delegation_brief.md"),
                    "prompt_txt": str(handoff_dir / "delegation_prompt.txt"),
                    "packet_md": str(handoff_dir / "packet.md"),
                    "incoming_dir": str(incoming_dir),
                    "incoming_count": len(list(incoming_dir.glob("*.json"))) if incoming_dir.exists() else 0,
                }
            )

    hard_cases: list[dict[str, Any]] = []
    if hard_case_root.exists():
        for artist_dir in sorted(path for path in hard_case_root.iterdir() if path.is_dir()):
            hard_cases.append(
                {
                    "artist_id": artist_dir.name,
                    "packet_md": str(artist_dir / "packet.md"),
                }
            )

    round2_packets: list[dict[str, Any]] = []
    if round2_root.exists():
        for artist_dir in sorted(path for path in round2_root.iterdir() if path.is_dir()):
            packet_path = artist_dir / "packet.md"
            incoming_dir = artist_dir / "incoming"
            round2_packets.append(
                {
                    "artist_id": artist_dir.name,
                    "packet_md": str(packet_path),
                    "upgrade_brief_md": str(artist_dir / "upgrade_brief.md"),
                    "upgrade_prompt_txt": str(artist_dir / "delegation_prompt.txt"),
                    "seed_packet_md": str(artist_dir / "seed_packet.md"),
                    "incoming_dir": str(incoming_dir),
                    "incoming_count": len(list(incoming_dir.glob("*.json"))) if incoming_dir.exists() else 0,
                    "seed_incoming_dir": str(artist_dir / "seed_incoming"),
                    "seed_incoming_count": len(list((artist_dir / "seed_incoming").glob("*.json"))) if (artist_dir / "seed_incoming").exists() else 0,
                }
            )

    generation_safety: dict[str, Any] = {
        "status_md": str(project_root / "reports" / "planning" / "generation_safety_pilot_status.md"),
        "status_json": str(project_root / "reports" / "planning" / "generation_safety_pilot_status.json"),
        "invalid_queue_md": str(project_root / "reports" / "planning" / "generation_safety_invalid_queue.md"),
        "invalid_queue_json": str(project_root / "reports" / "planning" / "generation_safety_invalid_queue.json"),
        "delegation_prompt_txt": str(generation_safety_root / "delegation_prompt.txt"),
        "batch_delegation_prompt_txt": str(generation_safety_root / "batch_delegation_prompt.txt"),
        "artists": [],
    }
    if generation_safety_root.exists():
        for artist_dir in sorted(
            path for path in generation_safety_root.iterdir() if path.is_dir() and (path / "packet.md").exists()
        ):
            incoming_dir = artist_dir / "incoming"
            generation_safety["artists"].append(
                {
                    "artist_id": artist_dir.name,
                    "packet_md": str(artist_dir / "packet.md"),
                    "brief_md": str(artist_dir / "brief.md"),
                    "incoming_dir": str(incoming_dir),
                    "incoming_count": len(list(incoming_dir.glob("*.json"))) if incoming_dir.exists() else 0,
                }
            )

    generation_safety_promotion: dict[str, Any] = {
        "handoff_md": str(project_root / "reports" / "planning" / "generation_safety_promotion_handoff.md"),
        "handoff_json": str(project_root / "reports" / "planning" / "generation_safety_promotion_handoff.json"),
        "batch_delegation_prompt_txt": str(generation_safety_promotion_root / "batch_delegation_prompt.txt"),
        "artists": [],
    }
    if generation_safety_promotion_root.exists():
        for artist_dir in sorted(
            path for path in generation_safety_promotion_root.iterdir() if path.is_dir() and (path / "packet.md").exists()
        ):
            incoming_dir = artist_dir / "incoming"
            generation_safety_promotion["artists"].append(
                {
                    "artist_id": artist_dir.name,
                    "packet_md": str(artist_dir / "packet.md"),
                    "packet_json": str(artist_dir / "packet.json"),
                    "incoming_dir": str(incoming_dir),
                    "incoming_count": len(list(incoming_dir.glob("*.json"))) if incoming_dir.exists() else 0,
                }
            )

    generation_safety_grounding: dict[str, Any] = {
        "handoff_md": str(project_root / "reports" / "planning" / "generation_safety_grounding_handoff.md"),
        "handoff_json": str(project_root / "reports" / "planning" / "generation_safety_grounding_handoff.json"),
        "batch_delegation_prompt_txt": str(generation_safety_grounding_root / "batch_delegation_prompt.txt"),
        "phase_batches_md": str(generation_safety_grounding_root / "phase_batches.md"),
        "phase_batches_json": str(generation_safety_grounding_root / "phase_batches.json"),
        "phase1_prompt_txt": str(generation_safety_grounding_root / "phase1_core_cleanup.prompt.txt"),
        "phase2_prompt_txt": str(generation_safety_grounding_root / "phase2_extended_cleanup.prompt.txt"),
        "phase3_prompt_txt": str(generation_safety_grounding_root / "phase3_provenance_plus_cleanup.prompt.txt"),
        "phase1_dir": str(generation_safety_grounding_root / "phase1_core_cleanup"),
        "phase2_dir": str(generation_safety_grounding_root / "phase2_extended_cleanup"),
        "phase3_dir": str(generation_safety_grounding_root / "phase3_provenance_plus_cleanup"),
        "artists": [],
        "phases": [],
    }
    if generation_safety_grounding_root.exists():
        for artist_dir in sorted(
            path for path in generation_safety_grounding_root.iterdir() if path.is_dir() and (path / "packet.md").exists()
        ):
            incoming_dir = artist_dir / "incoming"
            generation_safety_grounding["artists"].append(
                {
                    "artist_id": artist_dir.name,
                    "packet_md": str(artist_dir / "packet.md"),
                    "packet_json": str(artist_dir / "packet.json"),
                    "brief_md": str(artist_dir / "brief.md"),
                    "incoming_dir": str(incoming_dir),
                    "incoming_count": len(list(incoming_dir.glob("*.json"))) if incoming_dir.exists() else 0,
                }
            )
        for phase_dir in sorted(
            path for path in generation_safety_grounding_root.iterdir() if path.is_dir() and (path / "overview.json").exists()
        ):
            phase_payload = {
                "phase_id": phase_dir.name,
                "overview_md": str(phase_dir / "overview.md"),
                "overview_json": str(phase_dir / "overview.json"),
                "prompt_txt": str(phase_dir / "prompt.txt"),
                "artists": [],
            }
            for artist_dir in sorted(
                path for path in phase_dir.iterdir() if path.is_dir() and (path / "packet.md").exists()
            ):
                incoming_dir = artist_dir / "incoming"
                source_records_dir = artist_dir / "source_records"
                phase_payload["artists"].append(
                    {
                        "artist_id": artist_dir.name,
                        "packet_md": str(artist_dir / "packet.md"),
                        "packet_json": str(artist_dir / "packet.json"),
                        "brief_md": str(artist_dir / "brief.md"),
                        "source_records_dir": str(source_records_dir),
                        "incoming_dir": str(incoming_dir),
                        "incoming_count": len(list(incoming_dir.glob("*.json"))) if incoming_dir.exists() else 0,
                    }
                )
            generation_safety_grounding["phases"].append(phase_payload)

    generation_safety_lyric_grounding: dict[str, Any] = {
        "handoff_md": str(project_root / "reports" / "planning" / "generation_safety_phase1_blocked.md"),
        "handoff_json": str(project_root / "reports" / "planning" / "generation_safety_phase1_blocked.json"),
        "overview_md": str(generation_safety_lyric_grounding_root / "overview.md"),
        "overview_json": str(generation_safety_lyric_grounding_root / "overview.json"),
        "batch_delegation_prompt_txt": str(generation_safety_lyric_grounding_root / "batch_delegation_prompt.txt"),
        "artists": [],
    }
    if generation_safety_lyric_grounding_root.exists():
        for artist_dir in sorted(
            path
            for path in generation_safety_lyric_grounding_root.iterdir()
            if path.is_dir() and (path / "packet.md").exists()
        ):
            incoming_dir = artist_dir / "incoming"
            generation_safety_lyric_grounding["artists"].append(
                {
                    "artist_id": artist_dir.name,
                    "packet_md": str(artist_dir / "packet.md"),
                    "packet_json": str(artist_dir / "packet.json"),
                    "incoming_dir": str(incoming_dir),
                    "incoming_count": len(list(incoming_dir.glob("*.json"))) if incoming_dir.exists() else 0,
                }
            )

    generation_safety_remaining_source: dict[str, Any] = {
        "overview_md": str(project_root / "reports" / "planning" / "generation_safety_remaining_source_acquisition.md"),
        "overview_json": str(project_root / "reports" / "planning" / "generation_safety_remaining_source_acquisition.json"),
        "workflow_overview_md": str(generation_safety_remaining_source_root / "overview.md"),
        "workflow_overview_json": str(generation_safety_remaining_source_root / "overview.json"),
        "batch_delegation_prompt_txt": str(generation_safety_remaining_source_root / "batch_delegation_prompt.txt"),
        "gemini_delegation_prompt_txt": str(generation_safety_remaining_source_root / "gemini_delegation_prompt.txt"),
        "source_policy_md": str(generation_safety_remaining_source_root / "source_policy.md"),
        "artists": [],
    }
    if generation_safety_remaining_source_root.exists():
        for artist_dir in sorted(
            path
            for path in generation_safety_remaining_source_root.iterdir()
            if path.is_dir() and (path / "packet.md").exists()
        ):
            incoming_dir = artist_dir / "incoming"
            generation_safety_remaining_source["artists"].append(
                {
                    "artist_id": artist_dir.name,
                    "packet_md": str(artist_dir / "packet.md"),
                    "packet_json": str(artist_dir / "packet.json"),
                    "brief_md": str(artist_dir / "brief.md"),
                    "current_records_dir": str(artist_dir / "current_records"),
                    "round2_records_dir": str(artist_dir / "round2_records"),
                    "incoming_dir": str(incoming_dir),
                    "incoming_count": len(list(incoming_dir.glob("*.json"))) if incoming_dir.exists() else 0,
                }
            )

    return {
        "schema_version": "1.0",
        "record_type": "external_handoff_index",
        "artists": artists,
        "mode_support": mode_support,
        "hard_cases": hard_cases,
        "round2_expansion": round2_packets,
        "generation_safety": generation_safety,
        "generation_safety_promotion": generation_safety_promotion,
        "generation_safety_grounding": generation_safety_grounding,
        "generation_safety_lyric_grounding": generation_safety_lyric_grounding,
        "generation_safety_remaining_source": generation_safety_remaining_source,
        "round2_upgrade_overview": {
            "json": str(project_root / "reports" / "planning" / "round2_upgrade_overview.json"),
            "md": str(project_root / "reports" / "planning" / "round2_upgrade_overview.md"),
            "batch_prompt_txt": str(project_root / "data" / "_global" / "round2_expansion" / "batch_delegation_prompt.txt"),
        },
    }


def render_external_handoff_index(payload: dict[str, Any]) -> str:
    lines = ["# External Handoff Index", ""]
    for artist in payload.get("artists", []):
        lines.extend(
            [
                f"## {artist['artist_id']}",
                "",
                "### Anchor",
                f"- Manifest: `{artist['anchor']['manifest_md']}`",
                f"- Prompt: `{artist['anchor']['prompt_txt']}`",
                f"- Packet: `{artist['anchor']['packet_md']}`",
                f"- Incoming: `{artist['anchor']['incoming_dir']}` / files `{artist['anchor']['incoming_count']}`",
                "",
                "### Producer Expansion",
                f"- Manifest: `{artist['producer_expansion']['manifest_md']}`",
                f"- Brief: `{artist['producer_expansion']['brief_md']}`",
                f"- Prompt: `{artist['producer_expansion']['prompt_txt']}`",
                f"- Packet: `{artist['producer_expansion']['packet_md']}`",
                f"- Incoming: `{artist['producer_expansion']['incoming_dir']}` / files `{artist['producer_expansion']['incoming_count']}`",
                "",
                "### External Backlog",
            ]
        )
        tasks = artist.get("external_backlog", [])
        if tasks:
            lines.append("")
            for task in tasks:
                lines.append(
                    f"- `{task['priority']}` / `{task['track_id']}` / {task['summary']}"
                )
        else:
            lines.append("")
            lines.append("- none")
        lines.append("")
    lines.extend(["## mode_support", ""])
    for mode in payload.get("mode_support", []):
        lines.extend(
            [
                f"### {mode['mode_id']}",
                f"- Queue: `{mode['queue_json']}`",
                f"- Brief: `{mode['brief_md']}`",
                f"- Prompt: `{mode['prompt_txt']}`",
                f"- Packet: `{mode['packet_md']}`",
                f"- Incoming: `{mode['incoming_dir']}` / files `{mode['incoming_count']}`",
                "",
            ]
        )
    lines.extend(["## hard_case", ""])
    for item in payload.get("hard_cases", []):
        lines.extend(
            [
                f"### {item['artist_id']}",
                f"- Packet: `{item['packet_md']}`",
                "",
            ]
        )
    lines.extend(["## round2_expansion", ""])
    overview = payload.get("round2_upgrade_overview", {})
    if overview:
        lines.extend(
            [
                f"- Upgrade overview: `{overview.get('md', '')}`",
                f"- Batch prompt: `{overview.get('batch_prompt_txt', '')}`",
                "",
            ]
        )
    for item in payload.get("round2_expansion", []):
        lines.extend(
            [
                f"### {item['artist_id']}",
                f"- Packet: `{item['packet_md']}`",
                f"- Upgrade brief: `{item['upgrade_brief_md']}`",
                f"- Upgrade prompt: `{item['upgrade_prompt_txt']}`",
                f"- Incoming: `{item['incoming_dir']}` / files `{item['incoming_count']}`",
                f"- Seed packet: `{item['seed_packet_md']}`",
                f"- Seed incoming: `{item['seed_incoming_dir']}` / files `{item['seed_incoming_count']}`",
                "",
            ]
        )
    generation_safety = payload.get("generation_safety", {})
    if generation_safety:
        lines.extend(
            [
                "## generation_safety",
                "",
                f"- Pilot status: `{generation_safety.get('status_md', '')}`",
                f"- Invalid queue: `{generation_safety.get('invalid_queue_md', '')}`",
                f"- Delegation prompt: `{generation_safety.get('delegation_prompt_txt', '')}`",
                f"- Batch prompt: `{generation_safety.get('batch_delegation_prompt_txt', '')}`",
                "",
            ]
        )
        for item in generation_safety.get("artists", []):
            lines.extend(
                [
                    f"### {item['artist_id']}",
                    f"- Packet: `{item['packet_md']}`",
                    f"- Brief: `{item['brief_md']}`",
                    f"- Incoming: `{item['incoming_dir']}` / files `{item['incoming_count']}`",
                    "",
                ]
            )
    generation_safety_promotion = payload.get("generation_safety_promotion", {})
    if generation_safety_promotion:
        lines.extend(
            [
                "## generation_safety_promotion",
                "",
                f"- Handoff: `{generation_safety_promotion.get('handoff_md', '')}`",
                f"- Batch prompt: `{generation_safety_promotion.get('batch_delegation_prompt_txt', '')}`",
                "",
            ]
        )
        for item in generation_safety_promotion.get("artists", []):
            lines.extend(
                [
                    f"### {item['artist_id']}",
                    f"- Packet: `{item['packet_md']}`",
                    f"- Incoming: `{item['incoming_dir']}` / files `{item['incoming_count']}`",
                    "",
                ]
            )
    generation_safety_grounding = payload.get("generation_safety_grounding", {})
    if generation_safety_grounding:
        lines.extend(
            [
                "## generation_safety_grounding_upgrade",
                "",
                f"- Handoff: `{generation_safety_grounding.get('handoff_md', '')}`",
                f"- Batch prompt: `{generation_safety_grounding.get('batch_delegation_prompt_txt', '')}`",
                f"- Phase overview: `{generation_safety_grounding.get('phase_batches_md', '')}`",
                f"- Phase 1 prompt: `{generation_safety_grounding.get('phase1_prompt_txt', '')}`",
                f"- Phase 1 dir: `{generation_safety_grounding.get('phase1_dir', '')}`",
                f"- Phase 2 prompt: `{generation_safety_grounding.get('phase2_prompt_txt', '')}`",
                f"- Phase 2 dir: `{generation_safety_grounding.get('phase2_dir', '')}`",
                f"- Phase 3 prompt: `{generation_safety_grounding.get('phase3_prompt_txt', '')}`",
                f"- Phase 3 dir: `{generation_safety_grounding.get('phase3_dir', '')}`",
                "",
            ]
        )
        for phase in generation_safety_grounding.get("phases", []):
            lines.extend(
                [
                    f"### {phase['phase_id']}",
                    f"- Overview: `{phase['overview_md']}`",
                    f"- Prompt: `{phase['prompt_txt']}`",
                    "",
                ]
            )
            for item in phase.get("artists", []):
                lines.extend(
                    [
                        f"#### {item['artist_id']}",
                        f"- Packet: `{item['packet_md']}`",
                        f"- Brief: `{item['brief_md']}`",
                        f"- Source records: `{item.get('source_records_dir', '')}`",
                        f"- Incoming: `{item['incoming_dir']}` / files `{item['incoming_count']}`",
                        "",
                    ]
                )
        for item in generation_safety_grounding.get("artists", []):
            lines.extend(
                [
                    f"### {item['artist_id']}",
                    f"- Packet: `{item['packet_md']}`",
                    f"- Brief: `{item['brief_md']}`",
                    f"- Incoming: `{item['incoming_dir']}` / files `{item['incoming_count']}`",
                    "",
                ]
            )
    generation_safety_lyric_grounding = payload.get("generation_safety_lyric_grounding", {})
    if generation_safety_lyric_grounding:
        lines.extend(
            [
                "## generation_safety_lyric_grounding_source_acquisition",
                "",
                f"- Blocked report: `{generation_safety_lyric_grounding.get('handoff_md', '')}`",
                f"- Overview: `{generation_safety_lyric_grounding.get('overview_md', '')}`",
                f"- Batch prompt: `{generation_safety_lyric_grounding.get('batch_delegation_prompt_txt', '')}`",
                "",
            ]
        )
        for item in generation_safety_lyric_grounding.get("artists", []):
            lines.extend(
                [
                    f"### {item['artist_id']}",
                    f"- Packet: `{item['packet_md']}`",
                    f"- Incoming: `{item['incoming_dir']}` / files `{item['incoming_count']}`",
                    "",
                ]
            )
    generation_safety_remaining_source = payload.get("generation_safety_remaining_source", {})
    if generation_safety_remaining_source:
        lines.extend(
            [
                "## generation_safety_remaining_source_acquisition",
                "",
                f"- Overview: `{generation_safety_remaining_source.get('overview_md', '')}`",
                f"- Workflow overview: `{generation_safety_remaining_source.get('workflow_overview_md', '')}`",
                f"- Source policy: `{generation_safety_remaining_source.get('source_policy_md', '')}`",
                f"- Batch prompt: `{generation_safety_remaining_source.get('batch_delegation_prompt_txt', '')}`",
                f"- Gemini prompt: `{generation_safety_remaining_source.get('gemini_delegation_prompt_txt', '')}`",
                "",
            ]
        )
        for item in generation_safety_remaining_source.get("artists", []):
            lines.extend(
                [
                    f"### {item['artist_id']}",
                    f"- Packet: `{item['packet_md']}`",
                    f"- Brief: `{item['brief_md']}`",
                    f"- Current records: `{item['current_records_dir']}`",
                    f"- Round2 records: `{item['round2_records_dir']}`",
                    f"- Incoming: `{item['incoming_dir']}` / files `{item['incoming_count']}`",
                    "",
                ]
            )
    return "\n".join(lines)
