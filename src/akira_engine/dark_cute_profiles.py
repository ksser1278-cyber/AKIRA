from __future__ import annotations


def default_cute_word(title_seed: str) -> str:
    if "魔法" in title_seed or "少女" in title_seed:
        return "魔法"
    if "チョコ" in title_seed:
        return "甘い"
    return "かわいい"


def build_dark_cute_section_bank(
    *,
    title_seed: str,
    sweet: str,
    toxic: str,
    crack: str,
    cute_word: str,
    mask_word: str,
    aftertaste_word: str,
    hook: str,
    conditioned_decision: str,
    conditioned_release: str,
    source_variants: list[str],
) -> dict[str, list[str]]:
    return {
        "verse_1": [
            *source_variants[:2],
            f"{title_seed}の顔で 笑ったまま{crack}だけが先に増える",
            f"{cute_word}と言われるたび {toxic}ばかり喉に残る",
            f"{sweet}みたいにやわらかいふりで 傷んだ{mask_word}だけ隠しきれない",
            "ほどけたリボンの先で まだ平気なふりだけ上手くなる",
            f"{mask_word}に寄せるほど {crack}だけ妙にあざやかになる",
        ],
        "pre_chorus": [
            *source_variants[:2],
            f"甘い顔のままじゃ もう{toxic}を飲み込めない",
            f"{crack}ごと抱えた声が 先に高く軋んでいく",
            f"{title_seed}の奥で きれいな嘘だけ割れていく",
            f"{aftertaste_word}の方が かわいいより先に残ってしまう",
        ],
        "chorus": [
            hook,
            *source_variants[:1],
            f"{title_seed} かわいいままで{toxic}まで舐めきれない",
            f"{sweet}の皮を剥いだら {crack}ばかり光ってしまう",
            f"{conditioned_release} それでも甘く壊れていく",
        ],
        "verse_2": [
            *source_variants[:2],
            f"拍手の残り香で まだ{sweet}の仮面だけ貼り直してる",
            f"{cute_word}の型へ押し込むほど {toxic}だけ鮮やかになる",
            f"やさしい色で塗るたびに {crack}の線だけ浮き上がる",
            "食べ残した気休めより この痛みの方がよく喋る",
            f"{aftertaste_word}を隠すほど 似合ってる顔だけ雑になっていく",
        ],
        "bridge_rise": [
            *source_variants[:1],
            f"もう{sweet}のまま黙っていられない",
            f"{title_seed}ごと噛み砕いても {toxic}は消えない",
            conditioned_decision,
        ],
        "chorus_final": [
            hook,
            *source_variants[:1],
            f"{title_seed} かわいい顔でも{toxic}まで隠し切れない",
            f"{sweet}の殻を破れば {crack}の方がずっと正直だ",
            f"{conditioned_release} ここから先は甘く壊れたまま行く",
            conditioned_decision,
            f"{aftertaste_word}まで飲み込んで それでも笑ってしまう",
        ],
        "outro": [
            *source_variants[:1],
            f"{sweet}の残り香より {crack}の方がまだ離れない",
            f"{title_seed}のあとで 笑い声だけ少し毒になる",
            f"{aftertaste_word}だけ 次の朝まで甘く腐っていく",
        ],
    }
