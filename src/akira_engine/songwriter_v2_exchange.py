from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in records) + ("\n" if records else ""),
        encoding="utf-8",
    )
    return path


def discover_run_dirs(run_root: Path) -> list[Path]:
    prompt_paths = sorted(run_root.rglob("prompt_package.json"))
    return [path.parent for path in prompt_paths]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


TITLE_PATTERN = re.compile(r"^[\(\[（【]?\s*title\s*[:：]\s*(.+?)\s*[\)\]）】]?\s*$", re.IGNORECASE)
HEADER_WRAPPER_PATTERN = re.compile(r"^[\[\(（【]?\s*(.+?)\s*[\]\)）】]?\s*$")
BOLD_TITLE_PATTERN = re.compile(r"^\*\*(.+?)\*\*$")


def canonical_section_name(label: str) -> str | None:
    normalized = (
        label.strip().lstrip("#").strip()
        .lower()
        .replace("-", " ")
        .replace("_", " ")
        .replace("  ", " ")
        .replace("pre chorus", "pre_chorus")
        .replace("verse 1", "verse_1")
        .replace("verse 2", "verse_2")
        .replace("chorus final", "chorus_final")
        .replace("final chorus", "chorus_final")
    )
    normalized = normalized.replace("chorus  final", "chorus_final")
    normalized = normalized.replace("pre-chorus", "pre_chorus")

    lookup = {
        "intro": "intro",
        "verse_1": "verse_1",
        "verse one": "verse_1",
        "verse_2": "verse_2",
        "verse two": "verse_2",
        "pre_chorus": "pre_chorus",
        "chorus": "chorus",
        "chorus_final": "chorus_final",
        "bridge": "bridge",
        "outro": "outro",
    }
    if normalized in lookup:
        return lookup[normalized]
    return None


def normalize_prediction_markdown(markdown_text: str, track_id: str) -> str:
    lines = markdown_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    output: list[str] = []
    saw_title = False

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            output.append("")
            continue

        title_match = TITLE_PATTERN.match(line)
        if title_match and not saw_title:
            output.append(f"# {title_match.group(1).strip()}")
            saw_title = True
            continue

        bold_title_match = BOLD_TITLE_PATTERN.match(line)
        if bold_title_match and not saw_title:
            candidate_title = bold_title_match.group(1).strip()
            if not canonical_section_name(candidate_title):
                output.append(f"# {candidate_title}")
                saw_title = True
                continue

        if line.startswith("# "):
            output.append(line)
            saw_title = True
            continue

        bare = HEADER_WRAPPER_PATTERN.match(line)
        candidate_label = bare.group(1).strip() if bare else line
        candidate_label = candidate_label.lstrip("#").strip()
        section_name = canonical_section_name(candidate_label)
        if section_name:
            output.append(f"[{section_name}]")
            continue

        output.append(raw_line.rstrip())

    if not saw_title:
        output.insert(0, f"# {track_id}")
        output.insert(1, "")

    normalized_text = "\n".join(output).strip() + "\n"
    return normalized_text


def build_request_record(run_dir: Path) -> dict[str, Any]:
    plan = load_json(run_dir / "plan.json")
    prompt_package = load_json(run_dir / "prompt_package.json")
    total_target_lines = sum(int(card.get("line_target", 0) or 0) for card in plan.get("section_cards", []))
    output_contract = {
        "format": "markdown",
        "required_sections": plan.get("output_contract", {}).get("ordered_headers", []),
        "minimum_characters": max(220, total_target_lines * 12),
        "must_include": [
            "A title line starting with '# '",
            "Section headers like [verse_1], [chorus], [bridge], [chorus_final]",
            "Original Japanese lyrics only",
        ],
        "must_not_include": [
            "artist names",
            "citations",
            "analysis prose outside lyric notes",
        ],
    }
    user_prompt = "\n".join(
        [
            prompt_package["generator_prompt"],
            "Output contract reminders:",
            "- First line must be '# <Japanese title>'.",
            "- Keep the exact section headers and their order.",
            "- Do not add bold title styling, bullets, or explanatory notes.",
            "- Let the longer sections breathe and keep the short pivot sections intentionally compact.",
        ]
    )
    return {
        "request_id": f"{plan['track_id']}-request",
        "track_id": plan["track_id"],
        "artist_id": plan["artist_id"],
        "run_dir": str(run_dir),
        "output_filename": f"{plan['track_id']}.md",
        "schema_version": "1.0",
        "system_prompt": prompt_package["system_prompt"],
        "user_prompt": user_prompt,
        "critic_prompt": prompt_package["critic_prompt"],
        "output_contract": output_contract,
    }


def export_request_bundle(run_root: Path, output_dir: Path) -> dict[str, Any]:
    run_dirs = discover_run_dirs(run_root)
    records = [build_request_record(run_dir) for run_dir in run_dirs]
    records.sort(key=lambda item: item["track_id"])

    jsonl_path = write_jsonl(output_dir / "requests.jsonl", records)
    manifest = {
        "schema_version": "1.0",
        "run_root": str(run_root),
        "output_dir": str(output_dir),
        "request_count": len(records),
        "requests_jsonl": str(jsonl_path),
        "tracks": [record["track_id"] for record in records],
    }
    manifest_path = write_json(output_dir / "request_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def render_request_bundle_report(manifest: dict[str, Any]) -> str:
    lines = [
        "# Songwriter V2 Request Export",
        "",
        f"- Run root: `{manifest['run_root']}`",
        f"- Request count: `{manifest['request_count']}`",
        f"- Requests JSONL: `{manifest['requests_jsonl']}`",
        "",
        "## Tracks",
        "",
    ]
    for track_id in manifest["tracks"]:
        lines.append(f"- `{track_id}`")
    return "\n".join(lines)


def import_prediction_bundle(input_jsonl: Path, output_dir: Path) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    with input_jsonl.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))

    written: list[dict[str, Any]] = []
    for record in records:
        track_id = str(record.get("track_id") or record.get("request_id", "")).replace("-request", "")
        markdown = str(record.get("markdown") or record.get("output_markdown") or "")
        if not track_id or not markdown:
            continue
        output_path = output_dir / f"{track_id}.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        normalized_markdown = normalize_prediction_markdown(markdown, track_id)
        output_path.write_text(normalized_markdown, encoding="utf-8")
        written.append({"track_id": track_id, "output_path": str(output_path)})

    manifest = {
        "schema_version": "1.0",
        "input_jsonl": str(input_jsonl),
        "output_dir": str(output_dir),
        "written_count": len(written),
        "written": written,
    }
    manifest_path = write_json(output_dir / "import_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def render_import_report(manifest: dict[str, Any]) -> str:
    lines = [
        "# Songwriter V2 Prediction Import",
        "",
        f"- Input JSONL: `{manifest['input_jsonl']}`",
        f"- Written markdown files: `{manifest['written_count']}`",
        "",
        "## Outputs",
        "",
    ]
    for item in manifest["written"]:
        lines.append(f"- `{item['track_id']}` -> `{item['output_path']}`")
    return "\n".join(lines)
