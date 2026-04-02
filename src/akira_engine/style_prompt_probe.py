from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .style_prompt_content import load_json, resolve_style_prompt_content
from .suno_package import build_detailed_style_prompt, build_exclude_prompt, build_tag_style_prompt


def build_probe_plan(*, artist_id: str, mode_id: str, mode_atoms: dict[str, Any]) -> dict[str, Any]:
    return {
        "artist_id": artist_id,
        "track_id": f"{artist_id}_{mode_id}_probe",
        "primary_mode": mode_id,
        "arc_label": mode_atoms.get("default_arc_label", "steady_build_to_final_release"),
        "theme_axes": list(mode_atoms.get("default_theme_axes", [])),
        "form_profile": {
            "tags": list(mode_atoms.get("default_form_tags", [])),
        },
    }


def render_probe_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Style Prompt Probe: {payload['mode_id']}",
        "",
        f"- Artist id: `{payload['artist_id']}`",
        f"- Theme axes: `{', '.join(payload['theme_axes'])}`",
        f"- Form tags: `{', '.join(payload['form_tags'])}`",
        f"- Arc: `{payload['arc_label']}`",
        "",
        "## Detailed Style Prompt",
        "```text",
        payload["style_prompt_detailed"],
        "```",
        "",
        "## Tag Prompt Backup",
        "```text",
        payload["style_prompt_tags"],
        "```",
        "",
        "## Exclude Prompt",
        "```text",
        payload["exclude_prompt"],
        "```",
        "",
        "## Style Content Card",
        "```json",
        json.dumps(payload["style_content_card"], ensure_ascii=False, indent=2),
        "```",
        "",
    ]
    return "\n".join(lines)


def build_style_prompt_mode_probes(*, profile_path: Path, output_dir: Path) -> dict[str, Any]:
    profile = load_json(profile_path)
    artist_id = str(profile["artist_id"])
    output_dir.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, Any]] = []
    for mode_id, mode_atoms in profile.get("mode_atoms", {}).items():
        plan = build_probe_plan(artist_id=artist_id, mode_id=mode_id, mode_atoms=dict(mode_atoms))
        style_content = resolve_style_prompt_content(plan=plan, run_dir=profile_path.parent)
        record = {
            "artist_id": artist_id,
            "mode_id": mode_id,
            "theme_axes": plan["theme_axes"],
            "form_tags": plan["form_profile"]["tags"],
            "arc_label": plan["arc_label"],
            "style_prompt_detailed": build_detailed_style_prompt(plan, style_content),
            "style_prompt_tags": build_tag_style_prompt(plan, style_content),
            "exclude_prompt": build_exclude_prompt(plan, style_content),
            "style_content_card": style_content,
        }

        json_path = output_dir / "json" / f"{mode_id}.json"
        markdown_path = output_dir / "markdown" / f"{mode_id}.md"
        json_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        markdown_path.write_text(render_probe_markdown(record), encoding="utf-8")

        record["json_path"] = str(json_path)
        record["markdown_path"] = str(markdown_path)
        records.append(record)

    manifest = {
        "schema_version": "1.0",
        "artist_id": artist_id,
        "profile_path": str(profile_path),
        "output_dir": str(output_dir),
        "record_count": len(records),
        "modes": [record["mode_id"] for record in records],
    }
    manifest_path = output_dir / "style_prompt_probe_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest["manifest_path"] = str(manifest_path)
    return manifest
