from __future__ import annotations

import re


HANGUL_PATTERN = re.compile(r"[\uac00-\ud7af]")
REPLACEMENT_PATTERN = re.compile(r"[?�]")
JAPANESE_PATTERN = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]")
LATIN_PATTERN = re.compile(r"[A-Za-z]")


def clean_text(value: str) -> str:
    return " ".join(str(value).strip().split())


def japanese_text_quality(text: str) -> dict[str, float | bool]:
    cleaned = clean_text(text)
    if not cleaned:
        return {
            "usable": False,
            "hangul_ratio": 1.0,
            "replacement_ratio": 1.0,
            "japanese_ratio": 0.0,
            "latin_ratio": 0.0,
        }

    visible = cleaned.replace(" ", "")
    length = max(1, len(visible))
    hangul_ratio = len(HANGUL_PATTERN.findall(visible)) / length
    replacement_ratio = len(REPLACEMENT_PATTERN.findall(visible)) / length
    japanese_ratio = len(JAPANESE_PATTERN.findall(visible)) / length
    latin_ratio = len(LATIN_PATTERN.findall(visible)) / length

    usable = (
        replacement_ratio <= 0.02
        and hangul_ratio <= 0.02
        and japanese_ratio >= 0.35
        and latin_ratio <= 0.35
    )

    return {
        "usable": usable,
        "hangul_ratio": round(hangul_ratio, 4),
        "replacement_ratio": round(replacement_ratio, 4),
        "japanese_ratio": round(japanese_ratio, 4),
        "latin_ratio": round(latin_ratio, 4),
    }


def japanese_markdown_lyric_quality(markdown_text: str) -> dict[str, float | bool]:
    lyric_lines = []
    for raw_line in str(markdown_text).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or (line.startswith("[") and line.endswith("]")):
            continue
        lyric_lines.append(line)

    joined = " ".join(lyric_lines)
    return japanese_text_quality(joined)
