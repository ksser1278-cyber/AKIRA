# Claude Code Architecture & Workflow (LLM-Wiki Synthesis)

## 📌 개요 (Overview)
본 문서는 Anthropic의 **Claude Code** 터미널 에이전트 아키텍처와 이를 응용한 **claw-code-main** (오픈소스 포팅 및 멀티에이전트 프레임워크)의 코드베이스에서 추출한 설계 철학과 구조적 통찰을 정리한 지식 베이스입니다.

![Claude Code Overview](https://wikidocs.net/images/page/338204/claude_code.png)

---

## 🧭 구조와 기술 스택 (Tech Stack & Structure)
Claude Code의 기반 스택은 성능과 터미널 최적화에 중점을 둡니다.

- **코어 엔진:** TypeScript (Node.js/Bun)
- **TUI (터미널 UI):** `Ink` (React 기반의 컴포넌트형 터미널 렌더러) - 이중 버퍼링과 더티 트래킹(Dirty Tracking)을 통해 고성능 UI 출력 보장.
- **상태 관리:** `Zustand` (Immutable 글로벌 상태 관리)
- **빌드 및 최적화:** Bun 트리 쉐이킹(Tree-shaking) 및 `main.tsx` 단일 파일 압축 (가동 시 디스크 I/O를 최소화하기 위함)

---

## 🔄 4단계 핵심 파이프라인 (Execution Phases)
Claude Code의 동작은 4단계의 고정된 파이프라인을 순환합니다.

1. **STARTUP (초기화):** 인증, Git 상태 프리페치, 프로젝트 내 `CLAUDE.md` 파싱 등 기본 컨텍스트 주입.
2. **QUERY LOOP (엔진 코어):** `query.ts`가 비동기 제너레이터로 동작하며 Claude API 스트리밍 수신. `tool_use` 발생 시 인터럽트 및 툴 파이프라인으로 전환.
3. **TOOL EXECUTION (도구 계층):** 45+ 개의 툴 실행 루틴 (10단계의 방어적 설계 적용).
4. **DISPLAY (렌더링):** 결과를 Ink 컴포넌트로 터미널 화면에 반영.

---

## 🛡️ 방어적 도구 설계 (Defensive Tool Execution)
도구를 실행할 때 단순히 `exec()`를 콜하지 않고 10단계 파이프라인을 거칩니다.

- **입력 검증:** Zod 스키마를 활용한 입력값 유효성 검사
- **File Limits:** `MAX_READ_SIZE`, `MAX_WRITE_SIZE` 및 바이너리(NUL-byte) 탐지
- **권한 체계 (PermissionEnforcer):** 
  - Workspace 외부 파일 조작(Boundary Rules) 방어.
  - BashTool 구동 시 '읽기 전용' 모드 지원 (`readOnlyValidation`, `destructiveCommandWarning`).

---

## 🤖 멀티에이전트 워크플로우 통찰 (from Claw Code)
클로드 코드를 리버스 엔지니어링한 오픈소스 커뮤니티(`claw-code-main` / `oh-my-openagent` 등)의 주요 발전 철학은 다음과 같습니다.

### 1. 컨텍스트의 탈출 (Out-of-band Monitoring)
- **원리:** 코드 에이전트의 프롬프트(Context Window)는 매우 비쌉니다. 상태 알림, Git 로그 출력, 텔레메트리 덤프 등은 에이전트가 직접 처리하지 않고 백그라운드 이벤트 라우터(`clawhip`)가 처리합니다. 
- **효과:** 모델은 코딩(문제 해결)에만 온전히 집중하여 추론 성능 극대화.

### 2. 다중 에이전트 논쟁 (Multi-Agent Conflict Resolution)
- **구조:** 단일 에이전트가 코드를 완성하는 것이 아니라 리더(Coordinator) 하에 '작성자(Executor)'와 '검토자(Reviewer)'를 두고 코드를 종합합니다.
- **수렴 과정:** 두 에이전트 간 논리가 충돌(Conflict)할 시, 시스템이 충돌을 무시하거나 세션을 종료하는 것이 아니라, 수렴(Convergence)을 위한 재토론 단계로 유도합니다.

### 3. 상태 기반 런타임 (Registries)
- **TaskRegistry & CronRegistry:** 터미널 프로세스임에도 휘발성 프레임워크가 아닌 in-memory 레지스트리를 유지하여 백그라운드 태스크나 지속적 주기 작업을 가능케 합니다.
- MCP (Model Context Protocol) 툴 연동 시에도 `McpToolRegistry`를 거쳐 원격 자원과 로컬을 동기화합니다.
