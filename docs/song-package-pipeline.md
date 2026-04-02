# Song Package Pipeline

`AKIRA ENGINE`의 최종 목표는 `스타일 분석 엔진` 자체가 아니라, `Suno에 바로 넣을 수 있는 song package(style prompt + lyric)`를 안정적으로 뽑는 것이다.

현재 권장 경로는 아래와 같다.

1. `planner`
- `full_song_brief`와 conditioning record를 바탕으로 song plan을 만든다.
- 내부 draft 후보를 여러 개 만들고 critic으로 고른다.

2. `external generator`
- planner가 만든 request bundle을 외부 생성 모델에 보낸다.
- 외부 모델은 실제 lyric 문장 생성에 집중한다.

3. `import + scoring`
- 외부 생성 결과를 markdown으로 정규화한다.
- 기존 critic으로 점수를 매긴다.

4. `suno bundle`
- score 기준을 통과한 결과만 style prompt와 함께 묶는다.

## 단일 진입점

아래 스크립트가 이 흐름을 한 번에 묶는다.

- [run_song_package_pipeline.py](C:\JPop_Songwriter\AKIRA ENGINE\scripts\songwriter\run_song_package_pipeline.py)

## 사용 예시

### 1. planner + request export만 실행

```powershell
python scripts\songwriter\run_song_package_pipeline.py `
  --source-jsonl datasets\experiments\ado\full_song_brief.jsonl `
  --track-id utaten_hw22011303 `
  --external-mode export-only
```

이 모드는 아래만 만든다.

- `planner_run/`
- `request_bundle/requests.jsonl`

외부 생성기는 이 `requests.jsonl`만 받으면 된다.

### 2. Gemini까지 포함한 roundtrip 실행

```powershell
python scripts\songwriter\run_song_package_pipeline.py `
  --source-jsonl datasets\experiments\ado\full_song_brief.jsonl `
  --track-id utaten_hw22011303 `
  --external-mode gemini `
  --min-score 85
```

이 모드는 아래까지 끝낸다.

- planner run
- Gemini request
- prediction import
- external scoring
- SUNO bundle export

### 3. 외부 예측 JSONL을 가져와서 score + bundle만 실행

```powershell
python scripts\songwriter\run_song_package_pipeline.py `
  --source-jsonl datasets\experiments\ado\full_song_brief.jsonl `
  --track-id utaten_hw22011303 `
  --external-mode import-jsonl `
  --predictions-jsonl outputs\custom_predictions.jsonl `
  --min-score 85
```

## 출력 구조

- `planner_run/`
  - 내부 planning 결과
- `request_bundle/`
  - 외부 모델에 줄 요청 JSONL
- `imported_predictions/`
  - 외부 예측을 정규화한 markdown
- `scoring/`
  - critic 결과와 점수 리포트
- `suno_bundle/`
  - style prompt + lyric 묶음

## 운영 원칙

- rule-based lyric renderer는 최종 가사 엔진으로 보지 않는다.
- planner / critic / reranker는 내부 엔진이 맡는다.
- 실제 lyric 문장 품질은 외부 생성 모델이 책임진다.
- benchmark는 anchor track matrix로 유지한다.

즉 현재 프로젝트의 본체는 `planner + critic`이고, song package는 그 위에 외부 생성기를 붙여 완성한다.
