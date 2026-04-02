from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_invalid_handoff(root: Path | None = None) -> dict[str, Any]:
    root = root or project_root()
    queue_path = root / "reports" / "planning" / "generation_safety_invalid_queue.json"
    queue = load_json(queue_path)
    items = list(queue.get("items", []))
    by_artist: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        by_artist.setdefault(str(item.get("artist_id", "")).strip(), []).append(item)

    return {
        "schema_version": "1.0",
        "record_type": "generation_safety_invalid_handoff",
        "invalid_count": int(queue.get("invalid_count", 0)),
        "artist_count": len(by_artist),
        "artists": [
            {
                "artist_id": artist_id,
                "track_count": len(rows),
                "tracks": rows,
            }
            for artist_id, rows in sorted(by_artist.items())
        ],
    }


def render_invalid_handoff_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Generation Safety Invalid Handoff",
        "",
        f"- invalid records `{payload.get('invalid_count', 0)}`",
        f"- artists `{payload.get('artist_count', 0)}`",
        "",
        "## Required Upgrades",
        "",
        "- add trusted `lyric_sources` and `metadata_sources`",
        "- replace compact or chorus-only grounding with section-complete lyric grounding",
        "- keep `ready_for_prompting` disabled until provenance and grounding are restored",
        "- add mode alignment where `mode_fit_unverified` is present",
        "",
    ]
    for artist in payload.get("artists", []):
        lines.append(f"## {artist['artist_id']}")
        lines.append("")
        for track in artist.get("tracks", []):
            blockers = ", ".join(track.get("blockers", [])) or "none"
            lines.append(
                f"- `{track['track_id']}` / blockers `{blockers}` / path `{track['path']}`"
            )
        lines.append("")
    return "\n".join(lines)


def render_invalid_delegation_prompt(payload: dict[str, Any]) -> str:
    lines = [
        "이번 작업은 generation_safety invalid 11곡을 remediation 하는 것이다.",
        "",
        "목표:",
        "- 각 conditioning 파일을 invalid 에서 최소 audit_only 이상으로 복구할 수 있게 provenance와 grounding을 보강한다.",
        "- 가능하면 planner_safe 조건에 근접하도록 구조를 정리한다.",
        "",
        "중요:",
        "- 엔진 코드 수정 금지",
        "- 기존 track_id 유지",
        "- 기존 파일을 덮어쓸 수 있는 merge-friendly JSON만 제출",
        "- 근거 없는 confirmed / cross_checked 사용 금지",
        "- chorus-only compact record를 section-complete grounding으로 바꿀 것",
        "",
        "필수 보강:",
        "- source_provenance.lyric_sources",
        "- source_provenance.metadata_sources",
        "- lyric_ground_truth.full_text_status",
        "- lyric_ground_truth.sections",
        "- quality_control.ready_for_prompting는 provenance/grounding이 회복될 때만 true",
        "- mode_alignment 또는 동등한 mode verification 정보",
        "",
        "대상 파일:",
    ]
    for artist in payload.get("artists", []):
        lines.append(f"- {artist['artist_id']}")
        for track in artist.get("tracks", []):
            lines.append(f"  - {track['path']}")
    lines.extend(
        [
            "",
            "우선순위:",
            "- kanaria_king",
            "- kanaria_queen",
            "- iyowa_kyukurarin",
            "- maretu_pink",
            "- neru_tokyo_teddy_bear",
            "- syudou_bitter_choco_decoration",
            "- syudou_usseewa",
            "- kairiki_bear_darling_dance",
            "- kairiki_bear_bug",
            "- kairiki_bear_failure_girl",
            "- kairiki_bear_ruma",
        ]
    )
    return "\n".join(lines) + "\n"
