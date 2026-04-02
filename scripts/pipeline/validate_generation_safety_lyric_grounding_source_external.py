from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.reporting import write_utf8_json, write_utf8_text

HIRAGANA_KATAKANA_KANJI_RE = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff]")
HANGUL_RE = re.compile(r"[\u1100-\u11ff\u3130-\u318f\uac00-\ud7af]")
PLACEHOLDER_TERMS = [
    "Initial scenario setting",
    "Establishing the baseline emotion",
    "Rising tension",
    "Preparing the twist",
    "Peak expression",
    "Maximal sonic release",
    "placeholder",
    "scaffold",
    "summary",
]
DISALLOWED_SOURCE_TERMS = [
    "fandom.com",
    "wikia.com",
    "miraheze",
    "vocaloid lyrics wiki",
    "forum",
    "blog",
    "lyricstranslate",
    "machine translation",
    "ai-generated",
]
ACCEPTED_SOURCE_HINTS = [
    "official",
    "distributor",
    "tunecore",
    "linkco",
    "linkcore",
    "uta-net",
    "utaten",
    "petitlyrics",
    "j-lyric",
]
OFFICIAL_SOURCE_HINTS = [
    "official",
    "distributor",
    "tunecore",
    "linkco",
    "linkcore",
    "piapro",
]
SUPPORTING_SOURCE_HINTS = [
    "awa",
    "kkbox",
    "oricon",
]
LYRIC_DB_HINTS = [
    "uta-net",
    "utaten",
    "petitlyrics",
    "j-lyric",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate lyric grounding source-acquisition bundles before internal use.")
    parser.add_argument("--artist-id", required=True)
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--project-root", default=".")
    return parser.parse_args()


def _string_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value]
    return []


def _lines_from_sections(sections: object) -> list[str]:
    lines: list[str] = []
    if not isinstance(sections, list):
        return lines
    for section in sections:
        if not isinstance(section, dict):
            continue
        lines.extend(_string_list(section.get("lines")))
    return lines


def _contains_placeholder(texts: list[str]) -> bool:
    joined = "\n".join(texts).lower()
    return any(term.lower() in joined for term in PLACEHOLDER_TERMS)


def _contains_hangul(texts: list[str]) -> bool:
    return any(HANGUL_RE.search(text) for text in texts)


def _has_japanese(texts: list[str]) -> bool:
    return any(HIRAGANA_KATAKANA_KANJI_RE.search(text) for text in texts)


def _has_bad_encoding(texts: list[str]) -> bool:
    return any("\ufffd" in text or "??" in text for text in texts)


def _validate_sources(sources: object) -> list[str]:
    issues: list[str] = []
    if not isinstance(sources, list) or not sources:
        return ["source_provenance.lyric_sources missing"]
    accepted_hits = 0
    official_hits = 0
    lyric_db_hits = 0
    supporting_hits = 0
    for index, item in enumerate(sources):
        if not isinstance(item, dict):
            issues.append(f"lyric_sources[{index}] is not an object")
            continue
        label = str(item.get("label", "")).strip()
        url = str(item.get("url", "")).strip()
        status = str(item.get("status", "")).strip()
        if not label:
            issues.append(f"lyric_sources[{index}].label missing")
        if not url:
            issues.append(f"lyric_sources[{index}].url missing")
        if not status:
            issues.append(f"lyric_sources[{index}].status missing")
        lowered = f"{label} {url} {status}".lower()
        if any(term in lowered for term in DISALLOWED_SOURCE_TERMS):
            issues.append(f"lyric_sources[{index}] uses disallowed source class")
        if any(term in lowered for term in ACCEPTED_SOURCE_HINTS):
            accepted_hits += 1
        if any(term in lowered for term in OFFICIAL_SOURCE_HINTS):
            official_hits += 1
        if any(term in lowered for term in LYRIC_DB_HINTS):
            lyric_db_hits += 1
        if any(term in lowered for term in SUPPORTING_SOURCE_HINTS):
            supporting_hits += 1
    if accepted_hits == 0:
        issues.append("no trusted lyric source hint detected")
    if official_hits == 0 and lyric_db_hits + supporting_hits < 2:
        issues.append("single-source lyric bundle requires official or cross-checked support")
    return issues


def validate_bundle(payload: dict[str, object]) -> list[str]:
    issues: list[str] = []
    track_id = str(payload.get("track_identity", {}).get("track_id", "")).strip() if isinstance(payload.get("track_identity"), dict) else ""
    if not track_id:
        issues.append("track_identity.track_id missing")

    source_provenance = payload.get("source_provenance", {})
    if not isinstance(source_provenance, dict):
        source_provenance = {}
    issues.extend(_validate_sources(source_provenance.get("lyric_sources")))
    notes = source_provenance.get("notes")
    if isinstance(notes, str):
        notes_list = [notes] if notes.strip() else []
    elif isinstance(notes, list):
        notes_list = [str(item) for item in notes if str(item).strip()]
    else:
        notes_list = []
    if not notes_list:
        issues.append("source_provenance.notes missing")

    lyric_ground_truth = payload.get("lyric_ground_truth", {})
    if not isinstance(lyric_ground_truth, dict):
        lyric_ground_truth = {}
    if str(lyric_ground_truth.get("full_text_status", "")).strip() != "full":
        issues.append("lyric_ground_truth.full_text_status must be full")
    sections = lyric_ground_truth.get("sections")
    hooks = lyric_ground_truth.get("hook_lines")
    section_lines = _lines_from_sections(sections)
    hook_lines = _string_list(hooks)
    if not section_lines:
        issues.append("lyric_ground_truth.sections missing grounded lines")
    if not hook_lines:
        issues.append("lyric_ground_truth.hook_lines missing")

    edited_texts = section_lines + hook_lines
    if _has_bad_encoding(edited_texts):
        issues.append("bad encoding markers detected in sections or hook_lines")
    if _contains_placeholder(edited_texts):
        issues.append("placeholder or summary text detected in sections or hook_lines")
    if _contains_hangul(edited_texts):
        issues.append("non-Japanese script contamination detected in sections or hook_lines")
    if not _has_japanese(edited_texts):
        issues.append("sections and hook_lines do not contain Japanese lyric text")
    return issues


def render_report(payload: dict[str, object]) -> str:
    lines = [
        f"# Lyric Grounding Source Validation: {payload['artist_id']}",
        "",
        f"- Input dir: `{payload['input_dir']}`",
        f"- Valid: `{payload['valid_count']}`",
        f"- Invalid: `{payload['invalid_count']}`",
        "",
        "## Results",
        "",
    ]
    for item in payload["results"]:
        lines.extend(
            [
                f"### {item['filename']}",
                f"- Track id: `{item['track_id']}`",
                f"- Valid: `{item['valid']}`",
                *([f"- Issues: {'; '.join(item['issues'])}"] if item["issues"] else ["- Issues: none"]),
                "",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    input_dir = Path(args.input_dir).resolve()
    if not input_dir.exists():
        raise SystemExit(f"Input directory not found: {input_dir}")

    results = []
    for path in sorted(input_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        issues = validate_bundle(payload)
        track_id = ""
        if isinstance(payload.get("track_identity"), dict):
            track_id = str(payload["track_identity"].get("track_id", "")).strip()
        results.append(
            {
                "filename": path.name,
                "track_id": track_id,
                "valid": not issues,
                "issues": issues,
            }
        )

    output = {
        "schema_version": "1.0",
        "artist_id": args.artist_id,
        "input_dir": str(input_dir),
        "valid_count": sum(1 for item in results if item["valid"]),
        "invalid_count": sum(1 for item in results if not item["valid"]),
        "results": results,
    }
    out_dir = project_root / "reports" / "quality" / "external_validation"
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = write_utf8_json(out_dir / f"{args.artist_id}_generation_safety_lyric_grounding_source_validation.json", output)
    report_path = write_utf8_text(
        out_dir / f"{args.artist_id}_generation_safety_lyric_grounding_source_validation.md",
        render_report(output),
        trailing_newline=False,
    )
    print(manifest_path)
    print(report_path)
    if output["invalid_count"] > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
