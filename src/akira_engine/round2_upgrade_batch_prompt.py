from __future__ import annotations

from pathlib import Path

from .manifest_tools import load_json
from .reporting import write_utf8_text


def build_round2_upgrade_batch_prompt(project_root: Path) -> str:
    overview = load_json(project_root / "reports" / "planning" / "round2_upgrade_overview.json")
    tracks = overview.get("tracks", [])
    high_priority = [item for item in tracks if str(item.get("priority_label", "")).strip() == "high"]
    medium_priority = [item for item in tracks if str(item.get("priority_label", "")).strip() == "medium"]
    low_priority = [item for item in tracks if str(item.get("priority_label", "")).strip() == "low"]

    def render_group(items: list[dict], label: str) -> list[str]:
        lines = [f"{label}:"]
        if not items:
            lines.append("- none")
            return lines
        for item in items:
            lines.append(f"- {item['track_id']} ({item['artist_id']} / {item['likely_mode']})")
        return lines

    lines = [
        "이번 작업은 round2 expansion scaffold 32곡을 weak에서 usable 이상으로 올리는 작업이다.",
        "",
        "현재 상태:",
        "- round2 candidates 40곡 중 8곡은 이미 validated/gold",
        "- 남은 32곡은 scaffolded weak",
        "- 공통 blocker:",
        "  - song_intent.contrast_device missing or empty",
        "  - ready_for_prompting is false",
        "  - high-trust evidence ratio is too low",
        "  - lyric_sources missing",
        "  - metadata_sources missing",
        "  - full_text_status = partial",
        "",
        "중요:",
        "- 창작이 아니라 conditioning 보강 작업이다.",
        "- 기존 track_id, likely_mode, title 방향은 유지할 것.",
        "- 기존 scaffold를 덮어쓸 수 있는 merge-friendly JSON을 곡당 1개씩 제출할 것.",
        "- confirmed / cross_checked / estimated / inferred를 정확히 구분할 것.",
        "- JSON만 제출할 것.",
        "",
        "프로젝트 기준:",
        "- 루트: C:\\JPop_Songwriter\\AKIRA ENGINE",
        "- reliability framework:",
        "  C:\\JPop_Songwriter\\AKIRA ENGINE\\docs\\conditioning-reliability-framework.md",
        "- conditioning spec:",
        "  C:\\JPop_Songwriter\\AKIRA ENGINE\\docs\\track-conditioning-records.md",
        "",
        "전역 참고:",
        "- round2 upgrade overview:",
        "  C:\\JPop_Songwriter\\AKIRA ENGINE\\reports\\planning\\round2_upgrade_overview.md",
        "- external handoff index:",
        "  C:\\JPop_Songwriter\\AKIRA ENGINE\\reports\\planning\\external_handoff_index.md",
        "",
        "artist별 참고 packet/brief:",
        "- C:\\JPop_Songwriter\\AKIRA ENGINE\\data\\_global\\round2_expansion\\<artist_id>\\packet.md",
        "- C:\\JPop_Songwriter\\AKIRA ENGINE\\data\\_global\\round2_expansion\\<artist_id>\\upgrade_brief.md",
        "- C:\\JPop_Songwriter\\AKIRA ENGINE\\data\\_global\\round2_expansion\\<artist_id>\\delegation_prompt.txt",
        "",
        "목표:",
        "- 32곡 전부에 대해",
        "  - lyric_sources / metadata_sources 추가",
        "  - full_text_status 가능하면 full로 승급",
        "  - section_analysis 5개 유지",
        "  - hook_lines 2개 이상 유지",
        "  - song_intent.contrast_device 채우기",
        "  - ready_for_prompting을 true로 올릴 수 있을 만큼 내용 보강",
        "",
        "우선순위:",
    ]
    lines.extend(render_group(high_priority, "high priority"))
    lines.append("")
    lines.extend(render_group(medium_priority, "medium priority"))
    lines.append("")
    lines.extend(render_group(low_priority, "low priority"))
    lines.extend(
        [
            "",
            "출력 경로:",
            "- artist별 incoming 폴더",
            "  - C:\\JPop_Songwriter\\AKIRA ENGINE\\data\\_global\\round2_expansion\\deco27\\incoming",
            "  - C:\\JPop_Songwriter\\AKIRA ENGINE\\data\\_global\\round2_expansion\\pinocchiop\\incoming",
            "  - C:\\JPop_Songwriter\\AKIRA ENGINE\\data\\_global\\round2_expansion\\kanaria\\incoming",
            "  - C:\\JPop_Songwriter\\AKIRA ENGINE\\data\\_global\\round2_expansion\\kairiki_bear\\incoming",
            "  - C:\\JPop_Songwriter\\AKIRA ENGINE\\data\\_global\\round2_expansion\\maretu\\incoming",
            "  - C:\\JPop_Songwriter\\AKIRA ENGINE\\data\\_global\\round2_expansion\\iyowa\\incoming",
            "  - C:\\JPop_Songwriter\\AKIRA ENGINE\\data\\_global\\round2_expansion\\syudou\\incoming",
            "  - C:\\JPop_Songwriter\\AKIRA ENGINE\\data\\_global\\round2_expansion\\neru\\incoming",
            "",
            "파일명:",
            "- <track_id>.json",
            "",
            "금지:",
            "- 새 track_id 생성 금지",
            "- likely_mode를 엉뚱하게 바꾸기 금지",
            "- partial인데 full로 속이기 금지",
            "- confirmed를 근거 없이 쓰기 금지",
            "- 자유서술 해설문만 제출 금지",
            "- 스키마 임의 변경 금지",
        ]
    )
    return "\n".join(lines)


def write_round2_upgrade_batch_prompt(project_root: Path) -> Path:
    out_dir = project_root / "data" / "_global" / "round2_expansion"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "batch_delegation_prompt.txt"
    write_utf8_text(path, build_round2_upgrade_batch_prompt(project_root))
    return path
