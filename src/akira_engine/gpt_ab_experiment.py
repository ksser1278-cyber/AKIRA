from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .openai_songwriter import DEFAULT_MODEL, generate_markdown_openai, load_api_key


REQUIRED_OUTPUT_SECTIONS = ["[Style Prompt]", "[Lyrics]", "[Self Check]"]
LYRIC_SECTION_NAMES = {
    "intro",
    "verse",
    "verse 1",
    "verse 2",
    "pre-chorus",
    "pre_chorus",
    "chorus",
    "post-chorus",
    "post_chorus",
    "bridge",
    "outro",
}


@dataclass(frozen=True)
class ABExperimentConfig:
    project_root: Path
    output_dir: Path
    intent: str
    style: str
    title_seed: str = ""
    language: str = "ja"
    analysis_dir: Path | None = None
    model_name: str = DEFAULT_MODEL
    execute_api: bool = False
    direct_output_path: Path | None = None
    assisted_output_path: Path | None = None
    allow_ungrounded_assisted: bool = False


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")
    return path


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _section_headers(markdown: str) -> list[str]:
    headers: list[str] = []
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if line.startswith("[") and line.endswith("]") and len(line) > 2:
            headers.append(line)
    return headers


def _section_blocks(markdown: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current = ""
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line.strip("[]").strip()
            sections.setdefault(current, [])
            continue
        if current:
            sections.setdefault(current, []).append(line)
    return sections


def _lyric_lines(markdown: str) -> list[str]:
    sections = _section_blocks(markdown)
    lines: list[str] = []
    in_lyrics = False
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line == "[Lyrics]":
            in_lyrics = True
            continue
        if line == "[Self Check]":
            in_lyrics = False
        if not in_lyrics:
            continue
        if line.startswith("[") and line.endswith("]"):
            continue
        lines.append(line)
    if lines:
        return lines
    excluded = {"Style Prompt", "Self Check"}
    for section, section_lines in sections.items():
        if section not in excluded:
            lines.extend(section_lines)
    return lines


def _japanese_char_count(text: str) -> int:
    return sum(1 for char in text if "\u3040" <= char <= "\u30ff" or "\u4e00" <= char <= "\u9fff")


def _short_line_ratio(lines: list[str]) -> float:
    if not lines:
        return 0.0
    short = sum(1 for line in lines if 2 <= len(line) <= 14)
    return short / len(lines)


def _repeat_ratio(lines: list[str]) -> float:
    normalized = [re.sub(r"\s+", "", line) for line in lines if re.sub(r"\s+", "", line)]
    if not normalized:
        return 0.0
    unique = len(set(normalized))
    return 1.0 - unique / len(normalized)


def _chorus_lines(markdown: str) -> list[str]:
    sections = _section_blocks(markdown)
    lines: list[str] = []
    for section, section_lines in sections.items():
        if "chorus" in section.lower():
            lines.extend(section_lines)
    return lines


def _generic_phrase_penalty(markdown: str) -> float:
    generic_terms = [
        "dream",
        "heart",
        "night",
        "light",
        "feel alive",
        "never let go",
        "kira kira",
        "dokidoki",
        "suki suki",
    ]
    lowered = markdown.lower()
    hits = sum(lowered.count(term) for term in generic_terms)
    return min(20.0, hits * 3.0)


def score_song_output(markdown: str) -> dict[str, Any]:
    text = markdown.strip()
    headers = _section_headers(text)
    lines = _lyric_lines(text)
    chorus = _chorus_lines(text)
    lyric_text = "\n".join(lines)
    jp_ratio = _japanese_char_count(lyric_text) / max(1, len(re.sub(r"\s+", "", lyric_text)))
    repeat_ratio = _repeat_ratio(lines)
    short_ratio = _short_line_ratio(lines)
    lyric_section_count = sum(1 for header in headers if header.strip("[]").lower() in LYRIC_SECTION_NAMES)

    structure = min(20.0, len([section for section in REQUIRED_OUTPUT_SECTIONS if section in headers]) * 5.0 + lyric_section_count * 1.5)
    density = min(20.0, len(lines) * 0.9 + min(8.0, sum(len(line) for line in lines) / max(1, len(lines)) * 0.45))
    hook_repeat = min(1.0, _repeat_ratio(chorus) + _short_line_ratio(chorus) * 0.5)
    hook = min(20.0, len(chorus) * 1.4 + hook_repeat * 10.0)
    phonetic = min(20.0, jp_ratio * 12.0 + short_ratio * 8.0)
    originality = max(0.0, 20.0 - _generic_phrase_penalty(text) - max(0.0, repeat_ratio - 0.35) * 18.0)
    total = round(structure + density + hook + phonetic + originality, 2)

    notes: list[str] = []
    if "[Style Prompt]" not in headers:
        notes.append("missing_style_prompt_section")
    if "[Lyrics]" not in headers:
        notes.append("missing_lyrics_section")
    if "[Self Check]" not in headers:
        notes.append("missing_self_check_section")
    if len(lines) < 16:
        notes.append("low_lyric_line_count")
    if not chorus:
        notes.append("no_chorus_detected")
    if repeat_ratio > 0.45:
        notes.append("repetition_may_be_overused")
    if jp_ratio < 0.45:
        notes.append("low_japanese_script_density")

    return {
        "scores": {
            "total": total,
            "structure": round(structure, 2),
            "density": round(density, 2),
            "hook": round(hook, 2),
            "phonetic": round(phonetic, 2),
            "originality_proxy": round(originality, 2),
        },
        "diagnostics": {
            "line_count": len(lines),
            "chorus_line_count": len(chorus),
            "section_headers": headers,
            "japanese_char_ratio": round(jp_ratio, 3),
            "short_line_ratio": round(short_ratio, 3),
            "repeat_ratio": round(repeat_ratio, 3),
        },
        "notes": notes,
    }


def _load_analysis_summary(analysis_dir: Path | None, *, required: bool = False) -> dict[str, Any]:
    if analysis_dir is None:
        if required:
            raise ValueError("AKIRA-assisted generation requires --analysis-dir with collected analysis outputs.")
        return {}
    final_dir = analysis_dir.resolve()
    ai_profile = _read_json(final_dir / "ai_reconstruction.json") or {}
    pass_5 = _read_json(final_dir / "pass_5_recipe.json") or {}
    validation = _read_json(final_dir / "validation_report.json") or {}
    if required and not ai_profile and not pass_5:
        raise ValueError(f"No AKIRA analysis outputs found in analysis_dir: {final_dir}")
    if validation and validation.get("ok") is False:
        raise ValueError(f"AKIRA analysis validation failed in analysis_dir: {final_dir}")
    profile = ai_profile.get("ai_reconstruction_profile", {}) if isinstance(ai_profile, dict) else {}
    source_fields = [
        profile.get("song_identity", {}),
        profile.get("core_intent", {}),
        profile.get("lyric_engine", {}),
        profile.get("composition_engine", {}),
        profile.get("hook_engine", {}),
        profile.get("reuse_recipe", {}),
        pass_5.get("reuse_strategy", {}),
    ]
    data_fields_present = sum(1 for field in source_fields if field)
    if required and data_fields_present < 2:
        raise ValueError(f"AKIRA analysis summary is too sparse to ground assisted generation: {final_dir}")
    return {
        "analysis_dir": str(final_dir),
        "data_fields_present": data_fields_present,
        "song_identity": profile.get("song_identity", {}),
        "core_intent": profile.get("core_intent", {}),
        "lyric_engine": profile.get("lyric_engine", {}),
        "composition_engine": profile.get("composition_engine", {}),
        "hook_engine": profile.get("hook_engine", {}),
        "reuse_recipe": profile.get("reuse_recipe", pass_5.get("reuse_strategy", {})),
        "avoid": pass_5.get("reuse_strategy", {}).get("avoid", []),
    }


def _request_record(name: str, system_prompt: str, user_prompt: str) -> dict[str, Any]:
    return {
        "request_id": name,
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "output_contract": {
            "format": "markdown",
            "required_sections": REQUIRED_OUTPUT_SECTIONS,
        },
    }


def build_direct_request(config: ABExperimentConfig) -> dict[str, Any]:
    system_prompt = (
        "You are a professional Japanese Vocaloid/subculture songwriter. "
        "Write an original Suno-ready song package. Do not imitate any existing song or quote existing lyrics."
    )
    user_prompt = "\n".join(
        [
            f"Intent: {config.intent}",
            f"Style target: {config.style}",
            f"Title seed: {config.title_seed or '(decide freely)'}",
            f"Language: {config.language}",
            "",
            "Create one complete original song package.",
            "Output exactly these markdown sections:",
            "[Style Prompt]",
            "[Lyrics]",
            "[Self Check]",
            "",
            "Requirements:",
            "- The lyrics must be original.",
            "- Use section tags inside [Lyrics], such as [Intro], [Verse 1], [Pre-Chorus], [Chorus], [Bridge], [Final Chorus], [Outro].",
            "- Prioritize a memorable hook, strong premise, vocaloid-friendly phonetics, and non-generic imagery.",
            "- Keep the style prompt directly usable in Suno.",
        ]
    )
    return _request_record("gpt_direct_baseline", system_prompt, user_prompt)


def build_assisted_request(config: ABExperimentConfig, analysis_summary: dict[str, Any]) -> dict[str, Any]:
    if not analysis_summary:
        raise ValueError("AKIRA-assisted request cannot be built without analysis_summary.")
    system_prompt = (
        "You are a professional Japanese Vocaloid/subculture songwriter. "
        "Use only the supplied AKIRA analysis data as the assisted signal. "
        "Do not invent extra reference data, genre facts, or fake analysis. "
        "Do not imitate any existing song or quote existing lyrics."
    )
    brief_json = json.dumps(analysis_summary, ensure_ascii=False, indent=2)
    user_prompt = "\n".join(
        [
            f"Intent: {config.intent}",
            f"Style target: {config.style}",
            f"Title seed: {config.title_seed or '(decide freely)'}",
            f"Language: {config.language}",
            "",
            "AKIRA collected-analysis data:",
            brief_json,
            "",
            "Use the data above as the only assisted basis.",
            "If a needed detail is absent from the AKIRA data, do not pretend AKIRA supplied it.",
            "",
            "Output exactly these markdown sections:",
            "[Style Prompt]",
            "[Lyrics]",
            "[Self Check]",
            "",
            "Assisted requirements:",
            "- Apply only reusable patterns that are present in the AKIRA data.",
            "- Keep the new song original and separate from reference lyrics.",
            "- In [Self Check], list which AKIRA data fields were actually used.",
            "- In [Self Check], list missing data that limited the assisted result.",
            "- Keep the style prompt directly usable in Suno.",
        ]
    )
    return _request_record("akira_assisted_generation", system_prompt, user_prompt)


def _run_openai_request(project_root: Path, request_record: dict[str, Any], model_name: str) -> dict[str, Any]:
    api_key = load_api_key(project_root)
    return generate_markdown_openai(
        request_record,
        api_key=api_key,
        model=model_name,
        max_tokens=4096,
    )


def compare_outputs(direct_markdown: str, assisted_markdown: str) -> dict[str, Any]:
    direct_score = score_song_output(direct_markdown)
    assisted_score = score_song_output(assisted_markdown)
    direct_total = float(direct_score["scores"]["total"])
    assisted_total = float(assisted_score["scores"]["total"])
    delta = round(assisted_total - direct_total, 2)
    if delta > 3:
        verdict = "assisted_wins"
    elif delta < -3:
        verdict = "direct_wins"
    else:
        verdict = "tie_or_manual_review"
    return {
        "schema_version": "1.0",
        "record_type": "gpt_ab_comparison",
        "verdict": verdict,
        "assisted_minus_direct": delta,
        "direct": direct_score,
        "assisted": assisted_score,
        "warning": "Heuristic comparison only. Use as a regression signal, not final artistic judgment.",
    }


def render_ab_report(manifest: dict[str, Any]) -> str:
    comparison = manifest.get("comparison", {})
    lines = [
        "# GPT Direct vs AKIRA-Assisted Experiment",
        "",
        f"- Intent: `{manifest.get('intent', '')}`",
        f"- Style: `{manifest.get('style', '')}`",
        f"- Title seed: `{manifest.get('title_seed', '')}`",
        f"- Execution status: `{manifest.get('execution_status', '')}`",
        f"- Verdict: `{comparison.get('verdict', 'not_compared')}`",
        f"- Assisted minus direct: `{comparison.get('assisted_minus_direct', '')}`",
        "",
        "## Outputs",
        "",
    ]
    output_paths = manifest.get("output_paths", {})
    for key in ("direct_request", "assisted_request", "direct_output", "assisted_output", "comparison"):
        if output_paths.get(key):
            lines.append(f"- {key}: `{output_paths[key]}`")
    if comparison:
        lines.extend(
            [
                "",
                "## Scores",
                "",
                f"- Direct total: `{comparison['direct']['scores']['total']}`",
                f"- Assisted total: `{comparison['assisted']['scores']['total']}`",
                f"- Direct notes: `{', '.join(comparison['direct']['notes']) or 'none'}`",
                f"- Assisted notes: `{', '.join(comparison['assisted']['notes']) or 'none'}`",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def run_gpt_ab_experiment(config: ABExperimentConfig) -> dict[str, Any]:
    output_dir = config.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    needs_assisted = (
        config.execute_api
        or config.assisted_output_path is not None
        or config.analysis_dir is not None
        or config.allow_ungrounded_assisted
    )
    require_analysis = needs_assisted and not config.allow_ungrounded_assisted
    analysis_summary = _load_analysis_summary(config.analysis_dir, required=require_analysis)
    if config.allow_ungrounded_assisted and not analysis_summary:
        analysis_summary = {
            "analysis_dir": "",
            "data_fields_present": 0,
            "debug_warning": "Ungrounded assisted generation was explicitly allowed. Do not use this as AKIRA evidence.",
        }
    direct_request = build_direct_request(config)
    assisted_request = build_assisted_request(config, analysis_summary) if analysis_summary else None

    direct_request_path = _write_json(output_dir / "direct_request.json", direct_request)
    _write_text(output_dir / "direct_prompt.md", direct_request["user_prompt"])
    assisted_request_path = None
    if assisted_request:
        assisted_request_path = _write_json(output_dir / "assisted_request.json", assisted_request)
        _write_text(output_dir / "assisted_prompt.md", assisted_request["user_prompt"])

    direct_markdown = ""
    assisted_markdown = ""
    api_results: dict[str, Any] = {}
    execution_status = "prompt_only"

    if config.direct_output_path and config.direct_output_path.exists():
        direct_markdown = config.direct_output_path.read_text(encoding="utf-8")
    if config.assisted_output_path and config.assisted_output_path.exists():
        assisted_markdown = config.assisted_output_path.read_text(encoding="utf-8")

    if config.execute_api:
        if assisted_request is None:
            raise ValueError("API A/B execution requires grounded assisted_request from --analysis-dir.")
        direct_result = _run_openai_request(config.project_root, direct_request, config.model_name)
        assisted_result = _run_openai_request(config.project_root, assisted_request, config.model_name)
        api_results = {"direct": direct_result, "assisted": assisted_result}
        direct_markdown = direct_result.get("markdown", "")
        assisted_markdown = assisted_result.get("markdown", "")
        execution_status = "api_executed"
    elif direct_markdown and assisted_markdown:
        execution_status = "external_outputs_compared"

    output_paths = {
        "direct_request": str(direct_request_path),
        "direct_prompt": str((output_dir / "direct_prompt.md").resolve()),
    }
    if assisted_request_path:
        output_paths["assisted_request"] = str(assisted_request_path)
        output_paths["assisted_prompt"] = str((output_dir / "assisted_prompt.md").resolve())
    if direct_markdown:
        output_paths["direct_output"] = str(_write_text(output_dir / "direct_output.md", direct_markdown))
    if assisted_markdown:
        output_paths["assisted_output"] = str(_write_text(output_dir / "assisted_output.md", assisted_markdown))

    comparison = {}
    if direct_markdown and assisted_markdown:
        comparison = compare_outputs(direct_markdown, assisted_markdown)
        output_paths["comparison"] = str(_write_json(output_dir / "comparison.json", comparison))

    if api_results:
        output_paths["api_results"] = str(_write_json(output_dir / "api_results.json", api_results))

    manifest = {
        "schema_version": "1.0",
        "record_type": "gpt_ab_experiment_manifest",
        "intent": config.intent,
        "style": config.style,
        "title_seed": config.title_seed,
        "language": config.language,
        "analysis_dir": str(config.analysis_dir.resolve()) if config.analysis_dir else "",
        "analysis_required": require_analysis,
        "analysis_data_fields_present": analysis_summary.get("data_fields_present", 0) if analysis_summary else 0,
        "model_name": config.model_name,
        "execution_status": execution_status,
        "comparison": comparison,
        "output_paths": output_paths,
    }
    manifest_path = _write_json(output_dir / "ab_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    report_path = _write_text(output_dir / "ab_report.md", render_ab_report(manifest))
    manifest["output_paths"]["report"] = str(report_path)
    _write_json(output_dir / "ab_manifest.json", manifest)
    return manifest
