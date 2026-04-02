# Lyric Writing Basics Research

인터넷 리서치 기준으로 정리한 `작사의 기초` 요약이다. 목적은 읽기 좋은 이론 정리가 아니라, `AKIRA ENGINE`의 데이터셋/플래너/평가기로 바로 옮길 수 있는 기본 원칙을 추리는 데 있다.

## 핵심 결론

좋은 작사는 대체로 아래 순서로 설계된다.

1. `무슨 말을 하고 싶은지`를 제목/훅으로 압축한다.
2. Verse에서는 그 말을 설명하지 말고 `장면과 감각`으로 보여준다.
3. Chorus에서는 `핵심 메시지`를 반복 가능하게 말한다.
4. Verse 2와 Bridge는 정보를 다시 말하는 게 아니라 `관점이나 무게를 바꾼다`.
5. 말의 강세, 음절 길이, 반복 위치가 멜로디/리듬과 맞아야 한다.
6. 초안은 거의 항상 길고 뭉개져 있으므로, 최종 품질은 수정에서 결정된다.

## 1. 제목과 훅

- 좋은 훅은 보통 `제목`과 매우 가깝다.
- 훅은 대개 `chorus의 첫 줄 또는 마지막 줄` 같은 power position에 놓인다.
- 훅은 `많이 설명하는 문장`보다 `짧고 기억되는 문장`이 유리하다.
- 훅은 반복되지만, verse가 충분히 tension을 쌓아줘야 반복이 먹힌다.

엔진 적용:

- `title`
- `hook_core`
- `hook_power_positions`
- `chorus_first_line`
- `chorus_last_line`

이 5개를 분리해서 다뤄야 한다.

## 2. Verse와 Chorus의 역할 분리

- Verse는 `showing language`가 중심이다.
- Chorus는 `telling / summarizing language`가 중심이다.
- Verse는 작은 순간과 구체적인 감각을 담당하고, Chorus는 그 모든 장면이 뜻하는 바를 말한다.

엔진 적용:

- Verse에선 `scene / sensory detail / action / object`
- Chorus에선 `message / commitment / hook / refrain`

이걸 강하게 분리해야 한다.

## 3. Verse 2는 전진해야 한다

- Verse 2가 Verse 1의 단순 반복이면 곡이 멈춘다.
- Verse 2는 보통
  - 정보 추가
  - 감정 심화
  - 시점 전환
  - 제목 재해석
중 하나를 해야 한다.
- Berklee 계열 자료에서는 이를 `recoloration`처럼 설명한다. 같은 제목을 다른 각도에서 다시 보게 만드는 것이다.

엔진 적용:

- `verse_2_delta`
- `title_recoloration`
- `stakes_raise`
- `new_image_requirement`

같은 필드가 필요하다.

## 4. Bridge는 새 장소여야 한다

- Bridge는 그냥 chorus로 돌아가기 전 임시 대기실이 아니다.
- 좋은 bridge는 보통
  - `그래서 이제 어떻게 할 건데?`
  - `지금까지의 이야기의 도덕/핵심이 뭔데?`
  - `이 인물이 뭘 깨달았는데?`
를 다룬다.
- Bridge가 약하면, 대개 곡의 중심 아이디어가 아직 흐리다는 신호다.

엔진 적용:

- `bridge_turn_type`
  - decision
  - confession
  - reversal
  - moral
  - escalation
- `bridge_question`
- `bridge_answer`

를 explicit하게 두는 게 좋다.

## 5. 구체성이 추상성을 이긴다

- 좋은 가사는 추상 감정어만 반복하지 않는다.
- `외로움`, `불안`, `희망`만 반복하면 약해진다.
- 대신
  - 신체
  - 물건
  - 장소
  - 시간
  - 기상
  - 움직임
같은 구체적 단서가 먼저 와야 한다.
- 감정은 장면 뒤에 따라오는 편이 더 강하다.

엔진 적용:

- `imagery_density`
- `body imagery`
- `object imagery`
- `time/place/weather anchors`
- `abstract_word_ratio`

를 측정해야 한다.

## 6. Prosody는 필수다

- 말의 강세와 음악의 강세가 맞아야 자연스럽다.
- 단순히 음절 수만 맞추는 것으로는 부족하다.
- `강한 음절`이 강박에 오고, 중요한 단어가 멜로디의 중요한 위치에 있어야 한다.
- Berklee/Pat Pattison 계열 자료는 prosody를 `노래의 모든 요소가 같은 감정과 목적을 향해 움직이는 상태`로 본다.

엔진 적용:

- `line_syllable_profile`
- `stress_pattern`
- `hook_stress_positions`
- `phrase_length_profile`
- `stable_vs_unstable line design`

을 장기적으로 넣어야 한다.

## 7. 구조의 대비가 곡을 만든다

- Hook는 앞부분과의 `contrast` 덕분에 더 세게 느껴진다.
- Verse가 짧고 촘촘하면 Chorus는 넓고 길게.
- Verse가 내밀하면 Chorus는 크게.
- Pre-chorus는 대개 `압축`, Chorus는 `해방`.

엔진 적용:

- `section contrast plan`
- `pre_chorus compression`
- `chorus release`
- `bridge turn`
- `final chorus expansion`

이 구조적으로 계획되어야 한다.

## 8. 첫 줄은 바로 긴장을 걸어야 한다

- 첫 줄은 보통 설명보다 `감정`, `갈등`, `드라마`, `이상한 이미지`가 더 좋다.
- 청자가 계속 듣게 만드는 건 “정리된 정보”보다 “걸린 질문”이다.

엔진 적용:

- `opening_line_tension_score`
- `opening_conflict`
- `opening_image`

를 강제하는 게 좋다.

## 9. 반복은 같게 들리면 실패다

- Chorus 반복은 필요하지만, 완전히 똑같이만 들리면 힘이 빨리 빠진다.
- 좋은 반복은
  - 위치 변화
  - 앞 맥락 변화
  - final chorus의 새 이미지/새 결정
을 통해 의미가 커진다.

엔진 적용:

- `hook_repetition_plan`
- `final_chorus_new_image`
- `final_chorus_irreversible_decision`
- `hook_semantic_growth`

가 필요하다.

## 10. 수정은 삭제가 핵심이다

- 초안은 대개 길고, 설명이 많고, 안전하다.
- 수정 단계에서는 보통 아래를 잘라야 한다.
  - 의미 중복
  - 설명 접속사
  - 추상 감정어 반복
  - 약한 다리 문장
  - 제목과 연결되지 않는 좋은 문장

엔진 적용:

- `filler_line_detection`
- `duplicate_semantic_lines`
- `title_alignment_score`
- `weak_bridge_penalty`
- `abstract_word_penalty`

를 critic 쪽에 넣어야 한다.

## AKIRA ENGINE에 바로 필요한 것

현재 상태에서 가장 먼저 필요한 건 새 기능을 많이 더하는 게 아니라, 작사 기초를 구조 필드로 강제하는 것이다.

### 데이터셋 필수 필드

- `title_function`
- `hook_power_positions`
- `verse_1_job`
- `verse_2_delta`
- `pre_chorus_compression_style`
- `bridge_turn_type`
- `final_chorus_new_image`
- `final_chorus_decision`
- `imagery_density`
- `abstract_word_ratio`
- `prosody_notes`

### 플래너 필수 규칙

- Verse는 장면 중심
- Chorus는 메시지 중심
- Verse 2는 반드시 전진
- Bridge는 반드시 관점 전환
- Final chorus는 반드시 새 이미지 + 새 결정

### 평가기 필수 감점

- Verse 2 반복
- Bridge 무의미
- Hook가 title과 느슨함
- 장면 없이 추상어만 반복
- 강세/음절 흐름 어색
- final chorus가 chorus 1의 paraphrase

## 참고 소스

- Berklee Online, `Lyric Writing: Tools and Strategies`
  - idea generation, word choice, rhyme, rhythm, structure, prosody
  - [https://online.berklee.edu/courses/lyric-writing-tools-and-strategies](https://online.berklee.edu/courses/lyric-writing-tools-and-strategies)
- Berklee Online, `How to Write a Song Using Imagery`
  - verse는 작은 순간, chorus는 큰 메시지
  - [https://online.berklee.edu/takenote/how-to-write-a-song-using-imagery-a-video-tutorial-with-andrea-stolpe/](https://online.berklee.edu/takenote/how-to-write-a-song-using-imagery-a-video-tutorial-with-andrea-stolpe/)
- Berklee Online, `How to Write Killer Song Hooks`
  - 훅의 위치, 반복, 대비
  - [https://online.berklee.edu/takenote/how-to-write-songs-with-killer-hooks/](https://online.berklee.edu/takenote/how-to-write-songs-with-killer-hooks/)
- Berklee Online, `Simple Tools for Writing from the Title`
  - 제목에서 출발, verse 2 recoloration
  - [https://online.berklee.edu/takenote/simple-tools-for-writing-from-the-title/](https://online.berklee.edu/takenote/simple-tools-for-writing-from-the-title/)
- Berklee Online, `How to Write a Bridge to a Song`
  - bridge의 contrast, moral, what now
  - [https://online.berklee.edu/takenote/writing-bridges-for-your-songs-can-be-much-easier/](https://online.berklee.edu/takenote/writing-bridges-for-your-songs-can-be-much-easier/)
- Berklee Online, `Lyric Writing Roadblocks and How to Overcome Them`
  - 제목의 power positions, verse는 sensory detail, chorus는 summary
  - [https://online.berklee.edu/takenote/common-lyric-writing-roadblocks-and-ways-to-overcome-them/](https://online.berklee.edu/takenote/common-lyric-writing-roadblocks-and-ways-to-overcome-them/)
- Berklee Online, `Prosody in Music and Songwriting`
  - 모든 요소가 하나의 감정/목적을 향해 정렬되어야 함
  - [https://online.berklee.edu/takenote/prosody-in-music-and-songwriting/](https://online.berklee.edu/takenote/prosody-in-music-and-songwriting/)
- Berklee Online, `Songwriting Tools and Techniques`
  - lyrics, melody, harmony를 prosody로 정렬
  - [https://online.berklee.edu/courses/songwriting-tools-and-techniques](https://online.berklee.edu/courses/songwriting-tools-and-techniques)
- NSAI, `Anatomy of a Great Lyric`
  - 구조는 곡이 요구하는 바에 맞게, bridge는 꼭 의미 있게
  - [https://www.nashvillesongwriters.com/anatomy-great-lyric](https://www.nashvillesongwriters.com/anatomy-great-lyric)
- Country Music Hall of Fame, `Words & Music`
  - lyric writing 교육용 구조 자료
  - [https://www.countrymusichalloffame.org/learn/teacher-resource-portal/language-arts/words-and-music](https://www.countrymusichalloffame.org/learn/teacher-resource-portal/language-arts/words-and-music)
