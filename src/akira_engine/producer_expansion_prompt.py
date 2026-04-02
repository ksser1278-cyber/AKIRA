from __future__ import annotations

from pathlib import Path

from .producer_expansion_brief import build_producer_expansion_brief
from .reporting import write_utf8_text


def build_producer_expansion_prompt(project_root: Path, artist_id: str) -> str:
    payload = build_producer_expansion_brief(project_root, artist_id)

    lines = [
        f"This is a producer expansion conditioning promotion task for `{artist_id}`.",
        "",
        "Goal:",
        "- Promote scaffolded or weak conditioning records to usable or gold-candidate quality.",
        "- This is dataset enrichment work, not songwriting.",
        "- Keep the existing JSON schema unchanged.",
        "",
        "Rules:",
        "- If full lyric grounding is possible, set `lyric_ground_truth.full_text_status` to `full`.",
        "- If full grounding is not possible, keep it partial and state the limitation honestly.",
        "- Distinguish `confirmed`, `cross_checked`, `estimated`, and `inferred`.",
        "- Fill `source_provenance.lyric_sources` and `source_provenance.metadata_sources`.",
        "- Target at least 5 `section_analysis` entries. If not possible, provide at least 3 and note the limitation.",
        "- Do not leave `hook_lines`, `question_lines`, `prompt_conditioning`, or `quality_control` empty.",
        "- Output JSON only. Do not return free-form commentary.",
        "",
        "Output directory:",
        f"- `C:\\JPop_Songwriter\\AKIRA ENGINE\\data\\_global\\external_handoff\\{artist_id}\\producer_expansion\\incoming`",
        "",
        "Target tracks:",
    ]

    for track in payload.get("tracks", []):
        lines.append(f"- `{track['track_id']}`")
        lines.append(f"  current score: `{track['score']}`")
        lines.append(f"  current full_text_status: `{track['full_text_status']}`")
        lines.append(f"  target file: `{track['target_path']}`")
        lines.append(f"  priority: `{track['priority']}`")
        lines.append(f"  required work: {', '.join(track.get('required_external_work', []))}")
        blockers = track.get("blockers", [])
        warnings = track.get("warnings", [])
        lines.append(f"  blockers: {'; '.join(blockers) if blockers else 'none'}")
        lines.append(f"  warnings: {'; '.join(warnings) if warnings else 'none'}")
        lines.append("")

    lines.extend(
        [
            "Required output format:",
            "- One JSON file per track",
            "- Include `track_identity.track_id`",
            "- Return either a complete replacement JSON or a merge-friendly JSON payload",
            "",
            "Success condition:",
            "- Reduce weak records in producer expansion audit and move them toward usable or better",
            "",
        ]
    )
    return "\n".join(lines)


def write_producer_expansion_prompt(project_root: Path, artist_id: str) -> Path:
    prompt = build_producer_expansion_prompt(project_root, artist_id)
    output_path = project_root / "data" / "_global" / "external_handoff" / artist_id / "producer_expansion" / "delegation_prompt.txt"
    write_utf8_text(output_path, prompt)
    return output_path
