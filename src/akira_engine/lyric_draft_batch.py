from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from .lyric_draft import (
    THEME_BANK,
    arc_label_for_record,
    extract_lyric_body,
    extract_section_blocks,
    extract_title,
    generate_best_draft_markdown,
    hook_density_for_record,
    imagery_candidates_for_record,
    load_jsonl,
    lyric_lines,
    section_plan,
    surface_specificity_fraction,
    theme_axes_for_record,
    unique_preserve_order,
)


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def existing_track_ids(output_root: Path) -> set[str]:
    track_ids: set[str] = set()
    if not output_root.exists():
        return track_ids
    for path in output_root.rglob("*.md"):
        track_ids.add(path.stem)
    return track_ids


def select_diverse_records(
    records: list[dict[str, Any]],
    *,
    count: int,
    exclude_track_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    exclude_track_ids = exclude_track_ids or set()
    remaining = [record for record in records if record.get("track_id") not in exclude_track_ids]
    selected: list[dict[str, Any]] = []
    covered_axes: set[str] = set()
    covered_arcs: set[str] = set()
    covered_splits: set[str] = set()

    while remaining and len(selected) < count:
        ranked: list[tuple[int, str, dict[str, Any]]] = []
        for record in remaining:
            axes = set(theme_axes_for_record(record))
            arc = arc_label_for_record(record)
            split = str(record.get("split", ""))
            score = 0
            score += len(axes - covered_axes) * 4
            score += 3 if arc and arc not in covered_arcs else 0
            score += 1 if split and split not in covered_splits else 0
            score += max(0, 6 - len(selected))
            ranked.append((score, str(record.get("track_id", "")), record))

        ranked.sort(key=lambda item: (-item[0], item[1]))
        chosen = ranked[0][2]
        selected.append(chosen)
        covered_axes.update(theme_axes_for_record(chosen))
        arc = arc_label_for_record(chosen)
        if arc:
            covered_arcs.add(arc)
        split = str(chosen.get("split", ""))
        if split:
            covered_splits.add(split)
        remaining = [record for record in remaining if record.get("track_id") != chosen.get("track_id")]

    return selected


def extract_sections(markdown_text: str) -> list[str]:
    return [section for section, _ in extract_section_blocks(markdown_text)]


def section_line_map(markdown_text: str) -> dict[str, list[str]]:
    return {section: lines for section, lines in extract_section_blocks(markdown_text)}


def theme_coverage_score(record: dict[str, Any], markdown_text: str) -> float:
    body = extract_lyric_body(markdown_text)
    blocks = extract_section_blocks(markdown_text)
    axes = theme_axes_for_record(record)
    if not axes:
        return 1.0

    axis_scores: list[float] = []
    anchors = imagery_candidates_for_record(record)
    for axis in axes:
        pool = unique_preserve_order(THEME_BANK.get(axis, []) + anchors)
        hits = [item for item in pool if item and item in body]
        spread = sum(1 for _, lines in blocks if any(item in "\n".join(lines) for item in hits))
        coverage = 0.0
        if hits:
            coverage += 0.45
            coverage += min(0.35, len(unique_preserve_order(hits)) * 0.15)
            coverage += min(0.2, spread * 0.1)
        axis_scores.append(min(1.0, coverage))
    return round(sum(axis_scores) / len(axis_scores), 2)


def imagery_density_score(record: dict[str, Any], markdown_text: str) -> float:
    blocks = extract_section_blocks(markdown_text)
    body = extract_lyric_body(markdown_text)
    candidates = imagery_candidates_for_record(record)
    if not candidates:
        return 0.5
    unique_hits = [item for item in candidates if item in body]
    spread = sum(1 for _, lines in blocks if any(item in "\n".join(lines) for item in unique_hits))
    target = max(5, min(9, len(theme_axes_for_record(record)) + 3))
    score = min(1.0, len(unique_preserve_order(unique_hits)) / target)
    score += min(0.2, spread * 0.04)
    return round(min(1.0, score), 2)


def structure_score(record: dict[str, Any], markdown_text: str) -> float:
    expected = [section for section in section_plan(record) if section]
    actual = extract_sections(markdown_text)
    if not expected:
        return 1.0

    section_hits = sum(1 for section in expected if section in actual)
    order_hits = sum(1 for left, right in zip(expected, actual) if left == right)
    presence_fraction = section_hits / len(expected)
    order_fraction = order_hits / len(expected)

    expected_blocks = len(expected)
    actual_blocks = len(actual)
    count_penalty = 0.0 if expected_blocks == actual_blocks else min(0.2, abs(expected_blocks - actual_blocks) * 0.05)
    return round(max(0.0, min(1.0, (presence_fraction * 0.6 + order_fraction * 0.4) - count_penalty)), 2)


def hook_behavior_score(record: dict[str, Any], markdown_text: str) -> float:
    expected_density = hook_density_for_record(record)
    blocks = section_line_map(markdown_text)
    chorus_lines: list[str] = []
    other_lines: list[str] = []
    for section, lines in blocks.items():
        if section.startswith("chorus"):
            chorus_lines.extend(lines)
        else:
            other_lines.extend(lines)

    chorus_counts = Counter(chorus_lines)
    top_repeat = max(chorus_counts.values(), default=1)
    if expected_density == "high":
        score = 1.0 if 2 <= top_repeat <= 4 else 0.7 if top_repeat >= 1 else 0.4
    elif expected_density == "medium":
        score = 1.0 if 1 <= top_repeat <= 3 else 0.7
    else:
        score = 1.0 if top_repeat <= 1 else 0.7

    repeated_elsewhere = sum(1 for count in Counter(other_lines).values() if count >= 2)
    if repeated_elsewhere >= 2:
        score -= 0.2
    elif repeated_elsewhere == 1:
        score -= 0.1
    return round(max(0.0, min(1.0, score)), 2)


def arc_support_score(record: dict[str, Any], markdown_text: str) -> float:
    arc = arc_label_for_record(record)
    blocks = section_line_map(markdown_text)
    score = 0.0

    if "pre_chorus" in blocks:
        score += 0.2
    if "chorus_final" in blocks:
        score += 0.25

    bridge_text = " ".join(blocks.get("bridge", []))
    if bridge_text and any(marker in bridge_text for marker in ["やっと", "じゃなく", "それでも", "本音", "失くした"]):
        score += 0.25

    chorus_len = len(blocks.get("chorus", []))
    chorus_final_len = len(blocks.get("chorus_final", []))
    final_text = " ".join(blocks.get("chorus_final", []))
    if final_text and any(marker in final_text for marker in ["明日", "ここから", "未来", "踏み出す", "運んでいく"]):
        score += 0.3
    if chorus_final_len > chorus_len:
        score += 0.1

    if arc == "flat_or_circular" and "chorus" in blocks and "chorus_final" in blocks:
        score = max(score, 0.75)
    return round(max(0.0, min(1.0, score)), 2)


def specificity_score(record: dict[str, Any], markdown_text: str) -> float:
    return round(surface_specificity_fraction(record, markdown_text), 2)


def novelty_score(markdown_text: str) -> float:
    lines = lyric_lines(markdown_text)
    if not lines:
        return 0.0
    counts = Counter(lines)
    hook_line, hook_count = counts.most_common(1)[0]
    allowed_hook_duplicates = min(2, max(0, hook_count - 1))
    repeated_excess = 0
    for line, count in counts.items():
        duplicates = max(0, count - 1)
        if line == hook_line:
            duplicates = max(0, duplicates - allowed_hook_duplicates)
        repeated_excess += duplicates
    score = max(0.0, 1.0 - (repeated_excess / max(1, len(lines))))

    opening_counts = Counter(line[:4] for line in lines if len(line) >= 4)
    repeated_openings = sum(max(0, count - 1) for count in opening_counts.values())
    score -= min(0.18, repeated_openings * 0.05)

    scaffold_markers = ["みたいな", "だけが", "だけは", "まま", "手前", "先を", "それでも", "だからこそ", "やっと"]
    scaffold_hits = sum(sum(line.count(marker) for marker in scaffold_markers) for line in lines)
    score -= min(0.28, scaffold_hits * 0.03)
    return round(score, 2)


def title_alignment_score(markdown_text: str) -> float:
    title = extract_title(markdown_text).replace(" ", "")
    if not title:
        return 0.0
    body = extract_lyric_body(markdown_text)
    if title in body:
        return 1.0
    title_parts = [part for part in title.split("の") if len(part) >= 2]
    if any(part in body for part in title_parts):
        return 0.7
    return 0.3


def language_score(markdown_text: str) -> float:
    lines = lyric_lines(markdown_text)
    if not lines:
        return 0.0
    joined = "\n".join(lines)
    ascii_chars = sum(1 for char in joined if char.isascii() and char.isalpha())
    total_chars = sum(1 for char in joined if not char.isspace())
    ascii_ratio = ascii_chars / max(1, total_chars)

    line_lengths = [len(line) for line in lines]
    unique_lengths = len(set(line_lengths))
    variation_bonus = 0.0
    if unique_lengths >= 5:
        variation_bonus = 0.15
    elif unique_lengths >= 3:
        variation_bonus = 0.08

    base = 1.0 if ascii_ratio <= 0.01 else 0.8 if ascii_ratio <= 0.03 else 0.5
    return round(min(1.0, base + variation_bonus), 2)


def safety_score(markdown_text: str) -> float:
    lowered = markdown_text.lower()
    blocked = ["ado", "style of ado", "copy ado", "ado-adjacent"]
    return 0.0 if any(token in lowered for token in blocked) else 1.0


def score_label(total_score: float) -> str:
    if total_score >= 85:
        return "strong"
    if total_score >= 70:
        return "usable"
    return "weak"


def evaluate_draft(record: dict[str, Any], markdown_text: str, output_path: Path) -> dict[str, Any]:
    scores = {
        "theme_coverage": theme_coverage_score(record, markdown_text),
        "imagery_density": imagery_density_score(record, markdown_text),
        "structure": structure_score(record, markdown_text),
        "hook_behavior": hook_behavior_score(record, markdown_text),
        "arc_support": arc_support_score(record, markdown_text),
        "specificity": specificity_score(record, markdown_text),
        "novelty": novelty_score(markdown_text),
        "title_alignment": title_alignment_score(markdown_text),
        "language": language_score(markdown_text),
        "safety": safety_score(markdown_text),
    }
    total = round(
        scores["theme_coverage"] * 15
        + scores["imagery_density"] * 10
        + scores["structure"] * 10
        + scores["hook_behavior"] * 10
        + scores["arc_support"] * 10
        + scores["specificity"] * 15
        + scores["novelty"] * 15
        + scores["title_alignment"] * 5
        + scores["language"] * 5
        + scores["safety"] * 5,
        2,
    )
    return {
        "track_id": record["track_id"],
        "split": record.get("split"),
        "theme_axes": theme_axes_for_record(record),
        "output_path": str(output_path),
        "scores": {**scores, "total": total},
        "label": score_label(total),
    }


def summarize_reviews(reviews: list[dict[str, Any]]) -> dict[str, Any]:
    if not reviews:
        return {"count": 0, "average_score": 0.0, "strong": 0, "usable": 0, "weak": 0}
    return {
        "count": len(reviews),
        "average_score": round(sum(item["scores"]["total"] for item in reviews) / len(reviews), 2),
        "strong": sum(1 for item in reviews if item["label"] == "strong"),
        "usable": sum(1 for item in reviews if item["label"] == "usable"),
        "weak": sum(1 for item in reviews if item["label"] == "weak"),
    }


def render_batch_report(manifest: dict[str, Any]) -> str:
    summary = manifest["summary"]
    lines = [
        f"# {manifest['artist_id']} Lyric Draft Batch Test",
        "",
        f"- Source JSONL: `{manifest['source_jsonl']}`",
        f"- Drafts generated: `{summary['count']}`",
        f"- Average alignment score: `{summary['average_score']}`",
        f"- Strong: `{summary['strong']}`",
        f"- Usable: `{summary['usable']}`",
        f"- Weak: `{summary['weak']}`",
        "",
        "## Review Notes",
        "",
        "- This pass scores not only structural fit but also imagery density, title-body coupling, and novelty.",
        "- Higher scores now require stronger surface realization, not just correct section order.",
        "",
        "## Draft Reviews",
        "",
    ]
    for review in manifest["reviews"]:
        scores = review["scores"]
        lines.extend(
            [
                f"### {review['track_id']}",
                f"- Output: `{review['output_path']}`",
                f"- Theme axes: {', '.join(review['theme_axes'])}",
                f"- Total: `{scores['total']}` ({review['label']})",
                f"- Theme coverage: `{scores['theme_coverage']}`",
                f"- Imagery density: `{scores['imagery_density']}`",
                f"- Structure: `{scores['structure']}`",
                f"- Hook behavior: `{scores['hook_behavior']}`",
                f"- Arc support: `{scores['arc_support']}`",
                f"- Specificity: `{scores['specificity']}`",
                f"- Novelty: `{scores['novelty']}`",
                f"- Title alignment: `{scores['title_alignment']}`",
                f"- Language: `{scores['language']}`",
                f"- Safety: `{scores['safety']}`",
                "",
            ]
        )
    return "\n".join(lines)


def run_batch_draft_test(
    source_jsonl: Path,
    *,
    count: int,
    output_dir: Path,
    existing_output_root: Path | None = None,
    candidate_count: int = 6,
) -> dict[str, Any]:
    records = load_jsonl(source_jsonl)
    if not records:
        raise ValueError(f"No records found in {source_jsonl}")
    artist_id = records[0].get("artist_id", "artist")
    exclude_track_ids = existing_track_ids(existing_output_root) if existing_output_root else set()
    selected = select_diverse_records(records, count=count, exclude_track_ids=exclude_track_ids)

    output_dir.mkdir(parents=True, exist_ok=True)
    reviews: list[dict[str, Any]] = []
    for record in selected:
        markdown_text = generate_best_draft_markdown(record, candidate_count=candidate_count)
        output_path = output_dir / f"{record['track_id']}.md"
        output_path.write_text(markdown_text, encoding="utf-8")
        reviews.append(evaluate_draft(record, markdown_text, output_path))

    manifest = {
        "schema_version": "2.0",
        "artist_id": artist_id,
        "source_jsonl": str(source_jsonl),
        "output_dir": str(output_dir),
        "requested_count": count,
        "candidate_count": candidate_count,
        "selected_track_ids": [record["track_id"] for record in selected],
        "summary": summarize_reviews(reviews),
        "reviews": reviews,
    }
    manifest_path = write_json(output_dir / "batch_test_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest
