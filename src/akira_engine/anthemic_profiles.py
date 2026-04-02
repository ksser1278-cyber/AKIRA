from __future__ import annotations

from typing import Any

ANTHEMIC_PROFILE_SECTION_BANKS: dict[str, dict[str, list[str]]] = {
    "newgenesis": {
        "intro": [
            "新時代はこの未来だ ためらいまで置いていけ",
            "光の速度で 明日の輪郭を塗り替えていく",
        ],
        "verse_1": [
            "リアルゲームの縁で まだ息はギリギリ未来を選ぶ",
            "Do you wanna play の残響より 果てしない音楽が先に走る",
            "世界の向こうへ抜ける光は きれいな順番なんかで並ばない",
            "昨日のルールを越えた瞬間 まぶたの裏まで白くなる",
        ],
        "pre_chorus": [
            "リアルゲームの外で もう脈だけが新時代を呼ぶ",
            "果てしない音楽が 私の迷いをまとめて追い越す",
            "ためらいごと もっと向こうへ投げてしまえ",
        ],
        "verse_2": [
            "もっと向こうの景色なら もう遠慮の名前を持たない",
            "リアルゲームの駆け引きより 私の速度が先に裂ける",
            "ギリギリの今日を越えて まぶしい側へ重心が傾いた",
            "果てしない音楽が 世界ごと新しく開いていく",
        ],
        "pre_chorus_2": [
            "言い訳の形じゃ もうこの歌は止められない",
            "新時代だと きれいごとじゃなく言い切ってしまう",
            "まぶたの裏の光まで もっと向こうへ連れていく",
        ],
        "chorus_open": [
            "ためらいまで連れていけ いま拍が未来へ噛みつく",
            "綺麗じゃない願いも この拍で未来へ連れ出せる",
            "果てしない音楽を もっと向こうへ押し上げる",
        ],
        "chorus": [
            "ためらいまで連れていけ いま拍が未来へ噛みつく",
            "綺麗じゃない願いも この拍で未来へ連れ出せる",
            "果てしない音楽を もっと向こうへ引き上げる",
        ],
        "chorus_2": [
            "新時代だ まだ広がる",
            "答えにならなくても 果てしない音楽は止まらない",
            "新時代はこの未来だ そのまま世界へ押し返せ",
            "ここから誤魔化さない",
            "新時代だ",
        ],
        "bridge": [
            "追い風を信じる余白が まだこの胸に残っていた",
            "リアルゲームの外へ出るたび 自由の輪郭がはっきり浮かぶ",
            "新時代の拍が 迷いの全域を光へひらく",
        ],
        "bridge_rise": [
            "ためらいの骨ごと ここでは置いていかない",
            "張りつめた光より大きい声で 新時代を呼び直す",
            "世界の端まで もっと向こうへ連れていく",
        ],
        "chorus_final": [
            "響け 新時代",
            "世界中のためらいまで この音で抱え直していく",
            "新時代はこの未来だと叫んで ここから先へ踏み出す",
            "果てしない音楽で 世界中全部を塗り替えていく",
            "きれいなだけの明日じゃなく 変えていく方を信じる",
            "新時代だ",
        ],
        "outro": [
            "リアルゲームの残響さえ もう新時代に塗り替わっていく",
            "新時代はこの未来だ まだもっと向こうが呼んでいる",
        ],
    },
    "totmusica": {
        "intro": [
            "Gah zan tak 雨打つ祈りの底で 何処まで声が彷徨う",
            "枯れきらない願いが 黒い choir をもう一度呼び起こす",
        ],
        "verse_1": [
            "死をも転がす救いの讃歌で 求められた救世主の喉が裂ける",
            "祈りの真ん中で まだ誰も救えないまま立っている",
            "赦しより深い場所で 傷だけが先に名前を持った",
            "夜の底で鳴る和音が 人の顔をしたまま崩れていく",
        ],
        "pre_chorus": [
            "破滅まで転がす救いなら もう祈りじゃ間に合わない",
            "転がる救いの讃歌が かえって世界を赤く裂いていく",
            "ここから先は 綺麗に祈れない",
        ],
        "chorus_open": [
            "無条件 絶対 激昂なら Singing the song",
            "如何せん罵詈雑言でも 有象無象ごと Big Bang",
            "行け 破滅は届く まだ誰にも終わらせない",
        ],
        "chorus": [
            "無条件 絶対 激昂なら Singing the song",
            "如何せん罵詈雑言でも 有象無象ごと Big Bang",
            "行け 破滅は届く まだ誰にも終わらせない",
        ],
        "verse_2": [
            "転がすたび救いが濁って 求められた救世主だけが残る",
            "祈りを掲げた指先から 先に刃みたいな音が落ちる",
            "赦されたい声ほど いちばん派手に闇へ反響する",
            "幕の裏で笑う運命を まだ歌だけが真正面から睨む",
        ],
        "pre_chorus_2": [
            "破滅の方へ 傾いた拍がもう戻らない",
            "無条件 絶対のまま Singing the song を吐き切るだけだ",
            "ここから先は 祈りごと燃やしていく",
        ],
        "chorus_2": [
            "まだ終われない 破滅の譜を",
            "無条件 絶対 激昂なら Singing the song",
            "如何せん罵詈雑言でも 有象無象ごと Big Bang",
            "行け 破滅は届く いま世界の骨まで鳴らせ",
        ],
        "bridge": [
            "破滅を抱えた救世主なんて もう救済よりも凶暴だ",
            "祈りの形で隠した怒りが いちばん高く空を裂く",
            "Singing the song の残響だけが 誰より正しく夜を裁く",
        ],
        "bridge_rise": [
            "無条件 絶対のまま 行け 破滅を解き放て",
            "Singing the song が骨の奥の迷いまで全部燃やしていく",
            "次の一撃で 世界の静寂ごと割り切ってしまえ",
        ],
        "chorus_final": [
            "無条件 絶対 激昂なら Singing the song",
            "如何せん罵詈雑言でも 有象無象ごと Big Bang",
            "ここから踏み出す 破滅を連れていく 誰の祈りでも止められない",
            "救世主の名残さえ 灰にしてなお歌だけが立つ",
        ],
        "outro": [
            "破滅のあとで 救世主も祈りもまだ灰の中で揺れる",
            "Gah zan tak と途切れた息だけが 最後の夜を支配する",
        ],
    },
}


def detect_anthemic_profile(card: dict[str, Any]) -> str:
    source_lines = [str(line or "").strip() for line in card.get("source_lines", []) if str(line or "").strip()]
    source_text = " ".join(source_lines)
    motifs = " ".join(str(item) for item in card.get("required_motifs", []) if str(item).strip())

    if any(fragment in source_text for fragment in ["新時代", "果てしない音楽", "リアルゲーム", "もっと向こう"]) or any(
        fragment in motifs for fragment in ["新時代", "未来", "果てしない音楽", "もっと向こう"]
    ):
        return "newgenesis"
    if any(fragment in source_text for fragment in ["Tot Musica", "Singing the song", "破滅", "救世主"]) or any(
        fragment in motifs for fragment in ["Tot Musica", "破滅", "救世主", "祈り"]
    ):
        return "totmusica"
    return ""


def anthemic_profile_section_bank(profile: str, hook: str) -> dict[str, list[str]]:
    section_bank = ANTHEMIC_PROFILE_SECTION_BANKS.get(profile, {})
    if not section_bank:
        return {}
    resolved = {section: list(lines) for section, lines in section_bank.items()}
    for section_name in ("chorus_open", "chorus", "chorus_final"):
        if section_name in resolved:
            resolved[section_name] = [hook, *resolved[section_name]]
    return resolved
