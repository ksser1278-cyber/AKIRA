from __future__ import annotations

from typing import Any


def _bullet(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- none"


def build_human_report(
    *,
    pass_1: dict[str, Any],
    pass_2: dict[str, Any],
    pass_3: dict[str, Any],
    pass_4: dict[str, Any],
    pass_5: dict[str, Any],
    validation_report: dict[str, Any],
) -> str:
    identity = pass_1.get("core_identity", {})
    recipe = pass_5.get("core_formula", {})
    reuse = pass_5.get("reuse_strategy", {})

    lines = [
        "# 곡 단위 정밀 분석",
        "",
        f"- Song ID: `{pass_1.get('song_id', '')}`",
        f"- Validation OK: `{validation_report.get('ok')}`",
        "",
        "## 1. 곡의 핵심 설계 의도",
        f"- Surface mood: {', '.join(identity.get('surface_mood', []))}",
        f"- Hidden mood: {', '.join(identity.get('hidden_mood', []))}",
        f"- Speaker: {identity.get('speaker_type', '')}",
        f"- Core conflict: {identity.get('core_conflict', '')}",
        f"- Listener effect: {identity.get('main_listener_effect', '')}",
        "",
        "## 2. 작사 의도 분석",
    ]

    for section in pass_2.get("sections", []):
        lines.append(f"### {section.get('section', '')}")
        for item in section.get("lines", [])[:12]:
            tags = ", ".join(item.get("function_tags", []))
            lines.append(
                f"- `{item.get('original_line', '')}` [{tags}] "
                f"{item.get('songwriting_choice', '')} -> {item.get('listener_effect', '')}"
            )
    lines.extend(["", "## 3. 작곡 의도 분석"])
    for item in pass_4.get("composition_analysis", {}).get("melody_strategy", []):
        lines.append(f"- {item.get('choice', '')}: {item.get('reason', '')}")

    lines.extend(["", "## 4. 편곡/프로덕션 의도 분석"])
    arrangement = pass_4.get("arrangement_analysis", {})
    for name, payload in arrangement.items():
        lines.append(f"- {name}: {payload.get('role', '')} / {payload.get('probable_intent', '')}")

    lines.extend(["", "## 5. 훅 작동 원리"])
    hook = pass_4.get("hook_analysis", {})
    lines.append(f"- Main hook type: `{hook.get('main_hook_type', '')}`")
    lines.append(f"- Components: {', '.join(hook.get('hook_components', []))}")

    lines.extend(["", "## 6. 창작 응용 공식"])
    lines.append(f"- {recipe.get('one_sentence', '')}")
    for item in pass_5.get("lyric_formula", []):
        lines.append(f"- {item.get('step')}. {item.get('method', '')}: {item.get('purpose', '')}")

    lines.extend(["", "## 7. 피해야 할 점", _bullet(reuse.get("avoid", []))])

    lines.extend(["", "## 8. 분석 신뢰도"])
    lines.append(f"- Claim count: `{validation_report.get('summary', {}).get('claim_count', 0)}`")
    lines.append(f"- Line analysis count: `{validation_report.get('summary', {}).get('line_analysis_count', 0)}`")
    if validation_report.get("errors"):
        lines.append("- Errors:")
        lines.extend(f"  - {item}" for item in validation_report["errors"])
    else:
        lines.append("- Errors: none")

    return "\n".join(lines).rstrip() + "\n"


def build_ai_reconstruction_json(
    *,
    pass_1: dict[str, Any],
    pass_2: dict[str, Any],
    pass_3: dict[str, Any],
    pass_4: dict[str, Any],
    pass_5: dict[str, Any],
    validation_report: dict[str, Any],
) -> dict[str, Any]:
    identity = pass_1.get("core_identity", {})
    return {
        "ai_reconstruction_profile": {
            "song_identity": {
                "surface": identity.get("surface_mood", []),
                "inner": identity.get("hidden_mood", []),
                "core_contrast": pass_5.get("core_formula", {}).get("songwriting_axis", ""),
            },
            "verified_metadata": pass_1.get("verified_metadata", {}),
            "core_intent": {
                "main_goal": pass_5.get("core_formula", {}).get("one_sentence", ""),
                "listener_target_effect": identity.get("main_listener_effect", ""),
            },
            "lyric_engine": {
                "line_style": pass_2.get("lyric_strategy_summary", {}).get("main_strategy", ""),
                "speaker_design": identity.get("speaker_type", ""),
                "recommended_tags": pass_2.get("lyric_strategy_summary", {}).get("recommended_tags", []),
                "line_analysis": [
                    item
                    for section in pass_2.get("sections", [])
                    for item in section.get("lines", [])
                ],
            },
            "composition_engine": pass_4.get("composition_analysis", {}),
            "arrangement_engine": pass_4.get("arrangement_analysis", {}),
            "hook_engine": pass_4.get("hook_analysis", {}),
            "timeline_engine": pass_3,
            "reuse_recipe": pass_5.get("reuse_strategy", {}),
            "confidence_report": validation_report,
        }
    }
