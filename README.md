# AKIRA

## 목적

음악 생성/평가/선별 파이프라인 프로젝트

## 주요 구성

- src/: 핵심 엔진 코드
- scripts/: 실행 스크립트
- configs/: 설정 파일
- docs/: 설계 및 운영 문서
- prompts/: 생성 프롬프트 자산

## 실행 예시

python scripts/run_pipeline.py

## 제외 정책

outputs/, artifacts/, models/, logs/ 등 대용량 산출물은 GitHub에 올리지 않음

## 검토 요청 포인트

- 구조 분리
- 평가 로직 정확성
- 운영 안정성
