from __future__ import annotations

import hashlib
import random
import re
from typing import Any

from ..lexical_family_bank import is_cliche_term, pick_family_balanced_terms
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


_LOW_SIGNAL_NON_CHORUS_TERMS = {
    "ちゅっ",
    "いないいないばあっ",
    "痛い痛い痛い",
    "鏡よ鏡",
    "真っ赤な",
    "痛い",
}


def _is_low_signal_non_chorus_term(term: str, *, section: str) -> bool:
    if section in {"chorus", "chorus_final"}:
        return False
    return safe_text(term) in _LOW_SIGNAL_NON_CHORUS_TERMS


def _is_non_chorus_hook_term(term: str, hook: str, *, section: str) -> bool:
    if section in {"chorus", "chorus_final"}:
        return False
    return bool(safe_text(term)) and safe_text(term) == safe_text(hook)


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


def _render_context(card: dict[str, Any]) -> dict[str, Any]:
    context = card.get("_render_context", {})
    return context if isinstance(context, dict) else {}


def _render_artist_id(card: dict[str, Any]) -> str:
    return safe_text(_render_context(card).get("artist_id", ""))


def _chorus_proposition(card: dict[str, Any], hook: str) -> dict[str, Any]:
    context = _render_context(card)
    composition_brief = context.get("composition_brief", {})
    proposition = composition_brief.get("chorus_proposition", {}) if isinstance(composition_brief, dict) else {}
    core_phrase = safe_text(proposition.get("core_phrase"))
    if not core_phrase or not contains_japanese(core_phrase) or contains_bad_script(core_phrase):
        core_phrase = hook
    return {
        "core_phrase": core_phrase,
        "escalation_phrase": safe_text(proposition.get("escalation_phrase")).lower(),
        "release_phrase": safe_text(proposition.get("release_phrase")).lower(),
    }


def _hybrid_context_blocked_terms(card: dict[str, Any]) -> list[str]:
    context = _render_context(card)
    recent_terms = [
        safe_text(term)
        for term in context.get("last_non_chorus_terms", [])
        if safe_text(term)
    ][:2]
    usage = context.get("non_chorus_term_usage", {})
    recurring_terms = [
        safe_text(term)
        for term, count in usage.items()
        if safe_text(term) and int(count or 0) >= 2
    ]
    return unique_preserve_order(recent_terms + recurring_terms)


def _hook_blueprint(card: dict[str, Any]) -> dict[str, Any]:
    context = _render_context(card)
    hook_blueprint = context.get("hook_blueprint", {})
    return hook_blueprint if isinstance(hook_blueprint, dict) else {}


def _renderer_frame_family(mode: str, form_family_id: str) -> str:
    return f"{safe_text(mode)}/{safe_text(form_family_id)}"


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


def _count_hook_mentions(lines: list[str], hook: str) -> int:
    hook_clean = safe_text(hook).replace(" ", "")
    if not hook_clean:
        return 0
    return sum(re.sub(r"\s+", "", line).count(hook_clean) for line in lines)


def _realized_hook_pressure(chorus_lines: list[str], chorus_final_lines: list[str], hook: str) -> str:
    target_lines = list(chorus_lines) + list(chorus_final_lines)
    mentions = _count_hook_mentions(target_lines, hook)
    if mentions >= 5:
        return "high"
    if mentions >= 3:
        return "medium"
    return "low"


def _term_pool(card: dict[str, Any], hook: str, *, mode: str) -> list[str]:
    section = safe_text(card.get("section"))
    # Conditioning atoms from plan are highest priority — they are artist-specific
    conditioning_atoms = _clean_terms(list(card.get("conditioning_atoms", []))[:6], limit=6)
    primary = _clean_terms(
        list(card.get("required_imagery", []))
        + [card.get("scene", "")]
        + list(card.get("imagery_focus", [])),
        limit=8,
    )
    secondary = _clean_terms(list(card.get("required_motifs", [])), limit=8)
    defaults = _SECTION_DEFAULT_TERMS.get(safe_text(card.get("section")), []) + _MODE_DEFAULT_TERMS.get(mode, _MODE_DEFAULT_TERMS["default"])
    # conditioning_atoms first, then primary imagery, then secondary, then defaults
    pool = unique_preserve_order(conditioning_atoms + primary + [item for item in secondary if item not in primary] + defaults)
    if not pool:
        fallback_hook = hook if contains_japanese(hook) and not contains_bad_script(hook) else _MODE_FALLBACK_HOOKS.get(mode, "残響")
        pool = [fallback_hook] + _SECTION_DEFAULT_TERMS.get(safe_text(card.get("section")), ["残響", "体温", "呼吸"])
    filtered = [
        term
        for term in pool
        if not _is_low_signal_non_chorus_term(term, section=section)
        and not _is_non_chorus_hook_term(term, hook, section=section)
    ]
    if filtered:
        pool = filtered
    return unique_preserve_order(pool)


def _pick_terms(pool: list[str], offset: int, *, section: str, count: int = 4) -> list[str]:
    if not pool:
        pool = ["残響", "体温", "呼吸", "輪郭"]
    balanced = pick_family_balanced_terms(pool, section=section, offset=offset, count=count)
    if not balanced:
        head = list(pool[:2])
        tail = list(pool[2:6]) or list(pool[2:]) or list(pool[:])
        shift = offset % len(tail)
        balanced = head + list(tail[shift:] + tail[:shift])
    filtered = [term for term in balanced if not _is_low_signal_non_chorus_term(term, section=section)]
    if filtered:
        balanced = filtered
    if len(balanced) < count:
        fallback_terms = [term for term in pool if not _is_low_signal_non_chorus_term(term, section=section)]
        if not fallback_terms:
            fallback_terms = [
                term
                for term in _SECTION_DEFAULT_TERMS.get(section, []) + _MODE_DEFAULT_TERMS.get("default", [])
                if not _is_low_signal_non_chorus_term(term, section=section)
            ]
        if not fallback_terms:
            fallback_terms = list(pool)
        for term in fallback_terms:
            if len(balanced) >= count:
                break
            if term not in balanced:
                balanced.append(term)
    while len(balanced) < count:
        balanced.append(balanced[-1])
    return balanced[:count]


def _distinct_term(primary: str, *fallbacks: str) -> str:
    root = safe_text(primary)
    for candidate in fallbacks:
        text = safe_text(candidate)
        if not text:
            continue
        if text == root:
            continue
        if root and (text in root or root in text):
            continue
        return text
    return root


def _de_cliche_term(primary: str, *fallbacks: str) -> str:
    root = safe_text(primary)
    if root and not is_cliche_term(root):
        return root
    return _distinct_term(root, *fallbacks)


def _term_conflicts(term: str, blocked: list[str]) -> bool:
    text = safe_text(term)
    if not text:
        return True
    for other in blocked:
        candidate = safe_text(other)
        if not candidate:
            continue
        if text == candidate:
            return True
        if text in candidate or candidate in text:
            return True
    return False


def _section_alternate_terms(card: dict[str, Any], hook: str) -> list[str]:
    section = safe_text(card.get("section"))
    values = (
        list(card.get("required_motifs", []))
        + list(card.get("required_imagery", []))
        + list(card.get("imagery_focus", []))
        + [card.get("scene", "")]
    )
    if section in {"chorus", "chorus_final"}:
        values.append(hook)
    terms = _clean_terms(values, limit=12)
    filtered = [
        term
        for term in terms
        if not _is_low_signal_non_chorus_term(term, section=section)
        and not _is_non_chorus_hook_term(term, hook, section=section)
    ]
    if section not in {"chorus", "chorus_final"}:
        return filtered
    return filtered or terms


def _section_support_terms(card: dict[str, Any], hook: str) -> list[str]:
    section = safe_text(card.get("section"))
    banned = {
        safe_text(term)
        for term in list(card.get("required_imagery", []))[:2]
    }
    values = (
        list(card.get("imagery_focus", []))
        + [card.get("scene", "")]
        + list(card.get("required_motifs", []))
    )
    if section in {"chorus", "chorus_final"}:
        values.append(hook)
    terms = [
        term
        for term in _clean_terms(values, limit=12)
        if safe_text(term) not in banned
    ]
    filtered = [
        term
        for term in terms
        if not _is_low_signal_non_chorus_term(term, section=section)
        and not _is_non_chorus_hook_term(term, hook, section=section)
    ]
    if section not in {"chorus", "chorus_final"}:
        return filtered
    return filtered or terms


def _pick_section_distinct_term(primary: str, *, blocked: list[str], alternates: list[str], allow_cliche: bool = False) -> str:
    root = safe_text(primary)
    candidates = [root] + alternates
    for candidate in candidates:
        text = safe_text(candidate)
        if not text:
            continue
        if not allow_cliche and is_cliche_term(text):
            continue
        if _term_conflicts(text, blocked):
            continue
        return text
    for candidate in candidates:
        text = safe_text(candidate)
        if text and not _term_conflicts(text, blocked):
            return text
    return root


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
    # verse_1 packs: observational → introspective flow
    v1_packs = [
        [
            f"{a}の匂いがまだ残ってるくせに",
            f"もう{b}のことは忘れたふりをする",
            f"{c}のせいだって言い訳ばかり増えていく",
            f"それでも{support}だけは手放せない",
        ],
        [
            f"どうせ{a}なんて最初から壊れてた",
            f"{b}の輪郭をなぞるたび指が{sting}",
            f"{c}を隠すほど痛みがよく見える",
            f"{support}みたいな言葉ほど深く刺さる",
        ],
        [
            f"{a}を数えるたび{b}の膜だけ薄くなる",
            f"{c}のしびれで視界の端が揺れていく",
            f"まともな顔して笑ってるのが一番きつい",
            f"{support}の置き方ひとつで夜が濁っていく",
        ],
    ]
    # verse_2 packs: escalation → rawer, more direct
    v2_packs = [
        [
            f"{a}のこと好きだった気がする",
            f"でも{b}の裏にはいつも{c}が透けていた",
            f"嘘つき。全部嘘つき。",
            f"{support}すら信じられないまま朝が来る",
        ],
        [
            f"何度{a}を塗り替えても{b}が滲む",
            f"きれいな{c}ほど先に壊れていくって",
            f"誰が教えてくれた？ 誰も教えてくれない",
            f"{support}の残骸だけが正しく光る",
        ],
        [
            f"{a}を捨てろ、{b}を捨てろ、",
            f"そう言い聞かせるたび{c}が増えていく",
            f"矛盾ごと飲み込んで笑えるほど",
            f"もう{support}には慣れてしまった",
        ],
    ]
    if second_half:
        return v2_packs[variant % len(v2_packs)]
    return v1_packs[variant % len(v1_packs)]


def _pre_chorus_lines(card: dict[str, Any], hook: str, terms: list[str], flags: set[str], *, variant: int, second_half: bool) -> list[str]:
    a, b, c, d = terms
    collapse = "壊れそうだ" if "collapse" in flags else "ずれていく"
    can_title_drop = safe_text(card.get("title_drop_policy")) != "withhold"
    closing = f"もう{hook}しか聞こえない" if can_title_drop and second_half else f"もう{d}しか残ってない"
    packs = [
        [
            f"わかってる、全部わかってるのに",
            f"{b}が{c}を呼んでしまう",
            closing,
        ],
        [
            f"息を止めたって{a}は消えない",
            f"{b}の奥で{c}がまだ脈を打ってる",
            closing,
        ],
        [
            f"限界なんてとっくに超えてた",
            f"{a}も{b}も{c}も全部抱えたまま",
            closing,
        ],
    ]
    return packs[variant % len(packs)]


def _dense_intro_lines(card: dict[str, Any], hook: str, terms: list[str], flags: set[str], *, variant: int) -> list[str]:
    a, b, c, d = terms
    mentions = _policy_mentions("intro", hook, safe_text(card.get("title_drop_policy")), safe_text(card.get("hook_pressure")), variant=variant)
    packs = [
        [
            f"{a}の音だけ喉に錆びついている",
            f"{b}まみれの光がまぶたの裏を裂く",
            mentions[0] if mentions else f"{c}だけまだ歯の奥で鳴っている",
            f"{d}の甘さだけ胃の底で腐り続ける",
        ],
        [
            f"{a}の粒が胸の裏でひび割れながら鳴り続ける",
            f"{b}の気配が薄い膜みたいに首筋へ貼りつく",
            mentions[0] if mentions else f"{c}だけまだこちらを噛み返してくる",
            f"{d}の余熱が呼吸の縁で黒く燻っている",
        ],
        [
            f"{a}を噛むたび部屋の明度が骨ごと狂っていく",
            f"{b}の影だけきれいな顔で床へ転がっていく",
            mentions[0] if mentions else f"{c}の匂いがまだ喉の奥でほどけない",
            f"{d}まで静かに濡れてこちらへ寄ってくる",
        ],
    ]
    if "sweet" in flags and "unease" in flags:
        packs[0][3] = f"{d}の甘さだけ不穏に腐って残っている"
    return packs[variant % len(packs)]


def _dense_verse_lines(card: dict[str, Any], hook: str, terms: list[str], flags: set[str], *, variant: int, second_half: bool) -> list[str]:
    a, b, c, d = terms
    if second_half:
        alternates = [
            term
            for term in _section_alternate_terms(card, hook)
            if safe_text(term) != safe_text(a)
        ]
        a = _pick_section_distinct_term(
            "",
            blocked=[],
            alternates=alternates + [_de_cliche_term(a, b, d, hook)],
            allow_cliche=False,
        )
        b = _pick_section_distinct_term(
            b,
            blocked=[a],
            alternates=alternates,
            allow_cliche=False,
        )
        c = _pick_section_distinct_term(
            _de_cliche_term(c, b, d, a, hook),
            blocked=[a, b],
            alternates=alternates,
            allow_cliche=False,
        )
        d = _pick_section_distinct_term(
            _distinct_term(d, b, a, hook),
            blocked=[a, b, c],
            alternates=alternates,
            allow_cliche=False,
        )
    sting = _ending_word(flags, "曲がる")
    support = _support_word(flags, c, d)
    if second_half:
        support = _pick_section_distinct_term(
            _distinct_term(support, c, d, hook),
            blocked=[a, b, c, d],
            alternates=_section_support_terms(card, hook),
            allow_cliche=False,
        )
    verb = "増えていく" if not second_half else "剥がれていく"
    packs = [
        [
            f"{a}をなぞるたび{b}の輪郭が{verb}",
            f"{c}の匂いで呼吸が少し{sting}",
            f"{d}のせいで笑い方まで痺れていく",
            f"{support}を隠すほど痛みがよく見える",
        ],
        [
            f"{a}を舐めるたび{b}の温度だけ骨まで食い込んでくる",
            f"{c}の残り香で脈の速さが首を絞めていく",
            f"{d}の気配でまともな顔が先に剥がれる",
            f"{support}みたいな言葉ほど深く刺さって抜けない",
        ],
        [
            f"{a}を数えるたび{b}の膜だけ無防備に薄くなる",
            f"{c}のしびれで視界の端から順に裂けていく",
            f"{d}の笑みが静かに皮膚の裏へ移ってくる",
            f"{support}の置き方ひとつで夜が濁って戻れなくなる",
        ],
    ]
    return packs[variant % len(packs)]


def _dense_pre_chorus_lines(card: dict[str, Any], hook: str, terms: list[str], flags: set[str], *, variant: int, second_half: bool) -> list[str]:
    a, b, c, d = terms
    section = safe_text(card.get("section"))
    if second_half:
        alternates = [
            term
            for term in _section_alternate_terms(card, hook)
            if term not in {"ノイズ", "魔法み"} and safe_text(term) != safe_text(a)
        ]
        a = _pick_section_distinct_term(
            "",
            blocked=[],
            alternates=alternates + [_de_cliche_term(a, b, d, hook)],
            allow_cliche=False,
        )
        b = _pick_section_distinct_term(
            "",
            blocked=[a],
            alternates=alternates + [_distinct_term(b, a, d, hook)],
            allow_cliche=False,
        )
        c = _pick_section_distinct_term(
            "",
            blocked=[a, b],
            alternates=alternates + [_de_cliche_term(c, d, a, hook)],
            allow_cliche=False,
        )
        d = _pick_section_distinct_term(
            d,
            blocked=[a, b, c],
            alternates=alternates,
            allow_cliche=False,
        )
        fallback_terms = [
            term
            for term in _SECTION_DEFAULT_TERMS.get(section, []) + _MODE_DEFAULT_TERMS.get("default", [])
            if term
            and not _is_low_signal_non_chorus_term(term, section=section)
            and not _is_non_chorus_hook_term(term, hook, section=section)
        ]
        if not a and fallback_terms:
            a = fallback_terms[0]
        if not b:
            b = _pick_section_distinct_term("", blocked=[a], alternates=fallback_terms, allow_cliche=False)
        if not c:
            c = _pick_section_distinct_term("", blocked=[a, b], alternates=fallback_terms, allow_cliche=False)
        if not d:
            d = _pick_section_distinct_term("", blocked=[a, b, c], alternates=fallback_terms, allow_cliche=False)
    else:
        c = _de_cliche_term(c, d, a, b)
    collapse = "壊れそうだ" if "collapse" in flags else "ずれていく"
    closing = f"{hook}まであと少しで{collapse}" if safe_text(card.get("title_drop_policy")) != "withhold" and second_half else f"{d}まであと少しで{collapse}"
    packs = (
        [
            [
                f"{a}が点滅して心臓の位置ごとずらされる",
                f"{b}の隙間で{c}だけ先に膨れ上がる",
                closing,
            ],
            [
                f"{a}が脈の裏側で静かに裂け続けていく",
                f"{b}の継ぎ目から{c}だけ先に滲み始める",
                closing,
            ],
            [
                f"{a}に触れるたび呼吸の拍が壊れ始める",
                f"{b}の継ぎ目で{c}だけやけに明滅しすぎる",
                closing,
            ],
        ]
        if not second_half
        else [
            [
                f"{a}が点滅して胸骨の内側を急かし続ける",
                f"{b}の隙間で{c}だけ先に痙攣し始める",
                closing,
            ],
            [
                f"{a}が脈の裏側で静かに裂け続けていく",
                f"{b}の継ぎ目から{c}だけ先に逆流し始める",
                closing,
            ],
            [
                f"{a}に触れるたび呼吸の拍が壊れ始める",
                f"{b}の継ぎ目で{c}だけ喉元までせり上がる",
                closing,
            ],
        ]
    )
    return packs[variant % len(packs)]


def _dense_outro_lines(card: dict[str, Any], hook: str, terms: list[str], flags: set[str], *, variant: int) -> list[str]:
    a, b, c, d = terms
    a = _distinct_term(a, b, c, d, hook)
    b = _distinct_term(b, c, d, a, hook)
    c = _distinct_term(c, d, a, b, hook)
    mentions = _policy_mentions("outro", hook, safe_text(card.get("title_drop_policy")), safe_text(card.get("hook_pressure")), variant=variant)
    tail = mentions[0] if mentions else f"{hook}が遠くでまだ瞬いている"
    packs = [
        [
            f"{a}だけが最後まで部屋の湿度を抱え込んでいる",
            tail,
            f"{b}の残り香だけが靴底から離れない",
        ],
        [
            f"{a}だけが最後までこちらの体温を覚えている",
            tail,
            f"{c}の薄明かりだけが眠れずに貼りついている",
        ],
        [
            f"{a}だけが最後まで床の上でゆっくり腐っていく",
            tail,
            f"{d}の気配だけが朝まで指先に残っている",
        ],
    ]
    return packs[variant % len(packs)]


def _chorus_lines(card: dict[str, Any], hook: str, terms: list[str], flags: set[str], *, variant: int, final: bool) -> list[str]:
    a, b, c, d = terms
    proposition = _chorus_proposition(card, hook)
    core_phrase = safe_text(proposition.get("core_phrase")) or hook
    escalation_hint = safe_text(proposition.get("escalation_phrase"))
    release_hint = safe_text(proposition.get("release_phrase"))
    hook_blueprint = _hook_blueprint(card)
    policy = safe_text(card.get("title_drop_policy"))
    pressure = safe_text(card.get("hook_pressure"), "medium")
    mentions = _policy_mentions("chorus_final" if final else "chorus", core_phrase, policy, pressure, variant=variant)
    attack = "押し込んで" if "pressure" in escalation_hint else ("噛み砕いて" if "collapse" in flags or final else "締めて")
    dark_word = _support_word(flags, b, c)
    repetition_pressure = safe_text(hook_blueprint.get("repetition_pressure"), pressure)
    if final:
        packs = [
            [
                f"{core_phrase} {core_phrase}",
                f"{core_phrase}をやめるな",
                f"{a}の残響ごと胸骨まで割っていけ",
                f"{b}の甘さを最後まで誤魔化すな",
                f"{c}だけをここで逃がすな",
                f"{d}も名前も全部ひっくり返せ" if "irreversible" in release_hint else f"{d}の底でまだ笑ってみせろ",
            ],
            [
                f"{core_phrase} {core_phrase}",
                f"{core_phrase}をやめるな",
                f"{a}の火花で喉の奥まで焼き切って",
                f"{b}のかわいさで赦された気になるな",
                f"{c}ごと今すぐ引きずり落とせ",
                f"{core_phrase}の色で最後まで息を塞げ",
            ],
            [
                f"{core_phrase} {core_phrase}",
                f"{core_phrase}をやめるな",
                f"{a}の骨までまとめて踏み抜いていけ",
                f"{b}の明度を最後まで信じるな",
                f"{c}も拍もまとめて裂いてしまえ",
                f"{d}の底でまだ笑ってみせろ",
            ],
        ]
        lines = packs[variant % len(packs)]
        if repetition_pressure == "high" and len(lines) >= 2:
            lines[0] = f"{core_phrase} {core_phrase}"
            lines[1] = f"{core_phrase}をやめるな"
        return lines
    packs = [
        [
            f"{core_phrase} {core_phrase}",
            f"{core_phrase}をまだやめない",
            f"{a}の破片を奥歯の裏まで{attack}",
            f"{b}だけではまだ傷口が黙らない",
        ],
        [
            f"{core_phrase} {core_phrase}",
            f"{core_phrase}をまだ飲み込めない",
            f"{a}の熱だけ喉元まで連れていって",
            f"{dark_word}だけではもう呼吸がほどけない",
        ],
        [
            f"{core_phrase} {core_phrase}",
            f"{core_phrase}をまだ手放せない",
            f"{a}の残響を胸骨の内側まで押し当てて",
            f"{d}だけではまだ脈が止まらない",
        ],
    ]
    lines = packs[variant % len(packs)]
    if repetition_pressure != "high":
        lines[1] = f"{core_phrase}をまだ手放せない"
    return lines


def _bridge_lines(card: dict[str, Any], hook: str, terms: list[str], flags: set[str], *, variant: int) -> list[str]:
    a, b, c, d = terms
    alternates = _section_alternate_terms(card, hook)
    compact_a = safe_text(a).replace(" ", "")
    if len(compact_a) <= 2 or safe_text(a).endswith("い"):
        a = _pick_section_distinct_term(
            "",
            blocked=[],
            alternates=alternates + [b, c, d],
            allow_cliche=False,
        )
    packs = [
        [
            f"{a}の底だけ静かに濡れ続けている",
            f"{b}の反射で部屋の温度が少し下がる",
            f"{c}だけが指先から離れない",
        ],
        [
            f"{a}を伏せたまま秒針だけが進んでいく",
            f"{b}の膜が薄く笑っている",
            f"{c}まで黙らせることができない",
        ],
        [
            f"{a}を隠したまま水位だけ上がっていく",
            f"{b}だけ妙に白く光っている",
            f"{d}の沈黙だけがこっちを見ている",
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


def _render_dark_cute_compressed_section(
    card: dict[str, Any],
    *,
    hook: str,
    terms: list[str],
    flags: set[str],
    variant: int,
) -> list[str]:
    section = safe_text(card.get("section"))
    local_flags = set(flags) | {"sweet", "unease"}
    if section == "intro":
        return _dense_intro_lines(card, hook, terms, local_flags, variant=variant)
    if section == "verse_1":
        return _dense_verse_lines(card, hook, terms, local_flags, variant=variant, second_half=False)
    if section == "verse_2":
        return _dense_verse_lines(card, hook, terms, local_flags, variant=variant, second_half=True)
    if section == "pre_chorus":
        return _dense_pre_chorus_lines(card, hook, terms, local_flags, variant=variant, second_half=False)
    if section == "pre_chorus_2":
        return _dense_pre_chorus_lines(card, hook, terms, local_flags, variant=variant, second_half=True)
    if section == "chorus":
        return _chorus_lines(card, hook, terms, local_flags, variant=variant, final=False)
    if section == "bridge":
        return _bridge_lines(card, hook, terms, local_flags, variant=variant)
    if section == "chorus_final":
        return _chorus_lines(card, hook, terms, local_flags, variant=variant, final=True)
    if section == "outro":
        return _dense_outro_lines(card, hook, terms, local_flags, variant=variant)
    a, b, c, _ = terms
    return [f"{a}だけがまだ息をしている", f"{b}の奥で{c}がまだざらついている"]


def _hybrid_chorus_lines(card: dict[str, Any], hook: str, terms: list[str], *, final: bool) -> list[str]:
    a, b, c, _ = terms
    proposition = _chorus_proposition(card, hook)
    core_phrase = safe_text(proposition.get("core_phrase")) or hook
    if final:
        return [
            f"{core_phrase}だけではもう誤魔化せない",
            f"{core_phrase} {core_phrase}",
            f"{core_phrase}をやめるな",
            f"{b}の熱で喉元まで裂いていけ",
            f"{c}ごと今すぐ抱えたまま落ちていけ",
        ]
    return [
        f"{core_phrase}だけじゃまだ足りない",
        f"{core_phrase} {core_phrase}",
        f"{core_phrase}をまだ手放せない",
        f"{b}の熱で指先まで染め上げて",
        f"{c}の残り香を噛んだまま沈んでいけ",
    ]


def _hybrid_terms(card: dict[str, Any], hook: str, terms: list[str]) -> list[str]:
    section = safe_text(card.get("section"))
    a, b, c, d = terms
    blocked_terms: list[str] = []
    if section in {"intro", "verse_1", "verse_2", "pre_chorus", "pre_chorus_2", "bridge"}:
        blocked_terms = _hybrid_context_blocked_terms(card)
    alternates = [
        term
        for term in _section_alternate_terms(card, hook)
        if not _term_conflicts(term, blocked_terms)
    ]
    support_terms = [
        term
        for term in _section_support_terms(card, hook)
        if not _term_conflicts(term, blocked_terms)
    ]
    candidate_pool = alternates + support_terms
    if len(candidate_pool) < 2:
        blocked_terms = []
        alternates = _section_alternate_terms(card, hook)
        support_terms = _section_support_terms(card, hook)
        candidate_pool = alternates + support_terms
    a = _pick_section_distinct_term(
        "" if _term_conflicts(a, blocked_terms) else _de_cliche_term(a, b, c, d, hook),
        blocked=list(blocked_terms),
        alternates=candidate_pool,
        allow_cliche=False,
    )
    b = _pick_section_distinct_term(
        "" if _term_conflicts(b, blocked_terms + [a]) else _de_cliche_term(b, c, d, a, hook),
        blocked=list(blocked_terms) + [a],
        alternates=candidate_pool,
        allow_cliche=False,
    )
    c = _pick_section_distinct_term(
        "" if _term_conflicts(c, blocked_terms + [a, b]) else _de_cliche_term(c, d, a, b, hook),
        blocked=list(blocked_terms) + [a, b],
        alternates=candidate_pool,
        allow_cliche=False,
    )
    d = _pick_section_distinct_term(
        "" if _term_conflicts(d, blocked_terms + [a, b, c]) else _de_cliche_term(d, a, b, c, hook),
        blocked=list(blocked_terms) + [a, b, c],
        alternates=candidate_pool,
        allow_cliche=False,
    )
    selected = [a, b, c, d]
    fallback_terms = [
        term
        for term in unique_preserve_order(
            candidate_pool
            + _SECTION_DEFAULT_TERMS.get(section, [])
            + _MODE_DEFAULT_TERMS.get("dark_cute_breakdown", [])
        )
        if safe_text(term)
    ]
    for index, term in enumerate(selected):
        if safe_text(term):
            continue
        blocked = [item for pos, item in enumerate(selected) if pos != index and safe_text(item)]
        replacement = _pick_section_distinct_term(
            "",
            blocked=blocked,
            alternates=fallback_terms,
            allow_cliche=False,
        )
        selected[index] = replacement or (fallback_terms[index % len(fallback_terms)] if fallback_terms else hook)
    return selected


def _hybrid_intro_lines(card: dict[str, Any], hook: str, terms: list[str], *, variant: int) -> list[str]:
    a, b, c, d = _hybrid_terms(card, hook, terms)
    packs = [
        [
            f"{a}の通知だけまだ喉元でちらついている",
            f"{b}のやさしさが画面越しに爪を立てる",
            f"{d}だけうまく消せない",
            f"{c}の熱で笑顔まで少し遅れて滲む",
        ],
        [
            f"{a}の気配だけ先に指先へ貼りついてくる",
            f"{b}の明度がまぶたの裏でじわじわ歪んでいく",
            f"{c}だけまだ息の浅いところに残ってる",
            f"{d}の余熱で言い訳まで甘く腐っていく",
        ],
    ]
    return packs[variant % len(packs)]


def _hybrid_verse_lines(
    card: dict[str, Any],
    hook: str,
    terms: list[str],
    *,
    variant: int,
    second_half: bool,
) -> list[str]:
    a, b, c, d = _hybrid_terms(card, hook, terms)
    if second_half:
        packs = [
            [
                f"{a}の明滅ばかり追いかけて夜まで遅れ始める",
                f"{b}の温度を読むたび鼓動だけ先に急いていく",
                f"{c}を抱えたまま笑うほど逃げ場がなくなる",
                f"{d}より甘い言い訳ではもう隠しきれない",
            ],
            [
                f"{a}の気分ひとつで呼吸まで細くなっていく",
                f"{b}の残り香を測るたび視界だけ少し尖り出す",
                f"{c}を欲しがるほどかわいく壊れていく",
                f"{d}を真似した愛ではもう足りなくなる",
            ],
        ]
        return packs[variant % len(packs)]
    packs = [
        [
            f"{a}の既読ばかり気にして息が浅くなる",
            f"{b}の温度を測るたび指先まで嘘になる",
            f"{c}を欲しがるほどかわいく壊れていく",
            f"{d}みたいな愛ほど雑に刺さって抜けない",
        ],
        [
            f"{a}の輪郭ばかりなぞって朝まで眠れない",
            f"{b}の機嫌を待つたび心拍だけ先に濁っていく",
            f"{c}を隠すほど依存だけよく見えてしまう",
            f"{d}よりやさしいふりではもう誤魔化せない",
        ],
    ]
    return packs[variant % len(packs)]


def _hybrid_bridge_lines(terms: list[str]) -> list[str]:
    a, b, c, d = terms
    return [
        f"{a}を隠したまま視界だけ半拍遅れる",
        f"{b}の反射で{c}の輪郭が少し遠のく",
        f"{d}の余熱だけうまく捨てられない",
    ]


def _hybrid_outro_lines(terms: list[str], *, variant: int) -> list[str]:
    a, b, c, d = terms
    packs = [
        [
            f"{a}の余熱だけがまだ部屋に残っている",
            f"{b}の残り香だけが眠れずにいる",
            f"{c}の静電気だけ床を転がっていく",
        ],
        [
            f"{a}だけが最後までこちらを見ている",
            f"{b}の薄明かりだけが靴底に貼りついている",
            f"{d}の気配だけ朝まで抜けていかない",
        ],
    ]
    return packs[variant % len(packs)]


def _hybrid_pre_chorus_lines(card: dict[str, Any], hook: str, terms: list[str], *, second_half: bool, variant: int) -> list[str]:
    a, b, c, d = _hybrid_terms(card, hook, terms)
    if second_half:
        packs = [
            [
                f"{a}が胸の裏で半拍ずつ遅れ始める",
                f"{b}の継ぎ目で{c}まで喉元へ迫り上がる",
                f"{hook}まであと少しで壊れそうだ",
            ],
            [
                f"{a}が脈の裏側で静かにせり上がってくる",
                f"{b}の反射で{c}だけ先に逃げ場をなくす",
                f"{hook}まであと少しで戻れなくなる",
            ],
        ]
        return packs[variant % len(packs)]
    packs = [
        [
            f"{a}に触れるたび拍だけ先に乱れ始める",
            f"{b}の継ぎ目で{c}まで言い訳できなくなる",
            f"もう{d}しか残ってない",
        ],
        [
            f"{a}が喉の奥で少しずつ明滅していく",
            f"{b}の隙間から{c}まで静かに染まり始める",
            f"もう{d}だけでは足りない",
        ],
    ]
    return packs[variant % len(packs)]


def _hybrid_deco27_intro_lines(card: dict[str, Any], hook: str, terms: list[str], *, variant: int) -> list[str]:
    a, b, c, d = _hybrid_terms(card, hook, terms)
    packs = [
        [
            f"{a}の通知だけ先に指先へ貼りついてくる",
            f"{b}の明度がまぶたの裏でじわじわ歪んでいく",
            f"{c}だけまだ息の浅いところに残ってる",
            f"{d}の余熱で言い訳まで甘く腐っていく",
        ],
        [
            f"{a}の既読だけ増えて夜更けがやけに近い",
            f"{b}の輪郭が笑うたび体温まで言い逃れできない",
            f"{c}だけまだ胸の浅いところで光ってる",
            f"{d}の気配でやさしさまで少し遅れて濁っていく",
        ],
    ]
    return packs[variant % len(packs)]


def _hybrid_deco27_verse_lines(
    card: dict[str, Any],
    hook: str,
    terms: list[str],
    *,
    variant: int,
    second_half: bool,
) -> list[str]:
    a, b, c, d = _hybrid_terms(card, hook, terms)
    if second_half:
        packs = [
            [
                f"{a}の気分ひとつで呼吸まで細くなっていく",
                f"{b}の残り香を測るたび視界だけ少し尖り出す",
                f"{c}を欲しがるほどかわいく壊れていく",
                f"{d}を真似した愛ではもう足りなくなる",
            ],
            [
                f"{a}の温度差ひとつで笑い方までずれていく",
                f"{b}を撫でるたび鼓動だけやけに素直になる",
                f"{c}を抱えたままでもまだ逃げる気になれない",
                f"{d}より軽い言い訳ではもう抱き止めきれない",
            ],
        ]
        return packs[variant % len(packs)]
    packs = [
        [
            f"{a}の既読ばかり気にして息が浅くなる",
            f"{b}の温度を測るたび指先まで嘘になる",
            f"{c}を欲しがるほどかわいく壊れていく",
            f"{d}みたいな愛ほど雑に刺さって抜けない",
        ],
        [
            f"{a}の機嫌ばかり読んで朝まで眠れない",
            f"{b}を待つたび言い訳だけ先に熱を持つ",
            f"{c}を隠すほど依存だけよく見えてしまう",
            f"{d}よりやさしいふりではもう誤魔化せない",
        ],
    ]
    return packs[variant % len(packs)]


def _hybrid_deco27_pre_chorus_lines(card: dict[str, Any], hook: str, terms: list[str], *, second_half: bool, variant: int) -> list[str]:
    a, b, c, d = _hybrid_terms(card, hook, terms)
    if second_half:
        packs = [
            [
                f"{a}が胸の裏で半拍ずつ遅れ始める",
                f"{b}の継ぎ目から言い訳まで喉元へせり上がる",
                f"{hook}まであと少しで壊れそうだ",
            ],
            [
                f"{a}が脈の内側で静かにせり上がってくる",
                f"{b}の反射で{c}までまともに笑えなくなる",
                f"{hook}まであと少しで戻れなくなる",
            ],
        ]
        return packs[variant % len(packs)]
    packs = [
        [
            f"{a}が喉の奥で少しずつ明滅していく",
            f"{b}の継ぎ目から言い訳まで静かにほどけ始める",
            f"もう{d}だけでは足りない",
            f"{c}のちらつきで足元まで軋み始める",
        ],
        [
            f"{a}に触れるたび拍だけ先に乱れ始める",
            f"{b}の通知ひとつで{c}まで言い訳できなくなる",
            f"もう{d}しか残ってない",
        ],
    ]
    return packs[variant % len(packs)]


def _hybrid_deco27_bridge_lines(terms: list[str]) -> list[str]:
    a, b, c, d = terms
    return [
        f"{a}を隠したまま視界だけ半拍遅れる",
        f"{b}の反射で{c}の輪郭が少し遠のく",
        f"{d}の余熱だけうまく捨てられない",
    ]


def _hybrid_deco27_outro_lines(terms: list[str], *, variant: int) -> list[str]:
    a, b, c, d = terms
    packs = [
        [
            f"{a}の余熱だけがまだ部屋に残っている",
            f"{b}の残り香だけが眠れずにいる",
            f"{c}の静電気だけ床を転がっていく",
        ],
        [
            f"{a}だけが最後までこちらを見ている",
            f"{b}の薄明かりだけが靴底に貼りついている",
            f"{d}の気配だけ朝まで抜けていかない",
        ],
    ]
    return packs[variant % len(packs)]


def _render_dark_cute_hybrid_section(
    card: dict[str, Any],
    *,
    hook: str,
    terms: list[str],
    flags: set[str],
    variant: int,
) -> list[str]:
    section = safe_text(card.get("section"))
    local_flags = set(flags) | {"sweet", "unease"}
    artist_id = _render_artist_id(card)
    hybrid_terms = _hybrid_terms(card, hook, terms)
    if artist_id == "deco27":
        if section == "intro":
            return _hybrid_deco27_intro_lines(card, hook, hybrid_terms, variant=variant)
        if section == "verse_1":
            return _hybrid_deco27_verse_lines(card, hook, hybrid_terms, variant=variant, second_half=False)
        if section == "verse_2":
            return _hybrid_deco27_verse_lines(card, hook, hybrid_terms, variant=variant, second_half=True)
        if section == "pre_chorus":
            return _hybrid_deco27_pre_chorus_lines(card, hook, hybrid_terms, second_half=False, variant=variant)
        if section == "pre_chorus_2":
            return _hybrid_deco27_pre_chorus_lines(card, hook, hybrid_terms, second_half=True, variant=variant)
        if section == "bridge":
            return _hybrid_deco27_bridge_lines(hybrid_terms)
        if section == "outro":
            return _hybrid_deco27_outro_lines(hybrid_terms, variant=variant)
    if section == "intro":
        return _hybrid_intro_lines(card, hook, hybrid_terms, variant=variant)
    if section == "verse_1":
        return _hybrid_verse_lines(card, hook, hybrid_terms, variant=variant, second_half=False)
    if section == "verse_2":
        return _hybrid_verse_lines(card, hook, hybrid_terms, variant=variant, second_half=True)
    if section == "pre_chorus":
        return _hybrid_pre_chorus_lines(card, hook, hybrid_terms, second_half=False, variant=variant)
    if section == "pre_chorus_2":
        return _hybrid_pre_chorus_lines(card, hook, hybrid_terms, second_half=True, variant=variant)
    if section == "chorus":
        return _hybrid_chorus_lines(card, hook, hybrid_terms, final=False)
    if section == "bridge":
        return _hybrid_bridge_lines(hybrid_terms)
    if section == "chorus_final":
        return _hybrid_chorus_lines(card, hook, hybrid_terms, final=True)
    if section == "outro":
        return _hybrid_outro_lines(hybrid_terms, variant=variant)
    a, b, c, _ = hybrid_terms
    return [f"{a}の明滅だけがまだ収まらない", f"{b}の裏で{c}だけ先に跳ねている"]


def _render_section(
    card: dict[str, Any],
    *,
    hook: str,
    terms: list[str],
    mode: str,
    form_family_id: str,
    variant: int,
) -> list[str]:
    section = safe_text(card.get("section"))
    flags = _goal_flags(card)
    dense_mode = mode == "dark_cute_breakdown"
    if dense_mode and form_family_id == "compressed_hook":
        return _render_dark_cute_compressed_section(card, hook=hook, terms=terms, flags=flags, variant=variant)
    if dense_mode and form_family_id == "hybrid_release":
        return _render_dark_cute_hybrid_section(card, hook=hook, terms=terms, flags=flags, variant=variant)
    if dense_mode:
        flags.update({"sweet", "unease"})
    if section == "intro":
        if dense_mode:
            return _dense_intro_lines(card, hook, terms, flags, variant=variant)
        return _intro_lines(card, hook, terms, flags, variant=variant)
    if section == "verse_1":
        if dense_mode:
            return _dense_verse_lines(card, hook, terms, flags, variant=variant, second_half=False)
        return _verse_lines(card, hook, terms, flags, variant=variant, second_half=False)
    if section == "verse_2":
        if dense_mode:
            return _dense_verse_lines(card, hook, terms, flags, variant=variant, second_half=True)
        return _verse_lines(card, hook, terms, flags, variant=variant, second_half=True)
    if section == "pre_chorus":
        if dense_mode:
            return _dense_pre_chorus_lines(card, hook, terms, flags, variant=variant, second_half=False)
        return _pre_chorus_lines(card, hook, terms, flags, variant=variant, second_half=False)
    if section == "pre_chorus_2":
        if dense_mode:
            return _dense_pre_chorus_lines(card, hook, terms, flags, variant=variant, second_half=True)
        return _pre_chorus_lines(card, hook, terms, flags, variant=variant, second_half=True)
    if section == "chorus":
        return _chorus_lines(card, hook, terms, flags, variant=variant, final=False)
    if section == "bridge":
        return _bridge_lines(card, hook, terms, flags, variant=variant)
    if section == "chorus_final":
        return _chorus_lines(card, hook, terms, flags, variant=variant, final=True)
    if section == "outro":
        if dense_mode:
            return _dense_outro_lines(card, hook, terms, flags, variant=variant)
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
    form_family_id = safe_text(plan.get("form_family_id") or "hybrid_release")
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

    render_context = {
        "artist_id": artist_id,
        "composition_brief": dict(plan.get("composition_brief", {}) or {}),
        "hook_blueprint": dict(plan.get("hook_blueprint", {}) or {}),
        "form_family_id": form_family_id,
        "artist_grammar_bias": dict(plan.get("artist_grammar_bias", {}) or {}),
        "non_chorus_term_usage": {},
        "last_non_chorus_terms": [],
    }
    section_outputs: dict[str, list[str]] = {}
    lines = [f"# {hook}", ""]
    for position, card in enumerate(section_cards):
        section = safe_text(card.get("section"))
        if not section:
            continue
        pool = _term_pool(card, hook, mode=mode)
        offset = variant_index + position + rng.randint(0, 2)
        terms = _pick_terms(pool, offset, section=section, count=4)
        card["conditioning_atoms"] = unique_preserve_order(
            terms + list(card.get("conditioning_atoms", []))
        )[:6]
        card_payload = dict(card)
        card_payload["_render_context"] = render_context
        section_lines = _render_section(
            card_payload,
            hook=hook,
            terms=terms,
            mode=mode,
            form_family_id=safe_text(card_payload.get("form_family_id") or form_family_id),
            variant=variant_index + position,
        )
        target = int(card_payload.get("line_target", len(section_lines)) or len(section_lines))
        fitted = _fit_section_lines(
            section_lines,
            section=section,
            hook=hook,
            terms=terms,
            flags=_goal_flags(card_payload),
            line_target=target,
        )
        if scaffold_mode and section in {"chorus", "chorus_final"} and hook not in "".join(fitted):
            fitted.append(f"{hook}をまだやめない")
        if section not in {"chorus", "chorus_final"}:
            render_context["last_non_chorus_terms"] = list(terms)
            usage = render_context.setdefault("non_chorus_term_usage", {})
            for term in unique_preserve_order(list(terms)):
                text = safe_text(term)
                if text:
                    usage[text] = int(usage.get(text, 0)) + 1
        section_outputs[section] = list(fitted[:target])
        lines.append(f"[{section}]")
        lines.extend(fitted[:target])
        lines.append("")

    chorus_lines = section_outputs.get("chorus", [])
    chorus_final_lines = section_outputs.get("chorus_final", [])
    return {
        "candidate_id": f"{track_id}-candidate-{variant_index + 1}",
        "title": hook,
        "markdown": "\n".join(lines).strip() + "\n",
        "scaffold_mode": scaffold_mode,
        "artist_id": artist_id,
        "form_family_id": form_family_id,
        "renderer_frame_family": _renderer_frame_family(mode, form_family_id),
        "chorus_shape": _chorus_shape_id(form_family_id),
        "bridge_shape": _bridge_shape_id(form_family_id),
        "hook_pressure_realized": _realized_hook_pressure(chorus_lines, chorus_final_lines, hook),
    }
