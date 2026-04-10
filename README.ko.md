# 법무법인 진주 오케스트레이터 · Jinju Law Firm Orchestrator

**English:** [README.md](README.md)

> Claude Code 위에서 돌아가는 AI 로펌. 8명의 전문 변호사 에이전트가 실제 로펌처럼 협업해서 법률 의견서를 만든다.

**상태:** Phase 1 E2E 통과 (2026-04-10) · Phase 2.1/2.2 검증 완료 · Phase 2.3 (토론) + Case Replay 진행 중

---

## 개요

시중에 나와 있는 "법률 AI"는 대부분 질문 하나를 단일 LLM에게 던지는 구조다. 이 프로젝트는 다르다.

**오케스트레이터가 파트너 변호사 역할**을 맡아서, 들어오는 질문을 분류하고, 적합한 전문 변호사에게 배정하고, 그 사건에 맞는 협업 패턴(순차 핸드오프 / 병렬 리서치 / 멀티라운드 토론)을 직접 고른다. 8명의 하위 에이전트는 각자 다른 관할권(한국/EU)·도메인(개인정보/게임/계약/번역)·작업 유형(리서치/작성/검토)을 담당하는 진짜 Claude Code 에이전트이며, **이 프로젝트는 그들을 단 한 줄도 수정하지 않고 100% 그대로 재활용한다.**

모든 단계는 `events.jsonl`에 기록되어 재생 가능한 아티팩트로 남는다. 어느 변호사가 배정됐는지, 어떤 소스(Grade A/B/C)를 인용했는지, 팩트체커가 뭘 지적했는지 — 전부 보인다.

---

## 왜 이 아키텍처인가

멀티에이전트 시스템의 업계 표준은 LangGraph · CrewAI · AutoGen · Claude Agent SDK 같은 프레임워크를 웹 서버로 감싸는 것이다. Claude Code 자체를 오케스트레이션 런타임으로 쓰는 건 비주류이고, 개발자 열 명에게 보여주면 아홉은 "왜 Agent SDK 안 썼어?"부터 묻는다.

답은 자주 나오는 네 가지 오해를 풀면서 시작한다.

### 1. "에이전트 8개를 한 오케스트레이터에 꾸겨 넣으면 성능 저하 아닌가?"

아니다. 이건 Claude Code `Agent` tool이 어떻게 돌아가는지에 대한 오해다.

각 서브에이전트는 **완전히 독립된 새 Claude 인스턴스**이며, 200K 컨텍스트 윈도우를 통째로 새로 받는다. 오케스트레이터는 그 무게를 짊어지지 않고, 조율만 한다.

```
오케스트레이터 (200K context, 실사용 ~25-40K)
   │
   ├── Agent tool 호출 ──▶ 새 Claude 인스턴스 (200K, CLAUDE.md + skills + MCP 풀 로드)
   │                        └── 독립 실행 → 파일로 결과 반환
   │
   ├── Agent tool 호출 ──▶ 또 다른 새 Claude 인스턴스 (200K)
   │                        └── 독립 실행 → 파일로 결과 반환
   │
   └── ...
```

오케스트레이터가 실제로 쓰는 건 질문 분류(~2K) + 디스패치 프롬프트(~1K) + 결과 summary 읽기(~2K)뿐이다. 전문가 각각은 풀 캐파시티로 돌아간다 — 자기 CLAUDE.md, 모든 스킬, 지식 베이스, MCP 도구까지 전부 살아 있는 상태로. **이건 "꾸겨 넣기"의 반대다 — 구조적으로 가능한 가장 context-efficient한 멀티에이전트 설계다.**

### 2. "왜 남들처럼 LangGraph나 Agent SDK를 안 썼나?"

기존 Claude Code 에이전트를 웹 프레임워크로 감싸면 capability의 40~50%가 그냥 날아가기 때문이다:

- MCP 통합이 끊어진다
- 스킬 시스템을 바닥부터 재구현해야 한다
- Knowledge base 탐색 방식이 달라진다
- 결국 원본 에이전트의 절반짜리 퀄리티만 뽑는, 보기엔 예쁜 데모가 된다

그래서 트레이드오프를 정반대로 뒤집었다: **Claude Code를 런타임으로 쓰고, 에이전트 capability를 100% 보존하고, 시각화는 정적 Case Replay로 분리한다.** 결과물은 실제 법률 업무가 돌아가는 아키텍처다 — 데모가 아니라.

### 3. 프로세스 자체가 프로덕트다

Harvey AI는 블랙박스다. 답은 받지만 어떻게 나왔는지 알 수 없다.

법무법인 진주는 정반대다:

- 어느 변호사가 배정됐는가? → 보인다 (`events.jsonl` · `agent_assigned`)
- 어떤 소스(Grade A/B/C)를 참조했는가? → 보인다 (`source_graded`)
- 팩트체커가 뭘 플래그했는가? → 보인다 (`verbatim_verified`, `revision_requested`)
- 다관할권 토론이 어떻게 진행됐는가? → 보인다 (`debate_round_*`)
- 리뷰 파트너가 단 코멘트는? → 보인다 (`review_comment`)

각 전문 에이전트가 자기 소스 grading과 fact-checking 로직을 이미 갖추고 있기 때문에, **프로세스 자체가 프로덕트가 된다** — 답이 아니라.

### 4. Case Replay — 30초면 끝나는 데모가 아니다

대부분의 AI 데모는 30초 뒤에 사라진다. 이 프로젝트는 그렇지 않다.

처리된 모든 케이스는 `events.jsonl`(타임라인) + 에이전트별 `{agent}-result.md` / `{agent}-meta.json` + 최종 `opinion.md`/`.docx`로 디스크에 남는다. Phase 3에서는 이 데이터를 정적 JSON 피드 + 정적 뷰어(Case Replay)로 변환한다. **API 키 없이, 오프라인에서, 트윗에 임베드할 수 있는** 공유 가능한 아티팩트가 된다. 법률 프로세스가 콘텐츠이고, 시각화는 그걸 전달하는 수단일 뿐이다.

### 5. 그래, 토큰 엄청 태운다 — 그게 의도다

이 시스템에서 한 건의 케이스는 전문가 한 명당 60K~170K 토큰을 태운다. Phase 2.2 검증에서 한 병렬 실행(PIPA ∥ GDPR)이 124K, 한국 게임법 regression이 170K를 기록했다. 이건 버그가 아니라 설계다.

서브에이전트 각각에게 200K 컨텍스트 윈도우를 통째로 주는 이유는, 제대로 일하게 하기 위해서다:

- 자기 `CLAUDE.md` 전체 로드 (역할·원칙·도구 정책)
- 필요한 스킬 전부 로드
- 자체 지식 베이스 탐색
- 1차 소스에 대해 MCP 라이브 쿼리 실행
- 여러 턴에 걸쳐 생각하고 리비전할 여유 공간

컨텍스트 공유, 공격적 truncation, 프롬프트 단에서의 shortcut — 이런 걸 도입하면 토큰 사용량을 확 줄일 수 있다. 그리고 출력 퀄리티도 그만큼 확 떨어진다. **우리의 목적 함수는 "케이스당 퀄리티"이고, 토큰 비용은 그걸 사기 위한 가격이다.** Claude Code Max 구독에서는 호출당 달러 비용이 0이고, 실제로 지불하는 건 시간(파이프라인당 분 단위, 밀리초가 아님)이다 — 그 시간은 우리가 기꺼이 감당한다.

값싼 법률 챗봇이 필요하다면 이 프로젝트는 잘못된 선택이다. **감사 추적 가능한, 방어 가능한 법률 의견서**가 필요하다면, 저 소모량이 입장료다.

---

## 작동 방식

### 워크플로우

```
1. 사건 접수
   └── CASE_ID 생성, output/{CASE_ID}/ 디렉토리 생성, events.jsonl 시작

2. 질문 분류 (skills/route-case.md)
   └── 관할권 × 도메인 × 작업 유형 → 에이전트 조합 + 협업 패턴 결정

3. 에이전트 디스패치 (Agent tool)
   └── 각 에이전트는 독립된 Claude 인스턴스
        ├── 자체 CLAUDE.md + skills + knowledge base + MCP 로드
        └── 결과를 {agent}-result.md + {agent}-meta.json에 저장

4. 핸드오프 (필요 시)
   └── summary + key_findings만 다음 에이전트에 전달
        (전체 result.md는 파일 경로로만 참조 → 컨텍스트 효율)

5. 최종 어셈블 (skills/deliver-output.md)
   └── opinion.md + opinion.docx + events.jsonl + 소스 리스트
```

### 협업 패턴 3종

**Pattern 1 — 독립 리서치 → 통합 (병렬)**
서로 다른 관할권·도메인의 전문가가 각자 리서치하고, 그 결과를 writing이 합친다. Phase 2.2에서 검증 완료.
```
오케스트레이터 → [PIPA-expert ∥ GDPR-expert] → legal-writing → second-review
```

**Pattern 2 — 순차 핸드오프** (Phase 1 기본)
```
오케스트레이터 → general-legal-research → legal-writing → second-review
```

**Pattern 3 — 멀티라운드 토론** (Phase 2.3, 킬러 피처)
의견 충돌 가능성이 있는 다관할권 질문에 대해, 두 전문가가 의견 → 반론 → 재반론을 주고받은 뒤 writing이 verdict를 드래프트한다.
```
오케스트레이터 → Agent A 의견 → Agent B 반론 → Agent A 재반론 → writing verdict → review
```

Pattern 3가 이 아키텍처의 진짜 존재 이유다 — **단일 LLM 호출로는 절대 재현할 수 없는 깊이**가 여기서 나온다.

---

## 에이전트 로스터

| # | Agent ID | 담당 변호사 | 역할 | Phase |
|---|----------|------------|------|-------|
| 1 | `general-legal-research` | 김재식 | 범용 법률 리서치 | Phase 1 ✓ |
| 2 | `legal-writing-agent` | 한석봉 | 법률문서 작성 | Phase 1 ✓ |
| 3 | `second-review-agent` | 반성문 (파트너) | 품질 검토 및 최종 승인 | Phase 1 ✓ |
| 4 | `PIPA-expert` | 정보호 | 한국 개인정보보호법 | Phase 2 ✓ |
| 5 | `GDPR-expert` | 김덕배 | EU 데이터보호법 (GDPR) | Phase 2 ✓ |
| 6 | `game-legal-research` | 심진주 | 게임산업 국제법 | Phase 2 ✓ |
| 7 | `contract-review-agent` | 고덕수 | 계약서 검토 | Phase 2 |
| 8 | `legal-translation-agent` | 변혁기 | 법률문서 번역 | Phase 2 |

각 에이전트는 독립된 GitHub 리포지토리에 호스팅된다. `setup.sh`가 자동으로 클론하거나, 개발 중에는 `agents/` 하위에 심볼릭 링크를 만든다. **오케스트레이터는 하위 에이전트의 `CLAUDE.md`를 절대 수정하지 않는다** — 이것이 "100% 재활용"의 실천이다.

> 브리핑 계열 에이전트 2개(`game-legal-briefing`, `game-policy-briefing`)는 독립 Python 앱으로 존재하며 이 오케스트레이터의 스코프 바깥이라 의도적으로 위 목록에서 제외했다.

---

## 현재 상태

### 완료

**Phase 1 E2E 테스트 통과** — 2026-04-10
- 케이스: `20260410-012238-391f` (확률형 아이템 규제 의견서)
- 47 events, 33 sources (29 Grade A, 4 Grade B), revision cycle 1회 완료
- **메타-verification fallback 패턴 발견**: `legal-writing-agent`가 리비전 도중 rate limit에 걸렸을 때, 오케스트레이터가 직접 `korean-law` MCP로 verbatim 인용을 대조해서 리비전 사이클을 살려냄 (`evt_045` · `type=verbatim_verified` · `verifier=orchestrator_meta`)

**Phase 2.1 전문가 라우팅** — [`skills/route-case.md`](skills/route-case.md) v2
- 153줄 → 637줄로 확장: 8 에이전트 로스터, multi-domain 3-way 매트릭스, 공통 주입 블록, Events 스키마 부록, 토큰 예산표
- `/plan-eng-review`에서 나온 13 issues + 4 critical FM gap 전면 해결

**Phase 2.2 Pattern 1 병렬 디스패치** — 3건 mini E2E 검증 완료
- **T1** — PIPA-expert 단독: 9 sources (8A + 1B), 60k tokens, 582s. `library/grade-b/`에서 KB gap 발견 — **이후 해소** (아래 Phase 2.2 후속 작업 참조)
- **Regression** — game-legal-research 한국 게임법: 32 sources (25A + 7C), v1 baseline 대비 −3% comparable, 11/11 주제 coverage. library cache + 도메인 프레임의 실질 가치 입증.
- **T2** — PIPA ∥ GDPR 병렬: 각 13 sources (전부 Grade A), 두 브랜치가 실제로 병렬 실행, 5 dimension 태깅 정상 동작. 124k tokens, 334s.

**Phase 2.2 후속 작업: PIPA-expert `library/grade-b/` KB 보강** — 완료
- 6 토픽(동의·제3자 제공·안전조치/유출·국외이전·가명정보·민감/고유식별) 전반에 걸쳐 landmark 30건 수록
- 법제처 법령해석례 20건 + 대법원 판례 10건 (예: 2013두2945, 2015다24904, 2022두68923, 2024다210554 등)
- **원안 대비 스코프 변경:** 원래 계획은 PIPC 결정 20 + 판례 10이었으나 `get_pipc_decision_text` MCP endpoint 장애로 법제처 해석례 20건으로 대체. `pipc-decisions/`는 endpoint 복구 시 재개 대상으로 `source-registry.json`에 사유 기록.
- 모든 파일 `verification_status: VERIFIED`, MCP 원문 verbatim 인용. [kipeum86/PIPA-expert@6b8137c](https://github.com/kipeum86/PIPA-expert/commit/6b8137c) 참조.

### 진행 중 · 대기

- **`skills/manage-debate.md` 실제 로직** (Pattern 3) — 현재는 skeleton 상태
- **멀티라운드 토론 E2E** (킬러 피처 증명) — 후보 시나리오: "EU에 서버 둔 한국 게임사가 한국 이용자 개인정보를 EU로 국외이전할 때 법적 쟁점" (GDPR ↔ PIPA ↔ game-legal-research 3자 토론)
- **Case Replay MVP** (Next.js 정적 뷰어) — 독립 트랙, 샘플 데이터 풍부 (케이스 `20260410-012238-391f` + 3 mini E2E)
- **PIPC 결정문 재수집** — `get_pipc_decision_text` MCP endpoint 복구 대기

---

## 빠른 시작

### 1. 사전 조건

- [Claude Code](https://docs.claude.com/claude-code) 설치 (Max 구독 권장 — 호출당 API 비용 0)
- macOS / Linux (zsh 또는 bash)
- Python 3.10+ (DOCX 변환용)
- [법제처 Open API](https://open.law.go.kr/) 계정 (`LAW_OC` 키)

### 2. 클론 및 환경변수

```bash
git clone https://github.com/kipeum86/legal-agent-orchestrator.git
cd legal-agent-orchestrator

# Open Law API 키 (쉘 세션마다 필요 — Claude Code는 .env를 자동 로드하지 않음)
export LAW_OC=your_law_oc_key
```

### 3. 에이전트 설치

```bash
./setup.sh
```

GitHub에서 8개 하위 에이전트를 자동 클론하거나, 개발 중이면 로컬 복사본으로 심볼릭 링크를 생성한다.

### 4. Claude Code 실행

```bash
claude
```

Claude Code가 `CLAUDE.md`(오케스트레이터 시스템 프롬프트)와 `.mcp.json`(korean-law + kordoc MCP)을 자동 로드한다. 이제 법률 질문을 입력하면 오케스트레이터가 분류해서 적절한 파이프라인을 실행한다.

### 5. 결과 확인

```
output/{CASE_ID}/
├── events.jsonl            # 전체 타임라인 (Case Replay 입력)
├── {agent}-result.md       # 에이전트별 상세 분석
├── {agent}-meta.json       # 요약 + 소스 grading
├── opinion.md              # 최종 의견서 (markdown)
└── opinion.docx            # 최종 의견서 (DOCX, 스타일 가이드 §11)
```

---

## 프로젝트 구조

```
legal-agent-orchestrator/
├── CLAUDE.md                           # 오케스트레이터 시스템 프롬프트
├── .mcp.json                           # MCP 서버 설정 (korean-law + kordoc)
├── setup.sh                            # 에이전트 관리 (clone/link/status)
├── skills/
│   ├── route-case.md                   # 분류 + 파이프라인 선택
│   ├── deliver-output.md               # 최종 어셈블리
│   └── manage-debate.md                # Phase 2.3 토론 로직 (skeleton)
├── scripts/
│   └── md-to-docx.py                   # DOCX 변환 (스타일 가이드 §11)
├── agents/                             # 8 하위 에이전트 (심볼릭 링크 또는 클론)
├── output/                             # 케이스 아티팩트 ({case-id}/)
└── docs/
    ├── design.md                       # 디자인 문서 (office-hours APPROVED 9/10)
    ├── ko-legal-opinion-style-guide.md # 한국어 의견서 스타일 정본
    ├── session-log-*.md                # 개발 세션 로그
    └── notes/
        └── architecture-defense.md     # 이 README의 원재료
```

---

## 기술 스택

- **런타임**: Claude Code (Anthropic CLI)
- **에이전트 디스패치**: Claude Code `Agent` tool → 독립 200K 컨텍스트 서브에이전트
- **MCP 서버**:
  - `korean-law` — 법제처 공개 API 래퍼, Grade A 1차 소스 (법령·판례·해석례)
  - `kordoc` — 대한민국 법원 판결문 조회
- **스킬 시스템**: markdown 기반 절차 문서 (`skills/*.md`)
- **이벤트 로깅**: JSONL (append-only, replayable)
- **결과물 포맷**: Markdown → DOCX (python-docx, 이중 폰트: Times New Roman + 맑은 고딕)

---

## 로드맵

- [x] **Phase 0** — 기술 스파이크 (`Agent` tool / MCP / 병렬 실행 검증, 6/8 PASS)
- [x] **Phase 1** — 3 에이전트 기본 파이프라인 (research → writing → review) + E2E
- [x] **Phase 2.1** — 전문가 라우팅 (8 에이전트 로스터, multi-domain 매트릭스)
- [x] **Phase 2.2** — Pattern 1 병렬 디스패치 (3 mini E2E 검증 완료)
- [ ] **Phase 2.3** — Pattern 3 멀티라운드 토론 (킬러 피처)
- [ ] **Phase 3** — Case Replay (Next.js 정적 뷰어, 다크 테마 워룸 UI)
- [ ] 8 하위 에이전트 public 배포 + 라이선스 정리
- [ ] Classification regression 테스트 하네스 (route-case.md few-shot 자동 검증)

---

## 참고 문서

| 문서 | 설명 |
|------|------|
| [docs/design.md](docs/design.md) | 디자인 문서 (office-hours 6라운드 adversarial review, APPROVED 9/10) |
| [docs/notes/architecture-defense.md](docs/notes/architecture-defense.md) | 이 README의 원재료 — 확장된 "왜 이 아키텍처인가" 방어 노트 |
| [docs/ko-legal-opinion-style-guide.md](docs/ko-legal-opinion-style-guide.md) | 한국어 법률 의견서 스타일 정본 (한국어 에이전트 호출 시 강제 주입) |
| [skills/route-case.md](skills/route-case.md) | 분류 + 파이프라인 선택 로직 (v2, 637줄) |
| [resume.md](resume.md) | 개발 진행 상태 (세션 간 핸드오프 문서) |

---

## 라이선스

**Apache License 2.0** — [LICENSE](LICENSE) 참조.

하위 에이전트는 각자 리포지토리에서 별도의 라이선스를 따른다. 법률 데이터는 법제처 공개 API와 대한민국 법원 판결문(공공저작물)에서 수집한다.
