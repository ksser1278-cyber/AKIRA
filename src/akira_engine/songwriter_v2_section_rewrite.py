from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .lyric_draft import extract_section_blocks
from .songwriter_v2 import final_release_score
from .songwriter_v2_revision import load_json, render_revision_comparison_report, write_json, write_jsonl


SECTION_HEADER_PATTERN = re.compile(r"^\[(.+?)\]\s*$")


def clean_section_label(label: str) -> str:
    normalized = label.strip().lower().replace("-", "_").replace(" ", "_")
    return normalized


def section_lookup(markdown_text: str) -> dict[str, list[str]]:
    return {section: lines for section, lines in extract_section_blocks(markdown_text)}


def render_section_block(section_name: str, lines: list[str]) -> str:
    output = [f"[{section_name}]"]
    output.extend(lines)
    return "\n".join(output).strip() + "\n"


def normalize_section_markdown(markdown_text: str, section_name: str) -> str:
    lines = markdown_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    output: list[str] = []
    saw_header = False

    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped.startswith("# "):
            continue
        match = SECTION_HEADER_PATTERN.match(stripped)
        if match:
            candidate = clean_section_label(match.group(1))
            if candidate == clean_section_label(section_name):
                output.append(f"[{section_name}]")
                saw_header = True
            continue
        if not saw_header:
            output.append(f"[{section_name}]")
            saw_header = True
        output.append(stripped)

    if not output:
        output = [f"[{section_name}]"]
    if output[0] != f"[{section_name}]":
        output.insert(0, f"[{section_name}]")
    return "\n".join(output).strip() + "\n"


def extract_section_lines(markdown_text: str, section_name: str) -> list[str]:
    for section, lines in extract_section_blocks(markdown_text):
        if clean_section_label(section) == clean_section_label(section_name):
            return lines
    return []


def section_card_lookup(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(card.get("section")): card
        for card in plan.get("section_cards", [])
        if card.get("section")
    }


def section_diagnostic(plan: dict[str, Any], section_name: str, markdown_text: str) -> dict[str, Any]:
    cards = section_card_lookup(plan)
    card = cards.get(section_name, {})
    sections = section_lookup(markdown_text)
    lines = sections.get(section_name, [])
    text = " ".join(lines)
    required_motifs = [motif for motif in card.get("required_motifs", [])[:3] if motif]
    motif_hits = sum(1 for motif in required_motifs if motif in text)
    motif_score = motif_hits / max(1, len(required_motifs))
    line_target = int(card.get("line_target", 0) or 0)
    completeness = min(1.0, len(lines) / max(1, line_target)) if line_target else 1.0
    scene = str(card.get("scene", "")).strip()
    scene_score = 1.0 if scene and scene in text else 0.4 if scene else 0.7
    final_release = 1.0
    if section_name == "chorus_final":
        final_release = final_release_score(
            plan,
            "# temp\n\n" + "\n\n".join(
                [render_section_block(name, section_lines).strip() for name, section_lines in sections.items()]
            )
            + "\n",
        )
    hook_core = str(plan.get("hook_blueprint", {}).get("core_text", "")).strip()
    hook_score = 1.0
    if section_name.startswith("chorus") and hook_core:
        hook_score = 1.0 if hook_core in text else 0.45
    total = round(
        completeness * 0.35
        + motif_score * 0.35
        + scene_score * 0.15
        + hook_score * 0.1
        + final_release * 0.05,
        2,
    )
    return {
        "section_name": section_name,
        "score": total,
        "line_count": len(lines),
        "line_target": line_target,
        "motif_score": round(motif_score, 2),
        "scene_score": round(scene_score, 2),
        "hook_score": round(hook_score, 2),
        "final_release": round(final_release, 2),
        "required_motifs": required_motifs,
        "scene": scene,
        "current_lines": lines,
    }


def neighboring_context(plan: dict[str, Any], markdown_text: str, section_name: str) -> dict[str, str]:
    sections = extract_section_blocks(markdown_text)
    names = [section for section, _ in sections]
    try:
        index = names.index(section_name)
    except ValueError:
        index = -1
    previous_text = ""
    next_text = ""
    if index > 0:
        previous_text = "\n".join(sections[index - 1][1][:2])
    if index >= 0 and index + 1 < len(sections):
        next_text = "\n".join(sections[index + 1][1][:2])
    return {
        "previous_excerpt": previous_text,
        "next_excerpt": next_text,
    }


def build_section_rewrite_request(review: dict[str, Any], section_name: str) -> dict[str, Any]:
    run_dir = Path(review["run_dir"])
    prediction_path = Path(review["prediction_path"])
    plan = load_json(run_dir / "plan.json")
    prompt_package = load_json(run_dir / "prompt_package.json")
    markdown = prediction_path.read_text(encoding="utf-8")
    diagnostic = section_diagnostic(plan, section_name, markdown)
    neighbors = neighboring_context(plan, markdown, section_name)
    card = section_card_lookup(plan).get(section_name, {})
    line_target = int(card.get("line_target", 0) or 0)
    minimum_characters = max(40, line_target * 16)

    user_prompt = "\n".join(
        [
            "Rewrite only one section of this Japanese lyric.",
            "Return markdown for that section only.",
            f"Required section header: [{section_name}]",
            f"Target line count: {line_target}",
            f"Section goal: {card.get('goal', section_name)}",
            f"Scene to preserve or sharpen: {card.get('scene', '')}",
            f"Required motifs to land more clearly: {', '.join(diagnostic['required_motifs'])}",
            f"Hook core to preserve if relevant: {plan.get('hook_blueprint', {}).get('core_text', '')}",
            "Improve the weak points without rewriting the whole song.",
            f"- current section score: {diagnostic['score']}",
            f"- motif score: {diagnostic['motif_score']}",
            f"- completeness: {round(min(1.0, diagnostic['line_count'] / max(1, diagnostic['line_target'] or 1)), 2)}",
            "",
            "Context from neighboring sections:",
            f"- previous excerpt: {neighbors['previous_excerpt'] or '(none)'}",
            f"- next excerpt: {neighbors['next_excerpt'] or '(none)'}",
            "",
            "Current section to replace:",
            render_section_block(section_name, diagnostic["current_lines"]).strip(),
            "",
            "Return only the rewritten section block.",
        ]
    )

    return {
        "request_id": f"{review['track_id']}-{section_name}-section-rewrite",
        "track_id": review["track_id"],
        "artist_id": plan.get("artist_id"),
        "section_name": section_name,
        "source_prediction_path": str(prediction_path),
        "rewrite_mode": "section_rewrite",
        "output_filename": f"{review['track_id']}__{section_name}.md",
        "schema_version": "1.0",
        "system_prompt": (
            "You revise one section of a Japanese lyric while preserving the song's structure. "
            "Return only one markdown section block with the exact requested header. "
            "Do not add a title, commentary, or any extra sections. "
            "Keep the wording original and do not imitate any living artist."
        ),
        "user_prompt": user_prompt,
        "critic_prompt": prompt_package["critic_prompt"],
        "output_contract": {
            "format": "markdown_section",
            "required_sections": [f"[{section_name}]"],
            "max_sections": 1,
            "minimum_characters": minimum_characters,
        },
        "rewrite_context": {
            "section_name": section_name,
            "diagnostic": diagnostic,
            "critic_notes": review.get("critic_notes", []),
        },
    }


def build_section_rewrite_request_bundle(
    scoring_manifest: Path,
    output_dir: Path,
    *,
    score_threshold: float,
    max_tracks: int | None,
    sections_per_track: int,
) -> dict[str, Any]:
    payload = load_json(scoring_manifest)
    reviews = [
        review
        for review in payload.get("reviews", [])
        if float(review.get("scores", {}).get("total", 0.0)) < score_threshold
    ]
    reviews.sort(key=lambda item: float(item.get("scores", {}).get("total", 0.0)))
    if max_tracks is not None:
        reviews = reviews[:max_tracks]

    records: list[dict[str, Any]] = []
    track_sections: dict[str, list[str]] = {}
    for review in reviews:
        run_dir = Path(review["run_dir"])
        plan = load_json(run_dir / "plan.json")
        markdown = Path(review["prediction_path"]).read_text(encoding="utf-8")
        diagnostics = [
            section_diagnostic(plan, card["section"], markdown)
            for card in plan.get("section_cards", [])
            if card.get("section")
        ]
        diagnostics.sort(key=lambda item: (item["score"], item["section_name"]))
        chosen_sections = diagnostics[:sections_per_track]
        track_sections[review["track_id"]] = [item["section_name"] for item in chosen_sections]
        for item in chosen_sections:
            records.append(build_section_rewrite_request(review, item["section_name"]))

    jsonl_path = write_jsonl(output_dir / "requests.jsonl", records)
    manifest = {
        "schema_version": "1.0",
        "source_scoring_manifest": str(scoring_manifest),
        "output_dir": str(output_dir),
        "score_threshold": score_threshold,
        "track_count": len(track_sections),
        "request_count": len(records),
        "sections_per_track": sections_per_track,
        "requests_jsonl": str(jsonl_path),
        "track_sections": track_sections,
    }
    manifest_path = write_json(output_dir / "request_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def render_section_rewrite_request_report(manifest: dict[str, Any]) -> str:
    lines = [
        "# Songwriter V2 Section Rewrite Request Export",
        "",
        f"- Source scoring manifest: `{manifest['source_scoring_manifest']}`",
        f"- Score threshold: `{manifest['score_threshold']}`",
        f"- Track count: `{manifest['track_count']}`",
        f"- Request count: `{manifest['request_count']}`",
        f"- Sections per track: `{manifest['sections_per_track']}`",
        f"- Requests JSONL: `{manifest['requests_jsonl']}`",
        "",
        "## Tracks",
        "",
    ]
    for track_id, sections in manifest["track_sections"].items():
        lines.append(f"- `{track_id}` -> `{', '.join(sections)}`")
    return "\n".join(lines)


def merge_section_into_markdown(original_markdown: str, section_name: str, revised_lines: list[str]) -> str:
    lines = original_markdown.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    output: list[str] = []
    current_section: str | None = None
    replacing = False
    inserted = False

    for raw_line in lines:
        stripped = raw_line.strip()
        match = SECTION_HEADER_PATTERN.match(stripped)
        if match:
            found_section = clean_section_label(match.group(1))
            if replacing and not inserted:
                output.append(f"[{section_name}]")
                output.extend(revised_lines)
                output.append("")
                inserted = True
            replacing = found_section == clean_section_label(section_name)
            current_section = found_section
            if not replacing:
                output.append(raw_line)
            continue

        if replacing:
            continue
        output.append(raw_line)

    if replacing and not inserted:
        output.append(f"[{section_name}]")
        output.extend(revised_lines)
        output.append("")
        inserted = True

    if not inserted:
        output.append(f"[{section_name}]")
        output.extend(revised_lines)
        output.append("")

    return "\n".join(output).strip() + "\n"


def merge_section_prediction_bundle(predictions_jsonl: Path, output_dir: Path) -> dict[str, Any]:
    records = []
    with predictions_jsonl.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))

    merged_markdown: dict[str, str] = {}
    source_paths: dict[str, str] = {}
    revised_sections: dict[str, list[str]] = {}

    for record in records:
        if not record.get("ok"):
            continue
        track_id = str(record.get("track_id", "")).strip()
        section_name = str(record.get("section_name", "")).strip()
        source_prediction_path = str(record.get("source_prediction_path", "")).strip()
        if not track_id or not section_name or not source_prediction_path:
            continue

        source_path = Path(source_prediction_path)
        current_markdown = merged_markdown.get(track_id)
        if current_markdown is None:
            current_markdown = source_path.read_text(encoding="utf-8")

        normalized_section = normalize_section_markdown(str(record.get("markdown", "")), section_name)
        revised_lines = extract_section_lines(normalized_section, section_name)
        if not revised_lines:
            continue

        merged_markdown[track_id] = merge_section_into_markdown(current_markdown, section_name, revised_lines)
        source_paths[track_id] = str(source_path)
        revised_sections.setdefault(track_id, []).append(section_name)

    written: list[dict[str, Any]] = []
    for track_id, markdown in merged_markdown.items():
        output_path = output_dir / f"{track_id}.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        written.append(
            {
                "track_id": track_id,
                "output_path": str(output_path),
                "source_prediction_path": source_paths[track_id],
                "revised_sections": revised_sections.get(track_id, []),
            }
        )

    manifest = {
        "schema_version": "1.0",
        "predictions_jsonl": str(predictions_jsonl),
        "output_dir": str(output_dir),
        "written_count": len(written),
        "written": written,
    }
    manifest_path = write_json(output_dir / "merge_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def render_section_merge_report(manifest: dict[str, Any]) -> str:
    lines = [
        "# Songwriter V2 Section Rewrite Merge",
        "",
        f"- Predictions JSONL: `{manifest['predictions_jsonl']}`",
        f"- Written merged lyrics: `{manifest['written_count']}`",
        "",
        "## Outputs",
        "",
    ]
    for item in manifest["written"]:
        lines.append(
            f"- `{item['track_id']}` -> `{item['output_path']}` "
            f"(sections: {', '.join(item['revised_sections'])})"
        )
    return "\n".join(lines)


def render_section_rewrite_comparison_report(original_scoring: dict[str, Any], revised_scoring: dict[str, Any]) -> str:
    original_scoring["manifest_path"] = original_scoring.get("manifest_path", "")
    revised_scoring["manifest_path"] = revised_scoring.get("manifest_path", "")
    return render_revision_comparison_report(original_scoring, revised_scoring)
