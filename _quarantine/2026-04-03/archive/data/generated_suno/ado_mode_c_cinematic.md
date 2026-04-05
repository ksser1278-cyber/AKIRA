# 🔥 Ado Style — SUNO.AI 최적화 프롬프트

## ⚠️ 설계 원칙
- Ado 전곡 공통 패턴 기반 (프로듀서 불문)
- SUNO가 실제 반응하는 제어 방법만 사용
- 가사 내 리듬/보컬 연출 지시 내장

---

## 📋 Style of Music

```
Tempo 152 BPM, Dark J-Rock, Aggressive Female Vocal, Vocal Distortion, Growling, Dynamic Contrast, Whisper-to-Scream, Driving Drums, Distorted Guitar Layers, Snare-Forward, Tight Low End, Sharp Chorus Lift, Close-Mic Verses
```

### 🚫 Exclude Styles
```
English-heavy topline, cheap festival EDM drop, bubblegum sweetness, lo-fi bedroom, acoustic coffeehouse, auto-tune heavy
```

---

## 📝 Title
```
黙れ世界 (Damare Sekai)
```

---

## 📖 Lyrics

```
[Intro – Eerie, Minimal]
...

[Pre-Chorus – Whispered, Close-Mic]
ねぇ、聞こえてる?
(聞こえてるよ)
ねぇ、まだ笑ってんの?
(笑ってるよ)

[Verse – Restrained, Minimal Instrumentation + Intimate Vocal]
ちっちゃな箱に詰められた
優等生の形した爆弾
ニコニコ笑って はいはい従って
喉の奥で 牙が伸びる

通勤電車の窒息ラッシュ
誰もスマホしか見てない
正しい正しい正しいって
誰の正しさの話してんの?

[Pre-Chorus – Building Intensity]
胸の奥 ざわざわざわ
限界 ギリギリギリ
もう一秒も...

[Chorus – Aggressive, Energy Lift, Layered Vocals]
黙れ黙れ黙れ世界！
おまえの常識 知ったこっちゃない
喉が裂けたっていい 叫ぶ
(叫ぶ 叫ぶ 叫ぶ!)
丸ごと壊してやる この檻
はぁ? 文句あんなら言ってみろ
アタシの声で塗り潰す
全部 全部 全部！

[Break – Drum]

[Verse 2 – Angry, Driven]
制服の首 ギュッと締めて
「空気読め」って誰が決めた?
クソだりぃルール 飲み込むフリ
舌の裏で ナイフ研いでる

SNS 正義マン 匿名の銃口
撃つだけ撃って 責任ゼロ
偽善偽善偽善ばっか
ナニソレ? は? 黙ってくんねえ?

[Pre-Chorus – Primal Build]
血の味 ジンジンジン
衝動 ドクドクドク
もう止まんねぇ...!

[Chorus – More Intense, Anthemic, Layered Vocals]
黙れ黙れ黙れ世界！
おまえの正義 要らねぇんだよ
身体が壊れたっていい 叫ぶ
(叫ぶ! 叫ぶ! 叫ぶ!)
燃やし尽くしてやる この鎖
はぁ? まだ足りねぇか言ってみろ
アタシの存在で証明する
全部 全部 全部！

[Break]
. ! . . ! ! . ! ! !

[Bridge – Whispered, Intimate, Close-Mic]
...ほんとはね
ただ
わかってほしかっただけ...
(わかってほしかった...)

[Spoken Word Narration]
...でもさ、もう待つの飽きた

[Build]
! . ! . ! ! . ! ! ! ! !

[Chorus – Maximum Energy, Aggressive, Layered Vocals]
黙れ黙れ黙れ黙れ世界ぃぃぃ！
おまえの世界ごと ぶっ壊す！
声が枯れたっていい 叫べぇ！
(叫べ! 叫べ! 叫べぇぇぇ!)
Oooohhh! Aaahhhh!
もう誰にも止められねぇ
アタシはアタシを諦めない
絶対 絶対 絶対！

[Outro – Fading, Intimate]
...まだ、聞こえてる?
(聞こえてるよ...)
```

---

## 🎯 사용 가이드

| 항목 | 값 |
|------|-----|
| **Mode** | Custom |
| **Instrumental** | OFF |
| **Version** | v5 |
| **Style of Music** | 위의 태그 복사 |
| **Exclude Styles** | 위의 Exclude 태그 복사 |
| **Lyrics** | 위의 가사 전체 복사 |
| **Style Influence** | 75-85% |
| **Weirdness** | 40-50% |

---

## 🔧 SUNO 제어 기법 해설

### 사용된 Ado 패턴 ↔ SUNO 제어 매핑

| Ado 특성 | SUNO 구현 방법 | 가사 내 위치 |
|----------|---------------|-------------|
| **속삭임→절규 전환** | `[Pre-Chorus – Whispered]` → `[Chorus – Aggressive]` | Intro→Chorus 전체 |
| **3연타 반복** | `黙れ黙れ黙れ`, `全部全部全部` | Chorus 훅 |
| **콜앤리스폰스/더블링** | `(괄호)` 안의 에코 구절 | `(叫ぶ 叫ぶ 叫ぶ!)` |
| **후반 에스컬레이션** | Last Chorus에서 확장 모음 `ぃぃぃ`, `ぇぇぇ` + `Oooohhh!` | Last Chorus |
| **취약한 브릿지** | `[Bridge – Whispered, Intimate]` + 말줄임표 `...` | Bridge |
| **스킷/대사** | `[Spoken Word Narration]` | Bridge 직후 |
| **구어체/속어** | `クソだりぃ`, `くんねえ`, `はぁ?`, `ナニソレ?` | Verse 전체 |
| **신체 감각 이미지** | `喉が裂ける`, `血の味`, `牙が伸びる`, `舌の裏` | Verse/Pre-Chorus |
| **리듬 제어** | `[Break]` + `. ! . . ! !` 패턴 | Break 섹션 |
| **빌드업** | `[Build]` + `! . ! . ! ! . ! ! ! ! !` | Last Chorus 직전 |
| **페이드아웃 대비** | Outro에서 Intro와 같은 구절 반복 | Intro↔Outro |

### Style 태그 설계 근거

| 태그 | 근거 |
|------|------|
| `Dark J-Rock` | Ado 전곡 base — 보카로 프로듀서 루트의 기타+전자음 |
| `Aggressive Female Vocal` | Ado 보컬 핵심 — 공격적 여성 보컬 |
| `Vocal Distortion, Growling` | うっせぇわ/RuLe 계열 보컬 프라이/그로울 |
| `Dynamic Contrast, Whisper-to-Scream` | 전곡 공통 — 극단적 다이나믹 대비 |
| `Snare-Forward, Tight Low End` | 보카로 프로듀서 사운드 — 세밀한 프로덕션 힌트 |
| `Close-Mic Verses` | Verse에서 속삭이는 듯한 가까운 보컬 |
| `152 BPM` | うっせぇわ(~150) / レディメイド(~160) 중간값 |
