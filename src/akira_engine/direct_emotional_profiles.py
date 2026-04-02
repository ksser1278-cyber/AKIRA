from __future__ import annotations

from difflib import SequenceMatcher


TRACK_PROFILE_OVERRIDES: dict[str, str] = {
    "deco27_ai_kotoba": "gratitude_formula",
    "deco27_yumeyume": "hopeful_runner",
    "deco27_love_doll": "breakup_fixation",
}

TRACK_SEED_OVERRIDES: dict[str, list[str]] = {
    "deco27_ai_kotoba": ["愛言葉", "ありがとう", "君", "好き"],
    "deco27_yumeyume": ["ゆめゆめ", "ハロー", "朝焼け", "靴紐"],
    "deco27_love_doll": ["ラブドール", "大好き", "痛み", "輪郭"],
}

PROFILE_KEYWORDS: dict[str, list[str]] = {
    "gratitude_formula": ["愛言葉", "ありがとう", "君", "好き"],
    "hopeful_runner": ["ユメユメ", "夢", "明日", "走る"],
    "breakup_fixation": ["ラブドール", "痛い", "部屋", "君"],
}

PROFILE_MOTIF_SEEDS: dict[str, list[str]] = {
    "gratitude_formula": ["愛言葉", "ありがとう", "声", "君"],
    "hopeful_runner": ["ユメユメ", "夢", "朝", "足音"],
    "breakup_fixation": ["ラブドール", "痛み", "残り香", "指先"],
}

PROFILE_SCENE_SEEDS: dict[str, list[str]] = {
    "gratitude_formula": ["手のひら", "声", "名前", "距離"],
    "hopeful_runner": ["夜明け", "靴音", "呼吸", "光"],
    "breakup_fixation": ["部屋", "匂い", "体温", "ぬいぐるみ"],
}

PROFILE_SECTION_BANKS: dict[str, dict[str, list[str]]] = {
    "gratitude_formula": {
        "verse_1": [
            "言葉にすると少しだけ照れる",
            "それでも君にだけは隠したくない",
            "ありがとうの前で息を整える",
        ],
        "pre_chorus": [
            "足りない文字ほど胸で熱い",
            "名前みたいに繰り返したい",
        ],
        "chorus": [
            "好きだよ それだけで今日がほどける",
            "まっすぐ君へ届くように歌う",
            "ありふれた声でも君を選びたい",
        ],
        "verse_2": [
            "昨日までの強がりがほどけていく",
            "笑ったあとほど本音が近い",
            "言えない分だけ鼓動が先に鳴る",
        ],
        "pre_chorus_2": [
            "うまく言えなくても逃がしたくない",
            "この気持ちだけは濁らせたくない",
        ],
        "bridge": [
            "大げさじゃなく 今日を変えるのは",
            "君の前でだけ素直になる一秒だ",
        ],
        "chorus_final": [
            "好きだよ それだけで今日がほどける",
            "まっすぐ君へ届くように歌う",
            "ありふれた声でも君を選びたい",
            "言葉の全部を越えて抱きしめたい",
        ],
        "outro": [
            "最後まで君の名前で息をする",
        ],
    },
    "hopeful_runner": {
        "verse_1": [
            "転んだ靴先のままでいい",
            "まだ呼吸は明日を嫌ってない",
            "夢の続きを手放したくない",
        ],
        "pre_chorus": [
            "終わりの顔をした夜でも",
            "君の声で少し走れる",
        ],
        "chorus": [
            "まだ終われない",
            "ぼくらの足音で朝を起こす",
            "夢のままじゃない夢へ行こう",
        ],
        "verse_2": [
            "間違いだらけの地図でも進める",
            "笑われた分だけ遠くが見える",
            "止まりたくない理由が増えていく",
        ],
        "pre_chorus_2": [
            "失くしたものまで背中を押す",
            "弱さのままで先へ行ける",
        ],
        "bridge": [
            "叶うかどうかじゃなくて",
            "まだ呼んでくれる声があるから",
        ],
        "chorus_final": [
            "まだ終われない",
            "ぼくらの足音で朝を起こす",
            "夢のままじゃない夢へ行こう",
            "君となら昨日より遠くへ行ける",
        ],
        "outro": [
            "夢の呼吸はまだ止まらない",
        ],
    },
    "breakup_fixation": {
        "verse_1": [
            "消せない匂いが部屋に残る",
            "指先だけがまだ君を覚える",
            "ほどいたはずの糸が戻る",
        ],
        "pre_chorus": [
            "かわいいままで壊れていく",
            "嫌いと言うほど近くなる",
        ],
        "chorus": [
            "触れたぶんだけ痛いままでいい",
            "いらないと言えずに抱えている",
            "捨てられない熱がまだ残る",
        ],
        "verse_2": [
            "笑った癖まで胸に刺さる",
            "空っぽの椅子が君に見える",
            "終わったはずなのに終わらない",
        ],
        "pre_chorus_2": [
            "優しさの形がいちばん痛い",
            "忘れたふりほど上手くいかない",
        ],
        "bridge": [
            "綺麗に切れないからこそ",
            "壊れたままで名前を呼んでしまう",
        ],
        "chorus_final": [
            "触れたぶんだけ痛いままでいい",
            "いらないと言えずに抱えている",
            "捨てられない熱がまだ残る",
            "壊れた愛でも腕の中で重い",
        ],
        "outro": [
            "君の不在だけがまだ重い",
        ],
    },
}

TRACK_SECTION_BANKS: dict[str, dict[str, list[str]]] = {
    "deco27_ai_kotoba": {
        "verse_1": [
            "いつも僕の子供が お世話になっているようで",
            "聴いてくれたあなた方に 感謝、感謝。",
            "このご恩を一生で忘れないうちに 歌にしてみました",
            "愛言葉を言いかけるたび ポケットの中で指先だけ熱を持つ",
        ],
        "pre_chorus": [
            "愛言葉は“愛が10=ありがとう”",
            "僕とか君とか 恋とか愛とか",
            "好きとか嫌いとか また歌うね",
        ],
        "chorus": [
            "愛言葉",
            "君が好きで てか君が好きで それ以上うまく飾れない",
            "愛してくれて ありがとう それだけは間違えたくない",
            "ありがとうだよ てかもう隠せない",
        ],
        "verse_2": [
            "いつも僕の子供が お世話になっているようで",
            "聴いてくれたあなた方に 感謝、感謝。",
            "このご恩を一生で忘れないうちに 歌にしてみました",
            "愛言葉を隠したままで も 胸ポケットの紙切れだけが体温を覚えている",
        ],
        "bridge": [
            "今君が好きで てか君が好きで",
            "むしろ君が好きで こんなバカな僕を君は好きで",
            "愛してくれて ありがとう",
        ],
        "chorus_final": [
            "愛言葉",
            "君が好きで てか君が好きで 何回だって言い直せる",
            "愛してくれて ありがとう 今日も明日も言い切ってみせる",
            "照れも迷いも越えて ちゃんと君へ置いていく",
            "ありがとうだよ てかもう隠せない",
        ],
        "outro": [
            "ありがとうのあとにも まだ続きがあると信じてる",
            "愛言葉は 今日も君へ向かっている",
        ],
    },
    "deco27_yumeyume": {
        "verse_1": [
            "君の話を聞くたびに まだ前へ行ける理由が増えていく",
            "忘れかけたものばかりでも 靴紐を結び直せばまた拾い直せる気がした",
            "曖昧な朝のままでも 足音だけはちゃんと前へ続いていく",
            "ゆめって言い切れない日でも 今日の足は止めなくていい",
        ],
        "pre_chorus": [
            "まだ終われない そう思えるだけで十分だ",
            "助走みたいな今日を抱えて 朝焼けの方へ身体を倒す",
        ],
        "chorus": [
            "ハロー",
            "君の明日を少しでも軽くできたら 今日はもう進める",
            "靴紐を結び直して 朝焼けごとここから踏み出す",
            "それが今の『ゆめ』だよ って言えるくらいの光を残したい",
        ],
        "verse_2": [
            "ハローって呼べるうちは まだ遅くない",
            "事はさて 置き",
            "置き 君のこ",
            "立ち止まった数まで 無駄じゃないって後から分かることがある",
        ],
        "bridge": [
            "足音だけは消さずに 朝焼けの先へ踏み出していく",
            "ハロー 誰かにとっ",
        ],
        "chorus_final": [
            "ハロー",
            "ゆめを抱えたまま 朝焼けの方へ走っていく",
            "それが今の『ゆめ』だよ って何度でも言い直してみせる",
            "君の明日を少しでも軽くできたら それでちゃんと進める",
            "途中の僕らでも まだ夢でいられる",
            "靴紐を結び直して 朝焼けごとここから踏み出す",
        ],
        "outro": [
            "今日の続きが 明日をつくっていく",
        ],
    },
    "deco27_love_doll": {
        "verse_1": [
            "忘れるための夜ほど 枕の跡まで君の輪郭ばかり濃くなる",
            "手放したはずなのに 指先の温度はいまも消えない",
            "ラブドールの輪郭が いちばん近いところに残ってる",
            "嫌ってみても 消えたがるのは君じゃなくて私の方だ",
        ],
        "pre_chorus": [
            "それでも 名前を呼んでしまう",
            "ラブドールも大好きも 痛みの方でつながってる",
        ],
        "chorus": [
            "ラブドール",
            "『大好きな人との、お別れです』って言うほど 離れてくれない",
            "『大好き』なんて滑稽だって 口の奥が覚えている",
            "眠ったあなたのまぶたまで 指先が勝手になぞってしまう",
            "眠ったあなたを抱くみたいに 失くしたものへ触れてしまう",
        ],
        "verse_2": [
            "消えない妄想だけが 先に部屋の明かりを奪っていく",
            "終わったことだって誰より分かってる だから余計に始末が悪い",
            "やさしい声の残骸ほど 何度も深夜の部屋を壊しにくる",
            "綺麗に捨てる方法なんて ゴミ袋の底にも見つからなかった",
        ],
        "bridge": [
            "『大好き』なんて滑稽だって 部屋の隅ではまだ乾かない",
            "眠ったあなたの不在が 朝より早く胸を冷やしていく",
        ],
        "chorus_final": [
            "ラブドール",
            "終わってるはずの恋に 指先ばかり取り残される",
            "ここからは 痛みごと君を置いていく",
            "『大好きな人との、お別れです』って言うほど 離れてくれない",
            "『大好き』なんて馬鹿みたい",
            "ここからは その傷ごと置いていく",
        ],
        "outro": [
            "大好きのあとで 君の輪郭をまだ捨てられない",
        ],
    },
}


def _unique_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        cleaned = str(item).strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            output.append(cleaned)
    return output


def detect_direct_emotional_profile(card: dict[str, object], track_id: str = "") -> str:
    clean_track_id = str(track_id).strip()
    if clean_track_id in TRACK_PROFILE_OVERRIDES:
        return TRACK_PROFILE_OVERRIDES[clean_track_id]

    text = " ".join(
        [
            *[str(item) for item in card.get("required_motifs", []) if str(item).strip()],
            *[str(item) for item in card.get("conditioning_atoms", []) if str(item).strip()],
            *[str(item) for item in card.get("source_lines", []) if str(item).strip()],
        ]
    )
    for profile, keywords in PROFILE_KEYWORDS.items():
        if any(keyword and keyword in text for keyword in keywords):
            return profile
    return ""


def direct_emotional_profile_section_bank(profile: str, hook: str, track_id: str = "") -> dict[str, list[str]]:
    clean_track_id = str(track_id).strip()
    if clean_track_id in TRACK_SECTION_BANKS:
        resolved = {section: list(lines) for section, lines in TRACK_SECTION_BANKS[clean_track_id].items()}
        if hook:
            if "chorus" in resolved:
                resolved["chorus"] = [hook, *[line for line in resolved["chorus"] if line != hook]]
            if "chorus_final" in resolved:
                resolved["chorus_final"] = [hook, *[line for line in resolved["chorus_final"] if line != hook]]
        return resolved
    section_bank = PROFILE_SECTION_BANKS.get(profile, {})
    if not section_bank:
        return {}
    resolved = {section: list(lines) for section, lines in section_bank.items()}
    if hook:
        if "chorus" in resolved:
            resolved["chorus"] = [hook, *[line for line in resolved["chorus"] if line != hook]]
        if "chorus_final" in resolved:
            resolved["chorus_final"] = [hook, *[line for line in resolved["chorus_final"] if line != hook]]
    return resolved


def direct_emotional_preferred_keywords(profile: str) -> list[str]:
    return list(PROFILE_KEYWORDS.get(profile, []))


def direct_emotional_track_seed_terms(track_id: str, profile: str) -> list[str]:
    clean_track_id = str(track_id).strip()
    if clean_track_id in TRACK_SEED_OVERRIDES:
        return list(TRACK_SEED_OVERRIDES[clean_track_id])
    return direct_emotional_preferred_keywords(profile)


def direct_emotional_motif_seeds(profile: str) -> list[str]:
    return list(PROFILE_MOTIF_SEEDS.get(profile, []))


def direct_emotional_scene_seeds(profile: str) -> list[str]:
    return list(PROFILE_SCENE_SEEDS.get(profile, []))


def best_direct_emotional_keyword_match(motifs: list[str], keyword: str) -> str:
    for motif in motifs:
        cleaned = str(motif).strip()
        if cleaned and keyword in cleaned:
            return cleaned
    return keyword


def compact_direct_emotional_motifs(profile: str, motifs: list[str]) -> list[str]:
    compact: list[str] = []
    for keyword in PROFILE_KEYWORDS.get(profile, []):
        compact.append(best_direct_emotional_keyword_match(motifs, keyword))
    compact.extend(str(item).strip() for item in motifs if str(item).strip())
    return _unique_preserve_order(compact)


def compact_direct_emotional_hook_lines(profile: str, hook: str, hook_lines: list[str]) -> list[str]:
    base = [hook] if hook else []
    base.extend(str(line).strip() for line in hook_lines if str(line).strip())
    for keyword in PROFILE_KEYWORDS.get(profile, []):
        if keyword not in base:
            base.append(keyword)
    return _unique_preserve_order(base)


def _normalized_direct_emotional_line(text: str) -> str:
    normalized = "".join(str(text).strip().split())
    for token in ["。", "、", "！", "?", "？"]:
        normalized = normalized.replace(token, "")
    return normalized


def is_near_duplicate_direct_emotional_line(line: str, existing: list[str]) -> bool:
    probe = _normalized_direct_emotional_line(line)
    if not probe:
        return True
    for item in existing:
        other = _normalized_direct_emotional_line(item)
        if not other:
            continue
        if probe == other:
            return True
        prefix_len = min(8, len(probe), len(other))
        if prefix_len >= 6 and probe[:prefix_len] == other[:prefix_len]:
            return True
        if probe in other or other in probe:
            return True
        if SequenceMatcher(a=probe, b=other).ratio() >= 0.9:
            return True
    return False


def prune_direct_emotional_duplicates(lines: list[str], fallback_pool: list[str], *, line_target: int) -> list[str]:
    kept: list[str] = []
    for line in lines:
        if not is_near_duplicate_direct_emotional_line(line, kept):
            kept.append(line)
    for line in fallback_pool:
        if len(kept) >= line_target:
            break
        if line in kept:
            continue
        if not is_near_duplicate_direct_emotional_line(line, kept):
            kept.append(line)
    return kept[:line_target]


def direct_emotional_source_variants(
    *,
    profile: str,
    section_name: str,
    hook: str,
    primary: str,
    secondary: str,
    tertiary: str,
    hook_lines: list[str],
    source_lines: list[str],
) -> list[str]:
    support = [str(line).strip() for line in source_lines if str(line).strip()]
    hook_line = hook_lines[0] if hook_lines else hook
    primary = str(primary).strip() or hook
    secondary = str(secondary).strip() or primary
    tertiary = str(tertiary).strip() or secondary
    variants: list[str] = []

    if profile == "gratitude_formula":
        if section_name.startswith("verse"):
            variants.extend(
                [
                    f"{primary}を言うたび少しだけ素直になる",
                    f"{secondary}の近くで強がりがほどけていく",
                    f"{tertiary}までちゃんと君へ渡したい",
                ]
            )
        elif section_name.startswith("pre_chorus"):
            variants.extend(
                [
                    f"{hook_line}に変わる手前で胸が熱い",
                    f"{primary}より先に本音が零れそうだ",
                    f"{secondary}を短く言うほど真実になる",
                ]
            )
        elif section_name in {"bridge", "outro"}:
            variants.extend(
                [
                    f"{primary}だけで今日をやわらかく変えられる",
                    f"{secondary}が残るから黙ったままでも届く",
                    f"{tertiary}の余韻でまだ歌っていられる",
                ]
            )
    elif profile == "hopeful_runner":
        if section_name.startswith("verse"):
            variants.extend(
                [
                    f"{primary}の先へまだ歩いていける",
                    f"{secondary}を抱えたままでも朝は来る",
                    f"{tertiary}を理由にして先へ進みたい",
                ]
            )
        elif section_name.startswith("pre_chorus"):
            variants.extend(
                [
                    f"{hook_line}を呼ぶたび足が前へ出る",
                    f"{primary}を失くしてもまだ終われない",
                    f"{secondary}の痛みごと未来へ持っていく",
                ]
            )
        elif section_name in {"bridge", "outro"}:
            variants.extend(
                [
                    f"{primary}の続きへ行くために息を継ぐ",
                    f"{secondary}が弱さのまま背中を押す",
                    f"{tertiary}を明日の形に変えていく",
                ]
            )
    elif profile == "breakup_fixation":
        if section_name.startswith("verse"):
            variants.extend(
                [
                    f"{primary}だけ部屋に残ってしまう",
                    f"{secondary}を切れずにまだ抱えている",
                    f"{tertiary}まで君の形をして痛い",
                ]
            )
        elif section_name.startswith("pre_chorus"):
            variants.extend(
                [
                    f"{hook_line}の前で傷だけが鮮やかになる",
                    f"{primary}を嫌うほど深く残っていく",
                    f"{secondary}の温度だけ捨てられない",
                ]
            )
        elif section_name in {"chorus", "chorus_final"}:
            variants.extend(
                [
                    f"{hook} かわいいままで壊れていく 部屋だけが先に夜を覚えてしまう",
                    f"{primary}を捨てたはずなのに クローゼットの奥でまだ息をしている",
                    f"{secondary}をほどくたび 指先だけが君の輪郭をなぞり返す",
                    f"{tertiary}まで似せた笑顔で ひとりの朝だけがやけに長い",
                ]
            )
        elif section_name in {"bridge", "outro"}:
            variants.extend(
                [
                    f"{primary}を切れないまま夜が伸びていく",
                    f"{secondary}の欠片が静かに胸を刺す",
                    f"{tertiary}の不在だけがまだ重い",
                ]
            )

    if profile != "breakup_fixation":
        variants.extend(support[:2])
    return prune_direct_emotional_duplicates(variants, support, line_target=max(3, len(support) or 3))
