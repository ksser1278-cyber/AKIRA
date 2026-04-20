from __future__ import annotations

from pathlib import Path
from typing import Any

from .gemini_songwriter import (
    DEFAULT_API_URL as GEMINI_DEFAULT_API_URL,
    DEFAULT_MODEL as GEMINI_DEFAULT_MODEL,
    generate_markdown as generate_gemini_markdown,
    load_api_key as load_gemini_api_key,
)
from .lyric_utils import contains_bad_script, contains_japanese, safe_text
from .openai_songwriter import (
    DEFAULT_API_URL as OPENAI_DEFAULT_API_URL,
    DEFAULT_MODEL as OPENAI_DEFAULT_MODEL,
    generate_markdown_openai,
    load_api_key as load_openai_api_key,
)


def _resolve_api_project_root(project_root: Path) -> Path:
    current = project_root.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "config" / ".env").exists():
            return candidate
    return current


def _chorus_shape_id(form_family_id: str) -> str:
    if safe_text(form_family_id) == "compressed_hook":
        return "repeat_punch"
    if safe_text(form_family_id) == "hybrid_release":
        return "statement_hook_release"
    return "default"


def _bridge_shape_id(form_family_id: str) -> str:
    if safe_text(form_family_id) == "compressed_hook":
        return "withholding_drop"
    if safe_text(form_family_id) == "hybrid_release":
        return "perspective_delay"
    return "default"


def _count_hook_mentions(markdown: str, hook: str) -> int:
    hook_text = safe_text(hook).replace(" ", "")
    if not hook_text:
        return 0
    count = 0
    for raw_line in markdown.splitlines():
        line = raw_line.strip().replace(" ", "")
        if not line or line.startswith("#") or (line.startswith("[") and line.endswith("]")):
            continue
        count += line.count(hook_text)
    return count


def _realized_hook_pressure(markdown: str, hook: str) -> str:
    mentions = _count_hook_mentions(markdown, hook)
    if mentions >= 5:
        return "high"
    if mentions >= 3:
        return "medium"
    return "low"


def _normalize_markdown(markdown: str) -> str:
    text = safe_text(markdown).strip()
    if not text:
        return ""
    if not text.endswith("\n"):
        text += "\n"
    return text


def _provider_name(model_provider: str) -> str:
    provider = safe_text(model_provider).lower()
    if provider in {"gpt", "openai"}:
        return "openai"
    if provider in {"gemini", "google"}:
        return "gemini"
    return provider or "openai"


def generate_candidate_via_api(
    project_root: Path,
    runtime_plan: dict[str, Any],
    prompt_package: dict[str, Any],
    *,
    candidate_index: int,
    model_provider: str,
    model_name: str | None,
) -> dict[str, Any]:
    provider = _provider_name(model_provider)
    api_project_root = _resolve_api_project_root(project_root)
    if provider == "openai":
        api_key = load_openai_api_key(api_project_root)
        response = generate_markdown_openai(
            prompt_package,
            api_key=api_key,
            model=model_name or OPENAI_DEFAULT_MODEL,
            api_url=OPENAI_DEFAULT_API_URL,
        )
        resolved_model = model_name or OPENAI_DEFAULT_MODEL
    elif provider == "gemini":
        api_key = load_gemini_api_key(api_project_root)
        response = generate_gemini_markdown(
            prompt_package,
            api_key=api_key,
            model=model_name or GEMINI_DEFAULT_MODEL,
            api_url=GEMINI_DEFAULT_API_URL,
            timeout_seconds=90,
            temperature=0.9,
            top_p=0.95,
            max_output_tokens=8192,
            thinking_level=None,
            retry_attempts=3,
            sleep_seconds=2.0,
        )
        resolved_model = model_name or GEMINI_DEFAULT_MODEL
    else:
        raise ValueError(f"Unsupported lyric API provider: {model_provider}")

    markdown = _normalize_markdown(response.get("markdown", ""))
    hook = safe_text(runtime_plan.get("hook_blueprint", {}).get("core_text"))
    form_family_id = safe_text(runtime_plan.get("form_family_id"))

    return {
        "ok": bool(response.get("ok")) and bool(markdown) and contains_japanese(markdown) and not contains_bad_script(markdown),
        "candidate_id": f"{safe_text(runtime_plan.get('track_id'))}-candidate-{candidate_index + 1}",
        "title": hook,
        "markdown": markdown,
        "artist_id": safe_text(runtime_plan.get("artist_id")),
        "form_family_id": form_family_id,
        "renderer_frame_family": f"api/{provider}",
        "chorus_shape": _chorus_shape_id(form_family_id),
        "bridge_shape": _bridge_shape_id(form_family_id),
        "hook_pressure_realized": _realized_hook_pressure(markdown, hook),
        "generation_backend": "api",
        "api_provider": provider,
        "api_model": resolved_model,
        "api_status_code": response.get("status_code"),
        "api_finish_reason": safe_text(response.get("finish_reason")),
        "api_error": safe_text(response.get("error")),
        "raw_response": response.get("payload"),
        "prompt_package": prompt_package,
    }
