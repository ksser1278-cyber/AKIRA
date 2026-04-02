from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def render_markdown(record: dict) -> str:
    identity = record["track_identity"]
    intent = record["high_level_intent"]
    conditioning = record["distilled_conditioning"]
    quality = record["quality_flags"]

    lines = [
        f"# {identity['title_core']}",
        "",
        f"- Track ID: `{record['track_id']}`",
        f"- Intent Label: `{intent['intent_label']}`",
        f"- Ready For Conditioning: `{quality['ready_for_conditioning']}`",
        f"- Contrast Device: {intent['contrast_device']}",
        "",
        "## High-Level Intent",
        "",
        f"- Core Purpose: {intent['core_purpose']}",
        f"- Song Job: {intent['song_job']}",
        f"- Narrative Stance: {intent['narrative_stance']}",
        f"- Dramatic Arc: {', '.join(intent['dramatic_arc'])}",
        "",
        "## Section Dossier",
        "",
    ]

    for section in record["section_dossier"]:
        lines.extend(
            [
                f"### {section['section']}",
                f"- Function: {section['function']}",
                f"- Arrangement Intent: {section['arrangement_intent']}",
                f"- Dynamic Role: {section['dynamic_role']}",
                f"- Rhetorical Pattern: {section['rhetorical_pattern']}",
                f"- Source Sections: {', '.join(section['source_sections'])}",
                f"- Line Total: {section['line_total']}",
                "",
            ]
        )

    lines.extend(
        [
            "## Distilled Conditioning",
            "",
            f"- Purpose Axes: {', '.join(conditioning['purpose_axes'])}",
            f"- Preserve: {', '.join(conditioning['preserve'])}",
            f"- Avoid: {', '.join(conditioning['avoid'])}",
            "",
            "### Style Prompt Seed",
            "",
            conditioning["style_prompt_seed"],
            "",
            "## Quality Flags",
            "",
            f"- Curation Recommendation: `{quality['curation_recommendation']}`",
            f"- Caution Flags: {', '.join(quality['caution_flags']) if quality['caution_flags'] else 'none'}",
            f"- Manual Enrichment Recommended For: {', '.join(quality['manual_enrichment_recommended_for'])}",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export one dossier record from dossier JSONL.")
    parser.add_argument("--artist-id", required=True)
    parser.add_argument("--track-id", required=True)
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument(
        "--dossier-root",
        type=Path,
        default=Path("datasets") / "dossiers",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reports") / "dossiers" / "exports",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = args.project_root.resolve()
    dossier_root = args.dossier_root if args.dossier_root.is_absolute() else (project_root / args.dossier_root).resolve()
    output_dir = args.output_dir if args.output_dir.is_absolute() else (project_root / args.output_dir).resolve()

    dossier_path = dossier_root / args.artist_id / "track_dossiers.jsonl"
    records = load_jsonl(dossier_path)
    record = next((item for item in records if item["track_id"] == args.track_id), None)
    if record is None:
        raise FileNotFoundError(f"Track id not found in dossier set: {args.track_id}")

    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{args.artist_id}_{args.track_id}.json"
    md_path = output_dir / f"{args.artist_id}_{args.track_id}.md"

    json_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(record), encoding="utf-8")

    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")


if __name__ == "__main__":
    main()
