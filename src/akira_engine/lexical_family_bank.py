from __future__ import annotations

from collections import OrderedDict
from typing import Iterable

from .corpus_intelligence.novelty.risk import score_cliche_density
from .lyric_utils import safe_text


_FAMILY_KEYWORDS: "OrderedDict[str, tuple[str, ...]]" = OrderedDict(
    [
        (
            "childhood",
            (
                "\u30ad\u30e3\u30f3\u30c7\u30a3",
                "\u98f4",
                "\u904a\u5712\u5730",
                "\u304a\u3082\u3061\u3083",
                "\u30ea\u30dc\u30f3",
                "\u7c92",
                "\u304a\u83d3\u5b50",
            ),
        ),
        (
            "body",
            (
                "\u4f53\u6e29",
                "\u50b7",
                "\u722a",
                "\u9f13\u52d5",
                "\u5fc3\u81d3",
                "\u5589",
                "\u820c",
                "\u76ae\u819a",
                "\u547c\u5438",
                "\u9aa8",
                "\u8108",
                "\u80f8",
            ),
        ),
        (
            "mechanical",
            (
                "\u8b66\u5831",
                "\u65ad\u7dda",
                "\u6b8b\u97ff",
                "\u30ce\u30a4\u30ba",
                "\u96d1\u97f3",
                "\u9ede\u6ec5",
                "\u706b\u82b1",
                "\u914d\u7dda",
                "\u9759\u96fb",
                "\u7834\u7247",
            ),
        ),
        (
            "architectural",
            (
                "\u6559\u5ba4",
                "\u90e8\u5c4b",
                "\u5eca\u4e0b",
                "\u5929\u4e95",
                "\u58c1",
                "\u6697\u5ba4",
                "\u7a93",
                "\u5e8a",
            ),
        ),
        (
            "silence",
            (
                "\u6c88\u9ed9",
                "\u6c17\u914d",
                "\u4f59\u71b1",
                "\u5f71",
                "\u819c",
                "\u6b8b\u308a\u9999",
                "\u6e29\u5ea6",
                "\u9759\u3051\u3055",
            ),
        ),
        (
            "collapse",
            (
                "\u60b2\u9cf4",
                "\u6bd2",
                "\u58ca",
                "\u88c2",
                "\u843d\u4e0b",
                "\u8150",
                "\u7f70",
                "\u3072\u3073",
            ),
        ),
        (
            "color",
            (
                "\u30d4\u30f3\u30af",
                "\u660e\u5ea6",
                "\u5149",
                "\u8272",
                "\u30cd\u30aa\u30f3",
            ),
        ),
    ]
)

_SECTION_FAMILY_PRIORITIES: dict[str, tuple[str, ...]] = {
    "intro": ("childhood", "architectural", "silence"),
    "verse_1": ("body", "childhood", "architectural"),
    "verse_2": ("body", "mechanical", "architectural"),
    "pre_chorus": ("mechanical", "body", "silence"),
    "pre_chorus_2": ("mechanical", "collapse", "body"),
    "chorus": ("childhood", "body", "collapse"),
    "bridge": ("architectural", "silence", "collapse"),
    "chorus_final": ("collapse", "mechanical", "body"),
    "outro": ("silence", "architectural", "childhood"),
}

_DEMO_CLICHE_TERMS: tuple[str, ...] = (
    "\u30ce\u30a4\u30ba",
    "\u6bd2",
    "\u60b2\u9cf4",
    "\u8b66\u5831",
    "\u30d4\u30f3\u30af",
)


def is_cliche_term(term: str) -> bool:
    text = safe_text(term)
    if not text:
        return False
    return any(token in text for token in _DEMO_CLICHE_TERMS)


def classify_term_family(term: str) -> str | None:
    text = safe_text(term)
    if not text:
        return None
    for family, keywords in _FAMILY_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return family
    return None


def pick_family_balanced_terms(
    pool: Iterable[str],
    *,
    section: str,
    offset: int,
    count: int = 4,
) -> list[str]:
    cleaned = [safe_text(term) for term in pool if safe_text(term)]
    if not cleaned:
        return []

    seen: set[str] = set()
    ordered: list[str] = []
    for term in cleaned:
        if term not in seen:
            ordered.append(term)
            seen.add(term)

    family_buckets: dict[str, list[str]] = {}
    unclassified: list[str] = []
    for term in ordered:
        family = classify_term_family(term)
        if family is None:
            unclassified.append(term)
            continue
        family_buckets.setdefault(family, []).append(term)

    for family, bucket in list(family_buckets.items()):
        family_buckets[family] = sorted(
            bucket,
            key=lambda term: (
                1 if is_cliche_term(term) else 0,
                len(term),
                bucket.index(term),
            ),
        )

    selected: list[str] = []
    used: set[str] = set()

    def add_term(term: str) -> None:
        if term not in used and len(selected) < count:
            selected.append(term)
            used.add(term)

    lead_evidence = [term for term in ordered[:3] if not is_cliche_term(term)]
    if lead_evidence:
        add_term(lead_evidence[offset % len(lead_evidence)])

    preferred = _SECTION_FAMILY_PRIORITIES.get(section, ())
    for family_index, family in enumerate(preferred):
        bucket = family_buckets.get(family, [])
        if not bucket:
            continue
        add_term(bucket[(offset + family_index) % len(bucket)])

    remaining_families = [family for family in family_buckets.keys() if family not in preferred]
    remaining_families.sort(
        key=lambda family: (
            1 if all(is_cliche_term(term) for term in family_buckets.get(family, [])) else 0,
            family,
        )
    )
    for family_index, family in enumerate(remaining_families):
        if len(selected) >= count:
            break
        bucket = family_buckets.get(family, [])
        if not bucket:
            continue
        add_term(bucket[(offset + family_index) % len(bucket)])

    if len(selected) < count and unclassified:
        shift = offset % len(unclassified)
        rotated = list(unclassified[shift:] + unclassified[:shift])
        for term in rotated:
            if len(selected) >= count:
                break
            add_term(term)

    if len(selected) < count:
        shift = offset % len(ordered)
        rotated = list(ordered[shift:] + ordered[:shift])
        for term in rotated:
            if len(selected) >= count:
                break
            add_term(term)

    return selected[:count]


def score_family_diversity(text: str) -> tuple[float, dict[str, int]]:
    family_hits: dict[str, int] = {}
    for family, keywords in _FAMILY_KEYWORDS.items():
        hits = sum(text.count(keyword) for keyword in keywords)
        if hits > 0:
            family_hits[family] = hits

    unique_family_count = len(family_hits)
    score = min(1.0, unique_family_count / 4.0) if unique_family_count else 0.0
    return round(score, 2), family_hits


def score_demo_cliche_density(text: str) -> tuple[float, dict[str, float | int]]:
    base_density = score_cliche_density(text)
    lyric_lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
        and not line.startswith("#")
        and not (line.startswith("[") and line.endswith("]"))
    ]
    if not lyric_lines:
        return 0.0, {"base_density": 0.0, "demo_density": 0.0, "matched_lines": 0}

    matched_lines = sum(1 for line in lyric_lines if any(term in line for term in _DEMO_CLICHE_TERMS))
    demo_density = matched_lines / len(lyric_lines)
    return round(max(base_density, demo_density), 2), {
        "base_density": round(base_density, 2),
        "demo_density": round(demo_density, 2),
        "matched_lines": matched_lines,
    }
