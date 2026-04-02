from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any

import requests


DEFAULT_MODEL = "gpt-5.4-mini"
DEFAULT_API_URL = "https://api.openai.com/v1/chat/completions"


def load_api_key(project_root: Path, *, env_var_names: list[str] | None = None) -> str:
    env_var_names = env_var_names or ["OPENAI_API_KEY"]
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

    raise ValueError("No OpenAI API key was found in environment variables or config/.env.")


SECTION_HEADER_PATTERN = re.compile(r"^\[(.+?)\]\s*$")


def extract_section_headers(markdown_text: str) -> list[str]:
    headers: list[str] = []
    for raw_line in markdown_text.splitlines():
        match = SECTION_HEADER_PATTERN.match(raw_line.strip())
        if match:
            headers.append(f"[{match.group(1).strip()}]")
    return headers


def validate_markdown(request_record: dict[str, Any], markdown_text: str) -> tuple[bool, str | None]:
    text = markdown_text.strip()
    
    # Normalization: Strip code blocks
    text = re.sub(r"^```[a-z]*\n", "", text, flags=re.MULTILINE)
    text = text.replace("```", "").strip()

    if not text:
        return False, "empty_markdown"

    output_contract = request_record.get("output_contract", {})
    output_format = str(output_contract.get("format", "markdown"))

    # Lenient header check: check first few non-empty lines for #, [Style:, or Genre:
    first_lines = [line.strip() for line in text.splitlines() if line.strip()][:3]
    if not any(v in "".join(first_lines) for v in ["# ", "[Style:", "Genre:"]):
         if output_format != "markdown_section":
            return False, "missing_header_or_title"

    required_sections = list(output_contract.get("required_sections", []))
    found_sections = extract_section_headers(markdown_text)
    if required_sections:
        missing = [section for section in required_sections if section not in found_sections]
        if missing:
            return False, f"missing_sections:{', '.join(missing)}"

    return True, None


def generate_markdown_openai(
    request_record: dict[str, Any],
    *,
    api_key: str,
    model: str = DEFAULT_MODEL,
    api_url: str = DEFAULT_API_URL,
    timeout_seconds: int = 60,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    retry_attempts: int = 3,
    sleep_seconds: float = 2.0,
) -> dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    system_prompt = request_record.get("system_prompt", "")
    user_prompt = request_record.get("user_prompt", "")

    body = {
        "model": model,
        "messages": [
            {"role": "developer", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 1.0,
        "max_completion_tokens": max_tokens,
    }

    last_error = ""

    for attempt in range(retry_attempts):
        try:
            response = requests.post(api_url, headers=headers, json=body, timeout=timeout_seconds)
            if response.status_code == 200:
                res_json = response.json()
                choices = res_json.get("choices", [])
                if choices:
                    first_choice = choices[0]
                    markdown = first_choice.get("message", {}).get("content", "").strip()
                    finish_reason = first_choice.get("finish_reason", "stop")
                    
                    # Normalize markdown
                    markdown = re.sub(r"^```[a-z]*\n", "", markdown, flags=re.MULTILINE)
                    markdown = markdown.replace("```", "").strip()
                    
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
                    last_error = f"No choices in response: {res_json}"
            else:
                last_error = f"API Error {response.status_code}: {response.text}"
            
            if attempt < retry_attempts - 1:
                print(f"  [RETRY {attempt+1}] {last_error}")
                time.sleep(sleep_seconds * (attempt + 1))
            continue
        except requests.RequestException as exc:
            last_error = str(exc)

    return {
        "ok": False,
        "status_code": 0,
        "payload": None,
        "markdown": "",
        "error": last_error,
        "finish_reason": "ERROR",
    }
