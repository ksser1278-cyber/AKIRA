from __future__ import annotations

from pathlib import Path
from shutil import copy2
from typing import Any

from .reporting import load_json, write_utf8_json, write_utf8_text


RELEVANT_BLOCKERS = {
    "missing_provenance",
    "partial_grounding",
    "surface_noise_risk",
    "mode_fit_unverified",
    "renderer_policy_block",
}


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _track_suffix(artist_id: str, track_id: str) -> str:
    prefix = f"{artist_id}_"
    if track_id.startswith(prefix):
        return track_id[len(prefix) :]
    return track_id


def _current_record_path(root: Path, artist_id: str, track_id: str) -> Path:
    return root / "data" / artist_id / "reference_tracks" / f"{_track_suffix(artist_id, track_id)}.conditioning.json"


def _round2_scaffold_path(root: Path, artist_id: str, track_id: str) -> Path:
    return root / "data" / "_global" / "round2_expansion" / artist_id / "incoming" / f"{track_id}.json"


def _workflow_type(blockers: set[str]) -> str:
    if "missing_provenance" in blockers:
        return "source_plus_provenance"
    if "mode_fit_unverified" in blockers:
        return "source_plus_mode"
    return "source_only"


def _recommended_action(workflow_type: str) -> str:
    if workflow_type == "source_plus_provenance":
        return "acquire trusted lyric sources, metadata sources, and exact Japanese grounding bundle"
    if workflow_type == "source_plus_mode":
        return "acquire trusted lyric sources and exact Japanese grounding bundle, then verify a single supported narrative_role"
    return "acquire trusted lyric sources and exact Japanese grounding bundle"


def _existing_lyric_source_count(current_record: dict[str, Any]) -> int:
    source_provenance = current_record.get("source_provenance", {})
    if not isinstance(source_provenance, dict):
        return 0
    lyric_sources = source_provenance.get("lyric_sources", [])
    if not isinstance(lyric_sources, list):
        return 0
    return len([item for item in lyric_sources if isinstance(item, dict)])


def build_remaining_source_acquisition(root: Path | None = None) -> dict[str, Any]:
    root = root or project_root()
    pilot = load_json(root / "reports" / "planning" / "generation_safety_pilot_status.json")

    by_artist: dict[str, list[dict[str, Any]]] = {}
    workflow_counts = {
        "source_only": 0,
        "source_plus_mode": 0,
        "source_plus_provenance": 0,
    }

    for artist in pilot.get("artists", []):
        artist_id = str(artist.get("artist_id", "")).strip()
        if not artist_id:
            continue
        for track in artist.get("tracks", []):
            verdict = str(track.get("verdict", "")).strip()
            blockers = {str(item).strip() for item in track.get("blockers", []) if str(item).strip()}
            if verdict not in {"audit_only", "invalid"}:
                continue
            if not blockers.intersection(RELEVANT_BLOCKERS):
                continue

            track_id = str(track.get("track_id", "")).strip()
            if not track_id:
                continue

            current_path = _current_record_path(root, artist_id, track_id)
            current_record = load_json(current_path) if current_path.exists() else {}
            workflow_type = _workflow_type(blockers)
            workflow_counts[workflow_type] += 1
            round2_path = _round2_scaffold_path(root, artist_id, track_id)

            entry = {
                "artist_id": artist_id,
                "track_id": track_id,
                "current_verdict": verdict,
                "score": float(track.get("score", 0.0)),
                "blockers": sorted(blockers),
                "workflow_type": workflow_type,
                "recommended_action": _recommended_action(workflow_type),
                "current_record_path": str(current_path),
                "round2_scaffold_path": str(round2_path),
                "round2_scaffold_available": round2_path.exists(),
                "existing_lyric_source_count": _existing_lyric_source_count(current_record),
                "needs_provenance": "missing_provenance" in blockers,
                "needs_mode_verification": "mode_fit_unverified" in blockers,
                "needs_surface_replacement": any(
                    blocker in blockers for blocker in {"partial_grounding", "surface_noise_risk"}
                ),
            }
            by_artist.setdefault(artist_id, []).append(entry)

    artists: list[dict[str, Any]] = []
    for artist_id, tracks in sorted(by_artist.items()):
        tracks = sorted(
            tracks,
            key=lambda item: (
                {"source_plus_provenance": 0, "source_plus_mode": 1, "source_only": 2}.get(
                    str(item.get("workflow_type", "")),
                    99,
                ),
                item.get("score", 0.0),
                str(item.get("track_id", "")),
            ),
        )
        artists.append(
            {
                "artist_id": artist_id,
                "track_count": len(tracks),
                "workflow_counts": {
                    "source_only": sum(1 for item in tracks if item.get("workflow_type") == "source_only"),
                    "source_plus_mode": sum(1 for item in tracks if item.get("workflow_type") == "source_plus_mode"),
                    "source_plus_provenance": sum(
                        1 for item in tracks if item.get("workflow_type") == "source_plus_provenance"
                    ),
                },
                "tracks": tracks,
            }
        )

    return {
        "schema_version": "1.0",
        "record_type": "generation_safety_remaining_source_acquisition",
        "selected_count": sum(artist["track_count"] for artist in artists),
        "artist_count": len(artists),
        "workflow_counts": workflow_counts,
        "artists": artists,
    }


def render_remaining_source_acquisition_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Generation Safety Remaining Source Acquisition",
        "",
        f"- selected records `{payload.get('selected_count', 0)}`",
        f"- artists `{payload.get('artist_count', 0)}`",
        f"- source_only `{payload.get('workflow_counts', {}).get('source_only', 0)}`",
        f"- source_plus_mode `{payload.get('workflow_counts', {}).get('source_plus_mode', 0)}`",
        f"- source_plus_provenance `{payload.get('workflow_counts', {}).get('source_plus_provenance', 0)}`",
        "",
        "## Read",
        "",
        "- this batch covers the remaining `audit_only` and `invalid` generation_safety records after the phase1 normalization wave",
        "- the local round2 scaffold copies are still placeholder-heavy and cannot be merged directly",
        "- the next external task is trusted lyric-source acquisition, not scaffold cleanup patches",
        "",
    ]
    for artist in payload.get("artists", []):
        counts = artist.get("workflow_counts", {})
        lines.extend(
            [
                f"## {artist['artist_id']}",
                "",
                f"- source_only `{counts.get('source_only', 0)}` / source+mode `{counts.get('source_plus_mode', 0)}` / source+provenance `{counts.get('source_plus_provenance', 0)}`",
            ]
        )
        for track in artist.get("tracks", []):
            blockers = ", ".join(track.get("blockers", [])) or "none"
            lines.append(
                f"- `{track['track_id']}` / verdict `{track['current_verdict']}` / workflow `{track['workflow_type']}` / blockers `{blockers}` / current `{track['current_record_path']}` / round2 `{track['round2_scaffold_path']}`"
            )
        lines.append("")
    return "\n".join(lines)


def render_remaining_source_prompt(payload: dict[str, Any], source_policy_path: Path) -> str:
    lines = [
        "This task is generation_safety remaining-source acquisition batch 1.",
        "",
        "Goal:",
        "- Collect trusted Japanese lyric grounding source bundles for the remaining non-runtime-safe generation_safety records.",
        "- Do not patch main conditioning records directly in this workflow.",
        "",
        "Read first:",
        f"- `{source_policy_path}`",
        "",
        "Important:",
        "- Do not modify engine code.",
        "- Keep existing track_id values.",
        "- Use the bundled `current_records/` and `round2_records/` copies inside each artist package only as local context.",
        "- Submit one JSON source bundle per track into the matching artist `incoming/` directory.",
        "- If trusted lyric support is insufficient, leave the track unsubmitted.",
        "- Do not submit English summaries, inferred paraphrases, or wiki-style prose in `sections` or `hook_lines`.",
        "- Do not submit machine-translated or unattributed lyric mirrors.",
        "",
        "Required output fields:",
        "- `track_identity.track_id`",
        "- `source_provenance.lyric_sources`",
        "- `source_provenance.notes`",
        "- `lyric_ground_truth.full_text_status`",
        "- `lyric_ground_truth.sections`",
        "- `lyric_ground_truth.hook_lines`",
        "- `source_provenance.metadata_sources` when workflow type is `source_plus_provenance`",
        "",
        "Workflow types:",
        f"- source_only: `{payload.get('workflow_counts', {}).get('source_only', 0)}`",
        f"- source_plus_mode: `{payload.get('workflow_counts', {}).get('source_plus_mode', 0)}`",
        f"- source_plus_provenance: `{payload.get('workflow_counts', {}).get('source_plus_provenance', 0)}`",
        "",
        "Extra requirements by workflow type:",
        "- source_only: acquire trusted lyric-source support and exact or tightly transcribed Japanese sections/hook lines.",
        "- source_plus_mode: same as source_only, plus enough evidence for later internal single-mode verification.",
        "- source_plus_provenance: same as source_plus_mode, plus trusted metadata-source support suitable for later provenance restoration.",
        "",
        "Done when:",
        "- the submitted bundle passes the local lyric-source validator and no longer depends on a single unsupported lyric database.",
        "",
    ]
    for artist in payload.get("artists", []):
        lines.append(f"{artist['artist_id']}:")
        for track in artist.get("tracks", []):
            lines.append(f"- {track['track_id']} ({track['workflow_type']})")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_remaining_source_gemini_prompt(payload: dict[str, Any], workflow_dir: Path, source_policy_path: Path) -> str:
    lines = [
        "이번 작업은 `generation_safety_remaining_source_acquisition` batch 1이다.",
        "",
        "목표:",
        "- 남아 있는 `audit_only / invalid` generation_safety 레코드 28곡에 대해 trusted Japanese lyric grounding source bundle을 수집한다.",
        "- main conditioning record는 직접 수정하지 않는다.",
        "",
        "프로젝트 루트:",
        f"- `{project_root()}`",
        "",
        "반드시 먼저 읽을 파일:",
        f"- `{source_policy_path}`",
        f"- `{workflow_dir / 'overview.md'}`",
        f"- `{workflow_dir / 'batch_delegation_prompt.txt'}`",
        "",
        "작업 원칙:",
        "- 외부 조사는 허용한다.",
        "- trusted lyric source만 사용한다.",
        "- official source 우선, 없으면 line-for-line로 맞는 두 번째 trusted source가 필요하다.",
        "- source가 충돌하면 그 track은 제출하지 말 것.",
        "- paraphrase 금지.",
        "- English summary 금지.",
        "- machine-translated page, unattributed mirror, fan lyric wiki mirror 금지.",
        "- clean UTF-8 Japanese만 허용.",
        "",
        "공통 필수 필드:",
        "- `track_identity.track_id`",
        "- `source_provenance.lyric_sources`",
        "- `source_provenance.notes`",
        "- `lyric_ground_truth.full_text_status` = `full`",
        "- `lyric_ground_truth.sections`",
        "- `lyric_ground_truth.hook_lines`",
        "",
        "추가 필드:",
        "- workflow가 `source_plus_provenance`인 track은 `source_provenance.metadata_sources`도 반드시 제출",
        "",
        "출력 규칙:",
        "- artist별 `incoming/`에 `<track_id>.json`으로 저장",
        "- 충분한 trusted support를 못 확보하면 그 track은 제출하지 말 것",
        "",
        "artist packet:",
    ]
    for artist in payload.get("artists", []):
        artist_id = str(artist.get("artist_id", "")).strip()
        if not artist_id:
            continue
        lines.append(f"- `{workflow_dir / artist_id / 'packet.md'}`")
    lines.extend(
        [
            "",
            "workflow counts:",
            f"- source_only `{payload.get('workflow_counts', {}).get('source_only', 0)}`",
            f"- source_plus_mode `{payload.get('workflow_counts', {}).get('source_plus_mode', 0)}`",
            f"- source_plus_provenance `{payload.get('workflow_counts', {}).get('source_plus_provenance', 0)}`",
            "",
            "제출 기준:",
            "- single-source lyric DB만으로는 제출 금지",
            "- official source가 없으면 독립된 trusted source 2개가 line-for-line로 맞아야 함",
            "- `sections`와 `hook_lines`에는 Japanese lyric text만 들어가야 함",
            "- 불확실한 track은 비워 두는 것이 맞다",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _render_artist_packet_md(artist_id: str, tracks: list[dict[str, Any]]) -> str:
    lines = [
        f"# Remaining Source Acquisition Packet: {artist_id}",
        "",
        f"- track count `{len(tracks)}`",
        "",
    ]
    for track in tracks:
        blockers = ", ".join(track.get("blockers", [])) or "none"
        lines.extend(
            [
                f"## {track['track_id']}",
                "",
                f"- current verdict `{track['current_verdict']}`",
                f"- workflow `{track['workflow_type']}`",
                f"- blockers `{blockers}`",
                f"- existing lyric_sources `{track['existing_lyric_source_count']}`",
                f"- current record `{track['current_record_path']}`",
                f"- round2 scaffold `{track['round2_scaffold_path']}`",
                f"- recommended action `{track['recommended_action']}`",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _render_artist_brief_md(workflow_counts: dict[str, int]) -> str:
    lines = [
        "- do not patch main conditioning records in this workflow",
        "- submit only trusted lyric-source bundles",
        "- keep track_id stable",
        "- use clean UTF-8 Japanese only in lyric fields",
        "- do not submit English summaries or inferred paraphrases",
    ]
    if workflow_counts.get("source_plus_mode", 0) or workflow_counts.get("source_plus_provenance", 0):
        lines.append("- tracks flagged for mode review must preserve enough evidence for later internal single-mode verification")
    if workflow_counts.get("source_plus_provenance", 0):
        lines.append("- tracks flagged for provenance must include lyric-source and metadata-source citations suitable for internal review")
    return "# Remaining Source Acquisition Brief\n\n" + "\n".join(lines) + "\n"


def _copy_if_exists(source: Path, target: Path) -> None:
    if source.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        copy2(source, target)


def write_remaining_source_acquisition_outputs(root: Path | None = None) -> dict[str, Path]:
    root = root or project_root()
    payload = build_remaining_source_acquisition(root)

    reports_dir = root / "reports" / "planning"
    workflow_dir = root / "data" / "_global" / "generation_safety_remaining_source_acquisition"
    reports_dir.mkdir(parents=True, exist_ok=True)
    workflow_dir.mkdir(parents=True, exist_ok=True)

    source_policy_source = (
        root / "data" / "_global" / "generation_safety_lyric_grounding_source_acquisition" / "source_policy.md"
    )
    source_policy_target = workflow_dir / "source_policy.md"
    if source_policy_source.exists():
        copy2(source_policy_source, source_policy_target)

    paths = {
        "report_json": write_utf8_json(
            reports_dir / "generation_safety_remaining_source_acquisition.json",
            payload,
        ),
        "report_md": write_utf8_text(
            reports_dir / "generation_safety_remaining_source_acquisition.md",
            render_remaining_source_acquisition_markdown(payload),
            trailing_newline=False,
        ),
        "overview_json": write_utf8_json(workflow_dir / "overview.json", payload),
        "overview_md": write_utf8_text(
            workflow_dir / "overview.md",
            render_remaining_source_acquisition_markdown(payload),
            trailing_newline=False,
        ),
    }
    paths["batch_prompt_txt"] = write_utf8_text(
        workflow_dir / "batch_delegation_prompt.txt",
        render_remaining_source_prompt(payload, source_policy_target if source_policy_target.exists() else source_policy_source),
        trailing_newline=True,
    )
    paths["gemini_prompt_txt"] = write_utf8_text(
        workflow_dir / "gemini_delegation_prompt.txt",
        render_remaining_source_gemini_prompt(
            payload,
            workflow_dir,
            source_policy_target if source_policy_target.exists() else source_policy_source,
        ),
        trailing_newline=True,
    )

    for artist in payload.get("artists", []):
        artist_id = str(artist.get("artist_id", "")).strip()
        if not artist_id:
            continue
        artist_dir = workflow_dir / artist_id
        current_records_dir = artist_dir / "current_records"
        round2_records_dir = artist_dir / "round2_records"
        incoming_dir = artist_dir / "incoming"
        current_records_dir.mkdir(parents=True, exist_ok=True)
        round2_records_dir.mkdir(parents=True, exist_ok=True)
        incoming_dir.mkdir(parents=True, exist_ok=True)

        packet_tracks: list[dict[str, Any]] = []
        for track in artist.get("tracks", []):
            current_source = Path(str(track.get("current_record_path", "")))
            round2_source = Path(str(track.get("round2_scaffold_path", "")))
            current_name = f"{track['track_id']}.conditioning.json"
            round2_name = f"{track['track_id']}.json"
            _copy_if_exists(current_source, current_records_dir / current_name)
            _copy_if_exists(round2_source, round2_records_dir / round2_name)

            packet_track = dict(track)
            packet_track["current_record_path"] = str(Path("current_records") / current_name)
            packet_track["round2_scaffold_path"] = str(Path("round2_records") / round2_name)
            packet_tracks.append(packet_track)

        packet_payload = {
            "schema_version": "1.0",
            "record_type": "generation_safety_remaining_source_acquisition_packet",
            "artist_id": artist_id,
            "track_count": len(packet_tracks),
            "workflow_counts": artist.get("workflow_counts", {}),
            "tracks": packet_tracks,
        }
        paths[f"{artist_id}_packet_json"] = write_utf8_json(artist_dir / "packet.json", packet_payload)
        paths[f"{artist_id}_packet_md"] = write_utf8_text(
            artist_dir / "packet.md",
            _render_artist_packet_md(artist_id, packet_tracks),
            trailing_newline=True,
        )
        paths[f"{artist_id}_brief_md"] = write_utf8_text(
            artist_dir / "brief.md",
            _render_artist_brief_md(artist.get("workflow_counts", {})),
            trailing_newline=True,
        )

    return paths
