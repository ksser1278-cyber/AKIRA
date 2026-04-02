from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DIMENSIONS = [
    "voice_fit",
    "arrangement_fit",
    "chorus_lift",
    "emotional_arc",
    "lyric_naturalness",
    "overall",
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records)
    path.write_text(text, encoding="utf-8")
    return path


def clean_text(value: str) -> str:
    return " ".join(str(value).strip().split())


def format_terms(items: list[str], *, count: int) -> str:
    cleaned = [clean_text(item) for item in items if clean_text(item)]
    return ", ".join(cleaned[:count])


def source_record_id(payload: dict[str, Any]) -> str:
    if payload.get("track_id"):
        return clean_text(payload["track_id"])
    if payload.get("mode_id"):
        return clean_text(payload["mode_id"])
    raise ValueError("Record must contain either track_id or mode_id")


def source_record_label(payload: dict[str, Any]) -> str:
    if payload.get("title"):
        return clean_text(payload["title"])
    if payload.get("mode_id"):
        return clean_text(payload["mode_id"])
    return source_record_id(payload)


def source_record_type(payload: dict[str, Any]) -> str:
    if payload.get("lyric_markdown"):
        return "suno_song_bundle"
    return "style_prompt_probe"


def build_minimal_core_prompt(payload: dict[str, Any]) -> str:
    card = payload.get("style_content_card", {})
    genre_text = format_terms(card.get("genre_anchors", []), count=2) or "cinematic J-pop"
    tempo_text = format_terms(card.get("tempo_feels", []), count=1) or "midtempo"
    groove_text = format_terms(card.get("groove_anchors", []), count=1)
    vocal_text = format_terms(card.get("vocal_tones", []), count=1) or "Japanese lead vocal"
    production_text = format_terms(card.get("production_palette", []), count=3)
    arrangement_text = format_terms(card.get("arrangement_moves", []), count=2)
    arc_text = clean_text(card.get("energy_arc", "")) or "save the clearest release for the final chorus"

    sentences = [
        f"{genre_text} at {tempo_text} with {vocal_text}.",
        f"Groove: {groove_text}." if groove_text else "",
        f"Production: {production_text}." if production_text else "",
        f"Arrangement: {arrangement_text}." if arrangement_text else "",
        f"Arc: {arc_text}.",
        "Japanese topline only.",
    ]
    return " ".join(sentence for sentence in sentences if sentence)


def variant_records(payload: dict[str, Any]) -> list[dict[str, Any]]:
    pair_id = source_record_id(payload)
    shared = {
        "pair_id": pair_id,
        "label": source_record_label(payload),
        "source_type": source_record_type(payload),
        "exclude_prompt": clean_text(payload.get("exclude_prompt", "")),
        "advanced_options": payload.get("advanced_options", {}),
        "lyric_box_guidance": payload.get("lyric_box_guidance", {}),
        "lyric_markdown": payload.get("lyric_markdown"),
        "style_content_card": payload.get("style_content_card", {}),
    }

    return [
        {
            **shared,
            "run_id": f"{pair_id}-A",
            "variant_id": "A",
            "variant_label": "balanced_detailed",
            "style_prompt": clean_text(payload.get("style_prompt_detailed") or payload.get("style_prompt", "")),
        },
        {
            **shared,
            "run_id": f"{pair_id}-B",
            "variant_id": "B",
            "variant_label": "minimal_core",
            "style_prompt": build_minimal_core_prompt(payload),
        },
    ]


def load_source_records(source_dir: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(source_dir.glob("*.json")):
        payload = load_json(path)
        if payload.get("style_prompt_tags") and (payload.get("style_prompt_detailed") or payload.get("style_prompt")):
            records.append(payload)
    return records


def blank_result_record(variant: dict[str, Any]) -> dict[str, Any]:
    return {
        "pair_id": variant["pair_id"],
        "run_id": variant["run_id"],
        "variant_id": variant["variant_id"],
        "variant_label": variant["variant_label"],
        "voice_fit": None,
        "arrangement_fit": None,
        "chorus_lift": None,
        "emotional_arc": None,
        "lyric_naturalness": None,
        "overall": None,
        "preference_rank": None,
        "suno_url": None,
        "notes": None,
    }


def render_pair_scorecard(pair: dict[str, Any]) -> str:
    lines = [
        f"# Suno A/B Scorecard: {pair['pair_id']}",
        "",
        f"- Label: `{pair['label']}`",
        f"- Source type: `{pair['source_type']}`",
        "- Rule: keep everything except the style prompt constant when possible.",
        "- Score each dimension on a 1-10 scale.",
        "",
    ]

    for variant in pair["variants"]:
        lines.extend(
            [
                f"## Variant {variant['variant_id']}: {variant['variant_label']}",
                "",
                "### Style Prompt",
                "```text",
                variant["style_prompt"],
                "```",
                "",
                "### Exclude Prompt",
                "```text",
                variant["exclude_prompt"],
                "```",
                "",
            ]
        )

        lyric_box_guidance = variant.get("lyric_box_guidance") or {}
        if lyric_box_guidance:
            lines.extend(
                [
                    "### Lyrics Box Guidance",
                    f"- Default strategy: {lyric_box_guidance.get('default_strategy', '')}",
                    f"- Optional context header: `{lyric_box_guidance.get('optional_context_header', '')}`",
                    f"- Language guardrail: {lyric_box_guidance.get('language_guardrail', '')}",
                    f"- Editing hint: {lyric_box_guidance.get('editing_hint', '')}",
                    "",
                ]
            )

        if variant.get("lyric_markdown"):
            lines.extend(
                [
                    "### Lyrics",
                    "",
                    variant["lyric_markdown"].strip(),
                    "",
                ]
            )

        lines.extend(
            [
                "### Manual Scores",
                "- Voice fit:",
                "- Arrangement fit:",
                "- Chorus lift:",
                "- Emotional arc:",
                "- Lyric naturalness:",
                "- Overall:",
                "- Preference rank within this pair:",
                "- Suno URL:",
                "- Notes:",
                "",
            ]
        )

    return "\n".join(lines)


def render_runbook(manifest: dict[str, Any]) -> str:
    lines = [
        "# Suno A/B Runbook",
        "",
        "- Keep the lyric box, sliders, and excludes constant inside each pair.",
        "- Only change the style prompt between Variant A and Variant B.",
        "- If Suno drifts hard, rerun both variants once before judging.",
        "- Rank the pair after listening to both versions back to back.",
        "",
        "## Scoring Dimensions",
        "",
        "- `voice_fit`: does the voice behave the way the prompt intends?",
        "- `arrangement_fit`: does the instrumentation/production match the intended mode?",
        "- `chorus_lift`: does the chorus open and release properly?",
        "- `emotional_arc`: does the song rise or turn the way the prompt asked?",
        "- `lyric_naturalness`: if lyrics are present, do they sit naturally in the performance?",
        "- `overall`: overall musical usefulness",
        "",
        "## Pairs",
        "",
    ]
    for pair in manifest["pairs"]:
        lines.append(f"- `{pair['pair_id']}`: {pair['label']} ({pair['source_type']})")
    return "\n".join(lines)


def build_suno_ab_test_pack(*, source_dir: Path, output_dir: Path) -> dict[str, Any]:
    source_records = load_source_records(source_dir)
    pairs: list[dict[str, Any]] = []
    result_records: list[dict[str, Any]] = []

    for payload in source_records:
        variants = variant_records(payload)
        pair = {
            "pair_id": variants[0]["pair_id"],
            "label": variants[0]["label"],
            "source_type": variants[0]["source_type"],
            "variants": variants,
        }
        pairs.append(pair)
        result_records.extend(blank_result_record(variant) for variant in variants)

        scorecard_path = output_dir / "scorecards" / f"{pair['pair_id']}.md"
        scorecard_path.parent.mkdir(parents=True, exist_ok=True)
        scorecard_path.write_text(render_pair_scorecard(pair), encoding="utf-8")

    manifest = {
        "schema_version": "1.0",
        "source_dir": str(source_dir),
        "output_dir": str(output_dir),
        "record_count": len(pairs),
        "variant_count_per_pair": 2,
        "dimensions": DIMENSIONS,
        "pairs": pairs,
    }

    manifest_path = write_json(output_dir / "suno_ab_test_manifest.json", manifest)
    results_path = write_jsonl(output_dir / "results_template.jsonl", result_records)
    runbook_path = output_dir / "runbook.md"
    runbook_path.write_text(render_runbook(manifest), encoding="utf-8")

    manifest["manifest_path"] = str(manifest_path)
    manifest["results_template_path"] = str(results_path)
    manifest["runbook_path"] = str(runbook_path)
    return manifest
