from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .reporting import write_utf8_text


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_generation_safety_packets(project_root: Path) -> dict[str, Any]:
    queue_path = project_root / "reports" / "planning" / "generation_safety_invalid_queue.json"
    handoff_path = project_root / "reports" / "planning" / "generation_safety_invalid_handoff.json"
    queue = load_json(queue_path)
    handoff = load_json(handoff_path)

    root = project_root / "data" / "_global" / "generation_safety_invalid"
    root.mkdir(parents=True, exist_ok=True)
    incoming_root = root / "incoming"
    incoming_root.mkdir(parents=True, exist_ok=True)

    delegation_prompt_path = root / "delegation_prompt.txt"
    delegation_prompt_path.write_text(
        (
            "이번 작업은 generation_safety invalid conditioning records를 remediation 하는 것이다.\n"
            "\n"
            "목표:\n"
            "- trusted lyric_sources / metadata_sources 를 추가한다.\n"
            "- compact or chorus-only grounding 을 section-complete grounding 으로 교체한다.\n"
            "- mode_fit_unverified 가 있으면 현재 mode taxonomy 기준 mode alignment 를 보강한다.\n"
            "- provenance 와 grounding 이 회복되기 전에는 ready_for_prompting 을 true 로 올리지 않는다.\n"
            "\n"
            "중요:\n"
            "- 엔진 코드 수정 금지\n"
            "- 기존 track_id 유지\n"
            "- merge-friendly JSON 만 제출\n"
            "- 근거 없는 confirmed / cross_checked 사용 금지\n"
        ),
        encoding="utf-8",
    )
    batch_prompt_path = root / "batch_delegation_prompt.txt"

    packets: list[dict[str, Any]] = []
    by_artist: dict[str, list[dict[str, Any]]] = {}
    for item in queue.get("items", []):
        by_artist.setdefault(str(item.get("artist_id", "")).strip(), []).append(item)

    for artist in handoff.get("artists", []):
        artist_id = str(artist.get("artist_id", "")).strip()
        if not artist_id:
            continue
        artist_dir = root / artist_id
        artist_dir.mkdir(parents=True, exist_ok=True)
        incoming_dir = artist_dir / "incoming"
        incoming_dir.mkdir(parents=True, exist_ok=True)
        packet_path = artist_dir / "packet.md"
        brief_path = artist_dir / "brief.md"

        rows = sorted(by_artist.get(artist_id, []), key=lambda item: (float(item.get("score", 0.0)), str(item.get("track_id", ""))))
        lines = [
            f"# Generation Safety Invalid Packet: {artist_id}",
            "",
            "## Purpose",
            "Restore invalid conditioning records to at least audit-only or planner-safe status by fixing provenance and grounding gaps.",
            "",
            "## Tracks",
            "",
        ]
        for row in rows:
            blockers = ", ".join(row.get("blockers", [])) or "none"
            next_action = str(row.get("next_action", "")).strip() or "manual review"
            lines.append(
                f"- `{row['track_id']}` / score `{row['score']}` / blockers `{blockers}` / next `{next_action}`"
            )
        lines.extend(
            [
                "",
                "## Incoming Directory",
                "",
                f"- `{incoming_dir}`",
                "",
                "## Required Upgrades",
                "",
                "- add trusted `lyric_sources` and `metadata_sources`",
                "- replace compact or chorus-only grounding with section-complete lyric grounding",
                "- keep `ready_for_prompting` disabled until provenance and grounding are restored",
                "- add mode alignment where `mode_fit_unverified` is present",
                "",
            ]
        )
        write_utf8_text(packet_path, "\n".join(lines))
        brief_lines = [
            f"# Generation Safety Invalid Brief: {artist_id}",
            "",
            f"- invalid tracks `{len(rows)}`",
            f"- incoming dir `{incoming_dir}`",
            "",
            "## Priority",
            "",
        ]
        for row in rows:
            brief_lines.append(f"- `{row['track_id']}` / blockers `{', '.join(row.get('blockers', []))}`")
        brief_lines.extend(
            [
                "",
                "## Required Output",
                "",
                "- merge-friendly JSON only",
                "- keep `track_id` unchanged",
                "- restore provenance with trusted lyric and metadata sources",
                "- replace compact grounding with section-complete lyric grounding",
                "- leave `ready_for_prompting` false unless provenance and grounding are restored",
                "",
            ]
        )
        write_utf8_text(brief_path, "\n".join(brief_lines))
        packets.append(
            {
                "artist_id": artist_id,
                "packet_md": str(packet_path),
                "brief_md": str(brief_path),
                "incoming_dir": str(incoming_dir),
                "incoming_count": len(list(incoming_dir.glob("*.json"))),
                "track_count": len(rows),
            }
        )

    batch_lines = [
        "이번 작업은 generation_safety invalid 11곡 전체를 remediation 하는 것이다.",
        "",
        "핵심 규칙:",
        "- trusted `lyric_sources`와 `metadata_sources`를 추가한다.",
        "- chorus-only 또는 compact grounding을 section-complete grounding으로 교체한다.",
        "- `mode_fit_unverified`가 있으면 mode alignment를 보강한다.",
        "- provenance와 grounding이 회복되기 전에는 `ready_for_prompting`을 true로 올리지 않는다.",
        "- 엔진 코드 수정 금지, merge-friendly JSON만 제출한다.",
        "",
        "artist packets:",
    ]
    for item in packets:
        batch_lines.append(f"- {item['artist_id']}: {item['packet_md']}")
    batch_lines.append("")
    batch_lines.append("공통 prompt:")
    batch_lines.append(f"- {delegation_prompt_path}")
    batch_lines.append("")
    batch_lines.append("입력 대상:")
    for artist_id in sorted(by_artist):
        track_ids = ", ".join(str(item.get("track_id", "")).strip() for item in by_artist[artist_id])
        batch_lines.append(f"- {artist_id}: {track_ids}")
    batch_prompt_path.write_text("\n".join(batch_lines) + "\n", encoding="utf-8")

    payload = {
        "schema_version": "1.0",
        "record_type": "generation_safety_invalid_packets",
        "delegation_prompt_txt": str(delegation_prompt_path),
        "batch_delegation_prompt_txt": str(batch_prompt_path),
        "queue_json": str(queue_path),
        "handoff_json": str(handoff_path),
        "artists": packets,
    }
    (root / "manifest.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload
