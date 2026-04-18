from __future__ import annotations

import hashlib
import json
import random
import re
import sys
from pathlib import Path
from typing import Any

from .demo_planner import build_demo_plan, normalize_demo_plan_for_runtime, render_demo_plan_report
from .demo_renderer import render_demo_candidate, _surface_rewrite
from .demo_critic import score_demo_candidate
from .lyric_utils import unique_preserve_order
from .normalize.mod import contains_bad_script, contains_japanese

# vNext Phase 1 Integration
from .normalize.mod import run_normalize_stage
from .features.mod import run_features_stage
from .conditioning.mod import run_conditioning_stage
from .planner.mod import run_planner_stage, PlanResult
from .pre_audit.mod import run_pre_audit_stage, PreAuditResult
from .renderer.mod import run_renderer_stage
from .critic.mod import run_critic_stage, CriticResult
from .promotion.mod import run_promotion_stage

from .songwriter_io import load_artist_profile, load_conditioning_records

from .songwriter_v2 import (
    build_prompt_package,
    critique_candidate,
    dedupe_candidates,
    build_bestof_candidate,
)
from .gemini_songwriter import (
    generate_markdown as generate_gemini,
    load_api_key as load_gemini_key,
    DEFAULT_MODEL as GEMINI_MODEL,
    DEFAULT_API_URL as GEMINI_API_URL,
)
from .openai_songwriter import (
    generate_markdown_openai as generate_openai,
    load_api_key as load_openai_key,
    DEFAULT_MODEL as OPENAI_MODEL,
    DEFAULT_API_URL as OPENAI_API_URL,
)


# ---------------------------------------------------------------------------
# File I/O helpers
# ---------------------------------------------------------------------------

def _write_utf8_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _write_utf8_text(path: Path, text: str, *, trailing_newline: bool = True) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = text if not trailing_newline or text.endswith("\n") else text + "\n"
    path.write_text(content, encoding="utf-8")
    return path


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _safe_print(message: str) -> None:
    """Print without UnicodeEncodeError on CP949/CP932 terminals."""
    try:
        print(message)
    except UnicodeEncodeError:
        print(message.encode("utf-8", errors="replace").decode("utf-8", errors="replace"))


def _collect_surface_contamination(payload: Any, prefix: str = "") -> list[str]:
    issues: list[str] = []
    critical_surface = (
        prefix.endswith(".core_text")
        or ".required_motifs[" in prefix
        or ".required_imagery[" in prefix
        or ".imagery_focus[" in prefix
        or prefix.endswith(".scene")
        or ".release_markers[" in prefix
        or ".required_new_images[" in prefix
        or ".title_atoms[" in prefix
        or ".hook_atoms[" in prefix
        or ".contrast_terms[" in prefix
    )
    if isinstance(payload, dict):
        for key, value in payload.items():
            if str(key).endswith("_path"):
                continue
            child = f"{prefix}.{key}" if prefix else str(key)
            issues.extend(_collect_surface_contamination(value, child))
        return issues
    if isinstance(payload, list):
        for index, value in enumerate(payload):
            child = f"{prefix}[{index}]"
            issues.extend(_collect_surface_contamination(value, child))
        return issues
    if isinstance(payload, str):
        text = payload.strip()
        allowed_surface = re.compile(r"^[\u3040-\u30ff\u3400-\u9fff々ー・、。！？「」『』（）\s]+$")
        if text and contains_japanese(text) and contains_bad_script(text):
            issues.append(prefix or "value")
        elif critical_surface and text and not allowed_surface.fullmatch(text):
            issues.append(prefix or "value")
    return issues


def _is_clean_surface_text(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    if contains_bad_script(stripped):
        return False
    if not contains_japanese(stripped):
        return False
    allowed_surface = re.compile(r"^[\u3040-\u30ff\u3400-\u9fffー・！？、。0-9\s]+$")
    return bool(allowed_surface.fullmatch(stripped))


def _sanitize_vnext_grounding_card(card: Any) -> dict[str, Any]:
    if hasattr(card, "__dict__"):
        payload = dict(card.__dict__)
    elif isinstance(card, dict):
        payload = dict(card)
    else:
        return {}

    sanitized: dict[str, Any] = {}
    for key, value in payload.items():
        if key in {"required_motifs", "required_imagery", "imagery_focus", "narrative_goals"}:
            if isinstance(value, list):
                sanitized[key] = [
                    text for text in (_safe_text(item) for item in value)
                    if _is_clean_surface_text(text)
                ]
            else:
                sanitized[key] = []
            continue
        if isinstance(value, str):
            text = _safe_text(value)
            if key == "section" or _is_clean_surface_text(text):
                sanitized[key] = text
            else:
                sanitized[key] = ""
            continue
        sanitized[key] = value
    return sanitized


# ---------------------------------------------------------------------------
# Style metadata constants
# ---------------------------------------------------------------------------

_STYLE_KEYWORDS = [
    "Genre:", "Tempo:", "Vocal:", "Instruments:",
    "Beat Concept:", "Mood & Atmosphere:", "Theme:",
]


# ---------------------------------------------------------------------------
# LLM Generation
# ---------------------------------------------------------------------------

def _build_suno_style_block(plan: dict[str, Any]) -> str:
    """Build Suno-compatible style metadata from plan."""
    mode_ctx = plan.get("mode_support_context", {})
    production = ", ".join(mode_ctx.get("production_palette", []))
    vocals = ", ".join(mode_ctx.get("vocal_tones", []))
    mode = _safe_text(plan.get("primary_mode") or plan.get("mode_id"))
    return (
        "\n[SUNO STYLE PACKAGE — USE FOR METADATA BLOCK]:\n"
        f"- Genre: High-fidelity {mode} crossover, {production}\n"
        f"- Vocal: {vocals}, Vocaloid-processed digital texture\n"
        "- Mood: Intrinsic polarity, volatile atmosphere\n"
        "- PRODUCTION HINT: Use 'Pure Musical Texture' and 'Electronic Glitch' tags.\n"
    )


def _generate_llm_candidate(
    plan: dict[str, Any],
    prompt_package: dict[str, Any],
    *,
    index: int,
    api_key: str,
    model_provider: str,
    active_model: str,
    artist_id: str,
    rng: random.Random,
) -> dict[str, Any] | None:
    """Generate a single candidate via LLM (Gemini or OpenAI)."""
    suno_block = _build_suno_style_block(plan)
    generator_prompt = (
        f"{prompt_package.get('generator_prompt', '')}\n{suno_block}\n\n"
        "IMPORTANT: Start your response with the 'Style & Production Metadata' block "
        "(Genre, Tempo, Vocal, etc.) as defined in the system prompt, then the lyrics."
    )
    request_record = {
        "track_id": plan["track_id"],
        "system_prompt": prompt_package["system_prompt"],
        "user_prompt": generator_prompt,
        "output_contract": plan.get("output_contract", {}),
    }

    if model_provider in {"gpt", "openai"}:
        result = generate_openai(
            request_record,
            api_key=api_key,
            model=active_model,
            api_url=OPENAI_API_URL,
            timeout_seconds=60,
            temperature=0.8 + (index * 0.05),
            max_tokens=4096,
            retry_attempts=3,
            sleep_seconds=2.0,
        )
    else:
        result = generate_gemini(
            request_record,
            api_key=api_key,
            model=active_model,
            api_url=GEMINI_API_URL,
            timeout_seconds=60,
            temperature=0.8 + (index * 0.05),
            top_p=0.95,
            max_output_tokens=8192,
            thinking_level=None,
            retry_attempts=3,
            sleep_seconds=2.0,
        )

    if not result["ok"]:
        _safe_print(f"  [LLM ERROR] Candidate {index + 1} failed: {result.get('error')}")
        return None

    raw_markdown = result["markdown"]
    _safe_print(f"  [OK] Candidate {index + 1}: finish={result.get('finish_reason')}, length={len(raw_markdown)}")

    # Separate metadata from lyrics
    lyrics_raw: list[str] = []
    metadata_lines: list[str] = []
    for line in raw_markdown.splitlines():
        ls = line.strip()
        if any(ls.startswith(kw) for kw in _STYLE_KEYWORDS):
            metadata_lines.append(ls)
        elif ls.startswith("# ") or ls.startswith("[") or ls:
            lyrics_raw.append(line)

    # Apply artist fingerprint shaping with deterministic RNG
    shaped_lines = _surface_rewrite(lyrics_raw, artist_id, rng)

    formatted_content = "\n".join(shaped_lines).strip()
    if metadata_lines:
        formatted_content = (
            "### Style & Production Metadata\n"
            + "\n".join(metadata_lines)
            + "\n\n"
            + formatted_content
        )

    return {
        "candidate_id": f"{plan['track_id']}-llm-{index + 1}",
        "variant_index": index + 1,
        "title": _safe_text(plan.get("hook_blueprint", {}).get("core_text")),
        "markdown": formatted_content,
    }


# ---------------------------------------------------------------------------
# Revision Loop
# ---------------------------------------------------------------------------

def _run_revision(
    plan: dict[str, Any],
    prompt_package: dict[str, Any],
    candidate: dict[str, Any],
    notes: list[str],
    *,
    api_key: str,
    model_provider: str,
    active_model: str,
    artist_id: str,
    rng: random.Random,
) -> dict[str, Any]:
    """Revise a low-scoring candidate via LLM."""
    _safe_print(f"  [REVISION] Improving candidate {candidate.get('candidate_id', '?')}...")
    revision_prompt = (
        "Please revise the following lyric to significantly enhance its artist-fidelity. "
        "CRITICAL REQUIREMENTS:\n"
        + "\n".join(f"- {n}" for n in notes)
        + "\n- INJECT more grotesque, surreal, and tactile sensory imagery."
        + "\n- ENSURE RHYTHMIC VARIETY: Avoid robotic, repetitive line structures."
        + f"\n\nOriginal Draft:\n{candidate['markdown']}\n\nReturn one improved markdown version ONLY."
    )
    rev_request = {
        "track_id": plan["track_id"] + "-rev",
        "system_prompt": (
            prompt_package["system_prompt"]
            + "\n\nFOCUS: Hyper-Fidelity Polish. Capture the artist's darkest and most surreal nuances."
        ),
        "user_prompt": revision_prompt,
        "output_contract": plan.get("output_contract", {}),
    }

    if model_provider in {"gpt", "openai"}:
        rev_result = generate_openai(
            rev_request, api_key=api_key, model=active_model, api_url=OPENAI_API_URL,
            timeout_seconds=60, temperature=0.4, max_tokens=4096,
            retry_attempts=2, sleep_seconds=2.0,
        )
    else:
        rev_result = generate_gemini(
            rev_request, api_key=api_key, model=active_model, api_url=GEMINI_API_URL,
            timeout_seconds=60, temperature=0.4, top_p=0.95, max_output_tokens=8192,
            thinking_level=None, retry_attempts=2, sleep_seconds=2.0,
        )

    if not rev_result["ok"]:
        _safe_print("  [REVISION FAILED] Keeping original candidate.")
        return candidate

    rev_lyrics = [
        line for line in rev_result["markdown"].splitlines()
        if not line.strip().startswith("###") and not any(kw in line for kw in _STYLE_KEYWORDS)
    ]
    rev_shaped = _surface_rewrite(rev_lyrics, artist_id, rng)

    # Preserve metadata from original revision or original candidate
    rev_meta = [
        line for line in rev_result["markdown"].splitlines()
        if any(kw in line for kw in _STYLE_KEYWORDS)
    ]
    if not rev_meta:
        rev_meta = [
            line for line in candidate["markdown"].splitlines()
            if any(kw in line for kw in _STYLE_KEYWORDS)
        ]

    final_rev = ""
    if rev_meta:
        final_rev += "### Style & Production Metadata\n" + "\n".join(rev_meta) + "\n\n"
    final_rev += "\n".join(rev_shaped).strip()

    return {
        "candidate_id": candidate["candidate_id"] + "-revised",
        "variant_index": candidate["variant_index"],
        "title": candidate["title"],
        "markdown": final_rev,
    }


# ---------------------------------------------------------------------------
# Critique Result Normalization
# ---------------------------------------------------------------------------

def normalize_demo_critique_result(
    candidate: dict[str, Any],
    base_result: dict[str, Any],
    raw_result: dict[str, Any],
) -> dict[str, Any]:
    demo_scores = dict(raw_result.get("scores", {}))
    base_scores = dict(base_result.get("scores", {}))
    adjusted_total = float(demo_scores.get("adjusted_total", demo_scores.get("total", 0.0)))

    return {
        "candidate_id": _safe_text(raw_result.get("candidate_id")),
        "title": _safe_text(candidate.get("title")),
        "scores": {
            "total": adjusted_total,
            **demo_scores,
            "motif_coverage": float(base_scores.get("motif_coverage", 0.0)),
            "plan_alignment": float(base_scores.get("plan_alignment", 0.0)),
            "hook_control": float(base_scores.get("hook_control", 0.0)),
            "specificity": float(base_scores.get("specificity", 0.0)),
            "novelty": float(base_scores.get("novelty", 0.0)),
            "final_release": float(base_scores.get("final_release", 0.0)),
            "jp_hook_force": float(base_scores.get("jp_hook_force", 0.0)),
            "jp_section_flow": float(base_scores.get("jp_section_flow", 0.0)),
        },
        "critic_notes": list(raw_result.get("critic_notes", raw_result.get("notes", []))),
        "base_critic_notes": list(base_result.get("critic_notes", [])),
        "honest_metrics_active": raw_result.get("honest_metrics_active", False),
    }


# ---------------------------------------------------------------------------
# Report Rendering
# ---------------------------------------------------------------------------

def render_demo_run_report(run_manifest: dict[str, Any]) -> str:
    lines = [
        f"# AKIRA ENGINE: Lyric Generation Report",
        f"- Track ID: `{run_manifest['track_id']}`",
        f"- Artist: `{run_manifest['artist_id']}`",
        f"- Selection Path: `{run_manifest.get('selection_mode', 'RC-2026-03-31 (Frozen Baseline)')}`",
        "",
        "## Performance Snapshot",
    ]
    
    critic = run_manifest.get("critic", {})
    promo = run_manifest.get("promotion_result", {})
    grade = run_manifest.get("grade", "Hold").upper()
    total_score = run_manifest.get("selected_score", 0.0)
    
    lines.append(f"### [GRADE: {grade}] Total Final Score: **{total_score:.2f}**")
    lines.append("")
    
    metrics = {
        "Imagery Coverage": critic.get("imagery_coverage", 0.0),
        "Japanese Ratio": critic.get("japanese_char_ratio", 0.0),
        "Evidence Utilization": critic.get("evidence_utilization", 0.0),
        "Singability": critic.get("singability", 0.0),
        "Prosodic Flow": critic.get("musical_scores", {}).get("prosodic_flow", 0.0) if isinstance(critic.get("musical_scores", {}), dict) else 0.0,
        "Hook Memorability": critic.get("musical_scores", {}).get("hook_memorability", 0.0) if isinstance(critic.get("musical_scores", {}), dict) else 0.0,
        "Legacy Total": critic.get("legacy_total", total_score),
        "Musical Total": critic.get("musical_total", total_score),
        "Blended Total": critic.get("blended_total", total_score),
    }
    
    for label, val in metrics.items():
        # Ensure values are float for formatting
        try:
            f_val = float(val)
        except (TypeError, ValueError):
            f_val = 0.0
        lines.append(f"- **{label}**: `{f_val:.3f}`")
        
    lines.extend([
        "",
        "## Manifest Metadata",
        f"- Record Type: `{run_manifest.get('record_type')}`",
        f"- Schema Version: `{run_manifest.get('schema_version')}`",
        f"- Audit Status: `{run_manifest.get('pre_audit', {}).get('status', 'unknown')}`",
        f"- Honest Mode: `{run_manifest.get('honest_metrics', True)}`",
    ])
    return "\n".join(lines)


def _resolve_generation_backend(
    project_root: Path,
    *,
    requested_generation_mode: str,
    model_provider: str,
    model_name: str | None,
) -> dict[str, str]:
    if requested_generation_mode == "template":
        return {
            "requested_generation_mode": requested_generation_mode,
            "generation_mode": "template",
            "api_key": "",
            "active_model": "",
            "fallback_reason": "",
        }

    try:
        if model_provider in {"gpt", "openai"}:
            api_key = load_openai_key(project_root)
            active_model = model_name or OPENAI_MODEL
        else:
            api_key = load_gemini_key(project_root)
            active_model = model_name or GEMINI_MODEL
    except Exception as exc:
        if requested_generation_mode == "llm":
            raise RuntimeError(f"Requested llm generation but {model_provider} key is unavailable: {exc}") from exc
        return {
            "requested_generation_mode": requested_generation_mode,
            "generation_mode": "template",
            "api_key": "",
            "active_model": "",
            "fallback_reason": f"{model_provider}_key_unavailable",
        }

    return {
        "requested_generation_mode": requested_generation_mode,
        "generation_mode": "llm",
        "api_key": api_key,
        "active_model": active_model,
        "fallback_reason": "",
    }


def _template_revision_candidate(plan: dict[str, Any], *, variant_index: int) -> dict[str, Any]:
    revised = render_demo_candidate(plan, variant_index=variant_index)
    revised["candidate_id"] = revised["candidate_id"].replace("-candidate-", "-template-revision-")
    return revised


# ---------------------------------------------------------------------------
# Main Orchestrator
# ---------------------------------------------------------------------------

def run_demo_songwriter(
    project_root: Path,
    *,
    artist_id: str,
    output_dir: Path,
    candidate_count: int,
    mode_id: str | None = None,
    intent: str = "",
    title_seed: str = "",
    model_provider: str = "gpt",
    model_name: str | None = None,
    generation_mode: str = "auto",
) -> dict[str, Any]:
    """
    Unified demo songwriter pipeline.

    Flow: Plan → Normalize → (LLM Generate | Template Render) → Critique → Revise → Select → Output
    """
    # 1. vNext: Preparatory Normalization & Conditioning (Stage B, C, D)
    primary_artist = artist_id.split("+")[0]
    artist_profile = load_artist_profile(primary_artist) or {}
    
    # Bootstrap from the best available conditioning corpus, including archive roots.
    source_lyric = "..."
    for conditioning_payload in load_conditioning_records(primary_artist):
        sections = conditioning_payload.get("lyric_ground_truth", {}).get("sections", [])
        all_lines: list[str] = []
        for section in sections:
            all_lines.extend(section.get("lines", []))
        if all_lines:
            source_lyric = "\n".join(all_lines)
            break

    # Stage B: Normalize
    norm_result = run_normalize_stage(f"{primary_artist}_source", source_lyric)
    
    # Stage C: Features
    feature_profile = run_features_stage(f"{primary_artist}_source", norm_result.normalized_text)
    
    # Stage D: Conditioning
    conditioning_record = run_conditioning_stage(
        artist_id=primary_artist,
        track_id=f"{primary_artist}_conditioning_vnext",
        normalized_lyric_text=norm_result.normalized_text,
        artist_profile=artist_profile,
        song_intent={"core_theme": [intent or "demo"], "dramatic_arc": ["building"]},
        features=feature_profile,
        normalization_result=norm_result
    )
    
    # Save Conditioning Artifact
    cond_path = _write_utf8_json(output_dir / "conditioning_record.json", conditioning_record.__dict__)

    # 1. Build the plan
    demo_plan = build_demo_plan(
        project_root, artist_id, mode_id=mode_id, intent=intent, title_seed=title_seed,
        conditioning_record=conditioning_record.__dict__
    )
    vnext_plan = run_planner_stage(project_root, artist_id, mode_id=(mode_id or demo_plan.get("mode_id", "default")), title_seed=title_seed)
    pre_audit_result = run_pre_audit_stage(conditioning_record, vnext_plan)
    _write_utf8_json(output_dir / "pre_audit_result.json", pre_audit_result.__dict__)
    if not pre_audit_result.passed:
        raise ValueError(
            "demo_pre_audit_failed: "
            + "; ".join(pre_audit_result.diagnostics[:5])
        )

    runtime_plan = normalize_demo_plan_for_runtime(demo_plan, vnext_plan=vnext_plan)
    runtime_plan["vnext_grounding"] = {
        "motif_roster": [m.__dict__ if hasattr(m, "__dict__") else m for m in vnext_plan.motif_roster],
        "section_cards": [_sanitize_vnext_grounding_card(c) for c in vnext_plan.section_cards]
    }
    contamination_paths = _collect_surface_contamination(
        {
            "hook_blueprint": runtime_plan.get("hook_blueprint", {}),
            "section_cards": runtime_plan.get("section_cards", []),
            "vnext_grounding": runtime_plan.get("vnext_grounding", {}),
        }
    )
    if contamination_paths:
        raise ValueError(
            "demo_runtime_surface_contamination: "
            + ", ".join(contamination_paths[:12])
        )

    # Deterministic RNG
    seed_string = f"{runtime_plan['track_id']}:runtime"
    rng = random.Random(int(hashlib.md5(seed_string.encode("utf-8")).hexdigest()[:8], 16))

    # 2. Resolve generation backend
    backend = _resolve_generation_backend(project_root, requested_generation_mode=generation_mode, model_provider=model_provider, model_name=model_name)
    api_key, active_model = backend["api_key"], backend["active_model"]
    resolved_generation_mode = backend["generation_mode"]
    fallback_reason = backend["fallback_reason"]

    # 3. Execution Engine: Production Loop (Stage L)
    from src.akira_engine.execution.mod import run_production_loop
    
    def _candidate_generator_cb(plan: dict[str, Any], prompt: dict[str, Any], index: int, rng: random.Random) -> dict[str, Any] | None:
        if resolved_generation_mode == "llm":
            return _generate_llm_candidate(plan, prompt, index=index, api_key=api_key, model_provider=model_provider, active_model=active_model, artist_id=artist_id, rng=rng)
        else:
            return run_renderer_stage(plan, variant_index=index, scaffold_mode=(generation_mode == "scaffold"))

    execution_result = run_production_loop(
        project_root,
        runtime_plan,
        build_prompt_package(runtime_plan) if resolved_generation_mode == "llm" else {},
        candidate_generator_fn=_candidate_generator_cb,
        max_candidates=candidate_count
    )
    
    ok = execution_result.get("ok", False)
    winner = execution_result.get("selected_candidate")
    promotion = execution_result.get("promotion")
    winner_score = execution_result.get("critic")
    candidates = execution_result.get("batch_candidates", [])
    
    # 7. Final selection & Output
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_utf8_json(output_dir / "demo_plan.json", demo_plan)
    _write_utf8_json(output_dir / "runtime_plan.json", runtime_plan)
    _write_utf8_json(output_dir / "candidates.json", {"track_id": runtime_plan["track_id"], "candidates": [{"id": c["candidate_id"]} for c in candidates]})
    _write_utf8_json(output_dir / "critic_results.json", {"critic_results": [r.scores for r in execution_result.get("batch_critics", [])]})
    
    winner_path = None
    if winner:
        winner_path = _write_utf8_text(output_dir / "selected_lyric.md", winner["markdown"], trailing_newline=False)
    for c in candidates: 
        _write_utf8_text(output_dir / f"{c['candidate_id']}.md", c["markdown"], trailing_newline=False)
    
    # Generate Prompt Package Hash for traceability
    prompt_package = build_prompt_package(runtime_plan) if resolved_generation_mode == "llm" else {}
    prompt_hash = hashlib.md5(json.dumps(prompt_package, sort_keys=True).encode("utf-8")).hexdigest()[:12] if prompt_package else "template"

    # RC Manifest (Expanded Baseline Schema)
    manifest = {
        "schema_version": "2.1",
        "record_type": "demo_run_manifest",
        "track_id": runtime_plan["track_id"],
        "artist_id": runtime_plan["artist_id"],
        "mode_id": _safe_text(runtime_plan.get("primary_mode")),
        "router_mode": _safe_text(runtime_plan.get("primary_mode", "default")),
        "policy_version": execution_result.get("policy_version", "unknown"),
        "selection_mode": execution_result.get("selection_mode", "legacy_total"),
        "prompt_package_hash": prompt_hash,
        "ok": ok,
        "failure_reason": execution_result.get("failure_reason"),
        "attempt_history": execution_result.get("attempt_history", []),
        "requested_generation_mode": generation_mode,
        "generation_mode": resolved_generation_mode,
        "generation_fallback_reason": fallback_reason,
        "model_provider": model_provider,
        "candidate_count": len(candidates),
        "selected_candidate_id": winner["candidate_id"] if winner else None,
        "honest_metrics": winner_score.honest_metrics_active if winner_score else True,
        "selected_score": execution_result.get(
            "selected_score",
            winner_score.scores.get("blended_total", winner_score.scores.get("total", 0.0)) if winner_score else 0.0,
        ),
        "grade": promotion.grade if promotion else "Fail",
        "pre_audit": pre_audit_result.__dict__,
        "critic": winner_score.scores if winner_score else {},
        "promotion_result": promotion.__dict__ if promotion else {},
        "selection_diagnostics": execution_result.get("selection_diagnostics", {}),
        "selected_lyric_path": str(winner_path) if winner_path else None,
    }
    _write_utf8_text(output_dir / "run_report.md", render_demo_run_report(manifest), trailing_newline=False)
    manifest_path = _write_utf8_json(output_dir / "run_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest
