# Office Hours Session Log — 2026-04-02

## Session Overview

- **프로젝트**: legal-agent-orchestrator (법무법인 진주 오케스트레이터)
- **스킬**: /office-hours (Builder mode)
- **시작**: 2026-04-01 ~23:00 KST
- **종료**: 2026-04-02 ~03:00 KST
- **결과**: 디자인 문서 APPROVED (9/10, 6라운드 adversarial review)

---

## Phase 1: Context Gathering

### 기존 에이전트 인벤토리 탐색
두 개의 Explore 서브에이전트를 병렬 디스패치하여 기존 법률 AI 에이전트 파악:

**발견된 에이전트 (10개):**

| # | Agent | 담당 변호사 | 핵심 역할 |
|---|-------|------------|----------|
| 1 | general-legal-research | 김재식 | 범용 법률 리서치, Korean Law MCP 64 tools |
| 2 | legal-writing-agent | 한석봉 | 법률문서 작성/수정 |
| 3 | second-review-agent | 반성문 (파트너) | 품질 검토, 최종 승인 |
| 4 | GDPR-expert | 김덕배 | EU 데이터보호법, 1060 KB |
| 5 | PIPA-expert | 정보호 | 한국 개인정보보호법, 929 법률 파일 |
| 6 | game-legal-research | 심진주 | 게임산업 국제법, 17+ 관할권 |
| 7 | contract-review-agent | 고덕수 | 계약서 검토 |
| 8 | legal-translation-agent | 변혁기 | 5개 언어 법률 번역 |
| 9 | game-legal-briefing | 심진주 | 게임규제 뉴스 모니터링 |
| 10 | game-policy-briefing | 심진주 | 게임정책 브리핑 |

**유틸리티**: parlawatch (국회 모니터링)

**공통 기술 스택**: Claude Code, 구조화된 RAG (Markdown + YAML frontmatter), 소스 그레이딩 (A/B/C/D), 팩트체커 서브에이전트

---

## Phase 2B: Builder Mode — 핵심 질문

### Q1: 프로젝트 목표
- **선택**: 포트폴리오 / 오픈소스 → Builder mode

### Q2: 핵심 경험
- **질문**: "이걸 보여줬을 때 '와' 하고 반응할 포인트는?"
- **답변**: "다 섞어서" — 채팅 인터페이스 + 에이전트 협업 시각화 + 로펌 시뮬레이션 전부 통합
- **인사이트**: 타협보다 통합을 선호하는 사고방식

### Q3: 타겟 오디언스
- **선택**: AI/법률 커뮤니티

### Q4: 차별화
- **선택**: 멀티 에이전트 협업 + 오픈소스 투명성
- **인사이트**: Harvey AI의 정반대 포지셔닝. 블랙박스 vs 투명성.

### Q5: 기술 스택
- **선택**: 아직 미정 → 함께 고민

---

## Phase 2.75: Landscape Awareness

3개 웹 검색 실행:
1. "multi-agent orchestration pattern web UI 2026"
2. "legal AI multi-agent collaboration open source 2026"
3. "Claude Agent SDK multi-agent orchestration web service"

### 3-Layer 분석:
- **Layer 1 (누구나 아는 것)**: 오케스트레이터-워커 패턴이 표준. CrewAI, LangGraph 성숙.
- **Layer 2 (지금 뜨는 것)**: Claude Agent SDK가 서브에이전트, HTTP/WS 지원. AG-UI 프로토콜. 2026 = "Legal AI 에이전트의 해."
- **Layer 3 (우리만의 인사이트)**: 기존 10개 전문 에이전트가 이미 검증된 상태로 존재. 대부분의 프로젝트는 에이전트를 처음부터 만드는데, 여기는 조율 레이어만 추가하면 됨.

---

## Phase 3: Premise Challenge

4가지 전제 확인 → 사용자 전부 동의:
1. 기존 에이전트 재작성 금지
2. 웹 프론트엔드가 핵심 가치
3. 실시간 스트리밍 필요
4. Claude Agent SDK가 최적 기술

---

## Phase 3.5: Cross-Model Second Opinion

Codex 미설치 → Claude 서브에이전트로 독립 평가 실행

### 핵심 결과:
- **"Case Replay"**: 처리된 케이스를 정적 JSON + 뷰어로 리플레이하는 공유 가능 아티팩트 제안. 라이브 데모는 30초짜리지만 리플레이는 영속 콘텐츠.
- **50% 있는 도구**: AG-UI + CopilotKit
- **주말 프로토타입**: 3개 에이전트(research → writing → review)만으로 MVP

→ Case Replay 아이디어 채택.

---

## Phase 4: Approaches

### 제안된 접근 방식:
- **A: 풀 시뮬레이션** (Next.js + Agent SDK) — Effort: L, Risk: Med
- **B: 스마트 라우터** (최소 구현) — Effort: M, Risk: Low  
- **C: 로펌 라이브 대시보드** (시각화 특화) — Effort: XL, Risk: High

### 사용자 선택: A+C 하이브리드

---

## 핵심 전환점 — 아키텍처 피봇

### 사용자 질문 1: "유저가 기존 에이전트를 다운받게 하는 방식은?"

이 질문이 전체 아키텍처를 뒤집었다.

**분석 결과**: Agent SDK 웹서비스로 래핑하면 각 에이전트 기능의 50-60%만 재현. MCP 통합 불확실, 스킬 시스템 재구현 필요, KB 탐색 방식 변경. 법률 의견서 퀄리티가 원본의 절반 수준으로 하락.

**반면 Claude Code 네이티브**:
- 에이전트 100% 원본 그대로 작동
- 모든 스킬, MCP, KB, 팩트체커 완전 동작
- 실제 법률 전문가가 쓸 수 있는 결과물

### 사용자 결정: "결과물 퀄리티 포기하면서 가는것은 전혀 의미 없음"

→ **아키텍처 전면 재설계: Agent SDK 웹서비스 → Claude Code 네이티브 + Case Replay**

### 사용자 질문 2: "폴더 구조를 오케스트레이터를 루트로, 기존 에이전트를 하위 폴더로"

→ 모노레포 구조 결정

### 사용자 질문 3: "git submodule은 수동 업데이트 필요?"

→ git submodule 대신 setup.sh 스크립트 방식 결정

### 사용자 질문 4: "여러 변호사한테 업무 지시...GDPR-expert, PIPA-expert가 논의해서 verdict 가져오라는 식으로"

→ **킬러 피처 발견: 멀티라운드 토론 (Pattern 3)**
- 에이전트 간 법률 논쟁 (의견 → 반론 → 재반론)
- 실제 로펌의 파트너 토론 과정 재현
- Harvey AI가 절대 할 수 없는 것

---

## 최종 아키텍처

```
legal-agent-orchestrator/
├── CLAUDE.md                  ← 오케스트레이터
├── skills/ (5개)               ← route-case, compose-pipeline, manage-debate, emit-events, deliver-output
├── setup.sh                   ← 에이전트 자동 클론/업데이트
├── agents/ (10개)              ← 기존 에이전트 (setup.sh로 관리)
├── case-replay/               ← 포트폴리오 시각화 (Next.js 정적)
├── output/                    ← 케이스 결과물 + events.jsonl
└── README.md
```

### 3가지 협업 패턴:
1. **독립 리서치 → 통합**: 다른 관할권에서 독립 분석 → legal-writing이 통합
2. **순차 핸드오프**: A의 결과를 B가 참조하여 추가 분석
3. **멀티라운드 토론**: A가 의견 → B가 반론 → A가 재반론 → writing이 verdict

---

## Spec Review History

| Round | Score | 핵심 이슈 | 수정 내용 |
|-------|-------|---------|---------|
| 1 | 5/10 | 에이전트 목록 누락, 라우팅 로직 부재, 에러 처리 없음 | 에이전트 인벤토리, 라우팅 트리, 에러 처리 추가 |
| 2 | 7/10 | 토큰 예산 부재, 시크릿 관리, 비용 추정, 테스트 전략 | Token Budget, Secrets, Testing 섹션 추가 |
| 3 | 7/10 (이슈 성격 변화) | Phase 0 acceptance criteria 불명확, 타임아웃 근거 없음, 이벤트 스키마 비정형 | Phase 0 체크리스트, 타임아웃 P95 기반, 이벤트 테이블 정형화 |
| 4 | 6.5/10 (더 엄격) | Agent Output Contract 부재, 이벤트 기록 메커니즘 미정의, Fallback C가 전제 위반, Agent tool 미정의 | Output Contract, Handoff Protocol, Event Emission, Agent tool 정의, Fallback 열화 매트릭스 추가 |
| 5 | 8/10 | 재시도 정책, sources.json 스키마, 라우팅 분류 방식, Pattern 1 vs 3 구분 기준 | Retry Policy, sources.json 스키마, few-shot 분류 접근, 토론 트리거 키워드 |
| 6 | **9/10** | 모든 차원 PASS. 나머지 1점은 Phase 0 기술 불확실성 (문서가 아닌 현실의 한계). | — |

---

## 핵심 결정 사항

| 결정 | 선택 | 이유 |
|------|------|------|
| 실행 환경 | Claude Code 네이티브 | 에이전트 100% 재활용, 퀄리티 최우선 |
| 시각화 | Case Replay (정적 뷰어) | 실행과 시각화 디커플링, API 비용 없이 포트폴리오 |
| 에이전트 관리 | setup.sh | git submodule 대비 유지보수 단순화 |
| 서브에이전트 호출 | Agent tool (Phase 0 검증) | 기존 에이전트 무변경 재활용 |
| 핵심 차별화 | 멀티라운드 토론 (Pattern 3) | Harvey가 할 수 없는 것, 실제 로펌 프로세스 재현 |
| 기본 실행 | 순차 | 병렬은 Phase 0에서 확인 후 최적화 |
| 모델 | Claude Sonnet 4.6 (기본) | 비용 효율, 사용자가 Opus 선택 가능 |

---

## Next Steps

1. **Phase 0 (1일)**: Agent tool 서브에이전트 호출 패턴 스파이크 (5개 체크리스트)
2. **Phase 1 (주말)**: 3-에이전트 MVP + setup.sh
3. **Phase 2 (1주)**: 풀 에이전트 + 멀티라운드 토론
4. **Phase 3 (1주)**: Case Replay 뷰어 + 배포

---

## Founder Signals Observed

- "결과물 퀄리티 포기하면서 가는것은 전혀 의미 없음" — 화려한 데모보다 실제 작동 우선
- "다 섞어서" — 타협보다 통합 선호
- "유저가 기존 에이전트를 다운받게 하는 방식이 낫지 않나?" — 아키텍처 약점을 직감으로 포착
- "여러 변호사한테 업무 지시...verdict 가져오라는 식으로" — 킬러 피처 직감적 발견
- 에이전트 10개를 먼저 깊게 만들고 오케스트레이터를 나중에 고민 — 깊이 우선 사고

---

## Files

- **디자인 문서**: `docs/design.md`
- **세션 로그**: `docs/session-log-20260402.md` (이 파일)
