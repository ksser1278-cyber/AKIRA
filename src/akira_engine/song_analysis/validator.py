from __future__ import annotations

from typing import Any

from .schema import EvidenceStatus


CLAIM_FIELDS = ["choice", "reason", "effect", "reuse_method", "status", "confidence"]
INFERRED_STATUSES = {EvidenceStatus.INFERRED.value, EvidenceStatus.HYPOTHESIS.value}


def validate_claim(payload: dict[str, Any], *, location: str) -> list[str]:
    errors: list[str] = []
    for field in CLAIM_FIELDS:
        if field not in payload:
            errors.append(f"{location}: missing claim field {field}")

    status = payload.get("status")
    if status not in {item.value for item in EvidenceStatus}:
        errors.append(f"{location}: invalid status {status!r}")

    confidence = payload.get("confidence")
    if not isinstance(confidence, (int, float)) or not 0 <= float(confidence) <= 1:
        errors.append(f"{location}: confidence must be between 0 and 1")

    if status in INFERRED_STATUSES and not payload.get("evidence"):
        errors.append(f"{location}: inferred or hypothesis claim must include evidence")

    for field in ("choice", "reason", "effect", "reuse_method"):
        if not str(payload.get(field, "")).strip():
            errors.append(f"{location}: claim field {field} must not be empty")

    return errors


def iter_claims(payload: Any, *, prefix: str = "root") -> list[tuple[str, dict[str, Any]]]:
    claims: list[tuple[str, dict[str, Any]]] = []
    if isinstance(payload, dict):
        if all(field in payload for field in ("choice", "reason", "effect", "reuse_method")):
            claims.append((prefix, payload))
        for key, value in payload.items():
            claims.extend(iter_claims(value, prefix=f"{prefix}.{key}"))
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            claims.extend(iter_claims(value, prefix=f"{prefix}[{index}]"))
    return claims


def validate_outputs(outputs: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    for name in ("pass_1", "pass_2", "pass_3", "pass_4", "pass_5"):
        if name not in outputs:
            errors.append(f"missing output {name}")

    for output_name, payload in outputs.items():
        if output_name in {"human_report", "ai_reconstruction", "validation_report"}:
            continue
        for location, claim_payload in iter_claims(payload, prefix=output_name):
            errors.extend(validate_claim(claim_payload, location=location))

    pass_2 = outputs.get("pass_2", {})
    sections = pass_2.get("sections", []) if isinstance(pass_2, dict) else []
    line_count = sum(len(section.get("lines", [])) for section in sections if isinstance(section, dict))
    if line_count == 0:
        errors.append("pass_2 must contain line-level lyric analysis")

    pass_3 = outputs.get("pass_3", {})
    for index, item in enumerate(pass_3.get("timeline", []) if isinstance(pass_3, dict) else []):
        if not item.get("probable_intent"):
            errors.append(f"pass_3.timeline[{index}] missing probable_intent")
        if not item.get("listener_effect"):
            errors.append(f"pass_3.timeline[{index}] missing listener_effect")

    pass_5 = outputs.get("pass_5", {})
    reuse_strategy = pass_5.get("reuse_strategy", {}) if isinstance(pass_5, dict) else {}
    for field in ("must_keep", "can_change", "avoid"):
        if not reuse_strategy.get(field):
            errors.append(f"pass_5.reuse_strategy.{field} is required")

    ai_profile = outputs.get("ai_reconstruction", {}).get("ai_reconstruction_profile", {})
    if ai_profile and pass_5:
        profile_recipe = ai_profile.get("reuse_recipe", {})
        if not profile_recipe:
            errors.append("ai_reconstruction_profile.reuse_recipe is required")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "claim_count": sum(
                len(iter_claims(payload, prefix=name))
                for name, payload in outputs.items()
                if name.startswith("pass_")
            ),
            "line_analysis_count": line_count,
        },
    }
