from __future__ import annotations

import hashlib
import json
import random
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .alexandria_library import AlexandriaLibrary
from .lyric_utils import unique_preserve_order
from .mastery_blueprint import MasteryConstraints, get_universal_blueprint, validate_against_blueprint
from .phonetic_engine import apply_stutter_glitch


SECTION_HEADER_PATTERN = re.compile(r"^\[(.+?)\]$")


THEME_BANK = {
    "body": ["声", "手のひら", "心拍", "喉", "まぶた", "体温"],
    "noise": ["ノイズ", "雑音", "残響", "軋み", "ざわめき", "ハウリング"],
    "time": ["秒針", "夜明け", "明日", "昨日", "真夜中", "未来"],
    "defiance": ["逆風", "牙", "反抗", "抵抗線", "火花", "折れない息"],
    "light": ["逆光", "光", "閃き", "残照", "白線", "光の粒"],
    "city": ["街灯", "交差点", "高架下", "ネオン", "路地", "改札"],
    "fracture": ["ひび", "亀裂", "割れ目", "欠片", "継ぎ目", "断面"],
    "vulnerability": ["弱さ", "素肌", "本音", "傷あと", "震え", "ためらい"],
    "motion": ["加速", "助走", "足音", "揺れ", "疾走", "拍動"],
    "uplift": ["跳躍", "上昇気流", "浮力", "追い風", "反射光", "光跡"],
    "weather": ["雨粒", "風向き", "雷鳴", "霧", "湿度", "気圧"],
    "night": ["夜", "深夜", "藍色", "月明かり", "夜更け", "眠れない空"],
    "fire": ["火花", "炎", "灼熱", "燃えさし", "発火点", "余熱"],
    "darkness": ["暗がり", "影", "黒い水面", "盲点", "深淵", "無灯火"],
    "tension": ["緊張", "張りつめた糸", "警報", "息詰まり", "静電気", "高鳴り"],
}

THEME_SCENES = {
    "body": ["胸の内側", "握りしめた手のひら", "喉の奥", "まぶたの裏"],
    "noise": ["駅前のざわめき", "遠くで軋むスピーカー", "夜に残るハウリング"],
    "time": ["夜更けの改札", "秒針の鳴る部屋", "朝の手前"],
    "defiance": ["逆風の交差点", "引き返せない坂道", "歯を食いしばる高架下"],
    "light": ["逆光のホーム", "白線のきわ", "残照の窓辺"],
    "city": ["ネオンの路地", "高架下の湿った影", "信号待ちの横断歩道"],
    "fracture": ["ひび割れたガラス越し", "継ぎ目だらけの夜道", "欠片の散る足元"],
    "vulnerability": ["誰もいない踊り場", "触れたらほどけそうな距離", "眠れないままの部屋"],
    "motion": ["駆け出す寸前のホーム", "走り出した風の中", "足音だけが先に行く道"],
    "uplift": ["追い風の吹く非常階段", "浮力だけが残る夜空", "明るくなりきらない空"],
    "weather": ["雨上がりの歩道橋", "風向きの変わる角", "霧のかかった信号"],
    "night": ["真夜中の交差点", "月明かりの階段", "深夜の窓際"],
    "fire": ["火花の散る暗がり", "燃えさしみたいな息", "余熱の残る掌"],
    "darkness": ["灯りの届かない水面", "暗がりの端", "影だけが伸びる壁際"],
    "tension": ["警報みたいに静かな廊下", "張りつめた空気の隙間", "息をひそめる改札前"],
}

GENERIC_SCENES = [
    "真夜中の交差点",
    "朝の手前",
    "信号待ちの横断歩道",
    "誰もいない踊り場",
]

EMOTION_BANK = {
    "uplift": [
        "少しだけ上を向ける気がした",
        "まだ行けると息が言った",
        "追い風を信じる余白が残っていた",
        "落ちきらない光を拾っていた",
    ],
    "vulnerability": [
        "うまく言えないまま立ち尽くした",
        "触れたら壊れそうで笑えなかった",
        "隠しきれない本音が揺れていた",
        "弱さだけが先に名前を持った",
    ],
    "motion": [
        "止まれないまま考えていた",
        "足音だけが答えを急がせた",
        "走りながらようやく気づいた",
        "助走みたいに沈黙が伸びていく",
    ],
    "defiance": [
        "ここで引けないとやっと思えた",
        "折れない息だけは手放せない",
        "黙ったまま終われないと知った",
        "逆風ごと抱えて進むしかなかった",
    ],
    "darkness": [
        "灯りのない場所でも目を閉じなかった",
        "影の深さまで抱えていた",
        "暗がりの底でまだ息をしていた",
        "見えないままでも消えたくなかった",
    ],
    "tension": [
        "心拍だけが先に尖っていく",
        "息をひそめたまま朝を待った",
        "言い訳より先に鼓動が走った",
        "張りつめた糸みたいに夜が鳴る",
    ],
}

MODE_BANK = {
    "intimate_confessional": {
        "voices": ["私", "僕"],
        "addresses": ["君", "あなた", "名前のない誰か"],
        "confessions": [
            "まだほどけない",
            "ほんとは怖い",
            "うまく言えない",
            "引き返せない",
        ],
    },
    "night_drive": {
        "voices": ["私", "僕"],
        "addresses": ["君", "隣の影", "バックミラーの向こう"],
        "confessions": [
            "もうブレーキは遅い",
            "夜の速度に負けたくない",
            "振り切れないまま走っている",
            "もう眠れない",
        ],
    },
}

TITLE_ENDINGS = {
    "defiant": ["の前夜", "の抵抗線", "の残響", "の火花"],
    "uplift": ["の向こう側", "の跳躍", "の光跡", "の余熱"],
    "night": ["の輪郭", "の夜明け", "の秒針", "の余白"],
    "vulnerable": ["の温度", "の本音", "の片鱗", "の気配"],
}

REVERSAL_PREFIXES = ["それでも", "だけど", "だからこそ", "なのに"]
FINAL_RELEASES = [
    "終われない夜ごと抱いて それでも明日へ踏み出す",
    "言い訳より先に 私たちは次の光へ触れていく",
    "消えない残響ごと ここから先へ運んでいく",
    "ほどけない弱さまで 未来の方へ連れていく",
]
BRIDGE_TURNS = [
    "逃げ道みたいな光なら いらないとやっと言えた",
    "壊れるためじゃなく 変わるために震えていたんだ",
    "隠していた本音ほど いちばん大きく鳴っていた",
    "失くしたと思った熱は まだ喉の奥で生きていた",
]

BODY_SURFACES = ["胸の内側", "喉の奥", "まぶたの裏", "指先", "背中の近く"]


@dataclass
class LyricDraftRequest:
    source_jsonl: Path
    track_id: str | None = None
    output_path: Path | None = None
    candidate_count: int = 6


@dataclass
class GenerationContext:
    track_id: str
    theme_axes: list[str]
    dominant_emotions: list[str]
    primary_mode: str
    arc_label: str
    hook_density: str
    short_line_ratio: float
    voice: str
    address: str
    confession: str
    section_goals: dict[str, str]
    theme_words: dict[str, list[str]]
    imagery_anchors: list[str]
    scene_primary: str
    scene_secondary: str
    time_boundary: str
    body_surface: str
    emotion_line: str
    bridge_turn: str
    title: str
    hook_line: str
    hook_echo: str
    hook_release: str
    final_release: str
    is_final: bool = False
    mastery_constraints: MasteryConstraints | None = None
    glitch_mode: str = "none" # "explosive", "melodic", "none"
    glitch_intensity: float = 0.0


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def target_payload(record: dict[str, Any]) -> dict[str, Any]:
    return record.get("reference_target") or record.get("target", {})


def input_payload(record: dict[str, Any]) -> dict[str, Any]:
    return record.get("input_context", {})


def track_evidence(record: dict[str, Any]) -> dict[str, Any]:
    return input_payload(record).get("track_evidence", {})


def style_constraints(record: dict[str, Any]) -> dict[str, Any]:
    return target_payload(record).get("style_constraints", {})


def section_plan(record: dict[str, Any]) -> list[str]:
    target = target_payload(record)
    recommended = [item.get("section") for item in target.get("recommended_structure", []) if item.get("section")]
    if recommended:
        return recommended
    defaults = input_payload(record).get("artist_context", {}).get("structural_defaults", [])
    return [section for section in defaults if section]


def section_goals(record: dict[str, Any]) -> dict[str, str]:
    goals: dict[str, str] = {}
    for item in target_payload(record).get("recommended_structure", []):
        section = str(item.get("section", "")).strip()
        goal = str(item.get("goal", "")).strip()
        if section and goal:
            goals[section] = goal
    return goals


def theme_axes_for_record(record: dict[str, Any]) -> list[str]:
    target = target_payload(record)
    evidence = track_evidence(record)
    axes = []
    axes.extend(str(axis) for axis in target.get("theme_axes", []) if axis)
    axes.extend(str(axis) for axis in evidence.get("dominant_imagery_tags", []) if axis)
    return unique_preserve_order(axes)


def dominant_emotions_for_record(record: dict[str, Any]) -> list[str]:
    evidence = track_evidence(record)
    emotions = [str(item) for item in evidence.get("dominant_emotions", []) if item]
    return unique_preserve_order(emotions)


def hook_density_for_record(record: dict[str, Any]) -> str:
    return str(target_payload(record).get("hook_plan", {}).get("hook_density", "medium"))


def arc_label_for_record(record: dict[str, Any]) -> str:
    return str(track_evidence(record).get("overall_arc_label", "build_and_drop"))


def style_imagery_bank(record: dict[str, Any]) -> list[str]:
    normalization = {
        "手": "手のひら",
        "目": "まなざし",
        "飛": "飛翔",
    }
    output: list[str] = []
    for raw in style_constraints(record).get("imagery_bank", []):
        word = str(raw).strip()
        if not word:
            continue
        output.append(normalization.get(word, word))
    return unique_preserve_order(output)


def imagery_candidates_for_record(record: dict[str, Any]) -> list[str]:
    words: list[str] = []
    for axis in theme_axes_for_record(record):
        words.extend(THEME_BANK.get(axis, []))
    words.extend(style_imagery_bank(record))
    return unique_preserve_order(words)


def rng_for_record(record: dict[str, Any], *, salt: int = 0) -> random.Random:
    stable_id = record.get("record_id") or record.get("eval_id") or record.get("track_id") or "draft"
    raw = f"{stable_id}:{salt}"
    seed = int(hashlib.md5(raw.encode("utf-8")).hexdigest()[:8], 16)
    return random.Random(seed)


def choose_record(records: list[dict[str, Any]], track_id: str | None) -> dict[str, Any]:
    if track_id is None:
        return records[0]
    target_id = str(track_id)
    for record in records:
        # Check all possible ID keys
        rid = record.get("track_id") or record.get("id") or record.get("record_id")
        if rid is not None and str(rid) == target_id:
            return record
    raise ValueError(f"track_id '{track_id}' was not found in {len(records)} records.")


def canonical_section_name(section: str) -> str:
    if section.startswith("chorus") and section != "chorus_final":
        return "chorus"
    if section.startswith("pre_chorus"):
        return "pre_chorus"
    if section.startswith("verse_2"):
        return "verse_2"
    if section.startswith("verse"):
        return "verse_1"
    if section.startswith("bridge"):
        return "bridge"
    if section.startswith("outro"):
        return "outro"
    if section.startswith("intro"):
        return "intro"
    return section


def first_available_word(context: GenerationContext, rng: random.Random, *preferred_axes: str) -> str:
    for axis in preferred_axes:
        pool = context.theme_words.get(axis, [])
        if pool:
            return rng.choice(pool)
    fallback_pool = context.imagery_anchors[:]
    if fallback_pool:
        return rng.choice(fallback_pool)
    for pool in context.theme_words.values():
        if pool:
            return rng.choice(pool)
    return "夜"


def time_boundary_for_axes(theme_axes: list[str], rng: random.Random) -> str:
    if "night" in theme_axes:
        return rng.choice(["夜明けの手前", "真夜中の先", "朝の輪郭"])
    if "time" in theme_axes:
        return rng.choice(["明日の手前", "昨日の続き", "秒針の隙間"])
    if "uplift" in theme_axes or "light" in theme_axes:
        return rng.choice(["朝焼けの手前", "光の届く前", "明るくなる直前"])
    return rng.choice(["朝の手前", "次の信号の先", "息を吸い直す前"])


def build_title(theme_axes: list[str], theme_words: dict[str, list[str]], emotions: list[str], rng: random.Random) -> str:
    priority_axes = ["night", "time", "defiance", "light", "body", "motion", "fracture", "noise"]
    lead = ""
    for axis in priority_axes:
        pool = theme_words.get(axis, [])
        if pool:
            lead = rng.choice(pool)
            break
    if not lead:
        for pool in theme_words.values():
            if pool:
                lead = rng.choice(pool)
                break
    if not lead:
        lead = "夜"

    if "defiance" in theme_axes or "tension" in theme_axes:
        ending_pool = TITLE_ENDINGS["defiant"]
    elif "uplift" in theme_axes or "light" in theme_axes or "uplift" in emotions:
        ending_pool = TITLE_ENDINGS["uplift"]
    elif "night" in theme_axes or "time" in theme_axes:
        ending_pool = TITLE_ENDINGS["night"]
    else:
        ending_pool = TITLE_ENDINGS["vulnerable"]
    return f"{lead}{rng.choice(ending_pool)}"


def build_hook_bundle(
    title: str,
    theme_axes: list[str],
    emotions: list[str],
    voice: str,
    scene_primary: str,
    time_boundary: str,
    rng: random.Random,
) -> tuple[str, str, str]:
    if "defiance" in theme_axes or "tension" in theme_axes:
        hook_line = f"{title}ごと 今夜を越えていけ"
        hook_echo = f"{title}ごと まだ引き返さない"
        hook_release = f"{voice}は折れない息で {time_boundary}を裂いていく"
        return hook_line, hook_echo, hook_release
    if "uplift" in theme_axes or "light" in theme_axes or "uplift" in emotions:
        hook_line = f"{title}のままで ここから跳べ"
        hook_echo = f"{title}ごと 明日まで運べ"
        hook_release = f"{scene_primary}の向こうへ {voice}はもう一度手を伸ばす"
        return hook_line, hook_echo, hook_release
    if "vulnerability" in theme_axes or "vulnerability" in emotions:
        hook_line = f"{title}を まだ離さない"
        hook_echo = f"{title}だけは 嘘にしない"
        hook_release = f"{voice}の震えごと {time_boundary}へ連れていく"
        return hook_line, hook_echo, hook_release
    hook_line = f"{title}の先へ 今夜を運んでいけ"
    hook_echo = f"{title}のままで まだ止まらない"
    hook_release = f"{scene_primary}の縁で {voice}はやっと息を継ぐ"
    return hook_line, hook_echo, hook_release


def build_generation_context(record: dict[str, Any], rng: random.Random) -> GenerationContext:
    theme_axes = theme_axes_for_record(record)
    if not theme_axes:
        theme_axes = ["body", "motion", "night"]

    emotions = dominant_emotions_for_record(record)
    mode = str(target_payload(record).get("primary_mode", "intimate_confessional"))
    mode_payload = MODE_BANK.get(mode, MODE_BANK["intimate_confessional"])
    voice = rng.choice(mode_payload["voices"])
    address = rng.choice(mode_payload["addresses"])
    confession = rng.choice(mode_payload["confessions"])

    imagery_anchors = style_imagery_bank(record)
    theme_words: dict[str, list[str]] = {}
    for axis in theme_axes:
        base_words = unique_preserve_order(THEME_BANK.get(axis, []))
        shuffled = base_words[:]
        rng.shuffle(shuffled)
        theme_words[axis] = shuffled[:4]

    scene_pool = []
    for axis in theme_axes:
        scene_pool.extend(THEME_SCENES.get(axis, []))
    scene_pool = unique_preserve_order(scene_pool)
    if not scene_pool:
        scene_pool = GENERIC_SCENES[:]
    scene_primary = rng.choice(scene_pool)
    scene_secondary_candidates = [scene for scene in scene_pool if scene != scene_primary]
    scene_secondary = rng.choice(scene_secondary_candidates or GENERIC_SCENES)

    emotion_pool = []
    for emotion in emotions:
        emotion_pool.extend(EMOTION_BANK.get(emotion, []))
    if not emotion_pool:
        emotion_pool = EMOTION_BANK["vulnerability"] + EMOTION_BANK["motion"]
    emotion_line = rng.choice(unique_preserve_order(emotion_pool))

    time_boundary = time_boundary_for_axes(theme_axes, rng)
    title = build_title(theme_axes, theme_words, emotions, rng)
    hook_line, hook_echo, hook_release = build_hook_bundle(
        title,
        theme_axes,
        emotions,
        voice,
        scene_primary,
        time_boundary,
        rng,
    )

    evidence = track_evidence(record)
    short_line_ratio = float(
        evidence.get("language_profile", {})
        .get("line_length_profile", {})
        .get("short_line_ratio", 0.65)
    )

    return GenerationContext(
        track_id=str(record["track_id"]),
        theme_axes=theme_axes,
        dominant_emotions=emotions,
        primary_mode=mode,
        arc_label=arc_label_for_record(record),
        hook_density=hook_density_for_record(record),
        short_line_ratio=short_line_ratio,
        voice=voice,
        address=address,
        confession=confession,
        section_goals=section_goals(record),
        theme_words=theme_words,
        imagery_anchors=imagery_candidates_for_record(record),
        scene_primary=scene_primary,
        scene_secondary=scene_secondary,
        time_boundary=time_boundary,
        body_surface=rng.choice(BODY_SURFACES),
        emotion_line=emotion_line,
        bridge_turn=rng.choice(BRIDGE_TURNS),
        title=title,
        hook_line=hook_line,
        hook_echo=hook_echo,
        hook_release=hook_release,
        final_release=rng.choice(FINAL_RELEASES),
        mastery_constraints=get_universal_blueprint(),
    )


def line_count_for_section(section: str, context: GenerationContext) -> int:
    canonical = canonical_section_name(section)
    if canonical == "intro":
        return 2
    if canonical == "pre_chorus":
        return 2
    if canonical == "bridge":
        return 2
    if canonical == "outro":
        return 2
    if canonical in {"chorus", "chorus_final"}:
        return 4 if context.hook_density == "high" else 4 # Standardize to 4 for mastery
    return 4 if canonical == "verse_1" else 4 # Verse 1 is lean for latency


def unique_line_selection(lines: list[str], count: int) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for line in lines:
        cleaned = line.strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            output.append(cleaned)
        if len(output) >= count:
            break
    return output[:count]


def render_intro_lines(context: GenerationContext, rng: random.Random) -> list[str]:
    anchor = first_available_word(context, rng, "night", "time", "body", "motion")
    motion = first_available_word(context, rng, "motion", "time")
    candidates = [
        f"{context.scene_primary}で {anchor}だけが先に息をしていた",
        f"{motion}みたいな沈黙が {context.body_surface}をなぞっていく",
        f"{context.voice}はまだ {context.confession}まま 目をそらせない",
    ]
    rng.shuffle(candidates)
    return unique_line_selection(candidates, 2)


def render_verse_1_lines(context: GenerationContext, rng: random.Random) -> list[str]:
    motion = first_available_word(context, rng, "motion", "time", "night")
    city = first_available_word(context, rng, "city", "night", "weather")
    fracture = first_available_word(context, rng, "fracture", "noise", "darkness")
    light = first_available_word(context, rng, "light", "fire", "night")
    candidates = [
        f"{context.scene_primary}で、{context.voice}は言い切れない本音を隠したまま朝をやり過ごした",
        f"{motion}みたいな沈黙が {context.body_surface}をなぞっていく",
        f"{context.time_boundary}で {context.emotion_line}",
        f"{city}の縁で 言えないままの言葉ほど {light}みたいに残っていた",
        f"{fracture}の気配まで抱えたまま まだ引き返せるふりをしていた",
        f"{REVERSAL_PREFIXES[0]}、{context.voice}は弱さの輪郭を見ないふりできなかった",
    ]
    rng.shuffle(candidates)
    return unique_line_selection(candidates, line_count_for_section("verse_1", context))


def render_pre_chorus_lines(context: GenerationContext, rng: random.Random) -> list[str]:
    tension = first_available_word(context, rng, "tension", "noise", "motion")
    defiance = first_available_word(context, rng, "defiance", "motion", "uplift")
    candidates = [
        f"{context.confession}、それでも {tension}だけが先に尖っていく",
        f"{context.time_boundary}まであと少し、{context.voice}の心拍だけが走る",
        f"{defiance}の輪郭を噛みしめるたび 夜の密度が変わっていく",
    ]
    rng.shuffle(candidates)
    return unique_line_selection(candidates, 2)


def render_chorus_lines(context: GenerationContext, rng: random.Random, *, final: bool) -> list[str]:
    release_word = first_available_word(context, rng, "uplift", "light", "defiance", "motion")
    address_word = first_available_word(context, rng, "body", "light", "noise")
    lines = [context.hook_line]
    if context.hook_density == "high":
        lines.append(context.hook_echo if final else context.hook_line)
    else:
        lines.append(context.hook_echo)
    if final:
        lines.extend(
            [
                context.hook_release,
                f"{context.final_release}",
            ]
        )
    else:
        # Standardize Hook Repetition for Mastery (A-B-A-C style)
        lines = [
            context.hook_line,
            f"{context.address}に届かなくても {address_word}だけは嘘じゃない",
            context.hook_line if context.mastery_constraints and context.mastery_constraints.min_sectional_repetition > 0 else context.hook_echo,
            f"{release_word}の先で {context.voice}はまだ消えない方を選ぶ"
        ]
    return unique_line_selection(lines, line_count_for_section("chorus_final" if final else "chorus", context))


def render_verse_2_lines(context: GenerationContext, rng: random.Random) -> list[str]:
    city = first_available_word(context, rng, "city", "night", "weather")
    fire = first_available_word(context, rng, "fire", "light", "defiance")
    fracture = first_available_word(context, rng, "fracture", "noise", "tension")
    motion = first_available_word(context, rng, "motion", "uplift", "time")
    vulnerability = first_available_word(context, rng, "vulnerability", "body", "darkness")
    candidates = [
        f"{context.scene_secondary}で、{fracture}だけがまっすぐ鳴っていた",
        f"{fire}みたいに遅れてきた本音が {context.body_surface}で熱を持つ",
        f"{REVERSAL_PREFIXES[rng.randrange(len(REVERSAL_PREFIXES))]}、{context.voice}は{motion}の先を選び直す",
        f"{vulnerability}の欠片でさえ 今夜の証拠になっていく",
        f"{context.scene_secondary}を抜けるたび 隠していた気配だけが名前になる",
        f"{context.address}に言えなかった言葉ほど 未来の方へ急いでいく",
    ]
    rng.shuffle(candidates)
    return unique_line_selection(candidates, line_count_for_section("verse_2", context))


def render_bridge_lines(context: GenerationContext, rng: random.Random) -> list[str]:
    defiance = first_available_word(context, rng, "defiance", "tension", "uplift")
    body = first_available_word(context, rng, "body", "vulnerability", "light")
    candidates = [
        context.bridge_turn,
        f"{defiance}は飾りじゃなくて {context.voice}の{body}に残った証明だ",
        f"{context.scene_secondary}の端で やっと{context.voice}は目を上げた",
    ]
    rng.shuffle(candidates)
    return unique_line_selection(candidates, 2)


def render_outro_lines(context: GenerationContext, rng: random.Random) -> list[str]:
    noise = first_available_word(context, rng, "noise", "night", "body")
    light = first_available_word(context, rng, "light", "uplift", "fire")
    candidates = [
        f"消えない{noise}だけが まだ{context.body_surface}で揺れている",
        f"{context.scene_secondary}の隅で {context.voice}はようやく{light}を見つけた",
        f"{context.title}の余熱だけが 次の朝まで残っていく",
    ]
    rng.shuffle(candidates)
    return unique_line_selection(candidates, 2)


def name_for_voice(voice: str) -> str:
    return "本音" if voice == "私" else "弱さ"


def render_section(section: str, context: GenerationContext, rng: random.Random) -> str:
    canonical = canonical_section_name(section)
    if canonical == "intro":
        lines = render_intro_lines(context, rng)
    elif canonical == "pre_chorus":
        lines = render_pre_chorus_lines(context, rng)
    elif canonical == "chorus":
        lines = render_chorus_lines(context, rng, final=False)
    elif canonical == "verse_2":
        lines = render_verse_2_lines(context, rng)
    elif canonical == "bridge":
        lines = render_bridge_lines(context, rng)
    elif canonical == "chorus_final":
        lines = render_chorus_lines(context, rng, final=True)
    elif canonical == "outro":
        lines = render_outro_lines(context, rng)
    else:
        lines = render_verse_1_lines(context, rng)
    
    section_markdown = "\n".join(lines)
    
    # Final render (Glitch injection if enabled)
    final_lines = []
    if context.glitch_mode != "none":
        for line in section_markdown.splitlines():
            # Only glitch non-empty lines, favor choruses or high-tension spots
            if line and context.glitch_intensity > 0:
                glitched = apply_stutter_glitch(line, style=context.glitch_mode, intensity=context.glitch_intensity)
                final_lines.append(glitched)
            else:
                final_lines.append(line)
        return "\n".join(final_lines)
        
    return section_markdown


def extract_title(markdown_text: str) -> str:
    for line in markdown_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return ""


def extract_lyric_body(markdown_text: str) -> str:
    if "## Lyrics" not in markdown_text:
        return markdown_text
    return markdown_text.split("## Lyrics", 1)[1]


def extract_section_blocks(markdown_text: str) -> list[tuple[str, list[str]]]:
    body = extract_lyric_body(markdown_text)
    blocks: list[tuple[str, list[str]]] = []
    current_section = ""
    current_lines: list[str] = []
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = SECTION_HEADER_PATTERN.match(line)
        if match:
            if current_section:
                blocks.append((current_section, current_lines))
            current_section = match.group(1).strip()
            current_lines = []
            continue
        if current_section:
            current_lines.append(line)
    if current_section:
        blocks.append((current_section, current_lines))
    return blocks


def lyric_lines(markdown_text: str) -> list[str]:
    lines: list[str] = []
    for _, block_lines in extract_section_blocks(markdown_text):
        lines.extend(block_lines)
    return lines


def repeated_line_count(markdown_text: str) -> int:
    counts = Counter(lyric_lines(markdown_text))
    return sum(1 for count in counts.values() if count >= 2)


def theme_coverage_fraction(record: dict[str, Any], markdown_text: str) -> float:
    body = extract_lyric_body(markdown_text)
    axes = theme_axes_for_record(record)
    if not axes:
        return 1.0
    axis_scores: list[float] = []
    anchors = style_imagery_bank(record)
    for axis in axes:
        pool = unique_preserve_order(THEME_BANK.get(axis, []) + anchors)
        hits = sum(1 for item in pool if item and item in body)
        axis_scores.append(min(1.0, hits / 2))
    return round(sum(axis_scores) / len(axis_scores), 4)


def surface_specificity_fraction(record: dict[str, Any], markdown_text: str) -> float:
    body = extract_lyric_body(markdown_text)
    concrete_axes = {"body", "noise", "time", "light", "city", "motion", "weather", "night", "fire", "fracture"}
    concrete_words: list[str] = []
    for axis in theme_axes_for_record(record):
        if axis in concrete_axes:
            concrete_words.extend(THEME_BANK.get(axis, []))
    concrete_words.extend(style_imagery_bank(record))
    concrete_hits = sum(1 for item in unique_preserve_order(concrete_words) if item and item in body)

    abstract_markers = ["言葉", "気配", "弱さ", "本音", "未来", "輪郭", "密度", "証明", "明日", "夜"]
    abstract_hits = sum(body.count(marker) for marker in abstract_markers)
    return round(concrete_hits / max(1, concrete_hits + abstract_hits * 0.7), 4)


def uniqueness_fraction(markdown_text: str) -> float:
    lines = lyric_lines(markdown_text)
    if not lines:
        return 0.0
    counts = Counter(lines)
    hook_line, hook_count = counts.most_common(1)[0]
    allowed_hook_repeats = min(2, max(0, hook_count - 1))
    repeated_excess = 0
    for line, count in counts.items():
        duplicates = max(0, count - 1)
        if line == hook_line:
            duplicates = max(0, duplicates - allowed_hook_repeats)
        repeated_excess += duplicates
    return round(max(0.0, 1.0 - (repeated_excess / max(1, len(lines)))), 4)


def title_alignment_fraction(markdown_text: str) -> float:
    title = extract_title(markdown_text).replace(" ", "")
    if not title:
        return 0.0
    body = extract_lyric_body(markdown_text)
    if title in body:
        return 1.0
    title_parts = [part for part in title.split("の") if len(part) >= 2]
    if any(part in body for part in title_parts):
        return 0.7
    return 0.3


def hook_behavior_fraction(record: dict[str, Any], markdown_text: str) -> float:
    expected = hook_density_for_record(record)
    blocks = extract_section_blocks(markdown_text)
    chorus_lines: list[str] = []
    non_chorus_lines: list[str] = []
    for section, lines in blocks:
        if canonical_section_name(section) in {"chorus", "chorus_final"}:
            chorus_lines.extend(lines)
        else:
            non_chorus_lines.extend(lines)
    chorus_counts = Counter(chorus_lines)
    top_repeat = max(chorus_counts.values(), default=1)
    if expected == "high":
        score = 1.0 if 2 <= top_repeat <= 4 else 0.7 if top_repeat >= 1 else 0.4
    elif expected == "medium":
        score = 1.0 if 1 <= top_repeat <= 3 else 0.7
    else:
        score = 1.0 if top_repeat <= 1 else 0.7
    leakage = sum(1 for count in Counter(non_chorus_lines).values() if count >= 2)
    if leakage >= 2:
        score -= 0.2
    elif leakage == 1:
        score -= 0.1
    return round(max(0.0, min(1.0, score)), 4)


def arc_support_fraction(record: dict[str, Any], markdown_text: str) -> float:
    blocks = {section: lines for section, lines in extract_section_blocks(markdown_text)}
    sections = set(blocks)
    score = 0.0
    if "pre_chorus" in sections:
        score += 0.2
    if "chorus_final" in sections:
        score += 0.25
    bridge_lines = blocks.get("bridge", [])
    if bridge_lines and any(
        marker in " ".join(bridge_lines)
        for marker in ["やっと", "じゃなく", "それでも", "失くした", "本音"]
    ):
        score += 0.25
    final_lines = blocks.get("chorus_final", [])
    if final_lines and any(
        marker in " ".join(final_lines)
        for marker in ["明日", "ここから", "終われない", "未来", "運んでいく", "踏み出す"]
    ):
        score += 0.3
    return round(max(0.0, min(1.0, score)), 4)


def candidate_quality_score(record: dict[str, Any], markdown_text: str) -> float:
    theme = theme_coverage_fraction(record, markdown_text)
    hook = hook_behavior_fraction(record, markdown_text)
    arc = arc_support_fraction(record, markdown_text)
    uniqueness = uniqueness_fraction(markdown_text)
    title = title_alignment_fraction(markdown_text)
    specificity = surface_specificity_fraction(record, markdown_text)
    
    # Mastery Blueprint Alignment
    mastery_data = validate_against_blueprint(lyric_lines(markdown_text), "Chorus")
    mastery_score = mastery_data.get("total_mastery_score", 0.0)

    total = (
        theme * 0.20
        + hook * 0.14
        + arc * 0.10
        + uniqueness * 0.10
        + title * 0.10
        + specificity * 0.10
        + mastery_score * 0.26 # High weight for Mastery mechanics
    )
    return round(total, 4)


def render_draft_markdown(record: dict[str, Any], *, variant_seed: int = 0) -> str:
    target = target_payload(record)
    rng = rng_for_record(record, salt=variant_seed)
    context = build_generation_context(record, rng)
    sections = section_plan(record)

    lines = [
        f"# {context.title}",
        "",
        "## Draft Notes",
        "- This is an original lyric draft generated from abstracted corpus features only.",
        "- It avoids direct artist imitation and does not reuse scraped lyrics.",
        f"- Track source id: `{record['track_id']}`",
        f"- Theme axes: {', '.join(context.theme_axes)}",
        f"- Primary mode: {target.get('primary_mode', 'unspecified')}",
        "",
        "## Lyrics",
        "",
    ]

    for section in sections:
        lines.append(f"[{section}]")
        lines.append(render_section(section, context, rng))
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def generate_best_draft_markdown(record: dict[str, Any], *, candidate_count: int = 6) -> str:
    best_markdown = ""
    best_score = -1.0
    for variant_seed in range(max(1, candidate_count)):
        markdown_text = render_draft_markdown(record, variant_seed=variant_seed)
        score = candidate_quality_score(record, markdown_text)
        if score > best_score:
            best_score = score
            best_markdown = markdown_text
    return best_markdown


def default_output_path(source_jsonl: Path, record: dict[str, Any]) -> Path:
    artist_id = record.get("artist_id", "artist")
    return Path("outputs") / "lyric_drafts" / artist_id / f"{record['track_id']}.md"


def generate_lyric_draft(request: LyricDraftRequest) -> Path:
    records = load_jsonl(request.source_jsonl)
    if not records:
        raise ValueError(f"No records found in {request.source_jsonl}")
    record = choose_record(records, request.track_id)
    output_path = request.output_path or default_output_path(request.source_jsonl, record)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        generate_best_draft_markdown(record, candidate_count=request.candidate_count),
        encoding="utf-8",
    )
    return output_path
