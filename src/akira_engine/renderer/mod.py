from __future__ import annotations

import hashlib
import random
from typing import Any

from ..lyric_utils import contains_bad_script, contains_japanese, safe_text, unique_preserve_order


_SECTION_FALLBACKS: dict[str, list[str]] = {
    "intro": ["静寂", "街灯", "息"],
    "verse_1": ["鼓動", "傷", "記憶"],
    "verse_2": ["夜道", "影", "残響"],
    "pre_chorus": ["ノイズ", "沈黙", "心臓"],
    "pre_chorus_2": ["警報", "体温", "均衡"],
    "chorus": ["声", "破片", "光"],
    "chorus_final": ["断線", "悲鳴", "閃光"],
    "bridge": ["暗室", "静寂", "余熱"],
    "outro": ["残響", "歩幅", "夜明け"],
}


def _clean_terms(values: list[Any], *, limit: int = 6) -> list[str]:
    cleaned: list[str] = []
    for value in values:
        text = safe_text(value)
        if not text:
            continue
        if not contains_japanese(text):
            continue
        if contains_bad_script(text):
            continue
        if len(text.replace(" ", "")) > 12:
            continue
        if text not in cleaned:
            cleaned.append(text)
        if len(cleaned) >= limit:
            break
    return cleaned


def _terms_for_card(card: dict[str, Any], hook: str) -> list[str]:
    section = safe_text(card.get("section"))
    fallback = list(_SECTION_FALLBACKS.get(section, ["鼓動", "残響", "光"]))
    raw_values = (
        list(card.get("required_imagery", []))
        + list(card.get("required_motifs", []))
        + list(card.get("imagery_focus", []))
        + [card.get("scene", "")]
    )
    cleaned = _clean_terms(raw_values, limit=6)
    if contains_japanese(hook) and not contains_bad_script(hook):
        cleaned = [hook] + [item for item in cleaned if item != hook]
    if not cleaned:
        cleaned = [hook] if contains_japanese(hook) and not contains_bad_script(hook) else []
        cleaned.extend(fallback)
    return unique_preserve_order(cleaned)[:6]


def _pick_triplet(terms: list[str]) -> tuple[str, str, str]:
    pool = list(terms)
    while len(pool) < 3:
        pool.append(pool[-1] if pool else "鼓動")
    return pool[0], pool[1], pool[2]


def _generative_section_lines(section: str, hook: str, a: str, b: str, c: str, *, scaffold_mode: bool) -> list[str]:
    if section == "intro":
        lines = [
            f"{a}の奥で息が止まる",
            f"{b}だけがまだ揺れている",
            f"{hook}が静かに目を開く",
        ]
    elif "verse" in section:
        lines = [
            f"{a}を噛んで夜を飲みこむ",
            f"{b}の影が胸を擦っていく",
            f"{c}の匂いが指先に残る",
            "やさしい声ほど深く刺さる",
        ]
    elif "pre_chorus" in section:
        lines = [
            f"{a}が近づくたびにずれる",
            f"{b}の隙間で熱が暴れる",
            f"{hook}まであと少しなのに",
        ]
    elif section == "bridge":
        lines = [
            f"{a}だけがゆっくり沈んでいく",
            f"{b}が耳の奥で冷えていく",
            f"{hook}にも触れられないまま",
        ]
    elif section == "chorus_final":
        lines = [
            f"{hook} {hook}",
            f"{a}のままで壊れていけ",
            f"{b}の色ごと噛み砕いて",
            f"{c}まで全部ひっくり返せ",
            "かわいい顔で牙を立てろ",
        ]
    elif "chorus" in section:
        lines = [
            f"{hook} {hook}",
            f"{a}のままで壊れていく",
            f"{b}だけではもう足りない",
            "かわいい顔で牙を立てる",
        ]
    elif section == "outro":
        lines = [
            f"{a}だけが夜に沈んでいく",
            f"{hook}が遠くでまだ揺れている",
        ]
    else:
        lines = [
            f"{hook}が静かに揺れている",
            f"{a}が胸の奥で光っている",
        ]

    if scaffold_mode and section in {"chorus", "chorus_final"}:
        lines.append(f"{hook}をもう一度繰り返す")
    return lines


def run_renderer_stage(
    plan: dict[str, Any],
    *,
    variant_index: int,
    scaffold_mode: bool = False,
) -> dict[str, Any]:
    artist_id = safe_text(plan.get("artist_id", "default"))
    hook = safe_text(plan.get("hook_blueprint", {}).get("core_text", ""))
    rng = random.Random(int(hashlib.md5(f"{plan['track_id']}:{variant_index}".encode("utf-8")).hexdigest()[:8], 16))

    if not contains_japanese(hook) or contains_bad_script(hook):
        first_card = (plan.get("section_cards", []) or [{}])[0]
        hook_terms = _terms_for_card(first_card, "")
        hook = hook_terms[0] if hook_terms else "幻灯"

    lines = [f"# {hook}", ""]
    section_cards = list(plan.get("section_cards", []))
    rng.shuffle(section_cards)
    section_cards.sort(key=lambda card: safe_text(card.get("section")))

    ordered_sections = list(plan.get("form_profile", {}).get("section_order", []))
    if ordered_sections:
        index_map = {name: idx for idx, name in enumerate(ordered_sections)}
        section_cards.sort(key=lambda card: index_map.get(safe_text(card.get("section")), 999))

    for card in section_cards:
        section = safe_text(card.get("section"))
        if not section:
            continue
        terms = _terms_for_card(card, hook)
        a, b, c = _pick_triplet(terms)
        lines.append(f"[{section}]")
        lines.extend(_generative_section_lines(section, hook, a, b, c, scaffold_mode=scaffold_mode))
        lines.append("")

    return {
        "candidate_id": f"{plan['track_id']}-candidate-{variant_index + 1}",
        "title": hook,
        "markdown": "\n".join(lines).strip() + "\n",
        "scaffold_mode": scaffold_mode,
        "artist_id": artist_id,
    }
