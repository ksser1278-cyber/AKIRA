# AKIRA

## 목적

AKIRA는 음악 생성 / 평가 / 선별 파이프라인 프로젝트입니다.

## Canonical Structure

- `src/akira_engine/`: 핵심 런타임 및 엔진 로직
- `scripts/songwriter/`: 일반 실행용 CLI 진입점
- `scripts/production/`: 배치 / 운영 실행 스크립트
- `docs/`: 설계 및 운영 문서
- `prompts/`: 프롬프트 자산
- `data/<artist>/reference_tracks/`: 아티스트별 참조 트랙 데이터
- `outputs/`, `artifacts/`, `bundles/`, `models/`, `logs/`: 생성 산출물 및 대용량 자산 (Git 추적 제외)

## Primary CLI Entry Point

기본 실행 진입점은 `scripts/songwriter/run_demo_songwriter.py` 입니다.

```bash
python scripts/songwriter/run_demo_songwriter.py --artist-id pinocchiop
```

## Production Workflows

### RC-20 Pilot

```bash
python scripts/production/run_rc20_pilot.py
```

### Elite 100 Bundle

```bash
python scripts/production/generate_elite_100.py
```

## Configuration

API 키는 환경 변수 또는 `config/.env`에서 로드합니다.

예:

* `OPENAI_API_KEY`
* `GEMINI_API_KEY`

## Dependency Management

```bash
pip install -r requirements.txt
```

## Git Tracking Policy

다음 항목은 GitHub에 올리지 않습니다.

* `outputs/`
* `artifacts/`
* `bundles/`
* `models/`
* `logs/`
* 기타 생성 산출물 / 캐시 / 대용량 자산

참조용 소형 데이터는 추적할 수 있지만, 대용량 원천 데이터와 중간 산출물은 제외합니다.

## 검토 포인트

* 구조 분리
* 평가 로직 정확성
* 운영 안정성
