from __future__ import annotations

import hashlib
import random
from typing import Any

from ..lyric_utils import contains_bad_script, contains_japanese, safe_text, unique_preserve_order


_MODE_FALLBACK_HOOKS: dict[str, str] = {
    "dark_cute_breakdown": "飴の罰",
    "direct_emotional_pop": "未明の熱",
    "default": "残響",
}

_MODE_DEFAULT_TERMS: dict[str, list[str]] = {
    "dark_cute_breakdown": ["キャンディ", "遊園地", "毒", "ノイズ", "傷", "体温", "ひび", "静電気"],
    "direct_emotional_pop": ["鼓動", "夜明け", "涙", "体温", "名前", "ため息", "街灯", "残響"],
    "default": ["残響", "夜", "体温", "影", "光", "沈黙", "呼吸", "輪郭"],
}

_SECTION_DEFAULT_TERMS: dict[str, list[str]] = {
    "intro": ["光", "ノイズ", "体温"],
    "verse_1": ["呼吸", "輪郭", "傷"],
    "verse_2": ["残響", "膜", "しびれ"],
    "pre_chorus": ["警報", "点滅", "鼓動"],
    "pre_chorus_2": ["残響", "裂け目", "脈"],
    "chorus": ["熱", "毒", "笑顔"],
    "bridge": ["暗室", "沈黙", "水位"],
    "chorus_final": ["悲鳴", "落下", "火花"],
    "outro": ["余熱", "静電気", "教室"],
}

_STRONG_VERBS = ("壊", "裂", "砕", "刺", "噛", "締", "沈")
_LOW_VALUE_TERMS = {
    "誰に",
    "場所",
    "見え",
    "心を",
    "色に",
    "色で",
    "あと",
    "少し",
    "全部",
    "ことば",
    "言葉",
    "大切",
}


def _clean_terms(values: list[Any], *, limit: int = 8) -> list[str]:
    cleaned: list[str] = []
    for value in values:
        text = safe_text(value)
        if not text:
            continue
        if not contains_japanese(text):
            continue
        if contains_bad_script(text):
            continue
        visible = text.replace(" ", "")
        if text in _LOW_VALUE_TERMS:
            continue
        if len(visible) <= 3 and visible[-1] in {"に", "を", "が", "へ", "で", "と", "は", "も"}:
            continue
        if len(visible) > 14:
            continue
        if text not in cleaned:
            cleaned.append(text)
        if len(cleaned) >= limit:
            break
    return cleaned


def _goal_flags(card: dict[str, Any]) -> set[str]:
    goal_text = " ".join(str(v) for v in card.get("narrative_goals", []) if v)
    flags: set[str] = set()
    if any(token in goal_text for token in ("甘", "可愛", "やさしい")):
        flags.add("sweet")
    if any(token in goal_text for token in ("毒", "有害")):
        flags.add("poison")
    if any(token in goal_text for token in ("傷", "痛", "刺")):
        flags.add("wound")
    if any(token in goal_text for token in ("壊", "崩", "落下", "断線", "不能")):
        flags.add("collapse")
    if any(token in goal_text for token in ("笑",)):
        flags.add("smile")
    if any(token in goal_text for token in ("依存",)):
        flags.add("dependence")
    if any(token in goal_text for token in ("拒絶",)):
        flags.add("rejection")
    if any(token in goal_text for token in ("不穏", "警報", "ノイズ", "崩壊")):
        flags.add("unease")
    return flags


def _term_pool(card: dict[str, Any], hook: str, *, mode: str) -> list[str]:
    primary = _clean_terms(
        list(card.get("required_imagery", []))
        + [card.get("scene", "")]
        + list(card.get("imagery_focus", [])),
        limit=8,
    )
    secondary = _clean_terms(list(card.get("required_motifs", [])), limit=8)
    defaults = _SECTION_DEFAULT_TERMS.get(safe_text(card.get("section")), []) + _MODE_DEFAULT_TERMS.get(mode, _MODE_DEFAULT_TERMS["default"])
    pool = unique_preserve_order(primary + [item for item in secondary if item not in primary] + defaults)
    if not pool:
        fallback_hook = hook if contains_japanese(hook) and not contains_bad_script(hook) else _MODE_FALLBACK_HOOKS.get(mode, "残響")
        pool = [fallback_hook] + _SECTION_DEFAULT_TERMS.get(safe_text(card.get("section")), ["残響", "体温", "呼吸"])
    return unique_preserve_order(pool)


def _pick_terms(pool: list[str], offset: int, *, count: int = 4) -> list[str]:
    if not pool:
        pool = ["残響", "体温", "呼吸", "輪郭"]
    head = list(pool[:2])
    tail = list(pool[2:6]) or list(pool[2:]) or list(pool[:])
    shift = offset % len(tail)
    rotated = head + list(tail[shift:] + tail[:shift])
    while len(rotated) < count:
        rotated.append(rotated[-1])
    return rotated[:count]


def _policy_mentions(section: str, hook: str, policy: str, pressure: str, *, variant: int) -> list[str]:
    if not hook:
        return []
    if policy == "withhold":
        return []
    if policy == "primary":
        return [f"{hook} {hook}", f"{hook}をやめるな"] if section == "chorus_final" else [f"{hook} {hook}"]
    if policy == "anchor":
        return [f"{hook} {hook}"]
    if policy == "sparse":
        if section in {"intro", "outro"}:
            return [f"{hook}だけまだ笑ってる"] if variant % 2 == 0 else [f"{hook}が遠くでまだ瞬いている"]
        if pressure == "high" and section.startswith("chorus"):
            return [f"{hook} {hook}"]
        return []
    return []


def _support_word(flags: set[str], primary: str, secondary: str) -> str:
    if "poison" in flags:
        return "毒"
    if "wound" in flags:
        return "傷口"
    if "collapse" in flags:
        return "断線"
    if "smile" in flags:
        return "笑顔"
    return primary or secondary


def _ending_word(flags: set[str], fallback: str) -> str:
    if "collapse" in flags:
        return "壊れる"
    if "wound" in flags:
        return "刺さる"
    if "poison" in flags:
        return "濁る"
    if "dependence" in flags:
        return "離れない"
    if "rejection" in flags:
        return "戻れない"
    return fallback


def _intro_lines(card: dict[str, Any], hook: str, terms: list[str], flags: set[str], *, variant: int) -> list[str]:
    a, b, c, d = terms
    mentions = _policy_mentions("intro", hook, safe_text(card.get("title_drop_policy")), safe_text(card.get("hook_pressure")), variant=variant)
    packs = [
        [
            f"{a}の音だけ喉に残っている",
            f"{b}まみれの光がまぶたを刺す",
            mentions[0] if mentions else f"{c}だけまだ胸で跳ねている",
            f"{d}の甘さだけ夜に置き去りになる",
        ],
        [
            f"{a}の粒が胸の裏で鳴り続ける",
            f"{b}の気配が薄い膜みたいに貼りつく",
            mentions[0] if mentions else f"{c}だけまだこちらを見ている",
            f"{d}の余熱が呼吸の端でくすぶっている",
        ],
        [
            f"{a}を噛むたび部屋の明度が少し狂う",
            f"{b}の影だけきれいに床へ転がっていく",
            mentions[0] if mentions else f"{c}の匂いがまだ喉でほどけない",
            f"{d}まで静かに濁っている",
        ],
    ]
    if "sweet" in flags and "unease" in flags:
        packs[0][3] = f"{d}の甘さだけ不穏に残っている"
    return packs[variant % len(packs)]


def _verse_lines(card: dict[str, Any], hook: str, terms: list[str], flags: set[str], *, variant: int, second_half: bool) -> list[str]:
    a, b, c, d = terms
    sting = _ending_word(flags, "曲がる")
    support = _support_word(flags, c, d)
    verb = "増えていく" if not second_half else "剥がれていく"
    packs = [
        [
            f"{a}をなぞるたび{b}の輪郭が{verb}",
            f"{c}の匂いで呼吸が少し{sting}",
            f"{d}のせいで笑い方まで痺れていく",
            f"{support}を隠すほど痛みがよく見える",
        ],
        [
            f"{a}を舐めるたび{b}の温度だけ近づいてくる",
            f"{c}の残り香で脈の速さがずれていく",
            f"{d}の気配でまともな顔が先に崩れる",
            f"{support}みたいな言葉ほど深く刺さる",
        ],
        [
            f"{a}を数えるたび{b}の膜だけ薄くなる",
            f"{c}のしびれで視界の端が揺れていく",
            f"{d}の笑みが静かに皮膚へ移ってくる",
            f"{support}の置き方ひとつで夜が濁っていく",
        ],
    ]
    return packs[variant % len(packs)]


def _pre_chorus_lines(card: dict[str, Any], hook: str, terms: list[str], flags: set[str], *, variant: int, second_half: bool) -> list[str]:
    a, b, c, d = terms
    collapse = "壊れそうだ" if "collapse" in flags else "ずれていく"
    closing = f"{hook}まであと少しで{collapse}" if safe_text(card.get("title_drop_policy")) != "withhold" and second_half else f"{d}まであと少しで{collapse}"
    packs = [
        [
            f"{a}が点滅して心臓の位置がずれる",
            f"{b}の隙間で{c}だけ育っていく",
            closing,
        ],
        [
            f"{a}が脈の裏側で静かに裂けていく",
            f"{b}の継ぎ目から{c}だけ腐り始める",
            closing,
        ],
        [
            f"{a}に触れるたび呼吸の拍が狂っていく",
            f"{b}の裂け目で{c}がやけに明るい",
            closing,
        ],
    ]
    return packs[variant % len(packs)]


def _chorus_lines(card: dict[str, Any], hook: str, terms: list[str], flags: set[str], *, variant: int, final: bool) -> list[str]:
    a, b, c, d = terms
    policy = safe_text(card.get("title_drop_policy"))
    pressure = safe_text(card.get("hook_pressure"), "medium")
    mentions = _policy_mentions("chorus_final" if final else "chorus", hook, policy, pressure, variant=variant)
    attack = "噛み砕いて" if "collapse" in flags or final else "締めて"
    dark_word = _support_word(flags, b, c)
    last = f"{hook}を壊してもう一度鳴らせ" if final else f"{dark_word}ごと噛んで笑ってみせて"
    packs = [
        [
            *mentions,
            f"{a}の温度で首を{attack}",
            f"{b}だけならまだ生ぬるい",
            f"{c}ごと抱えてこちらへ落ちてこい" if final else last,
            f"{d}の骨までひっくり返していけ" if final else last,
        ],
        [
            *mentions,
            f"{a}の破片で耳の奥まで染め上げて",
            f"{b}だけではまだ何も足りない",
            f"{c}を笑顔のままで飲み込んで",
            f"{hook}を傷口へまっすぐ結びつけて" if final else f"{d}ごと噛んで踊ってみせて",
        ],
        [
            *mentions,
            f"{a}の残響で胸骨まで揺らして",
            f"{b}の甘さを最後まで誤魔化すな",
            f"{c}だけをここで逃がすな",
            f"{hook}の色で全部塗りつぶして" if final else f"{d}の毒まできれいに見せて",
        ],
    ]
    lines = packs[variant % len(packs)]
    if pressure == "high" and len(mentions) == 1 and not final:
        lines.insert(1, f"{hook}をまだやめない")
    return lines


def _bridge_lines(card: dict[str, Any], hook: str, terms: list[str], flags: set[str], *, variant: int) -> list[str]:
    a, b, c, d = terms
    mentions = _policy_mentions("bridge", hook, safe_text(card.get("title_drop_policy")), safe_text(card.get("hook_pressure")), variant=variant)
    packs = [
        [
            f"{a}を隠したまま水位だけ上がっていく",
            f"{b}だけ妙に白く光っている",
            mentions[0] if mentions else f"{c}さえうまく飲み込めない",
            f"{d}の沈黙だけがこっちを見ている",
        ],
        [
            f"{a}の底だけ静かに濡れ続けている",
            f"{b}の反射で部屋の温度が少し下がる",
            mentions[0] if mentions else f"{c}だけが指先から離れない",
            f"{d}の跡だけがやけに正確だ",
        ],
        [
            f"{a}を伏せたまま秒針だけが進んでいく",
            f"{b}の膜が薄く笑っている",
            mentions[0] if mentions else f"{c}まで黙らせることができない",
            f"{d}の輪郭だけがきれいすぎる",
        ],
    ]
    return packs[variant % len(packs)]


def _outro_lines(card: dict[str, Any], hook: str, terms: list[str], flags: set[str], *, variant: int) -> list[str]:
    a, b, c, d = terms
    mentions = _policy_mentions("outro", hook, safe_text(card.get("title_drop_policy")), safe_text(card.get("hook_pressure")), variant=variant)
    tail = mentions[0] if mentions else f"{hook}が遠くでまだ瞬いている"
    packs = [
        [
            f"{a}だけが最後まで腐らない",
            tail,
            f"{b}の静電気だけ床を転がっていく",
        ],
        [
            f"{a}の余熱だけがまだ部屋に残っている",
            tail,
            f"{c}の残り香だけが眠れずにいる",
        ],
        [
            f"{a}だけが最後までこちらを見ている",
            tail,
            f"{d}の薄明かりだけが靴底に貼りついている",
        ],
    ]
    if "aftertaste" in safe_text(card.get("function")):
        packs[0][2] = f"{b}の残り香だけが眠れずにいる"
    return packs[variant % len(packs)]


def _supplemental_line(section: str, hook: str, terms: list[str], flags: set[str], step: int) -> str:
    a, b, c, d = terms
    support = _support_word(flags, c, d)
    pools = {
        "intro": [
            f"{a}の明るさだけやけに怖い",
            f"{b}の粒がまだ舌の裏で鳴っている",
        ],
        "verse_1": [
            f"{a}の肌ざわりだけが嘘みたいにやさしい",
            f"{support}の置き方ひとつで全部ずれていく",
        ],
        "verse_2": [
            f"{a}の破片がまぶたの内側でこすれる",
            f"{support}がほどけるほど拒めなくなる",
        ],
        "pre_chorus": [
            f"{a}のちらつきで足元まで軋み始める",
            f"{b}の奥からまだ警報が消えない",
        ],
        "pre_chorus_2": [
            f"{a}の裂け目から熱が少し漏れている",
            f"{b}まで巻き込んで拍が揃わない",
        ],
        "chorus": [
            f"{a}のかわいさで全部ごまかすな",
            f"{hook}の周りだけやけに色が濃い",
        ],
        "bridge": [
            f"{a}の水位だけが正直だ",
            f"{b}の白さがいちばん危ない",
        ],
        "chorus_final": [
            f"{a}の火花までまとめて踏み抜け",
            f"{hook}の名前だけ最後まで濁らせるな",
        ],
        "outro": [
            f"{a}の余韻だけが妙に静かだ",
            f"{b}の跡だけまだ剥がれない",
        ],
    }
    candidates = pools.get(section, [f"{a}の輪郭だけがまだ消えない"])
    return candidates[step % len(candidates)]


def _fit_section_lines(
    lines: list[str],
    *,
    section: str,
    hook: str,
    terms: list[str],
    flags: set[str],
    line_target: int,
) -> list[str]:
    fitted = unique_preserve_order([safe_text(line) for line in lines if safe_text(line)])
    if line_target <= 0:
        return fitted
    step = 0
    while len(fitted) < line_target and step < 8:
        candidate = _supplemental_line(section, hook, terms, flags, step)
        if candidate not in fitted:
            fitted.append(candidate)
        step += 1
    return fitted[:line_target]


def _render_section(
    card: dict[str, Any],
    *,
    hook: str,
    terms: list[str],
    mode: str,
    variant: int,
) -> list[str]:
    section = safe_text(card.get("section"))
    flags = _goal_flags(card)
    if mode == "dark_cute_breakdown":
        flags.update({"sweet", "unease"})
    if section == "intro":
        return _intro_lines(card, hook, terms, flags, variant=variant)
    if section == "verse_1":
        return _verse_lines(card, hook, terms, flags, variant=variant, second_half=False)
    if section == "verse_2":
        return _verse_lines(card, hook, terms, flags, variant=variant, second_half=True)
    if section == "pre_chorus":
        return _pre_chorus_lines(card, hook, terms, flags, variant=variant, second_half=False)
    if section == "pre_chorus_2":
        return _pre_chorus_lines(card, hook, terms, flags, variant=variant, second_half=True)
    if section == "chorus":
        return _chorus_lines(card, hook, terms, flags, variant=variant, final=False)
    if section == "bridge":
        return _bridge_lines(card, hook, terms, flags, variant=variant)
    if section == "chorus_final":
        return _chorus_lines(card, hook, terms, flags, variant=variant, final=True)
    if section == "outro":
        return _outro_lines(card, hook, terms, flags, variant=variant)
    a, b, c, _ = terms
    return [f"{a}だけがまだ残っている", f"{b}の気配で{c}まで少し揺れる"]


def run_renderer_stage(
    plan: dict[str, Any],
    *,
    variant_index: int,
    scaffold_mode: bool = False,
) -> dict[str, Any]:
    artist_id = safe_text(plan.get("artist_id", "default"))
    mode = safe_text(plan.get("primary_mode") or plan.get("mode_id") or "default")
    track_id = safe_text(plan.get("track_id", f"{artist_id}_{mode}_demo"))
    raw_hook = safe_text(plan.get("hook_blueprint", {}).get("core_text", ""))
    hook = raw_hook if contains_japanese(raw_hook) and not contains_bad_script(raw_hook) else _MODE_FALLBACK_HOOKS.get(mode, _MODE_FALLBACK_HOOKS["default"])

    rng_seed = int(hashlib.md5(f"{track_id}:{variant_index}".encode("utf-8")).hexdigest()[:8], 16)
    rng = random.Random(rng_seed)

    section_cards = list(plan.get("section_cards", []))
    ordered_sections = list(plan.get("form_profile", {}).get("section_order", []))
    if ordered_sections:
        index_map = {name: idx for idx, name in enumerate(ordered_sections)}
        section_cards.sort(key=lambda card: index_map.get(safe_text(card.get("section")), 999))
    else:
        section_cards.sort(key=lambda card: safe_text(card.get("section")))

    lines = [f"# {hook}", ""]
    for position, card in enumerate(section_cards):
        section = safe_text(card.get("section"))
        if not section:
            continue
        pool = _term_pool(card, hook, mode=mode)
        offset = variant_index + position + rng.randint(0, 2)
        terms = _pick_terms(pool, offset, count=4)
        section_lines = _render_section(card, hook=hook, terms=terms, mode=mode, variant=variant_index + position)
        target = int(card.get("line_target", len(section_lines)) or len(section_lines))
        fitted = _fit_section_lines(
            section_lines,
            section=section,
            hook=hook,
            terms=terms,
            flags=_goal_flags(card),
            line_target=target,
        )
        if scaffold_mode and section in {"chorus", "chorus_final"} and hook not in "".join(fitted):
            fitted.append(f"{hook}をまだやめない")
        lines.append(f"[{section}]")
        lines.extend(fitted[:target])
        lines.append("")

    return {
        "candidate_id": f"{track_id}-candidate-{variant_index + 1}",
        "title": hook,
        "markdown": "\n".join(lines).strip() + "\n",
        "scaffold_mode": scaffold_mode,
        "artist_id": artist_id,
    }
