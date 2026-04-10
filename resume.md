# Resume — 법무법인 진주 오케스트레이터

**최종 업데이트:** 2026-04-10 (세션 4)
**상태:** ✅ Phase 1 E2E 통과 + git initial commit 완료. Phase 2 (나머지 7 에이전트 라우팅 + 멀티라운드 토론) 진입 준비.

---

## 0. 빠른 재개 (다음 세션에서)

```bash
# 1. 환경변수 설정 (매 쉘 세션마다 필요 — .env 자동 로드 X)
export LAW_OC=kipeum86

# 2. 프로젝트 디렉토리로
cd "/Users/kpsfamily/코딩 프로젝트/legal-agent-orchestrator"

# 3. 확인
echo $LAW_OC   # kipeum86 출력되어야 함

# 4. Claude Code 시작
claude
```

Claude Code 시작 후:
1. **MCP 확인**: `mcp__korean-law__*` tools 보이면 성공
2. **git 상태 확인**: `git log --oneline` (초기 커밋 `f4a5582` 이후 작업)
3. **다음 작업**: 아래 "다음 할 일" 섹션 — Phase 2 route-case.md 확장부터

---

## 1. 프로젝트 개요

**한 줄 정의**: Claude Code 위에 돌아가는 멀티 에이전트 로펌 오케스트레이터. 10명의 전문 법률 AI 에이전트가 실제 로펌처럼 협업해서 법률 의견서를 생성.

**핵심 원칙**: 기존 에이전트를 100% 그대로 재활용. 웹 프레임워크로 감싸면 기능이 50-60%로 깎이므로, 반대로 Claude Code를 런타임으로 사용하고 Agent tool로 서브에이전트를 디스패치.

**킬러 피처**: 멀티라운드 토론 (Pattern 3). 서로 다른 관할권의 전문 에이전트들이 의견 → 반론 → 재반론으로 논쟁하고, 파트너가 최종 판단. 단일 LLM 호출로는 절대 불가능한 깊이.

**차별화**: Harvey AI는 블랙박스, 이 프로젝트는 완전 투명. 어느 변호사가 배정됐는지, 어떤 소스(Grade A/B/C)를 참조했는지, 논쟁이 어떻게 진행됐는지 전부 events.jsonl에 기록되고 Case Replay로 재생 가능.

---

## 2. 개발 진행 상황

### ✅ 완료

| Phase | 상태 | 내용 |
|-------|------|------|
| /office-hours | 9/10 승인 | 디자인 문서 (6라운드 adversarial review) |
| /plan-eng-review | CLEAR | 8개 이슈 발견/해결 |
| Phase 0 기술 스파이크 | 6/8 통과 | Agent tool 검증 |
| Phase 1 파일 작성 | 완료 | CLAUDE.md, 3 skills, setup.sh, .mcp.json |
| 스타일 가이드 정본 | 완료 | docs/ko-legal-opinion-style-guide.md |
| scripts/md-to-docx.py | 완료 | 스타일 가이드 §11 구현, opinion.docx 생성 |
| **Phase 1 E2E 테스트** | ✅ **PASSED** | 확률형 아이템 의견서, 47 events, 33 sources (29A/4B), revision cycle 1 완료 |
| **git initial commit** | ✅ `f4a5582` | 15 files, 3016 insertions |
| 10개 에이전트 GitHub public | 확인됨 | setup.sh로 자동 클론 가능 |

### ⏸️ 대기 중 (Phase 2 — 지금 시작 가능)

| 항목 | 선행 조건 |
|------|-----------|
| **route-case.md 확장** (7 에이전트 라우팅 트리) | ★ Phase 2 진입점 — 없음 |
| manage-debate.md 실제 로직 | route-case 확장 |
| 멀티라운드 토론 E2E 테스트 (킬러 피처 증명) | 위 두 개 완료 |
| Case Replay MVP (Next.js 뷰어) | 독립 트랙, 지금도 가능 (샘플 데이터: case `20260410-012238-391f`) |
| README 작성 | 독립 트랙, docs/notes/architecture-defense.md 원재료 |
| 퀄리티 비교 (오케스트레이터 vs 직접) | 비교 기준 정의 필요 |

---

## 3. Phase 0 기술 스파이크 결과

| # | 체크리스트 | 결과 | 비고 |
|---|-----------|------|------|
| 1 | CLAUDE.md 자동 로드 | ✅ PASS | 에이전트 identity 확인 |
| 2 | Skills 인식 | ✅ PASS | 22개 스킬 디렉토리 접근 |
| 3 | MCP 서버 상속 | ⚠️ FAIL → RESOLVED | 루트 .mcp.json으로 우회 |
| 4 | KB 파일 탐색 | ✅ PASS | library/ 구조 + 파일 읽기 |
| 5 | 결과 반환 | ✅ PASS | 서브에이전트 → 오케스트레이터 |
| 6 | 중첩 서브에이전트 | ❌ FAIL | Agent tool 미제공, 영향 낮음 |
| 7 | 파일 기반 출력 계약 | ✅ PASS | 절대 경로로 파일 쓰기 성공 |
| 8 | 병렬 실행 | ✅ PASS | 2개 동시 디스패치 성공 |

**실패 항목 영향:**
- **#3**: 해결됨. 루트 `.mcp.json`에 korean-law + kordoc 설정. 세션 재시작 시 적용.
- **#6**: 영향 낮음. general-legal-research의 deep-researcher, second-review-agent의 citation-verifier만 비활성. 오케스트레이터가 단일 관할권 리서치로 지시하면 우회 가능.

**Verdict**: GO — Phase 1 진입 가능

---

## 4. 현재 파일 구조

```
legal-agent-orchestrator/
├── CLAUDE.md                    ← 오케스트레이터 시스템 프롬프트 (완성)
├── resume.md                    ← 이 파일
├── skills/
│   ├── route-case.md            ← 질문 분류 + 파이프라인 실행 (완성)
│   ├── deliver-output.md        ← 결과물 어셈블리 (완성)
│   └── manage-debate.md         ← Phase 2 skeleton
├── setup.sh                     ← 에이전트 관리 (clone/link/status)
├── .mcp.json                    ← korean-law + kordoc MCP
├── .env                         ← LAW_OC=kipeum86 (gitignored)
├── .env.example                 ← 키 없이 구조만
├── .gitignore                   ← agents/, output/, .env
├── scripts/
│   └── md-to-docx.py            ← (확인 필요 - 언제 추가됐는지)
├── agents/                      ← 10개 에이전트 심볼릭 링크 (개발용)
│   ├── general-legal-research → /Users/kpsfamily/코딩 프로젝트/general-legal-research
│   ├── legal-writing-agent → ...
│   ├── second-review-agent → ...
│   ├── GDPR-expert → ...
│   ├── PIPA-expert → ...
│   ├── game-legal-research → ...
│   ├── contract-review-agent → ...
│   ├── legal-translation-agent → ...
│   ├── game-legal-briefing → ...
│   └── game-policy-briefing → ...
├── output/                      ← 케이스 결과물
│   └── spike-20260406-230405/   ← Phase 0 스파이크 테스트 결과
└── docs/
    ├── design.md                ← 디자인 문서 (APPROVED 9/10)
    ├── session-log-20260402.md  ← office-hours 세션 로그
    ├── ko-legal-opinion-style-guide.md  ← 한국어 의견서 스타일 정본
    └── notes/
        └── architecture-defense.md  ← README 원재료
```

---

## 5. 주요 아키텍처 결정

### 디자인 대비 변경사항 (엔지니어링 리뷰 반영)

1. **스킬 5개 → 3개 통합**: emit-events는 CLAUDE.md 인라인, route-case + compose-pipeline 통합
2. **파일 기반 출력 계약**: 서브에이전트가 `{case-id}/{agent-id}-meta.json`에 JSON 저장 (응답 내 JSON 대신)
3. **절대 경로**: 서브에이전트 프롬프트에 output 디렉토리 절대 경로 주입
4. **case-id**: CLAUDE.md 워크플로우 1단계에서 Bash로 생성
5. **파일 존재 확인**: 서브에이전트 반환 후 meta.json 존재 체크 → 없으면 응답 텍스트 직접 파싱 (fallback)
6. **MCP 해결**: 오케스트레이터 루트 .mcp.json (korean-law + kordoc). 서브에이전트는 부모 세션 MCP 상속.
7. **스타일 가이드 강제**: CLAUDE.md + route-case.md에서 한국어 에이전트 호출 시 정본 절대 경로 주입
8. **Claude Code Max 구독**: 추가 API 비용 없음
9. **Meta-verification fallback (E2E에서 발견)**: 서브에이전트가 토큰 한도 도달해 재호출 불가할 때, 오케스트레이터가 직접 MCP (`mcp__korean-law__get_law_text`)로 verbatim 대조. `evt_045` type=`verbatim_verified`, data.verifier=`orchestrator_meta`. revision cycle이 살아남게 해준 핵심 패턴. Phase 2 manage-debate.md 설계에 반영 필요 (토론 중 한쪽 에이전트 실패 시 fallback 경로).

### 에이전트 협업 패턴

- **Pattern 1**: 독립 리서치 → 통합 (병렬) — `[A ∥ B] → writing → review`
- **Pattern 2**: 순차 핸드오프 — `A → B → writing → review` (Phase 1 기본)
- **Pattern 3**: 멀티라운드 토론 — `A 의견 → B 반론 → A 재반론 → writing verdict → review`

---

## 6. 대화 히스토리 요약

### 세션 1 (2026-04-02)
- `/office-hours` Builder mode로 프로젝트 디자인
- 핵심 피봇: Agent SDK 웹서비스 → Claude Code 네이티브
- 킬러 피처 발견: 멀티라운드 토론 (Pattern 3)
- 디자인 문서 APPROVED 9/10 (6라운드 adversarial review)

### 세션 2 (2026-04-03 ~ 04-06)
- `/plan-eng-review`로 엔지니어링 리뷰 (8개 이슈 발견/해결)
- 주요 결정:
  - 스킬 5 → 3개 통합
  - 파일 기반 출력 계약
  - Claude Code Max 구독 확인 (비용 걱정 해소)
- Phase 0 기술 스파이크 실행 (6/8 통과)
- Phase 1 파일 전부 작성

### 세션 3 (2026-04-07 ~ 04-10)
- 체크포인트 저장 → 세션 재시작 → MCP 여전히 미연결 발견
- 아키텍처 정당성 논의 → `docs/notes/architecture-defense.md` 기록
- 스타일 가이드 정본 복사 + 강제 주입 로직 추가
- 심볼릭 링크 vs GitHub 배포 설명
- 개발자 친구에게 설명하는 법 논의
- resume.md v1 작성

### 세션 4 (2026-04-10, 현재 세션)
- MCP 연결 확인 (`mcp__korean-law__*` deferred tools 가용)
- **Phase 1 E2E 테스트 실행 및 통과**:
  - 질문: "한국 게임산업법의 확률형 아이템(가챠) 규제에 대한 법률 의견서"
  - 파이프라인: general-legal-research → legal-writing-agent → second-review-agent → revision cycle 1
  - 산출물: [opinion.docx](output/20260410-012238-391f/opinion.docx), [opinion.md](output/20260410-012238-391f/opinion.md), [events.jsonl](output/20260410-012238-391f/events.jsonl) (47 events), [sources.json](output/20260410-012238-391f/sources.json) (33 sources 29A/4B)
- **새 패턴 발견**: legal-writing-agent rate_limit → 오케스트레이터 meta-verification (evt_045, [verbatim-verification.md](output/20260410-012238-391f/verbatim-verification.md))
- **scripts/md-to-docx.py 작성**: 스타일 가이드 §11 구현 (Times New Roman + 맑은 고딕 이중 폰트, A4, 인용 블록 테이블)
- **git initial commit**: `f4a5582` (15 files, 3016 insertions)
- resume.md v2 업데이트 (이 버전)
- 다음: Phase 2 진입 — route-case.md 확장부터

---

## 7. 다음 할 일 (우선순위)

### ★ Phase 2 진입점 — route-case.md 확장

현재 `skills/route-case.md`는 Phase 1 파이프라인(research → writing → review)만 처리. 나머지 7 에이전트와 **언제 어떤 조합으로** 호출할지 결정 트리/분류 로직 필요.

**설계 필요 사항:**
1. **분류 차원** — 관할권(KR/EU/US/국제), 도메인(개인정보/게임/계약/번역/뉴스), 작업 유형(리서치/드래프팅/검토/번역/브리핑), 복잡도(단순/복합/다관할권 토론)
2. **트리거 조건** — 언제 Pattern 1(병렬) vs Pattern 2(순차) vs Pattern 3(토론)?
3. **에이전트 매핑 표** — 10 에이전트의 (관할권 × 도메인 × 작업) 커버리지 매트릭스
4. **Compound 질문 처리** — 1개 질문이 여러 전문가 필요한 경우 분해 로직 (예: "EU 게임사가 한국 이용자 데이터 처리" → GDPR + PIPA + game-legal-research 병렬/토론)
5. **토론 트리거 명시** — 어떤 조합이 Pattern 3 토론으로 가야 하는가 (의견 충돌 가능성 있는 다관할권 질문 예시)

**접근 방법 브레인스토밍 필요:**
- 결정 트리 (하드코딩 if/else)
- 키워드 매칭 (JSON 매핑)
- LLM intent classification (오케스트레이터가 자체 판단)
- 하이브리드 (키워드로 후보 추림 → LLM로 최종 결정)

→ `/brainstorming` 스킬로 설계 세션 권장.

### Phase 2 후속 (route-case 확장 완료 후)

1. **`skills/manage-debate.md` 실제 로직** — skeleton에서 실제 구현으로.
   - 토론 라운드 스케줄링 (의견 → 반론 → 재반론 → verdict)
   - 각 라운드 이벤트 로깅 (`debate_round_start`, `debate_opinion`, `debate_rebuttal`, `debate_verdict`)
   - **Meta-verification fallback 통합** (세션 4 발견 패턴) — 토론 중 한쪽이 토큰 한도 도달 시 오케스트레이터가 MCP로 직접 증거 대조해 해당 라운드 대체
   - writing-agent가 verdict 드래프트, second-review가 최종 승인
2. **멀티라운드 토론 E2E** — 실제 킬러 피처 증명. 후보 시나리오: "EU에 서버 둔 한국 게임사가 한국 이용자 개인정보를 EU로 국외이전할 때 법적 쟁점" (GDPR-expert ↔ PIPA-expert ↔ game-legal-research 3자 토론)
3. **3개 프리로드 데모 케이스 녹화** — 리플레이 뷰어용

### Phase 3 — Case Replay (Next.js 정적 뷰어)

- 이벤트 스키마 확정됨 (47 events 샘플 존재: case `20260410-012238-391f`)
- 타임라인 + 이벤트 카드 + 소스 Grade A/B/C/D 컬러 코딩
- 다크 테마 워룸 UI
- GitHub Pages/Vercel 배포
- 독립 트랙 — Phase 2와 병렬 진행 가능

### 독립 트랙 (언제든 가능)

- **README 작성** — [docs/notes/architecture-defense.md](docs/notes/architecture-defense.md)의 킬러 포인트 4개 활용
- **퀄리티 비교 테스트** — 오케스트레이터 경유 vs 에이전트 직접 실행 (평가 기준 정의 필요)

---

## 8. 알려진 이슈 / 확인 필요

- [x] ~~**scripts/md-to-docx.py** — 언제, 왜 추가됐는지 확인 필요~~ → 세션 4에서 확인: 스타일 가이드 §11 구현, E2E 중 opinion.docx 생성용. 정당한 추가.
- [ ] **LAW_OC 환경변수** — Claude Code가 .env를 자동 로드하지 않음 확정. 쉘에서 매번 `export LAW_OC=kipeum86` 필요. 해결안: direnv 도입 또는 Claude Code 세션 시작 스크립트.
- [ ] **중첩 서브에이전트 비활성**: general-legal-research의 deep-researcher, second-review-agent의 citation-verifier가 오케스트레이터 경유 시 동작 안 함. E2E에서 영향 정도 측정 필요 (쇠약화 여부). 영향이 크면 Phase 2에서 우회 로직 설계.
- [ ] **Rate limit 견고성**: 세션 4 E2E에서 legal-writing-agent가 revision cycle 1 중 `Anthropic usage limit hit`. 오케스트레이터 meta-verification fallback이 구해줬지만, 이건 임시방편. Phase 2에서 rate_limit에 대한 공식 재시도/대기/fallback 정책 설계 필요.
- [ ] **10개 에이전트 GitHub public 재확인** — 배포 직전
- [ ] **각 에이전트 라이선스** — knowledge/ 디렉토리 재배포 가능 여부

---

## 9. README 킬러 포인트 (docs/notes/architecture-defense.md에서)

1. **컨텍스트 격리의 오해** — "꾸겨 넣는 게 아니라 가장 context-efficient한 멀티에이전트 구조"
2. **왜 LangGraph가 아닌가** — "기존 에이전트 100% 재활용 vs 50-60% 재현"
3. **투명성 vs Harvey 블랙박스** — "프로세스 자체가 프로덕트"
4. **Case Replay** — "30초 데모가 아닌 영속적 아티팩트"

---

## 10. 핵심 레퍼런스

| 파일 | 설명 |
|------|------|
| [docs/design.md](docs/design.md) | 디자인 문서 (APPROVED 9/10) |
| [docs/session-log-20260402.md](docs/session-log-20260402.md) | office-hours 세션 로그 |
| [docs/ko-legal-opinion-style-guide.md](docs/ko-legal-opinion-style-guide.md) | 한국어 의견서 스타일 정본 |
| [docs/notes/architecture-defense.md](docs/notes/architecture-defense.md) | README 원재료 |
| [~/.claude/plans/squishy-drifting-mango.md](/Users/kpsfamily/.claude/plans/squishy-drifting-mango.md) | 엔지니어링 리뷰 플랜 |
| [~/.gstack/projects/legal-agent-orchestrator/checkpoints/](/Users/kpsfamily/.gstack/projects/legal-agent-orchestrator/checkpoints/) | gstack 체크포인트 |

---

## 11. 컨텍스트 주요 사항

- **사용자**: Claude Code Max 구독 ($100/월), 별도 API 키 사용 안 함
- **LAW_OC**: `kipeum86` (Open Law API 키, .env에 저장, gitignored)
- **개발 환경**: macOS, darwin 25.3.0, zsh
- **선호**: 한국어 대화, 직설적 피드백, 타협보다 통합, 결과물 퀄리티 > 시각적 임팩트
- **의사결정 스타일**: 약점을 직감으로 포착하는 질문으로 아키텍처를 뒤집음 (예: "유저가 기존 에이전트를 다운받게 하는 방식은?")
