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

_MODE_FALLBACK_HOOKS: dict[str, str] = {
    "dark_cute_breakdown": "飴の罰",
    "direct_emotional_pop": "残響灯",
    "default": "幻灯",
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


def _terms_for_card(card: dict[str, Any], hook: str, *, force_hook: bool) -> list[str]:
    section = safe_text(card.get("section"))
    fallback = list(_SECTION_FALLBACKS.get(section, ["鼓動", "残響", "光"]))
    raw_values = (
        list(card.get("required_imagery", []))
        + list(card.get("required_motifs", []))
        + list(card.get("imagery_focus", []))
        + [card.get("scene", "")]
    )
    cleaned = _clean_terms(raw_values, limit=6)
    if force_hook and contains_japanese(hook) and not contains_bad_script(hook):
        cleaned = [hook] + [item for item in cleaned if item != hook]
    if not cleaned:
        cleaned = [hook] if force_hook and contains_japanese(hook) and not contains_bad_script(hook) else []
        cleaned.extend(fallback)
    return unique_preserve_order(cleaned)[:6]


def _rotate_values(values: list[str], offset: int) -> list[str]:
    if not values:
        return []
    shift = offset % len(values)
    return list(values[shift:] + values[:shift])


def _pick_triplet(terms: list[str], *, offset: int = 0) -> tuple[str, str, str]:
    pool = _rotate_values(list(terms), offset)
    while len(pool) < 3:
        pool.append(pool[-1] if pool else "鼓動")
    return pool[0], pool[1], pool[2]


def _choose_lines(packs: list[list[str]], variant: int) -> list[str]:
    if not packs:
        return []
    return list(packs[variant % len(packs)])


def _lines_for_dark_cute_breakdown(
    section: str,
    hook: str,
    a: str,
    b: str,
    c: str,
    *,
    artist_id: str,
    variant: int,
) -> list[str]:
    if section == "intro":
        return _choose_lines(
            [
                [
                    f"{a}の鈴が喉で鳴る",
                    f"{b}に混ざる砂糖のノイズ",
                    f"{hook}だけまだ笑ってる",
                ],
                [
                    f"{a}が舌の裏で軋んでいる",
                    f"{b}の灯りが指先を汚す",
                    f"{hook}だけがやけに甘い",
                ],
                [
                    f"{a}を噛むたび歯が冷えていく",
                    f"{b}の粒が喉の奥で跳ねる",
                    f"{hook}だけまだ息をしている",
                ],
            ],
            variant,
        )
    if section in {"verse_1", "verse_2"}:
        if artist_id == "maretu":
            return _choose_lines(
                [
                    [
                        f"{a}を舐めれば歯形が増える",
                        f"{b}の体温が夜を汚す",
                        f"{c}の匂いで呼吸が曲がる",
                        "やさしい敬語ほど深く刺さる",
                    ],
                    [
                        f"{a}を噛むたび砂糖が割れる",
                        f"{b}の膜だけきれいに剥がれる",
                        f"{c}の残り香で脈が狂う",
                        "丁寧なことばほど毒がよく回る",
                    ],
                    [
                        f"{a}を数えるほど舌が荒れる",
                        f"{b}の輪郭だけ夜に浮いている",
                        f"{c}の気配で呼吸が浅くなる",
                        "まともな顔ほど先に壊れていく",
                    ],
                    [
                        f"{a}を舐めた指がまだ熱い",
                        f"{b}のしずくが喉まで落ちる",
                        f"{c}の気圧で視界が濁る",
                        "やわらかい声ほど最後に牙を持つ",
                    ],
                ],
                variant,
            )
        return _choose_lines(
            [
                [
                    f"{a}を舐めれば歯形が増える",
                    f"{b}の体温が夜を汚す",
                    f"{c}の匂いで呼吸が曲がる",
                    "やさしい声ほど深く刺さる",
                ],
                [
                    f"{a}を噛むたび色が濃くなる",
                    f"{b}の熱だけ胸で暴れる",
                    f"{c}の気配でまぶたが軋む",
                    "かわいい嘘ほど深く刺さる",
                ],
            ],
            variant,
        )
    if "pre_chorus" in section:
        return _choose_lines(
            [
                [
                    f"{a}が点滅して心臓がずれる",
                    f"{b}の隙間で警報が育つ",
                    f"{hook}まであと少しで壊れる",
                ],
                [
                    f"{a}がまばたきのたび増えていく",
                    f"{b}の継ぎ目で熱だけ跳ねている",
                    f"{hook}までまだ引き返せない",
                ],
                [
                    f"{a}が静かに鼓膜を叩く",
                    f"{b}の裂け目で甘さが腐る",
                    f"{hook}まで息を止めていたい",
                ],
            ],
            variant,
        )
    if section == "bridge":
        return _choose_lines(
            [
                [
                    f"{a}を抱いたまま沈んでいく",
                    f"{b}が耳の奥で冷えていく",
                    f"{hook}にも触れられないまま",
                ],
                [
                    f"{a}を隠したまま水位が上がる",
                    f"{b}だけ妙に白く光っている",
                    f"{hook}さえまだ飲み込めない",
                ],
                [
                    f"{a}の底で静寂が割れていく",
                    f"{b}の温度だけ手首に残る",
                    f"{hook}まであと少し届かない",
                ],
            ],
            variant,
        )
    if section == "chorus_final":
        if artist_id == "maretu":
            return _choose_lines(
                [
                    [
                        f"{hook} {hook}",
                        f"{a}の色ごと壊していけ",
                        f"{b}の骨まで舐め尽くして",
                        f"{c}も全部ひっくり返せ",
                        "かわいい顔で毒を盛れ",
                        "笑ったままで終わらせるな",
                    ],
                    [
                        f"{hook} {hook}",
                        f"{a}の膜ごと裂いていけ",
                        f"{b}の奥まで甘さを流し込め",
                        f"{c}の名残まで蹴り倒せ",
                        "かわいい顔で毒を混ぜろ",
                        "きれいなままで助かると思うな",
                    ],
                    [
                        f"{hook} {hook}",
                        f"{a}の輪郭から崩していけ",
                        f"{b}の脈まで赤く塗り替えろ",
                        f"{c}の残響ごと踏み潰せ",
                        "笑う口先で毒を盛れ",
                        "やさしさなんか最後に捨てろ",
                    ],
                ],
                variant,
            )
        return _choose_lines(
            [
                [
                    f"{hook} {hook}",
                    f"{a}の色ごと壊していけ",
                    f"{b}の骨まで舐め尽くして",
                    f"{c}も全部ひっくり返せ",
                    "かわいい顔で毒を盛れ",
                    "かわいい顔で牙を立てろ",
                ],
                [
                    f"{hook} {hook}",
                    f"{a}の形ごと崩していけ",
                    f"{b}の奥まで赤く染めろ",
                    f"{c}の名残まで踏み倒せ",
                    "かわいい顔で毒を盛れ",
                    "最後の熱で噛みついていけ",
                ],
            ],
            variant,
        )
    if section == "chorus":
        return _choose_lines(
            [
                [
                    f"{hook} {hook}",
                    f"{a}のままで噛みついて",
                    f"{b}だけではもう足りない",
                    "かわいい顔で毒を盛れ",
                ],
                [
                    f"{hook} {hook}",
                    f"{a}ごと抱えて噛み砕いて",
                    f"{b}だけじゃまだ満たされない",
                    "笑う口先で毒を塗れ",
                ],
                [
                    f"{hook} {hook}",
                    f"{a}の温度で首を締めて",
                    f"{b}だけならまだ生ぬるい",
                    "かわいい顔で深く刺され",
                ],
            ],
            variant,
        )
    if section == "outro":
        return _choose_lines(
            [
                [
                    f"{a}だけが夜に残っている",
                    f"{hook}が遠くでまだ点滅する",
                ],
                [
                    f"{a}だけが喉の奥で残っている",
                    f"{hook}がやけに静かに滲んでいる",
                ],
                [
                    f"{a}だけが最後まで腐らない",
                    f"{hook}が遠くでまだ瞬いている",
                ],
            ],
            variant,
        )
    return [
        f"{hook}が静かに揺れている",
        f"{a}が胸の奥で光っている",
    ]


def _lines_for_direct_emotional_pop(section: str, hook: str, a: str, b: str, c: str, *, variant: int) -> list[str]:
    if section == "intro":
        return _choose_lines(
            [
                [f"{a}に触れた手がまだ熱い", f"{b}だけが窓辺でほどけていく", f"{hook}を言えないまま朝になる"],
                [f"{a}の余熱だけがまだ残る", f"{b}が静かにガラスを曇らせる", f"{hook}をこぼせないまま夜が明ける"],
            ],
            variant,
        )
    if section in {"verse_1", "verse_2"}:
        return _choose_lines(
            [
                [f"{a}の温度をまだ覚えてる", f"{b}が胸の奥を擦っていく", f"{c}の影だけ追いかけていた", "言えないことほど歌になっていく"],
                [f"{a}の気配だけ離れない", f"{b}がまぶたの裏をなぞっていく", f"{c}の名前だけ息に残った", "遅れた気持ちほど歌になっていく"],
            ],
            variant,
        )
    if "pre_chorus" in section:
        return [
            f"{a}が近づくほど息が浅い",
            f"{b}を越えれば戻れなくなる",
            f"{hook}まであと少しなのに",
        ]
    if section == "bridge":
        return [
            f"{a}だけを置いて夜が明ける",
            f"{b}の匂いが指先に残る",
            f"{hook}にも触れられないまま",
        ]
    if section == "chorus_final":
        return [
            f"{hook} {hook}",
            f"{a}の痛みも抱きしめて",
            f"{b}の向こうへ踏み出して",
            f"{c}の残響を越えていけ",
            "最後の声で名前を呼ぶ",
        ]
    if section == "chorus":
        return [
            f"{hook} {hook}",
            f"{a}のままで触れていたい",
            f"{b}だけではもう足りない",
            "この心音ごと連れていって",
        ]
    if section == "outro":
        return [
            f"{a}だけが静かに残っている",
            f"{hook}が夜明けに溶けていく",
        ]
    return [
        f"{hook}が静かに揺れている",
        f"{a}が胸の奥で光っている",
    ]


def _lines_for_default(section: str, hook: str, a: str, b: str, c: str, *, variant: int) -> list[str]:
    if section == "intro":
        return _choose_lines(
            [
                [f"{a}の奥で息が止まる", f"{b}だけがまだ揺れている", f"{hook}が静かに目を開く"],
                [f"{a}の影で足が止まる", f"{b}だけが胸に残っている", f"{hook}がゆっくり輪郭を持つ"],
            ],
            variant,
        )
    if section in {"verse_1", "verse_2"}:
        return [
            f"{a}を噛んで夜を飲みこむ",
            f"{b}の影が胸を擦っていく",
            f"{c}の匂いが指先に残る",
            "やさしい声ほど深く刺さる",
        ]
    if "pre_chorus" in section:
        return [
            f"{a}が近づくたびにずれる",
            f"{b}の隙間で熱が暴れる",
            f"{hook}まであと少しなのに",
        ]
    if section == "bridge":
        return [
            f"{a}だけがゆっくり沈んでいく",
            f"{b}が耳の奥で冷えていく",
            f"{hook}にも触れられないまま",
        ]
    if section == "chorus_final":
        return [
            f"{hook} {hook}",
            f"{a}のままで壊れていけ",
            f"{b}の色ごと噛み砕いて",
            f"{c}まで全部ひっくり返せ",
            "かわいい顔で牙を立てろ",
        ]
    if section == "chorus":
        return [
            f"{hook} {hook}",
            f"{a}のままで壊れていく",
            f"{b}だけではもう足りない",
            "かわいい顔で牙を立てる",
        ]
    if section == "outro":
        return [
            f"{a}だけが夜に沈んでいく",
            f"{hook}が遠くでまだ揺れている",
        ]
    return [
        f"{hook}が静かに揺れている",
        f"{a}が胸の奥で光っている",
    ]


def _render_section(
    section: str,
    hook: str,
    a: str,
    b: str,
    c: str,
    *,
    mode: str,
    artist_id: str,
    variant: int,
) -> list[str]:
    if mode == "dark_cute_breakdown":
        return _lines_for_dark_cute_breakdown(section, hook, a, b, c, artist_id=artist_id, variant=variant)
    if mode == "direct_emotional_pop":
        return _lines_for_direct_emotional_pop(section, hook, a, b, c, variant=variant)
    return _lines_for_default(section, hook, a, b, c, variant=variant)


def run_renderer_stage(
    plan: dict[str, Any],
    *,
    variant_index: int,
    scaffold_mode: bool = False,
) -> dict[str, Any]:
    artist_id = safe_text(plan.get("artist_id", "default"))
    mode = safe_text(plan.get("primary_mode") or plan.get("mode_id") or "default")
    hook = safe_text(plan.get("hook_blueprint", {}).get("core_text", ""))
    rng = random.Random(int(hashlib.md5(f"{plan['track_id']}:{variant_index}".encode("utf-8")).hexdigest()[:8], 16))

    if not contains_japanese(hook) or contains_bad_script(hook):
        hook = _MODE_FALLBACK_HOOKS.get(mode, _MODE_FALLBACK_HOOKS["default"])

    lines = [f"# {hook}", ""]
    section_cards = list(plan.get("section_cards", []))

    ordered_sections = list(plan.get("form_profile", {}).get("section_order", []))
    if ordered_sections:
        index_map = {name: idx for idx, name in enumerate(ordered_sections)}
        section_cards.sort(key=lambda card: index_map.get(safe_text(card.get("section")), 999))
    else:
        section_cards.sort(key=lambda card: safe_text(card.get("section")))

    for card in section_cards:
        section = safe_text(card.get("section"))
        if not section:
            continue
        force_hook = section in {"chorus", "chorus_final", "outro"}
        terms = _terms_for_card(card, hook, force_hook=force_hook)
        if not force_hook and terms and terms[0] == hook and len(terms) > 1:
            terms = terms[1:] + terms[:1]
        term_offset = variant_index + sum(ord(ch) for ch in section)
        a, b, c = _pick_triplet(terms, offset=term_offset)
        lines.append(f"[{section}]")
        section_lines = _render_section(
            section,
            hook,
            a,
            b,
            c,
            mode=mode,
            artist_id=artist_id,
            variant=variant_index + len(lines),
        )
        if scaffold_mode and section in {"chorus", "chorus_final"}:
            section_lines = list(section_lines) + [f"{hook}をもう一度繰り返す"]
        lines.extend(section_lines)
        lines.append("")

    return {
        "candidate_id": f"{plan['track_id']}-candidate-{variant_index + 1}",
        "title": hook,
        "markdown": "\n".join(lines).strip() + "\n",
        "scaffold_mode": scaffold_mode,
        "artist_id": artist_id,
    }
