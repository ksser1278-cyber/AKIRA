from __future__ import annotations

from typing import Any

INTIMATE_PROFILE_SECTION_BANKS: dict[str, dict[str, list[str]]] = {
    "readymade": {
        "intro": [
            "ロンリーの値札が あたしの平熱を少しずらす",
            "レディメイドの棚だけが 先にこっちを値踏みしてくる",
        ],
        "verse_1": [
            "固定観念の棚で まともな顔だけが先に売り切れていく",
            "赤裸々に言うほど 綺麗な傷じゃ済まされない",
            "路肩に寝転ぶ人生が きっと今のあたしにお似合いだ",
            "出来合いのラベルを貼るたび 本音だけが鈍く軋んでいく",
        ],
        "pre_chorus": [
            "メイビーで濁すたび 赤裸々だけが濃くなる",
            "いい子の顔じゃ まだ追いつけない",
            "固定観念の手前で あたしの鼓動だけが先に暴れる",
        ],
        "chorus_open": [
            "1.2.3で弾け飛んだ",
            "固定観念バットで打って まだ黙らせない",
            "どうだい どうだい レディメイドじゃ笑えない",
            "ここから誤魔化さない",
        ],
        "chorus": [
            "1.2.3で弾け飛んだ",
            "固定観念バットで打って まだ黙らせない",
            "どうだい どうだい レディメイドじゃ笑えない",
            "ここから誤魔化さない",
        ],
        "verse_2": [
            "ロンリーの顔でやり過ごすたび ノイズだけが骨へ残る",
            "赤裸々に見せた順から かえって嘘が剥がれていく",
            "バットで砕けるのは ガラスじゃなく出来合いの正しさだ",
            "メイビーの奥で 本音ばかりがやっと熱を持つ",
        ],
        "pre_chorus_2": [
            "噛みしめた声さえ もう綺麗に整わない",
            "なのに今度は レディメイドごと隠さない",
            "固定観念の外で 弾けた鼓動を呼び直す",
        ],
        "bridge": [
            "売り場の明かりじゃ あたしの傷まで均せない",
            "赤裸々より先に バットの重さが本音を選んでいた",
            "レディメイドの値札ごと ここで引きちぎってしまう",
        ],
        "bridge_rise": [
            "弾けた余熱ごと ここでは飲み込まない",
            "浅い呼吸より大きい声で レディメイドを呼び直す",
            "ノイズの底でも 喉の奥で噛み砕く",
        ],
        "chorus_final": [
            "1.2.3で弾け飛んだ",
            "固定観念バットで打って 最後まで黙らせない",
            "どうだい どうだい レディメイドじゃ笑えない",
            "ここから バットみたいな本音で値札を剥がしていく",
            "壊れたままでも あたしは出来合いに戻らない",
        ],
        "outro": [
            "赤裸々の隅で あたしはようやくレディメイドを見失わない",
            "ノイズめいた余熱が 次の朝までまだ居座っている",
        ],
    },
}


def detect_intimate_profile(card: dict[str, Any]) -> str:
    source_lines = [str(line or "").strip() for line in card.get("source_lines", []) if str(line or "").strip()]
    source_text = " ".join(source_lines)
    motifs = " ".join(str(item) for item in card.get("required_motifs", []) if str(item).strip())

    if any(fragment in source_text for fragment in ["レディメイド", "固定観念", "バット", "ロンリー", "赤裸々"]) or any(
        fragment in motifs for fragment in ["レディメイド", "ロンリー", "赤裸々"]
    ):
        return "readymade"
    return ""


def intimate_profile_section_bank(profile: str, hook: str) -> dict[str, list[str]]:
    del hook
    section_bank = INTIMATE_PROFILE_SECTION_BANKS.get(profile, {})
    return {section: list(lines) for section, lines in section_bank.items()}
