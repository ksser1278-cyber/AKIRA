from __future__ import annotations

import hashlib
import random
import re
from typing import Any

from .lyric_utils import (
    unique_preserve_order,
    is_safe_lyric_term,
    contains_japanese,
    contains_bad_script,
    safe_text,
    extract_japanese_lexical_atoms,
)
from .songwriter_io import (
    load_artist_profile,
    load_conditioning_records,
    matching_conditioning_record,
)
from .songwriter_v2 import (
    conditioning_hook_atoms,
    conditioning_contrast_terms,
    high_signal_conditioning_atoms,
)


_META_TERM_BLOCKLIST = {
    "title",
    "hook",
    "chorus",
    "bridge",
    "verse",
    "section",
    "motif",
    "release",
    "line",
    "lyric",
    "planner",
    "renderer",
    "critic",
    "narrative",
    "goal",
    "delivery",
    "テンプレ",
    "タイトル",
    "フック",
    "コーラス",
    "ブリッジ",
    "ヴァース",
    "セクション",
    "モチーフ",
    "リリース",
    "ライン",
    "歌詞",
    "プラン",
    "レンダラ",
    "クリティック",
    "ナラティブ",
    "目標",
    "確定",
    "再固定",
}


_ARTIST_IMAGERY_DEFAULTS = {
    "kanaria": ["視線", "輪郭", "沈黙", "名前", "拍手", "罠", "支配", "飾り"],
    "maretu": ["注射", "体温", "嘲笑", "残骸", "錆", "刃", "雑音", "倫理"],
    "kairiki_bear": ["鼓動", "呼吸", "指先", "衝動", "傷口", "笑顔", "雑音", "体温"],
    "iyowa": ["階段", "窓辺", "蛍光", "落書き", "小指", "残響", "影", "夢"],
    "syudou": ["舌打ち", "冗談", "悪意", "夜更け", "石", "本音", "視線", "残響"],
    "neru": ["街灯", "鉄線", "制服", "喉", "排気", "ガラクタ", "怒り", "残響"],
}


def _conditioning_seed_terms(artist_id: str, mode: str) -> list[str]:
    records = load_conditioning_records(artist_id)
    if not records:
        return []

    best_record: dict[str, Any] | None = None
    best_key: tuple[int, int, float] | None = None
    for record in records:
        generation_safety = record.get("generation_safety", {}) if isinstance(record.get("generation_safety", {}), dict) else {}
        verdict = str(generation_safety.get("verdict", "")).strip()
        if verdict not in {"planner_safe", "benchmark_safe"}:
            continue
        roles = record.get("song_intent", {}).get("narrative_role", [])
        if isinstance(roles, str):
            roles = [roles]
        role_list = [str(item).strip() for item in roles if str(item).strip()]
        title = str(record.get("track_identity", {}).get("title", "")).strip()
        lyric_ground_truth = record.get("lyric_ground_truth", {}) if isinstance(record.get("lyric_ground_truth", {}), dict) else {}
        hook_lines = lyric_ground_truth.get("hook_lines", [])
        if not isinstance(hook_lines, list):
            hook_lines = []
        if not hook_lines and not (contains_japanese(title) and not contains_bad_script(title)):
            continue
        mode_match = 1 if mode and mode in role_list else 0
        benchmark_bonus = 1 if verdict == "benchmark_safe" else 0
        score = float(generation_safety.get("score", 0.0) or 0.0)
        key = (mode_match, benchmark_bonus, score)
        if best_key is None or key > best_key:
            best_key = key
            best_record = record

    if not best_record:
        return []

    raw_values: list[Any] = []
    contrast_device = best_record.get("song_intent", {}).get("contrast_device", [])
    if isinstance(contrast_device, list):
        raw_values.extend(contrast_device)
    elif isinstance(contrast_device, str) and contrast_device.strip():
        raw_values.append(contrast_device)
    lyric_ground_truth = best_record.get("lyric_ground_truth", {}) if isinstance(best_record.get("lyric_ground_truth", {}), dict) else {}
    raw_values.append(best_record.get("track_identity", {}).get("title", ""))
    raw_values.extend(lyric_ground_truth.get("hook_lines", []))
    for section in lyric_ground_truth.get("sections", [])[:3]:
        if not isinstance(section, dict):
            continue
        raw_values.extend(section.get("lines", [])[:2])

    atoms: list[str] = []
    for value in raw_values:
        text = safe_text(value)
        if not text:
            continue
        atoms.extend(extract_japanese_lexical_atoms([text], limit=4))
        if " " not in text and "　" not in text:
            cleaned = _clean_term(text)
            if cleaned:
                atoms.append(cleaned)
    return unique_preserve_order([item for item in _filtered_japanese_atoms(atoms, limit=10) if " " not in item and "　" not in item])[:10]


def _clean_term(value: Any) -> str:
    text = safe_text(value).strip()
    if not text:
        return ""
    if not contains_japanese(text):
        return ""
    if contains_bad_script(text):
        return ""
    lowered = text.lower()
    for token in _META_TERM_BLOCKLIST:
        if token in lowered or token in text:
            return ""
    if len(text) > 16:
        return ""
    return text


def _filtered_japanese_atoms(values: list[Any], *, limit: int = 12) -> list[str]:
    raw: list[str] = []
    for value in values:
        text = safe_text(value)
        if not text:
            continue
        raw.extend(extract_japanese_lexical_atoms([text], limit=4))
        cleaned_text = _clean_term(text)
        if cleaned_text:
            raw.append(cleaned_text)

    cleaned: list[str] = []
    for item in unique_preserve_order(raw):
        candidate = _clean_term(item)
        if not candidate:
            continue
        if not is_safe_lyric_term(candidate):
            continue
        cleaned.append(candidate)
        if len(cleaned) >= limit:
            break
    return cleaned


def _artist_imagery_defaults(artist_id: str, mode: str) -> list[str]:
    return unique_preserve_order(_ARTIST_IMAGERY_DEFAULTS.get(artist_id, []) + _mode_defaults(mode))


def _section_terms(
    card: dict[str, Any],
    terms: list[str],
    *,
    artist_id: str,
    mode: str,
    hook: str,
) -> list[str]:
    raw_values: list[Any] = (
        list(card.get("required_motifs", []))
        + [card.get("scene", "")]
        + list(card.get("imagery_focus", []))
        + list(card.get("emotion_focus", []))
        + list(terms)
        + _artist_imagery_defaults(artist_id, mode)
    )
    cleaned = _filtered_japanese_atoms(raw_values, limit=12)
    if contains_japanese(hook) and not contains_bad_script(hook) and hook not in cleaned:
        cleaned.insert(0, hook)
    if not cleaned:
        cleaned = [hook] + [term for term in _artist_imagery_defaults(artist_id, mode) if term != hook]
    return unique_preserve_order(cleaned)[:12]




def _mode_defaults(mode: str) -> list[str]:
    if mode == "direct_emotional_pop":
        return ["鼓動", "熱", "指先", "夜明け", "まなざし", "声", "秘密", "涙"]
    if mode == "dark_cute_breakdown":
        return ["傷", "熱", "悪夢", "指先", "噛み跡", "体温", "ノイズ", "孤独"]
    return ["正体", "ノイズ", "街", "名前", "画面", "嘘", "拍手", "本音"]


def _safe_terms(plan: dict[str, Any], *, limit: int = 12) -> list[str]:
    demo_plan = plan.get("artist_synthesis_context", {}).get("demo_plan", {})
    composite = demo_plan.get("composite_style", {})
    raw: list[str] = []
    for value in (
        list(composite.get("theme_axes", []))
        + list(composite.get("imagery_anchors", []))
        + list(composite.get("seed_phrases", []))
    ):
        text = safe_text(value)
        if not text:
            continue
        raw.extend(extract_japanese_lexical_atoms([text], limit=4))
        if contains_japanese(text):
            raw.append(text)

    cleaned: list[str] = []
    for item in unique_preserve_order(raw):
        if not is_safe_lyric_term(item):
            continue
        if not contains_japanese(item):
            continue
        if contains_bad_script(item):
            continue
        if len(item) > 12:
            continue
        cleaned.append(item)
        if len(cleaned) >= limit:
            break
    return cleaned


def _seed_terms(plan: dict[str, Any], mode: str) -> list[str]:
    artist_id = str(plan.get("artist_id", "")).strip()
    return unique_preserve_order(
        _safe_terms(plan, limit=8)
        + _conditioning_seed_terms(artist_id, mode)
        + _artist_imagery_defaults(artist_id, mode)
    )


def _pick(rng: random.Random, values: list[str], fallback: str) -> str:
    options = [value for value in values if str(value).strip()]
    return rng.choice(options) if options else fallback


def _title_options(artist_id: str, mode: str, hook: str, secondary: str) -> list[str]:
    if artist_id == "deco27":
        if mode == "direct_emotional_pop":
            return [hook, f"{hook}の温度", f"{hook}の行方"]
        return [f"{hook}の傷", f"{secondary}の底", f"{hook}の気配"]
    if artist_id == "pinocchiop":
        return [hook, f"{hook}の正体", f"{secondary}のルール"]
    if artist_id == "kanaria":
        return [hook, f"{hook}の罠", f"{secondary}の輪郭"]
    if artist_id == "maretu":
        return [f"{hook}の残骸", f"{secondary}の倫理", f"{hook}の底"]
    return [hook, f"{hook}の正体", f"{secondary}の行方"]


def _demo_title(plan: dict[str, Any], rng: random.Random, hook: str, terms: list[str]) -> str:
    artist_id = str(plan.get("artist_id", "")).strip()
    mode = str(plan.get("primary_mode", "")).strip()
    secondary = next((item for item in terms if item != hook), "声")
    return _pick(rng, _title_options(artist_id, mode, hook, secondary), hook)


def _release_terms(artist_id: str, hook: str, a: str, b: str) -> tuple[str, str]:
    approved_terms = _artist_imagery_defaults(artist_id, "")
    picked: list[str] = []
    for item in [_clean_term(a), _clean_term(b)]:
        if not item or item == hook or item in picked:
            continue
        if item not in approved_terms:
            continue
        picked.append(item)
        if len(picked) >= 2:
            break
    for item in approved_terms:
        if not item or item == hook or item in picked:
            continue
        picked.append(item)
        if len(picked) >= 2:
            break
    while len(picked) < 2:
        picked.append(hook)
    return picked[0], picked[1]


def _variant_index(plan: dict[str, Any]) -> int:
    try:
        return int(plan.get("_demo_variant_index", 0))
    except Exception:
        return 0


def _artist_verse_lines(artist_id: str, mode: str, hook: str, a: str, b: str, c: str) -> list[str]:
    if artist_id == "deco27":
        return [
            f"{a}を隠すほど　{hook}だけが大きくなる",
            f"{b}に触れたあとで　言い訳だけが遅れてくる",
            f"{c}みたいに軽く笑えたら　こんな夜は要らないのに",
            "あなたを見るたび　ちゃんと壊れていく",
        ]
    if artist_id == "pinocchiop":
        return [
            f"{a}ばかり増えて　肝心なことは黙ったまま",
            f"{b}の向こうで　正解みたいな顔が並んでいる",
            f"{c}ひとつで片づくほど　単純なら楽なのに",
            "笑っているうちに　本音だけ置いていかれた",
        ]
    if artist_id == "kanaria":
        return [
            f"{a}を見せるたび　余裕みたいな顔だけ上手くなる",
            f"{b}の輪郭で　駆け引きだけが研ぎ澄まされる",
            f"{c}より先に　視線の熱が答えになっていく",
            f"静かなふりほど　深く噛みついている (Ah-hah)",
        ]
    if artist_id == "maretu":
        return [
            f"{a}の匂いだけ　綺麗に部屋へ残っています",
            f"{b}を選ぶたび　まともさだけが剥がれていくのです",
            f"{c}みたいな倫理で　今さら救われるはずもありません",
            "やさしい言葉ほど　最後に毒へ変わるのです",
        ]
    if artist_id == "kairiki_bear":
        return [
            f"{a}-{a}ー{a}を見つめるたび　{b}だけが歪んでいく",
            f"あー、{c}に触れたあとで　ボクだけが壊れていく",
            f"ダメ、ダメ、{a}なんて要らないよ",
            "呼吸をするたび　透明な傷が増えていく",
        ]
    if artist_id == "syudou":
        return [
            f"{a}ばかり並べて　肝心なことは笑ったまま",
            f"ハッハー！ {b}の向こうで　正解みたいな顔が並んでいる",
            f"{c}ひとつで救われるほど　世間は甘くないのに",
            "ビターな言葉で　甘い毒を塗りたくっていく",
        ]
    if artist_id == "neru":
        return [
            f"{a}をブチ壊して　{b}のガラクタで踊るんだ",
            f"最底辺の{c}で　息を止めて待っている",
            f"ねえ、{a}なんて全部ガラクタだろ？",
            "喉を掻き切るような　歪んだ音が鳴り響く",
        ]
    if artist_id == "iyowa":
        return [
            f"{a}が回るたび　昨日の夢がこぼれていく",
            f"{b}に触れた指先から　パステルカラーの熱が逃げる",
            f"{c}の底で　静かに壊れていくのを見ていた",
            "きゅうくらりんと　世界が反転していく",
        ]
    if mode == "dark_cute_breakdown":
        return [
            f"{a}をなぞるたび　やさしさまで傷になった",
            f"{b}で塞いでも　静かな痛みだけ残ってる",
            f"{c}みたいな顔で　平気だなんて言わないで",
            "かわいい嘘ほど　最後に深く刺さる",
        ]
    if mode == "direct_emotional_pop":
        return [
            f"{a}を隠すほど　{hook}だけが大きくなる",
            f"{b}に触れたあとで　言い訳だけが遅れてくる",
            f"{c}みたいに軽く笑えたら　こんな夜は要らないのに",
            "あなたを見るたび　ちゃんと壊れていく",
        ]
    return [
        f"{a}ばかり増えて　肝心なことは黙ったまま",
        f"{b}の奥で　正解みたいな顔が並んでいる",
        f"{c}ひとつで救われるほど　単純なら楽なのに",
        "笑っているうちに　本音だけ置いていかれた",
    ]


def _artist_pre_lines(artist_id: str, mode: str, hook: str, a: str, b: str) -> list[str]:
    if artist_id == "deco27":
        return [
            f"{a}を飲み込むたび　体温だけが先に走る",
            f"{b}じゃ足りないから　今さら引き返せない",
            f"ねえ　{hook}の名前で呼んで",
        ]
    if artist_id == "pinocchiop":
        return [
            f"{a}を数えるほど　冗談だけが上手くなる",
            f"{b}じゃ足りないって　ほんとはもう知っている",
            f"ねえ　{hook}の外で息をして",
        ]
    if artist_id == "kanaria":
        return [
            f"{a}を飾るほど　駆け引きだけが冴えていく",
            f"{b}で済むなら　こんな視線はいらない",
            f"ねえ　{hook}のままで試して",
        ]
    if artist_id == "maretu":
        return [
            f"{a}をほどくたびに　まともさだけが遠ざかります",
            f"{b}で眠れるほど　やさしくはできていません",
            f"ねえ　{hook}まで落としてください",
        ]
    if artist_id == "kairiki_bear":
        return [
            f"{a}を数えるほど　ボクだけがトんでいく",
            f"{b}じゃ足りないって　ボクはもう知っているんだ",
            f"ねえ　{hook}の外で息をして！",
        ]
    if artist_id == "syudou":
        return [
            f"{a}を数えるほど　冗談だけが上手くなる",
            f"{b}じゃ足りないって　お前ももう知っているんだろ？",
            "ハッハー！ そのツラを見てな",
        ]
    if artist_id == "neru":
        return [
            f"{a}を数えるほど　狂気だけが加速する",
            f"{b}じゃ足りないって　全部ぶち壊してしまえよ",
            f"ねえ　{hook}の外で叫んでみろよ",
        ]
    if artist_id == "iyowa":
        return [
            f"{a}を数えるほど　昨日の夢がこぼれていく",
            f"{b}じゃ足りないから　きゅうくらりんと沈んでいく",
            f"ねえ　{hook}の外で息をして",
        ]
    if mode == "dark_cute_breakdown":
        return [
            f"{a}をほどくたび　優しさまで濁っていく",
            f"{b}で眠れないなら　もうごまかせない",
            f"ねえ　{hook}まで連れていって",
        ]
    if mode == "direct_emotional_pop":
        return [
            f"{a}を飲み込むたび　体温だけが先に走る",
            f"{b}じゃ足りないから　今さら引き返せない",
            f"ねえ　{hook}の名前で呼んで",
        ]
    return [
        f"{a}を数えるほど　冗談だけが上手くなる",
        f"{b}じゃ足りないって　ほんとはもう知っている",
        f"ねえ　{hook}の外で息をして",
    ]


def _artist_chorus_lines(artist_id: str, mode: str, hook: str, a: str, b: str) -> list[str]:
    if artist_id == "deco27":
        return [
            f"{hook}　{hook}　もう誤魔化せない",
            f"{a}ごと抱きしめて　いまさら綺麗には戻れない",
            f"{b}より速く　この気持ちが先に叫んでる",
            "ねえ　痛いくらいでちょうどいい",
        ]
    if artist_id == "pinocchiop":
        return [
            f"{hook}　{hook}　笑っていられない",
            f"{a}まで本音にして　都合のいい顔を剥がしていく",
            f"{b}より先に　ため息だけが真実になる",
            "ねえ　まともなふりはもう要らない",
        ]
    if artist_id == "kanaria":
        return [
            f"{hook}　{hook}　まだ見抜けない",
            f"{a}まで武器にして　余裕の形を塗り替えていく",
            f"{b}より鋭く　視線だけが答えを奪っていく",
            "ねえ　その沈黙ごと奪いたい (Ah-hah)",
        ]
    if artist_id == "maretu":
        return [
            f"{hook}　{hook}　まだほどけません",
            f"{a}まで飲み込んで　まともな顔だけ剥がしていくのです",
            f"{b}より深く　やさしさだけが毒に変わるのです",
            "ねえ　綺麗なままじゃ終われません",
        ]
    if artist_id == "kairiki_bear":
        return [
            f"{hook}-{hook}ー{hook}　笑っていられない",
            f"{a}まで本音にして　ボクの顔を剥がしていく",
            f"{b}より先に　バグだけが真実になる！？",
            "ねえ　まともなふりはもうムリだよ",
        ]
    if artist_id == "syudou":
        return [
            f"{hook}　{hook}　くだらないね",
            f"{a}まで本音にして　安全な場所で石を投げる",
            f"{b}より先に　爆笑だけが真実になる",
            "ハッハー！ まともなふりはもう要らない",
        ]
    if artist_id == "neru":
        return [
            f"{hook}　{hook}　全部ブチ壊せ",
            f"{a}を武器にして　最底辺から這い上がっていく",
            f"{b}より強く　怒りだけが真実になる",
            "ねえ　まともなふりなんてクソ食らえだ",
        ]
    if artist_id == "iyowa":
        return [
            f"{hook}　{hook}　きゅうくらりん",
            f"{a}まで本音にして　くらくらした夢を剥がしていく",
            f"{b}より先に　浮遊感だけが真実になる",
            "ねえ　まともなふりはもう疲れたよ",
        ]
    if mode == "dark_cute_breakdown":
        return [
            f"{hook}　{hook}　まだほどけない",
            f"{a}まで飲み込んで　やさしさのふりを壊していく",
            f"{b}より深く　触れた傷だけ光ってる",
            "ねえ　綺麗なままじゃ終われない",
        ]
    if mode == "direct_emotional_pop":
        return [
            f"{hook}　{hook}　もう誤魔化せない",
            f"{a}ごと抱きしめて　いまさら綺麗には戻れない",
            f"{b}より速く　この気持ちが先に叫んでる",
            "ねえ　痛いくらいでちょうどいい",
        ]
    return [
        f"{hook}　{hook}　笑っていられない",
        f"{a}まで本音にして　都合のいい顔を剥がしていく",
        f"{b}より先に　ため息だけが真実になる",
        "ねえ　まともなふりはもう要らない",
    ]


def _artist_bridge_lines(artist_id: str, mode: str, hook: str, a: str, b: str) -> list[str]:
    if artist_id == "deco27":
        return [
            f"{a}のせいじゃないって　言えたら楽だった",
            f"{b}の向こうで　まだあなたを待っている",
            f"だから　{hook}だけ置いていかないで",
        ]
    if artist_id == "pinocchiop":
        return [
            f"{a}に合わせた顔で　ここまで生きてしまった",
            f"{b}の外側に　本音がまだ残っている",
            f"せめて　{hook}だけは借りものにしない",
        ]
    if artist_id == "kanaria":
        return [
            f"{a}を纏ったままじゃ　ほんとの顔まで鈍っていく",
            f"{b}の裏側で　まだ手放したくない熱がある",
            f"だから　{hook}だけは飾りにしない",
        ]
    if artist_id == "maretu":
        return [
            f"{a}を許したふりで　ここまで沈んでしまいました",
            f"{b}の底にも　まだやわらかい傷が残っているのです",
            f"それでも　{hook}だけは捨てられません",
        ]
    if artist_id == "kairiki_bear":
        return [
            f"{a}に合わせたボクで　ここまで生きてしまった",
            f"{b}の外側に　バグがまだ残っているんだ",
            f"せめて　{hook}だけは借りものにしない",
        ]
    if artist_id == "syudou":
        return [
            f"{a}に合わせた顔で　ここまで生きてしまった",
            f"{b}の外側に　本音がまだ残っているんだろ？",
            "ハッハー！ その顔を見てな",
        ]
    if artist_id == "neru":
        return [
            f"{a}に合わせた顔で　ここまで死んだフリをしていた",
            f"{b}の外側に　怒りがまだ燃えているんだ",
            f"せめて　{hook}だけはガラクタにしない",
        ]
    if artist_id == "iyowa":
        return [
            f"{a}を隠すほど　ほんとはもっと痛かった",
            f"{b}の底まで　やさしさが届かない",
            f"それでも　{hook}だけはきゅうくらりんと沈まない",
        ]
    if mode == "dark_cute_breakdown":
        return [
            f"{a}を隠すほど　ほんとはもっと痛かった",
            f"{b}の底まで　やさしさが届かない",
            f"それでも　{hook}だけは嘘にしない",
        ]
    if mode == "direct_emotional_pop":
        return [
            f"{a}のせいじゃないって　言えたら楽だった",
            f"{b}の向こうで　まだあなたを待っている",
            f"だから　{hook}だけ置いていかないで",
        ]
    return [
        f"{a}に合わせた顔で　ここまで生きてしまった",
        f"{b}の外側に　本音がまだ残っている",
        f"せめて　{hook}だけは借りものにしない",
    ]


def _artist_final_lines(artist_id: str, mode: str, hook: str, a: str, b: str) -> list[str]:
    if artist_id == "deco27":
        return [
            f"{hook}　{hook}　もう逃がさない",
            f"{a}も弱さも　この声でまとめて抱えていく",
            f"{b}より熱く　ここからちゃんと壊れてみせる",
            "ここから　もう誤魔化さない",
            f"{hook}　{hook}　最後まで離さない",
        ]
    if artist_id == "pinocchiop":
        return [
            f"{hook}　{hook}　まだ終われない",
            f"{a}も建前も　このまま笑って剥がしていく",
            f"{b}よりも強く　ここからちゃんと暴いてみせる",
            "ここから　もう黙っていない",
            f"{hook}　{hook}　最後までごまかさない",
        ]
    if artist_id == "kanaria":
        return [
            f"{hook}　{hook}　まだ見逃さない",
            f"{a}も沈黙も　このまま優雅に奪いきる",
            f"{b}より鋭く　ここから支配してみせる",
            "ここから　もう目を逸らさない",
            f"{hook}　{hook}　最後まで譲らない",
        ]
    if artist_id == "maretu":
        return [
            f"{hook}　{hook}　まだ壊れません",
            f"{a}も倫理も　笑って踏み外していくのです",
            f"{b}より深く　ここからちゃんと濁ってみせます",
            "ここから　もう綺麗ではいられません",
            f"{hook}　{hook}　最後までほどけません",
        ]
    if artist_id == "kairiki_bear":
        return [
            f"{hook}-{hook}ー{hook}　まだ終われない",
            f"{a}もバグも　このまま笑って壊していくよ",
            f"{b}よりも強く　ここからちゃんと暴いてみせる！？",
            "ここから　もう黙っていない",
            f"{hook}　{hook}　最後までごまかさないナイナイ",
        ]
    if artist_id == "syudou":
        return [
            f"{hook}　{hook}　まだ終われない",
            f"{a}も建前も　笑って剥がしていく",
            f"{b}よりも強く　ここから暴いてみせる",
            "ハッハー！ もう黙っていないぜ",
            f"{hook}　{hook}　最後までごまかさない",
        ]
    if artist_id == "neru":
        return [
            f"{hook}　{hook}　狂い咲け",
            f"{a}も世界も　このままぶち壊していく",
            f"{b}よりも強く　ここから叫んでみせる",
            "ここから　もう黙っていない",
            f"{hook}　{hook}　最後までぶち壊してしまえ",
        ]
    if artist_id == "iyowa":
        return [
            f"{hook}　{hook}　まだ消えない",
            f"{a}も涙も　きれいなままでは返さない",
            f"{b}より深く　ここからきゅうくらりん",
            "ここから　もう綺麗じゃいられないの",
            f"{hook}　{hook}　最後まで壊れない",
        ]
    if mode == "dark_cute_breakdown":
        return [
            f"{hook}　{hook}　まだ消えない",
            f"{a}も涙も　きれいなままでは返さない",
            f"{b}より深く　ここからちゃんと落ちていく",
            "ここから　もう綺麗じゃいられない",
            f"{hook}　{hook}　最後まで壊れない",
        ]
    if mode == "direct_emotional_pop":
        return [
            f"{hook}　{hook}　もう逃がさない",
            f"{a}も弱さも　この声でまとめて抱えていく",
            f"{b}より熱く　ここからちゃんと壊れてみせる",
            "ここから　もう誤魔化さない",
            f"{hook}　{hook}　最後まで離さない",
        ]
    return [
        f"{hook}　{hook}　まだ終われない",
        f"{a}も建前も　このまま笑って剥がしていく",
        f"{b}より強く　ここからちゃんと暴いてみせる",
        "ここから　もう黙っていない",
        f"{hook}　{hook}　最後までごまかさない",
    ]


def _artist_outro_lines(artist_id: str, mode: str, hook: str, a: str) -> list[str]:
    if artist_id == "pinocchiop":
        return [
            f"{a}の残響で　拍手だけが少し遅れて鳴った",
            f"{hook}の正体を　まだ誰も言い当てられない",
        ]
    if artist_id == "deco27":
        return [
            f"{a}の余熱で　まだ胸の奥がうるさい",
            f"{hook}を見失わずに　夜明けまで立っている",
        ]
    if artist_id == "kanaria":
        return [
            f"{a}の残響で　支配の熱だけが残った",
            f"{hook}の輪郭を　まだ誰も奪えない (Ah-hah)",
        ]
    if artist_id == "maretu":
        return [
            f"{a}の残響で　やさしさだけが濁ってしまいました",
            f"{hook}の倫理を　まだ誰も救えません",
        ]
    if artist_id == "kairiki_bear":
        return [
            f"{a}の残響で　バグだけが遅れて鳴った",
            f"{hook}の正体を　ボクはもう言い当てられないナイ",
        ]
    if artist_id == "syudou":
        return [
            f"{a}の残響で　爆笑だけが少し遅れて鳴った",
            "ハッハー！ くだらない正体だったね",
        ]
    if mode == "ironic_meta":
        return [
            f"{a}の残響で　拍手だけが少し遅れて鳴った",
            f"{hook}の正体を　まだ誰も言い当てられない",
        ]
    return [
        f"{a}の余熱で　まだ胸の奥がうるさい",
        f"{hook}を見失わずに　夜明けまで立っている",
    ]


def _rotate(lines: list[str], offset: int) -> list[str]:
    if not lines:
        return lines
    shift = offset % len(lines)
    return lines[shift:] + lines[:shift]


def _boost_final_release(lines: list[str], hook: str, a: str, b: str, artist_id: str) -> list[str]:
    release_a, release_b = _release_terms(artist_id, hook, a, b)
    release_templates = {
        "kanaria": [
            f"{hook} {hook} ここからもう逸らさない",
            f"{release_a}も{release_b}も　このまま奪いきる",
        ],
        "maretu": [
            f"{hook} {hook} ここからまだ終われない",
            f"{release_a}も{release_b}も　最後まで手放しません",
        ],
        "neru": [
            f"{hook} {hook} 壊れたままで終わらせない",
            f"{release_a}も{release_b}も　最後まで黙らない",
        ],
        "iyowa": [
            f"{hook} {hook} ここからまだほどけない",
            f"{release_a}も{release_b}も　最後まで見失わない",
        ],
    }
    additions = release_templates.get(
        artist_id,
        [
            f"{hook} {hook} ここからもう隠さない",
            f"{release_a}も{release_b}も抱えたまま 最後まで手放さない",
        ],
    )
    base = list(lines[:-2]) if len(lines) >= 2 else list(lines)
    return base + additions


def _surface_rewrite_line(line: str, artist_id: str = "default", rng: random.Random | None = None) -> str:
    rng = rng or random.Random(0)
    text = line.strip()
    if not text or text.startswith("#") or text.startswith("["):
        return line

    # 1. Generic Particle & Phrase Cleanup
    leak_replacements = {
        "Sets the mood and initial conflict.": "",
        "dizzy": "",
        "タイトルを再固定するも": "",
        "タイトルを確定させるも": "",
        "タイトルを再固定する": "",
        "タイトルを確定させる": "",
    }
    for src, dst in leak_replacements.items():
        text = text.replace(src, dst)
    text = re.sub(r"^[A-Za-z][A-Za-z,\-!.' ]+,\s*", "", text)
    text = re.sub(r"\((?:Ah-hah|Yeah|Check it|Kira-kira|Gishi-gishi|Baki-baki|Click|Stardust|System Error|Ra-re-ri-ro|Ta-ta-ta-ta)\)", "", text)
    text = re.sub(r"[A-Za-z][A-Za-z0-9,\-!.' ]{8,}", "", text)
    text = re.sub(r"\s{2,}", " ", text).strip()

    replacements = {
        "を隠すほど": "が隠れるほど",
        "に触れたあとで": "に触れたあと",
        "を飲み込むたび": "を飲み込むたびに",
        "を数えるほど": "数えるほど",
        "をほどくたび": "をほどくたびに",
        "たびにに": "たびに",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)

    text = re.sub(r"(.+?)を隠すほど", r"\1が隠れるほど", text)
    text = re.sub(r"(.+?)を飲み込むたび", r"\1を飲み込むたびに", text)
    text = re.sub(r"(.+?)をほどくたび", r"\1をほどくたびに", text)
    text = re.sub(r"(.+?)みたいに軽く笑えたら", r"\1みたいに軽く笑えたなら", text)

    # 2. Artist-Specific Shaping
    if artist_id == "maretu":
        # 1. Polite Cruelty (Aggressive Keigo Conversion)
        text = text.replace("まだ", "__MADA__")
        text = re.sub(r"だ(?=[\s！？?」\)]|$)", "です", text)
        text = text.replace("__MADA__", "まだ")
        if text.endswith("まだ"):
            text += "です"
        text = text.replace("だよ", "ですよ").replace("った", "ってしまいました")
        text = text.replace("ある", "あります").replace("いる", "います").replace("るね", "りますね")
        
        for v_src, v_dst in [("す", "します"), ("る", "ます"), ("う", "います"), ("く", "きます")]:
             for target in ["消", "殺", "壊", "嫌", "嗤", "狂", "泣", "笑", "痛"]:
                 text = text.replace(f"{target}{v_src}", f"{target}{v_dst}")
        
        # 2. Rhythmic Doubling (Maretu's signature stutter)
        for term in ["傷", "嘘", "ゴミ", "エラー"]:
            if term in text and "　" not in text:
                text = text.replace(term, f"{term}　{term}")
        
        # 3. Random Glitch Stutter
        if len(text) > 4 and rng.random() < 0.3:
            text = f"{text[0]}　{text}"
        
        # 4. Katakana Shift for Digital Aesthetic
        katakana_map = {
            "君": "キミ", "ぼく": "ボク", "あなた": "アナタ",
            "愛": "アイ", "死": "シ", "心": "ココロ", "笑": "ワライ", "嘘": "ウソ",
        }
        for k_src, k_dst in katakana_map.items():
            if k_src in text and rng.random() < 0.4:
                text = text.replace(k_src, k_dst)
        
        # 5. Clinical Kango Substitutions
        kango_map = {"笑って": "嘲笑", "泣いて": "落涙", "壊して": "破壊", "殺して": "抹殺"}
        for s, d in kango_map.items():
            if s in text:
                text = text.replace(s, d)

    elif artist_id == "deco27":
        # 1. Bratty Conversational Particles
        if rng.random() < 0.4:
            text = re.sub(r"だ$", "じゃん", text)
            text = re.sub(r"な$", "だろ", text)
        
        # 2. Obsessive 3x repetition for Hook Intensity
        if "[" in text or "#" in text: # Usually titles or headers carry the core
             pass 
        elif len(text) < 10 and rng.random() < 0.2:
             tokens = text.split()
             if tokens:
                 text = f"{tokens[0]}　{tokens[0]}　{tokens[0]}"
        
        # 3. Iconic Ad-libs
        if rng.random() < 0.1:
            text += " (愛、愛、愛)"

    elif artist_id == "kanaria":
        # 1. Arrogant/Minimalist Ad-libs
        if rng.random() < 0.18:
            text += "　ほら"
        elif rng.random() < 0.06:
            text = "ねえ、" + text
        
        # 2. Katakana Shift (KING/QUEEN/EYE vibes)
        for k_src, k_dst in [("王", "KING"), ("女王", "QUEEN"), ("目", "EYE")]:
            text = text.replace(k_src, k_dst)

    elif artist_id == "kairiki_bear":
        # 1. Rhythmic Doubling with Dashes (Signature Stutter)
        for term in ["ベノム", "ダーリン", "ボク", "キミ", "壊", "痛"]:
            if term in text and "-" not in text:
                text = text.replace(term, f"{term}-{term}ー{term}")
        
        # 2. Negative Repetition (nai-nai)
        if "ない" in text and rng.random() < 0.3:
            text = text.replace("ない", "ナイナイ")

    elif artist_id == "iyowa":
        # 1. "Kyukurarin" floaty particles
        if rng.random() < 0.2:
            text = "きゅうくらりんと、" + text
        
        # 2. Soft Katakana Shift
        if "ゆめ" in text: text = text.replace("ゆめ", "ユメ")
        if "ゆび" in text: text = text.replace("ゆび", "ユビ")

    elif artist_id == "hachi":
        # 1. Rhythmic Grit (Dash-stutters for action verbs)
        for v in ["壊す", "叫ぶ", "踊る", "回る", "叩く"]:
            if v in text and rng.random() < 0.4:
                text = text.replace(v, f"{v[0]}-{v[0]}-{v}")
        
        # 2. Patchwork Repetition (Only for specific conceptual anchors)
        anchors = ["愛", "毒", "夢", "錆", "心", "嘘"]
        if any(a in text for a in anchors) and len(text) < 10 and rng.random() < 0.3:
             text = f"{text}　{text}　{text}"
        
        # 3. Gritty Directness Particles (Lowered frequency to avoid robotic feel)
        if rng.random() < 0.05:
            text += " (〜よ)"
        elif rng.random() < 0.03:
            text += " (〜さ)"
        elif rng.random() < 0.04:
            text += " (縫い目)" # Patchwork/Stitch marker

        # 4. Nonsense Rhythmic Chants (V5: Removed hardcoded Panda)
        if rng.random() < 0.1:
            text += " (Ra-re-ri-ro)" # Abstract phonetic skip
        elif rng.random() < 0.05:
            text += " (Ta-ta-ta-ta)" # Percussive anchor
        
        # 5. Grotesque Katakana Shift
        for k_src, k_dst in [("心", "ココロ"), ("愛", "アイ"), ("壊", "コワス"), ("錆", "サビ")]:
            text = text.replace(k_src, k_dst)

    elif artist_id == "harumakigohan":
        # 1. "Sotto" floaty particles
        if rng.random() < 0.2:
            text = "そっと、" + text
        
        # 2. Melty Katakana Shift
        for k_src, k_dst in [("溶ける", "トケル"), ("星", "ホシ"), ("夢", "ユメ"), ("青", "アオ")]:
            text = text.replace(k_src, k_dst)
            
        # 3. Dreamy Ad-libs
        if rng.random() < 0.2:
            text += " (Stardust)"

    elif artist_id == "cosmo":
        # 1. High-speed Tech Stutter
        if rng.random() < 0.3:
            text = "B-B-BPM, " + text
        
        # 2. Clinical/Digital Ad-libs
        if rng.random() < 0.2:
            text += " (System Error)"

    elif artist_id == "giga":
        # 1. Vocal Chop Stutter
        if rng.random() < 0.2:
            text = "Ready-dy-dy, " + text
        elif rng.random() < 0.1:
            text = "Ga-ga-giga, " + text
        
        # 2. Trap Ad-libs
        if rng.random() < 0.2:
            text += " (Yeah)"
        elif rng.random() < 0.1:
            text += " (Check it)"

    elif artist_id == "ezfg":
        # 1. Binary Lock Insertions
        if rng.random() < 0.2:
            text = "1 " + text
        elif rng.random() < 0.1:
            text = "0 " + text
        
        # 2. Mechanical Click
        if text.endswith("。") or text.endswith("！"):
            text = text[:-1] + " (Click)"
        elif rng.random() < 0.2:
            text += " (Click)"

    elif artist_id == "40mp":
        # 1. Hesitant Breath-Marks
        if rng.random() < 0.15:
            text = text.replace("、", "...")
        
        # 2. Gentle Conversation
        if rng.random() < 0.2:
            text = "ねぇ、" + text

    elif artist_id == "atols":
        # 1. Fragmented Surreal ad-libs
        if rng.random() < 0.15:
            text += " (Macaron)"
        elif rng.random() < 0.1:
            text += " (Glitch)"
            
        # 2. Viscous Katakana Shift
        if "とける" in text: text = text.replace("とける", "トケル")

    elif artist_id == "chinozo":
        # 1. Self-Declaration Slogans
        if rng.random() < 0.2:
            text = "さあ、" + text
        
        # 2. Action Ad-libs
        if rng.random() < 0.15:
            text += " (Goodbye)"

    elif artist_id == "balloon":
        # 1. Quiet Hesitation
        if rng.random() < 0.2:
            text = "... " + text
        
        # 2. Melodic Softness
        if rng.random() < 0.1:
            text += " (Sotto)"

    elif artist_id == "honeyworks":
        # 1. Youthful Ad-libs
        if rng.random() < 0.2:
            text += " (Yeah!)"
        elif rng.random() < 0.1:
            text += " (Kira-kira)"
        
        # 2. Piano-Pop Sincerity
        if "ねぇ" not in text and rng.random() < 0.15:
            text = "ねぇ、" + text

    elif artist_id == "hiragi_kirai":
        # 1. Aggressive Rhythmic Stabs
        if rng.random() < 0.25:
            text += " (Gishi-gishi)"
        elif rng.random() < 0.15:
            text += " (Baki-baki)"
        
        # 2. Stuttered Negative Verbs
        if "ない" in text and rng.random() < 0.3:
            text = text.replace("ない", "な-ない")
    return text


def _surface_rewrite(lines: list[str], artist_id: str = "default", rng: random.Random | None = None) -> list[str]:
    rng = rng or random.Random(0)
    return [_surface_rewrite_line(line, artist_id, rng) for line in lines]


def _generative_section_lines(
    section: str,
    hook: str,
    a: str,
    b: str,
    c: str,
    mode: str,
) -> list[str]:
    if section == "intro":
        return [
            f"{a}を数えるほど　冗談だけが上手くなる",
            f"{b}じゃ足りないって　ほんとはもう知っている",
            f"ねえ　{hook}の外で息をして",
        ]
    if section in {"verse_1", "verse_2"}:
        return [
            f"{a}ばかり増えて　肝心なことは黙ったまま",
            f"{b}の奥で　正解みたいな顔가 並んでいる",
            f"{c}ひとつで救われるほど　単純なら楽なのに",
            "笑っているうちに　本音だけ置いていかれた",
        ]
    if section in {"pre_chorus", "pre_chorus_2"}:
        return [
            f"{a}を数えるほど　冗談だけ가 上手くなる",
            f"{b}じゃ足りないって　ほんとはもう知っている",
            f"ねえ　{hook}の外で息をして",
        ]
    if section == "bridge":
        return [
            f"{a}に合わせた顔で　ここまで生きてしまった",
            f"{b}の外側に　本音がまだ残っている",
            f"せめて　{hook}だけは借りものにしない",
        ]
    if section == "chorus_final" or section == "chorus":
        return [
            f"{hook}　{hook}　笑っていられない",
            f"{a}まで本音にして　都合のいい顔を剥がしていく",
            f"{b}より先に　ため息だけが真実になる",
            "ねえ　まともなふりはもう要らない",
        ]
    if section == "outro":
        return [
            f"{a}の余熱で　まだ胸の奥がうるさい",
            f"{hook}を見失わずに　夜明けまで立っている",
        ]
    return []


def render_demo_candidate(
    plan: dict[str, Any],
    *,
    variant_index: int,
    scaffold_mode: bool = False,
) -> dict[str, Any]:
    rng = random.Random(int(hashlib.md5(f"{plan['track_id']}:{variant_index}:demo".encode("utf-8")).hexdigest()[:8], 16))
    mode = str(plan.get("primary_mode", "")).strip()
    artist_id = str(plan.get("artist_id", "")).strip()
    hook = str(plan.get("hook_blueprint", {}).get("core_text", "")).strip()
    terms = _seed_terms(plan, mode)
    compact_terms = [
        term
        for term in terms
        if contains_japanese(term)
        and not contains_bad_script(term)
        and " " not in term
        and "　" not in term
        and len(term) <= 8
    ]
    if not contains_japanese(hook) or contains_bad_script(hook):
        hook = compact_terms[0] if compact_terms else _artist_imagery_defaults(artist_id, mode)[0]
    title = _demo_title(plan, rng, hook, terms)
    variant = variant_index

    lines = [f"# {title}", ""]
    for idx, card in enumerate(plan.get("section_cards", [])):
        section = str(card.get("section", "")).strip()
        if not section:
            continue
        section_terms = _section_terms(
            card,
            terms,
            artist_id=artist_id,
            mode=mode,
            hook=hook,
        )
        if section in {"intro", "verse_1", "verse_2", "pre_chorus", "pre_chorus_2", "bridge"} and len(section_terms) > 1 and section_terms[0] == hook:
            section_terms = section_terms[1:] + section_terms[:1]
        # Use section index (idx) to rotate the primary motif starting point for variety
        a_idx = idx % len(section_terms) if section_terms else 0
        b_idx = (idx + 1) % len(section_terms) if section_terms else 0
        c_idx = (idx + 2) % len(section_terms) if section_terms else 0

        a = section_terms[a_idx] if section_terms else hook
        b = section_terms[b_idx] if section_terms else a
        c = section_terms[c_idx] if section_terms else b
        lines.append(f"[{section}]")
        if scaffold_mode:
            if section == "intro":
                section_lines = _artist_pre_lines(artist_id, mode, hook, a, b)
            elif section in {"verse_1", "verse_2"}:
                section_lines = _artist_verse_lines(artist_id, mode, hook, a, b, c)
            elif section in {"pre_chorus", "pre_chorus_2"}:
                section_lines = _artist_pre_lines(artist_id, mode, hook, a, b)
            elif section == "bridge":
                section_lines = _artist_bridge_lines(artist_id, mode, hook, a, b)
            elif section == "chorus_final":
                section_lines = _artist_final_lines(artist_id, mode, hook, a, b)
            elif section == "outro":
                section_lines = _artist_outro_lines(artist_id, mode, hook, a)
            else:
                section_lines = _artist_chorus_lines(artist_id, mode, hook, a, b)
        else:
            section_lines = _generative_section_lines(
                section=section,
                hook=hook,
                a=a,
                b=b,
                c=c,
                mode=mode,
            )

        section_lines = _rotate(section_lines, variant)
        if section == "chorus_final":
            section_lines = _boost_final_release(section_lines, hook, a, b, artist_id)
        line_target = int(card.get("line_target", len(section_lines)) or len(section_lines))
        lines.extend(_surface_rewrite(section_lines[:line_target], (artist_id if scaffold_mode else "default"), rng))
        lines.append("")

    markdown_text = "\n".join(lines).strip() + "\n"
    return {
        "candidate_id": f"{plan['track_id']}-candidate-{variant_index + 1}",
        "variant_index": variant_index + 1,
        "title": title,
        "markdown": markdown_text,
    }
