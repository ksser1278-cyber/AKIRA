from __future__ import annotations

from pathlib import Path

from .manifest_tools import load_json
from .reporting import write_utf8_text


def build_round2_upgrade_prompt(project_root: Path, artist_id: str) -> str:
    queue = load_json(project_root / "data" / artist_id / "reference_tracks" / "round2_queue.json")
    round2_dir = project_root / "data" / "_global" / "round2_expansion" / artist_id
    incoming_dir = round2_dir / "incoming"
    targets = [
        str(item.get("track_id", "")).strip()
        for item in queue.get("queue", [])
        if str(item.get("status", "")).strip() == "scaffolded"
    ]
    target_lines = "\n".join(f"- {track_id}" for track_id in targets) or "- none"
    return f"""이번 작업은 round2 scaffold conditioning을 full-grounded usable/gold record로 올리는 작업이다.

artist_id:
- {artist_id}

대상 track_id:
{target_lines}

중요:
- 창작이 아니라 conditioning 보강 작업이다.
- 기존 track_id, likely_mode, title 방향은 유지할 것.
- 기존 scaffold를 덮어쓸 수 있는 merge-friendly JSON을 곡당 1개씩 제출할 것.
- lyric_sources / metadata_sources를 confirmed 또는 cross_checked로 추가할 것.
- full_text_status는 가능하면 full로 올릴 것.
- section_analysis는 최소 5개 유지.
- hook_lines는 최소 2개 유지.
- song_intent.contrast_device를 반드시 채울 것.
- quality_control.ready_for_prompting은 실제 근거가 있을 때만 true로 올릴 것.

출력 경로:
- {incoming_dir}

파일명:
- <track_id>.json
"""


def write_round2_upgrade_prompt(project_root: Path, artist_id: str) -> Path:
    out_dir = project_root / "data" / "_global" / "round2_expansion" / artist_id
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "delegation_prompt.txt"
    write_utf8_text(path, build_round2_upgrade_prompt(project_root, artist_id))
    return path
