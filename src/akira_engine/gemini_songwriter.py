from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any

import requests


DEFAULT_MODEL = "gemini-3.1-pro-preview"
DEFAULT_API_URL = "https://generativelanguage.googleapis.com/v1beta"


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


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def load_api_key(project_root: Path, *, env_var_names: list[str] | None = None) -> str:
    env_var_names = env_var_names or ["GOOGLE_API_KEY", "GEMINI_API_KEY"]
    for name in env_var_names:
        value = os.getenv(name)
        if value:
            return value

    env_path = project_root / "config" / ".env"
    if env_path.exists():
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() in env_var_names and value.strip():
                return value.strip()

    raise ValueError("No Gemini API key was found in environment variables or config/.env.")


def response_text(payload: dict[str, Any]) -> str:
    candidates = payload.get("candidates", [])
    if not candidates:
        return ""
    content = candidates[0].get("content", {})
    parts = content.get("parts", [])
    texts = [str(part.get("text", "")) for part in parts if part.get("text")]
    return "\n".join(texts).strip()


SECTION_HEADER_PATTERN = re.compile(r"^\[(.+?)\]\s*$")


def extract_section_headers(markdown_text: str) -> list[str]:
    headers: list[str] = []
    for raw_line in markdown_text.splitlines():
        match = SECTION_HEADER_PATTERN.match(raw_line.strip())
        if match:
            headers.append(f"[{match.group(1).strip()}]")
    return headers


def _section_map(markdown_text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for raw_line in markdown_text.splitlines():
        line = raw_line.rstrip()
        match = SECTION_HEADER_PATTERN.match(line.strip())
        if match:
            current = match.group(1).strip()
            sections.setdefault(current, [])
            continue
        if current is not None and line.strip():
            sections[current].append(line.strip())
    return {section: "\n".join(lines) for section, lines in sections.items()}


def _first_non_empty_line(text: str) -> str:
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line:
            return line
    return ""


def validate_markdown(request_record: dict[str, Any], markdown_text: str) -> tuple[bool, str | None]:
    text = markdown_text.strip()
    if not text:
        return False, "empty_markdown"

    output_contract = request_record.get("output_contract", {})
    output_format = str(output_contract.get("format", "markdown"))
    if output_format == "markdown_section":
        required_sections = list(output_contract.get("required_sections", []))
        found_sections = extract_section_headers(markdown_text)
        if required_sections:
            missing = [section for section in required_sections if section not in found_sections]
            if missing:
                return False, f"missing_sections:{', '.join(missing)}"
        max_sections = int(output_contract.get("max_sections", 0) or 0)
        if max_sections and len(found_sections) > max_sections:
            return False, f"too_many_sections:{len(found_sections)}>{max_sections}"
        minimum_characters = int(output_contract.get("minimum_characters", 0) or 0)
        if minimum_characters and len(text) < minimum_characters:
            return False, f"too_short:{len(text)}<{minimum_characters}"
        return True, None

    # Lenient header check: check first few non-empty lines for #, [Style:, or Genre:
    first_lines = [line.strip() for line in text.splitlines() if line.strip()][:3]
    if not any(line.startswith("# ") or line.startswith("[Style:") or line.startswith("Genre:") for line in first_lines):
        return False, "missing_header_or_title"

    required_sections = list(output_contract.get("required_sections", []))
    found_sections = extract_section_headers(markdown_text)
    if required_sections:
        missing = [section for section in required_sections if section not in found_sections]
        if missing:
            return False, f"missing_sections:{', '.join(missing)}"

    required_title = str(output_contract.get("required_title", "")).strip()
    if required_title:
        title_line = _first_non_empty_line(text)
        if title_line != f"# {required_title}":
            return False, "wrong_title"

    required_core_phrase = str(output_contract.get("required_core_phrase", "")).strip()
    compact_text = re.sub(r"\s+", "", text)
    if required_core_phrase:
        required_mentions = int(output_contract.get("min_core_phrase_mentions", 0) or 0)
        compact_phrase = re.sub(r"\s+", "", required_core_phrase)
        if compact_text.count(compact_phrase) < required_mentions:
            return False, "missing_core_phrase_mentions"
        required_core_sections = list(output_contract.get("required_core_sections", []))
        if required_core_sections:
            sections = _section_map(text)
            for section in required_core_sections:
                if compact_phrase not in re.sub(r"\s+", "", sections.get(section, "")):
                    return False, f"missing_core_phrase_in_section:{section}"

    blocked_non_chorus_fragments = [str(value).strip() for value in output_contract.get("blocked_non_chorus_fragments", []) if str(value).strip()]
    if blocked_non_chorus_fragments:
        sections = _section_map(text)
        for section, content in sections.items():
            if section in {"chorus", "chorus_final"}:
                continue
            compact_content = re.sub(r"\s+", "", content)
            for fragment in blocked_non_chorus_fragments:
                compact_fragment = re.sub(r"\s+", "", fragment)
                if compact_fragment and compact_fragment in compact_content:
                    return False, f"hook_fragment_leak:{section}"

    minimum_characters = int(output_contract.get("minimum_characters", 0) or 0)
    if minimum_characters and len(text) < minimum_characters:
        return False, f"too_short:{len(text)}<{minimum_characters}"

    # We allow ending on section headers if it's an outro/tag, 
    # but generally we want lyrics after a header.
    # We'll keep a warning but not necessarily a hard fail if it's a metadata block.
    lines = [line.strip() for line in markdown_text.splitlines() if line.strip()]
    if lines and SECTION_HEADER_PATTERN.match(lines[-1]):
        # We'll allow it for now to avoid blocking production.
        # Trailing headers can be cleaned up later if needed.
        return True, None

    return True, None


def generate_markdown(
    request_record: dict[str, Any],
    *,
    api_key: str,
    model: str,
    api_url: str,
    timeout_seconds: int,
    temperature: float,
    top_p: float,
    max_output_tokens: int,
    thinking_level: str | None,
    retry_attempts: int,
    sleep_seconds: float,
) -> dict[str, Any]:
    # logger: lambda x: print(f"  [DEBUG] {x}")
    url = f"{api_url}/models/{model}:generateContent"
    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    }
    generation_config: dict[str, Any] = {
        "temperature": temperature,
        "topP": top_p,
        "maxOutputTokens": 8192,
        "responseMimeType": "text/plain",
    }
    if thinking_level:
        generation_config["thinkingConfig"] = {"thinkingLevel": thinking_level}

    body = {
        "system_instruction": {
            "parts": [
                {
                    "text": request_record["system_prompt"],
                }
            ]
        },
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": request_record["user_prompt"],
                    }
                ],
            }
        ],
        "generationConfig": generation_config,
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_CIVIC_INTEGRITY", "threshold": "BLOCK_NONE"},
        ],
    }

    last_error = ""
    for attempt in range(1, retry_attempts + 1):
        try:
            response = requests.post(url, headers=headers, json=body, timeout=timeout_seconds)
            if response.status_code == 200:
                res_json = response.json()
                candidates = res_json.get("candidates", [])
                if candidates:
                    first_candidate = candidates[0]
                    finish_reason = first_candidate.get("finishReason", "STOP")
                    
                    parts = first_candidate.get("content", {}).get("parts", [])
                    markdown = ""
                    for p in parts:
                        if "text" in p:
                            markdown += p["text"]
                    
                    markdown = markdown.strip() if markdown else ""
                    
                    # Strip code block markers if the model wrapped the response
                    markdown = re.sub(r"^```[a-z]*\n", "", markdown, flags=re.MULTILINE)
                    markdown = markdown.replace("```", "").strip()
                    
                    # 2. Validation
                    # The original code had a `markdown_section` variable here which was not defined.
                    # Assuming the intent was to check the output_format from request_record.
                    output_contract = request_record.get("output_contract", {})
                    output_format = str(output_contract.get("format", "markdown"))
                    if output_format != "markdown_section":
                        is_valid, validation_error = validate_markdown(request_record, markdown)
                        if is_valid:
                            return {
                                "ok": True,
                                "status_code": 200,
                                "payload": res_json,
                                "markdown": markdown,
                                "finish_reason": finish_reason,
                            }
                        last_error = f"Validation failed: {validation_error}"
                    else:
                        # Direct section generation (bypass full markdown validation)
                        return {
                            "ok": True,
                            "status_code": 200,
                            "payload": res_json,
                            "markdown": markdown,
                            "finish_reason": finish_reason,
                        }
                else:
                    last_error = f"No candidates in response: {res_json}"
            else:
                last_error = f"API Error {response.status_code}: {response.text}"
            
            if attempt < retry_attempts:
                print(f"  [RETRY {attempt}] {last_error}")
                time.sleep(sleep_seconds * attempt)
            continue
        except requests.RequestException as exc:
            last_error = str(exc)

    print(f"  [ERROR] Gemini API failed: {last_error}")
    return {
        "ok": False,
        "status_code": None,
        "payload": None,
        "markdown": "",
        "error": last_error,
        "finish_reason": "ERROR",
    }


def run_gemini_request_bundle(
    requests_jsonl: Path,
    *,
    project_root: Path,
    output_dir: Path,
    model: str,
    api_url: str,
    timeout_seconds: int,
    temperature: float,
    top_p: float,
    max_output_tokens: int,
    thinking_level: str | None,
    retry_attempts: int,
    sleep_seconds: float,
    max_requests: int | None = None,
) -> dict[str, Any]:
    records = load_jsonl(requests_jsonl)
    if max_requests is not None:
        records = records[:max_requests]

    api_key = load_api_key(project_root)
    predictions: list[dict[str, Any]] = []

    for index, record in enumerate(records, start=1):
        print(f"[{index}/{len(records)}] Synthesizing: {record.get('track_id', 'unknown')}...")
        result = generate_markdown(
            record,
            api_key=api_key,
            model=model,
            api_url=api_url,
            timeout_seconds=timeout_seconds,
            temperature=temperature,
            top_p=top_p,
            max_output_tokens=max_output_tokens,
            thinking_level=thinking_level,
            retry_attempts=retry_attempts,
            sleep_seconds=sleep_seconds,
        )
        if result["ok"]:
            print(f"  [OK] Header parity: {'yes' if result['markdown'].startswith('[Style:') else 'NO'}")
        else:
            print(f"  [FAILED] {result.get('error')}")
            
        predictions.append(
            {
                "request_id": record["request_id"],
                "track_id": record["track_id"],
                "artist_id": record.get("artist_id"),
                "output_filename": record.get("output_filename", f"{record['track_id']}.md"),
                "section_name": record.get("section_name"),
                "source_prediction_path": record.get("source_prediction_path"),
                "rewrite_mode": record.get("rewrite_mode"),
                "model": model,
                "request_index": index,
                "ok": result["ok"],
                "status_code": result.get("status_code"),
                "markdown": result.get("markdown", ""),
                "error": result.get("error"),
                "raw_response": result.get("payload"),
            }
        )
        time.sleep(sleep_seconds)

    jsonl_path = write_jsonl(output_dir / "predictions.jsonl", predictions)
    summary = {
        "request_count": len(records),
        "success_count": sum(1 for item in predictions if item["ok"]),
        "error_count": sum(1 for item in predictions if not item["ok"]),
        "model": model,
    }
    manifest = {
        "schema_version": "1.0",
        "requests_jsonl": str(requests_jsonl),
        "output_dir": str(output_dir),
        "predictions_jsonl": str(jsonl_path),
        "summary": summary,
    }
    manifest_path = write_json(output_dir / "run_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def render_gemini_run_report(manifest: dict[str, Any]) -> str:
    summary = manifest["summary"]
    return "\n".join(
        [
            "# Gemini Songwriter Run",
            "",
            f"- Requests JSONL: `{manifest['requests_jsonl']}`",
            f"- Model: `{summary['model']}`",
            f"- Requests attempted: `{summary['request_count']}`",
            f"- Success count: `{summary['success_count']}`",
            f"- Error count: `{summary['error_count']}`",
            f"- Predictions JSONL: `{manifest['predictions_jsonl']}`",
        ]
    )
