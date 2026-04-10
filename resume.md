# Resume — 법무법인 진주 오케스트레이터

**최종 업데이트:** 2026-04-10
**상태:** Phase 1 파일 작성 완료, E2E 테스트 대기 (세션 재시작 필요)

---

## 0. 빠른 재개 (다음 세션에서)

```bash
# 1. 환경변수 설정
export LAW_OC=kipeum86

# 2. 프로젝트 디렉토리로
cd "/Users/kpsfamily/코딩 프로젝트/legal-agent-orchestrator"

# 3. 확인
echo $LAW_OC   # kipeum86 출력되어야 함

# 4. Claude Code 시작
claude
```

Claude Code 시작 후:
1. **MCP 확인**: "korean-law MCP tools 사용 가능?" → search_law 같은 tool이 보이면 성공
2. **체크포인트 복구**: `/checkpoint resume`
3. **첫 E2E 테스트**: 아래 "다음 할 일" 섹션 참조

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
| 10개 에이전트 GitHub public | 확인됨 | setup.sh로 자동 클론 가능 |

### ⏸️ 대기 중

| 항목 | 블로커 |
|------|--------|
| Phase 1 E2E 테스트 | 세션 재시작 필요 (MCP 연결) |
| git initial commit | E2E 테스트 성공 후 |
| Phase 2 (풀 에이전트 + 토론) | Phase 1 완료 후 |
| Phase 3 (Case Replay Next.js) | 이벤트 스키마 확정됨, 지금 시작 가능 |
| README | 지금 시작 가능 |

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

### 세션 3 (2026-04-07 ~ 04-10, 현재 세션)
- 체크포인트 저장 → 세션 재시작 → MCP 여전히 미연결 발견
- 아키텍처 정당성 논의 → `docs/notes/architecture-defense.md` 기록
- 스타일 가이드 정본 복사 + 강제 주입 로직 추가
- 심볼릭 링크 vs GitHub 배포 설명
- 개발자 친구에게 설명하는 법 논의
- 이 resume.md 작성

---

## 7. 다음 할 일 (우선순위)

### 즉시 (세션 재시작 후)

**A. Phase 1 E2E 테스트** (가장 중요)

테스트 질문:
```
법무법인 진주 오케스트레이터로 다음 질문을 처리해줘:
"한국 게임산업법의 확률형 아이템(가챠) 규제에 대한 법률 의견서를 작성해줘"

CLAUDE.md의 워크플로우를 따라 case-id를 생성하고,
route-case.md로 파이프라인을 결정하고,
Agent tool로 research → writing → review 순서로 호출해줘.
```

검증 포인트:
- [ ] case-id 생성됨
- [ ] output/{case-id}/events.jsonl 생성됨
- [ ] research-result.md + research-meta.json 생성됨
- [ ] opinion.md + writing-meta.json 생성됨 (한국어 스타일 가이드 준수)
- [ ] review-result.md + review-meta.json 생성됨
- [ ] sources.json 통합 생성됨
- [ ] 최종 events.jsonl에 전체 파이프라인 기록

### E2E 성공 후

1. **git initial commit** — 최초 커밋
2. **퀄리티 비교** — 오케스트레이터 경유 vs 에이전트 직접 실행

### 병렬 가능 (MCP 재시작 없이도 가능)

- **Case Replay MVP** (Next.js 정적 뷰어) — 이벤트 스키마 확정됨, 샘플 데이터로 진행 가능
- **README 작성** — docs/notes/architecture-defense.md의 킬러 포인트 4개 활용

### Phase 2 (Phase 1 E2E 성공 후)

- 나머지 7개 에이전트 라우팅 활성화
- `skills/manage-debate.md` skeleton → 실제 토론 로직
- 3개 프리로드 케이스 녹화

### Phase 3

- Next.js 리플레이 뷰어 MVP (타임라인 + 이벤트 카드 + 소스 그레이딩 컬러)
- 다크 테마 워룸 UI
- GitHub Pages/Vercel 배포
- README + 데모 GIF

---

## 8. 알려진 이슈 / 확인 필요

- [ ] **scripts/md-to-docx.py** — 언제, 왜 추가됐는지 확인 필요
- [ ] **LAW_OC 환경변수** — Claude Code가 .env를 자동 로드하는지 불확실. 쉘에서 export로 해결.
- [ ] **중첩 서브에이전트 비활성**: general-legal-research의 deep-researcher, second-review-agent의 citation-verifier가 오케스트레이터 경유 시 동작 안 함. E2E 테스트 시 퀄리티 영향 체크.
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
