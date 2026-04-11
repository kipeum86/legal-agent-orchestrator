# 법무법인 진주 오케스트레이터 · Jinju Law Firm Orchestrator

**English:** [README.md](README.md)

> Claude Code 위에서 돌아가는 AI 로펌. 8명의 전문 변호사 에이전트가 각자 다른 관할권, 지식 베이스, MCP 도구를 가진 채 실제 로펌처럼 협업해서 전 과정이 감사 가능한 법률 의견서를 만든다.

![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)
![Runtime: Claude Code](https://img.shields.io/badge/Runtime-Claude_Code-orange)
![MCP: korean-law](https://img.shields.io/badge/MCP-korean--law-green)
![Status: Phase 2.2 검증 완료](https://img.shields.io/badge/Status-Phase_2.2_validated-brightgreen)

**상태:** Phase 1 E2E 통과 (2026-04-10) · Phase 2.1/2.2 검증 완료 (mini E2E 3건) · Phase 2.3 (멀티라운드 토론) + Case Replay 진행 중.

---

## 목차

- [실제 케이스 한눈에 보기](#실제-케이스-한눈에-보기)
- [개요](#개요)
- [왜 이 아키텍처인가](#왜-이-아키텍처인가)
- [작동 방식](#작동-방식)
- [어떤 질문을 던질 수 있는가](#어떤-질문을-던질-수-있는가)
- [에이전트 로스터](#에이전트-로스터)
- [샘플 케이스 완주기](#샘플-케이스-완주기)
- [측정된 성능](#측정된-성능)
- [이벤트 분류체계](#이벤트-분류체계)
- [빠른 시작](#빠른-시작)
- [프로젝트 구조](#프로젝트-구조)
- [기술 스택](#기술-스택)
- [로드맵](#로드맵)
- [FAQ](#faq)
- [참고 문서](#참고-문서)
- [라이선스](#라이선스)

---

## 실제 케이스 한눈에 보기

이 리포에 실제로 있는 케이스 하나다. 모의 데이터가 아니다. 아래에서 언급하는 모든 파일은 [`samples/20260410-012238-391f/`](samples/20260410-012238-391f/) 아래에 그대로 있고, 이 케이스(및 Phase 2.2 mini E2E 3건)에서 각 서브에이전트가 구체적으로 무슨 일을 했는지는 [`samples/README.md`](samples/README.md)에 에이전트별로 풀어놨다.

**질문 (사용자가 한 문장으로 입력한 것):**

> "한국 게임산업법의 확률형 아이템(가챠) 규제에 대한 법률 의견서를 작성해줘"

**오케스트레이터가 끝까지 한 일:**

1. **질문을 분류했다** — `jurisdiction=[KR]`, `domain=game_regulation`, `task=drafting`, `complexity=compound`. 라우터가 `[general-legal-research → legal-writing-agent → second-review-agent]` 파이프라인(Pattern 2, 순차 핸드오프)을 선택.
2. **`general-legal-research` (김재식) 디스패치.** 이 서브에이전트가 `korean-law` MCP를 통해 법제처에서 **1차 소스 14건**을 직접 가져왔다 — 게임산업법 §33② (확률형 아이템 표시의무), §38 ⑨~⑪ (시정명령 집행 체인), §45 xi (2년 이하 징역 / 2천만원 이하 벌금), 2024-01-05 공정위 전원회의 의결에서 넥슨에 **116억 4,200만원** 과징금(사건번호 2021전자1052) 등. 11개 key finding 반환.
3. **`legal-writing-agent` (한석봉) 디스패치.** 한국 로펌 표준 MEMORANDUM 형식으로 의견서 초안 작성: 결론 요약, 면책조항, 사실관계 가정, 7개 쟁점별 검토, 리스크 매트릭스, 8개 권고사항, 서명 블록.
4. **`second-review-agent` (반성문, 파트너) 디스패치.** 파트너가 `approved_with_revisions`를 리턴하면서 **9개 코멘트 — Critical 2건 + Major 3건 + Minor 4건** 달았다. 그중 하나가 초안의 §38 ⑩⑪ 블록 인용구가 현행 법률 원문과 실제로 다르다는 지적.
5. **리비전 사이클 1 발동.** 그 도중 `legal-writing-agent`가 `rate_limit`에 걸렸다 (`"Anthropic usage limit hit, reset 6am Asia/Seoul"`). 오케스트레이터는 포기하는 대신 직접 나섰다. **수정된 인용구를 `korean-law` MCP로 직접 verbatim 대조** (`verifier=orchestrator_meta`)해서 Critical 2 + Major 1 + Minor 1을 통과시켰다.
6. **`opinion.docx` 생성** — 56 KB, 138 문단, 5 표, Times New Roman + 맑은 고딕 이중 폰트. 한국어 법률 의견서 스타일 가이드 §11을 그대로 따름.

**케이스 폴더에 디스크로 남아있는 파일들:**

| 파일 | 크기 | 용도 |
|------|------|------|
| `events.jsonl` | 17 KB | **이벤트 47건** — 전체 재생 가능한 타임라인 |
| `research-result.md` + `research-meta.json` | 37 KB + 10 KB | 변호사 1 (김재식)의 풀 분석 + 2000 토큰 요약 |
| `opinion-v1.md` → `opinion.md` | 39 KB → 47 KB | 초안 + 리비전 후 최종본 |
| `review-result.md` + `review-meta.json` | 23 KB + 16 KB | 파트너 (반성문) 코멘트, 라인 레벨 인용 포함 |
| `verbatim-verification.md` | 5 KB | 오케스트레이터 메타 검증 로그 |
| `opinion.docx` | 123 KB | 클라이언트 제출용 최종 DOCX |
| `sources.json` | 8 KB | 전체 33개 grading된 소스 |

**핵심 숫자:** 소스 33건 (Grade A 1차 소스 29건 + Grade B 2차 소스 4건) · 리비전 사이클 1회 · 메타 검증 rescue 1회 · **승인**.

이 README의 나머지는 왜 이런 아키텍처를 선택했는지, 어떻게 작동하는지, 그리고 왜 토큰을 일부러 많이 태우는지 설명한다. 위 케이스의 [완전한 walkthrough](#샘플-케이스-완주기)는 아래쪽에 있다 — 파트너가 실제로 잡아낸 리뷰 코멘트까지 전부 포함.

---

## 개요

시중의 "법률 AI" 제품은 대부분 단일 LLM에 질문을 던지는 구조다. 이 프로젝트는 다르다.

**오케스트레이터가 파트너 변호사 역할**을 맡아서, 들어오는 질문을 분류하고, 적합한 전문 변호사에게 배정하고, 그 사건에 맞는 협업 패턴(순차 핸드오프 / 병렬 리서치 / 멀티라운드 토론)을 직접 고른다. 8명의 하위 에이전트는 각자 다른 관할권(한국/EU)·도메인(개인정보/게임/계약/번역)·작업 유형(리서치/작성/검토)을 담당하는 진짜 Claude Code 에이전트다. **이 프로젝트는 그들을 단 한 줄도 수정하지 않고 100% 그대로 재활용한다.**

모든 단계는 `events.jsonl`에 기록되어 재생 가능한 아티팩트로 남는다. 어느 변호사가 배정됐는지, 어떤 소스(Grade A/B/C)를 인용했는지, 팩트체커가 뭘 지적했는지, 다관할권 토론이 어떻게 흘러갔는지 — 전부 보인다.

---

## 왜 이 아키텍처인가

멀티에이전트 시스템의 업계 표준은 LangGraph · CrewAI · AutoGen · Claude Agent SDK 같은 프레임워크를 웹 서버로 감싸는 것이다. Claude Code 자체를 오케스트레이션 런타임으로 쓰는 건 비주류이고, 개발자 열 명에게 보여주면 아홉은 "왜 Agent SDK 안 썼어?"부터 묻는다.

답은 자주 나오는 네 가지 오해를 푸는 것에서 시작해서, 정직한 트레이드오프 하나로 끝나고, 비교표로 뒷받침된다.

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

오케스트레이터가 실제로 쓰는 토큰은 질문 분류(~2K) + 디스패치 프롬프트(~1K) + 결과 summary 읽기(~2K)뿐이다. 전문가 각각은 풀 캐파시티로 돌아간다 — 자기 CLAUDE.md, 모든 스킬, 지식 베이스, MCP 도구까지 전부 살아 있는 상태로. **이건 "꾸겨 넣기"의 반대다 — 구조적으로 가능한 가장 context-efficient한 멀티에이전트 설계다.**

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
- 팩트체커가 뭘 플래그했는가? → 보인다 (`review_completed` with `approval=approved_with_revisions`)
- 리비전 사이클이 어떻게 진행됐는가? → 보인다 (`revision_requested`, `verbatim_verified`)
- 파트너가 어떤 코멘트를 달았는가? → `review-result.md`에 코멘트 단위로 라인 참조까지 전부 기록

실제 47-event 케이스 파일 ([`samples/20260410-012238-391f/events.jsonl`](samples/20260410-012238-391f/events.jsonl))에서 15건을 뽑아봤다:

```jsonl
{"id":"evt_001","type":"case_received","data":{"query":"한국 게임산업법의 확률형 아이템(가챠) 규제에 대한 법률 의견서를 작성해줘"}}
{"id":"evt_002","type":"case_classified","data":{"jurisdiction":["KR"],"domain":"game_regulation","task":"drafting","pipeline":["general-legal-research","legal-writing-agent","second-review-agent"]}}
{"id":"evt_003","type":"agent_assigned","agent":"general-legal-research","data":{"name":"김재식","role":"범용 법률 리서치"}}
{"id":"evt_014","type":"source_graded","agent":"general-legal-research","data":{"source":"공정위 2024.1.5. 전원회의 의결 ㈜넥슨코리아... 과징금 116억 4,200만원","grade":"A","citation":"사건번호 2021전자1052"}}
{"id":"evt_018","type":"research_completed","data":{"sources_count":14,"key_findings_count":11}}
{"id":"evt_019","type":"agent_assigned","agent":"legal-writing-agent","data":{"name":"한석봉","role":"법률문서 작성"}}
{"id":"evt_034","type":"writing_completed","data":{"output_file":"opinion.md","sources_count":14}}
{"id":"evt_035","type":"agent_assigned","agent":"second-review-agent","data":{"name":"반성문","role":"품질 검토 / 파트너 최종 승인"}}
{"id":"evt_041","type":"review_completed","data":{"approval":"approved_with_revisions","comments_count":9}}
{"id":"evt_042","type":"revision_requested","data":{"cycle":1,"max_cycles":2,"critical":2,"major":3,"minor":4}}
{"id":"evt_043","type":"agent_assigned","agent":"legal-writing-agent","data":{"role":"법률문서 수정 (revision cycle 1)"}}
{"id":"evt_044","type":"error","agent":"legal-writing-agent","data":{"error_type":"rate_limit","message":"Anthropic usage limit hit, reset 6am Asia/Seoul"}}
{"id":"evt_045","type":"verbatim_verified","agent":"orchestrator","data":{"verifier":"orchestrator_meta","reason":"review-agent token limit hit; meta verification via korean-law MCP","critical_pass":2,"major_pass":1,"final_status":"approved"}}
{"id":"evt_046","type":"docx_generated","data":{"output":"opinion.docx","size_bytes":56519,"tables":5,"paragraphs":138}}
{"id":"evt_final","type":"final_output","data":{"total_sources":33,"grade_distribution":{"A":29,"B":4},"review_cycle":1,"final_approval":"approved"}}
```

이 스트림을 잘 읽어보자. `evt_044`는 **진짜로 발생한 rate limit 실패**다. 서브에이전트가 리비전 중간에 죽었다. `evt_045`가 그 구조다 — 오케스트레이터가 직접 수정본의 verbatim 인용구를 `korean-law` MCP로 대조해서 리비전을 통과시켰다. 단일 LLM 시스템에서는 그냥 "모델이 에러 반환함"이라는 메시지만 남았을 것이다. 여기서는 **실패 자체와 그 해결 경로가 영구 기록의 일부**가 된다. 그게 "프로세스 자체가 프로덕트"의 진짜 의미다.

각 전문 에이전트가 자기만의 소스 grading과 fact-checking 로직을 이미 갖추고 있기 때문에, 이 정도 수준의 observability는 공짜다. 별도의 감사 레이어를 만들 필요가 없다.

### 4. Case Replay — 30초면 끝나는 데모가 아니다

대부분의 AI 데모는 30초 뒤에 사라진다. 이 프로젝트는 그렇지 않다.

처리된 모든 케이스는 `events.jsonl`(타임라인) + 에이전트별 `{agent}-result.md` / `{agent}-meta.json` + 최종 `opinion.md`/`.docx`로 디스크에 남는다. Phase 3에서는 이 데이터를 정적 JSON 피드 + 정적 뷰어(Case Replay)로 변환한다. **API 키 없이, 오프라인에서, 트윗에 임베드할 수 있는** 공유 가능한 아티팩트가 된다. 법률 프로세스가 콘텐츠이고, 시각화는 그걸 전달하는 수단일 뿐이다.

### 5. 그래, 토큰 엄청 태운다 — 그게 의도다

이 시스템에서 한 건의 케이스는 전문가 한 명당 60K~170K 토큰을 태운다. Phase 2.2 검증에서 한 병렬 실행(PIPA ∥ GDPR)이 124K, 한국 게임법 regression이 170K를 기록했다. Phase 1 E2E는 리비전 사이클 포함해서 서브에이전트 합쳐 200K를 훌쩍 넘었다. **이건 버그가 아니라 설계다.**

서브에이전트 각각에게 200K 컨텍스트 윈도우를 통째로 주는 이유는, 제대로 일하게 하기 위해서다:

- 자기 `CLAUDE.md` 전체 로드 (역할·원칙·도구 정책)
- 필요한 스킬 전부 로드
- 자체 지식 베이스 탐색
- 1차 소스에 대해 MCP 라이브 쿼리 실행
- 여러 턴에 걸쳐 생각하고 리비전할 여유 공간

컨텍스트 공유, 공격적 truncation, 프롬프트 단에서의 shortcut — 이런 걸 도입하면 토큰 사용량을 확 줄일 수 있다. 그리고 출력 퀄리티도 그만큼 확 떨어진다. **우리의 목적 함수는 "케이스당 퀄리티"이고, 토큰 비용은 그걸 사기 위한 가격이다.** Claude Code Max 구독에서는 호출당 달러 비용이 0이고, 실제로 지불하는 건 시간(파이프라인당 분 단위, 밀리초가 아님)이다 — 그 시간은 우리가 기꺼이 감당한다.

값싼 법률 챗봇이 필요하다면 이 프로젝트는 잘못된 선택이다. **감사 추적 가능한, 방어 가능한 법률 의견서**가 필요하다면, 저 소모량이 입장료다.

### 비교표

| 측면 | 단일 LLM | LangGraph / Agent SDK | **법무법인 진주** |
|------|----------|----------------------|-------------------|
| 멀티 전문가 추론 | 프롬프트 페르소나로 시뮬레이션 | 프레임워크 내에 에이전트 재구현 | **진짜 Claude Code 에이전트, 100% 재활용** |
| 지식 베이스 | 컨텍스트에 꾸겨 넣어야 함 | 프레임워크용으로 재구축 필요 | 각 에이전트의 네이티브 KB 그대로 |
| MCP 도구 / 1차 소스 | 호출자의 도구만 상속 | 서버사이드에서 다시 배선 | 각 에이전트가 자기 MCP 설정 유지 |
| 전담 팩트체커 | 없거나 임시방편 | 커스텀 구현 | 자체 CLAUDE.md를 가진 실제 에이전트 (`second-review-agent`) |
| 감사 추적 | 채팅 로그 | 커스텀 로깅 레이어 | 케이스당 네이티브 `events.jsonl` |
| 다관할권 토론 | 한 모델이 양쪽 다 롤플레이 | 순차 상태 머신 hop | 병렬 디스패치 + 메타 검증 fallback |
| 의견서당 토큰 비용 | 낮음 (10–30K) | 중간 (30–80K) | **높음 (전문가 합산 150–400K)** |
| 퀄리티 상한 | 단일 모델의 "변호사 모드" 한계 | 재구현 충실도 한계 | 각 전문가의 실제 capability 한계 |
| 데모 영속성 | 탭 닫으면 채팅 사라짐 | 서버 띄워둬야 함 | 정적 `events.jsonl` + `opinion.md/.docx` 파일 |

---

## 작동 방식

### 시스템 다이어그램

```
┌──────────────────────────────────────────────────────────────────────┐
│                          오케스트레이터                                │
│          (Claude Code 메인 세션, context 실사용 ~25-40K)               │
│                                                                       │
│  1. 사건 접수 ─────────────────────────────────────────────────────│
│     CASE_ID 생성, output/{CASE_ID}/ 생성, events.jsonl 초기화         │
│                                                                       │
│  2. 분류 (skills/route-case.md)                                      │
│     관할권 × 도메인 × 작업 → 전문가 조합 + 패턴                       │
│                                                                       │
│  3. 디스패치 (Claude Code Agent tool) ──┐                            │
└──────────────────────────────────────────┼────────────────────────────┘
                                           │
                  ┌────────────────────────┼────────────────────────┐
                  ▼                        ▼                        ▼
        ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
        │   서브에이전트 A   │    │   서브에이전트 B   │    │   서브에이전트 C   │
        │  (새 Claude 인스턴스, │  │  (새 Claude 인스턴스, │  │  (새 Claude 인스턴스, │
        │   fresh 200K)    │    │   fresh 200K)    │    │   fresh 200K)    │
        │                  │    │                  │    │                  │
        │  자체 CLAUDE.md  │    │  자체 CLAUDE.md  │    │  자체 CLAUDE.md  │
        │  자체 skills     │    │  자체 skills     │    │  자체 skills     │
        │  자체 KB         │    │  자체 KB         │    │  자체 KB         │
        │  자체 MCP 도구    │    │  자체 MCP 도구    │    │  자체 MCP 도구    │
        │                  │    │                  │    │                  │
        │  출력:           │    │  출력:           │    │  출력:           │
        │  A-result.md     │    │  B-result.md     │    │  C-result.md     │
        │  A-meta.json     │    │  B-meta.json     │    │  C-meta.json     │
        └────────┬─────────┘    └────────┬─────────┘    └────────┬─────────┘
                 │                       │                       │
                 └───────────────────────┼───────────────────────┘
                                         ▼
┌──────────────────────────────────────────────────────────────────────┐
│                          오케스트레이터                                │
│                                                                       │
│  4. 핸드오프: 다음 에이전트에는 summary + key_findings만 전달          │
│     (전체 result.md는 파일 경로로만 참조 → context 효율)               │
│                                                                       │
│  5. 최종 어셈블 (skills/deliver-output.md)                           │
│     opinion.md + opinion.docx + events.jsonl + sources.json          │
└──────────────────────────────────────────────────────────────────────┘
```

### 5단계 워크플로우

1. **사건 접수** — `CASE_ID` 생성, `output/{CASE_ID}/` 생성, `events.jsonl` 시작.
2. **분류** ([`skills/route-case.md`](skills/route-case.md)) — 관할권 × 도메인 × 작업 유형 → 에이전트 조합 + 협업 패턴 결정.
3. **에이전트 디스패치** (Claude Code `Agent` tool) — 각 에이전트는 독립된 Claude 인스턴스. 자체 CLAUDE.md + skills + 지식 베이스 + MCP 로드. 결과를 `{agent}-result.md` + `{agent}-meta.json`에 저장.
4. **핸드오프** (필요 시) — 다음 에이전트에는 `summary` + `key_findings`만 전달. 전체 `result.md`는 파일 경로로만 참조하므로 오케스트레이터 context가 효율적.
5. **최종 어셈블** ([`skills/deliver-output.md`](skills/deliver-output.md)) — `opinion.md` + `opinion.docx` + `events.jsonl` + `sources.json`.

### 협업 패턴 3종

**Pattern 1 — 독립 리서치 → 통합 (병렬)**
서로 다른 관할권·도메인의 전문가가 각자 리서치하고, writing이 그 결과를 합친다. Phase 2.2에서 검증 완료.
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

### Pattern 3 walkthrough — 구체 시나리오

다음 질문이 오케스트레이터에 들어왔다고 상상해보자:

> "프랑크푸르트(AWS `eu-central-1`)에 라이브 서비스 서버를 둔 한국 게임 회사가, 한국 이용자의 개인정보를 그 서버로 국외이전할 때 K-PIPA(국외이전 조항)와 GDPR(국제이전 조항) 양쪽 컴플라이언스가 모두 필요한지, 그리고 같은 정보주체가 한국에서 한국 국민으로서 게임을 하지만 데이터는 EU에서 처리되는 경우 두 규제가 어떻게 상호작용하는지를 알고 싶다."

단일 LLM은 양쪽을 진짜로 논쟁할 수 없다. "PIPA 전문가 롤플레이"와 "GDPR 전문가 롤플레이"는 여전히 같은 priors에서 나온다. 진짜 답을 내려면 서로 상대방의 지식 베이스를 모르는 두 에이전트가 필요하고, 그 위에 판결을 내리는 세 번째가 필요하다.

Pattern 3은 이렇게 라우팅한다:

```
Round 1 ── 의견 개진
  ├── PIPA-expert    주장: "정보주체가 한국인이므로 K-PIPA §28-8 국외이전이
  │                        적용되며, 프랑크푸르트 처리는 국경 간 이전 규정을
  │                        trigger한다."
  │                        → Grade A 소스 약 8건 emit
  │
  └── GDPR-expert    주장: "컨트롤러가 EU 이용자를 타게팅하므로 GDPR Art.3(2)
                          역외 적용이 발동한다. 데이터가 한국 국민 것이라는
                          사실이 EU 영토에서의 처리를 면제해주지 않는다."
                          → Grade A 소스 약 7건 emit

Round 2 ── 반론
  ├── PIPA-expert    GDPR의 역외 적용 주장을 반박: "EU 이용자 타게팅이
  │                  핵심 사실이 아니다 — EU 서버는 인프라일 뿐 시장이 아님"
  │
  └── GDPR-expert    PIPA의 스코프 주장을 반박: "프랑크푸르트가 실제
                    establishment라면 Art.3(1)의 establishment 기반 처리가
                    여전히 적용된다. 정보주체가 EU 외 국민이어도 마찬가지"

Round 3 ── 판결 (legal-writing-agent)
  "양쪽 다 적용된다, 어떻게 상호작용하는지 설명"의 메모 +
  양 regime 모두 충족하는 컴플라이언스 체크리스트 드래프트.

Final ── second-review-agent 최종 승인.
```

핵심 설계 결정: **오케스트레이터는 어느 편의 주장도 하지 않는다.** 라운드 스케줄링, 이벤트 기록, writing 에이전트에게 verdict를 요청하는 역할만 한다. 토론 중 한쪽이 rate limit에 걸리면, 위 샘플 케이스의 `evt_045`에서 본 메타 검증 fallback이 그 라운드를 대체한다. 현재 [`skills/manage-debate.md`](skills/manage-debate.md)는 skeleton 상태이고, 실제 로직은 Phase 2.3에서 ship.

---

## 어떤 질문을 던질 수 있는가

[`skills/route-case.md`](skills/route-case.md)의 라우터는 8개 카테고리의 질문에 맞춰져 있다. 각 카테고리별 예시 쿼리:

**한국 게임법** → `game-legal-research` (또는 `general-legal-research`) → writing → review

> "확률형 아이템 공급 확률 정보공개 의무 — 해외 관계회사가 한국 이용자 대상 게임을 운영할 때 국내대리인 지정 요건과 위반 시 리스크는?"

**한국 개인정보법 (PIPA)** → `PIPA-expert` → writing → review

> "의료기기 스타트업이 환자 음성 데이터를 AI 학습에 사용하려고 합니다. 가명처리만으로 충분한가요, 별도 동의가 필요한가요?"

**EU GDPR** → `GDPR-expert` → writing → review

> "서울에 본사를 둔 SaaS 제품인데 EU 이용자가 약 12%입니다. GDPR Art.27 대리인이 필요한가요? 선임 안 하면 어떻게 되나요?"

**다관할권 (병렬, Pattern 1)** → `[PIPA-expert ∥ GDPR-expert]` → writing → review

> "독일로 진출하려는 한국 핀테크가 생체인식 liveness detection으로 KYC를 돌리려고 합니다. K-PIPA + GDPR 결합 컴플라이언스 전경, DPIA trigger 여부까지 정리해주세요."

**다관할권 (토론, Pattern 3)** → `[PIPA ↔ GDPR ↔ game-legal]` → verdict → review

> "EU에 본사를 둔 게임 퍼블리셔가 한국에 라이브 서비스 서버를 둔 경우 — 이용자는 독일인이고 데이터는 서울에 떨어질 때 국제이전 규정이 어떻게 상호작용하는지?"

**계약서 검토** → `contract-review-agent` → writing (optional) → review

> "이 SaaS 계약서 한번 봐주세요. 한국법 준거에 맞지 않는 조항, 일방적 해지 조항, 자동 갱신 조항 잡아주고 협상 포인트 정리해주세요."

**법률문서 번역** → `legal-translation-agent` → review

> "이 한국어 의견서를 영어로 번역해주세요. 법률 문어체 톤과 인용 형식을 그대로 유지해야 합니다."

**범용 법률 리서치** (라우터가 특정 전문가를 고르지 못할 때) → `general-legal-research` → writing → review

> "상가임대차보호법상 권리금 보호 제외 사유에 대한 최근 3년 대법원 판례를 정리해주세요."

모든 카테고리가 모든 에이전트를 부르는 건 아니다. 라우터는 최소 필요 파이프라인을 선택한다 — 단순한 질문은 `research → review` (writing 스킵) 정도로 끝나고, 복잡한 다관할권 질문은 3자 토론으로 간다.

---

## 에이전트 로스터

| # | Agent ID | 담당 변호사 | 역할 | Phase | 관할권 |
|---|----------|------------|------|-------|--------|
| 1 | `general-legal-research` | 김재식 | 한국법 범용 법률 리서치 (어느 도메인이든) | Phase 1 ✓ | KR |
| 2 | `legal-writing-agent` | 한석봉 | 한국 로펌 표준 MEMORANDUM 형식으로 의견서 작성 (스타일 가이드 강제 주입) | Phase 1 ✓ | KR |
| 3 | `second-review-agent` | 반성문 (파트너) | 품질 검토 파트너. MCP로 1차 소스 verbatim 대조 후 Critical/Major/Minor 코멘트 발행 | Phase 1 ✓ | KR |
| 4 | `PIPA-expert` | 정보호 | 한국 개인정보보호법 전문가. PIPA/PIPC 전용 지식 베이스 보유 | Phase 2 ✓ | KR |
| 5 | `GDPR-expert` | 김덕배 | EU General Data Protection Regulation 전문가 | Phase 2 ✓ | EU |
| 6 | `game-legal-research` | 심진주 | 국제 게임법 전문가 (확률형 아이템, 국경 간 라이브 서비스, 콘텐츠 규제) | Phase 2 ✓ | KR + 국제 |
| 7 | `contract-review-agent` | 고덕수 | 한국법 하에서 상사계약서 검토 (SaaS, NDA, 고용, 라이선스) | Phase 2 | KR |
| 8 | `legal-translation-agent` | 변혁기 | 법률문서 번역 (KR ↔ EN). 어조와 인용 형식 보존 | Phase 2 | KR / EN |

각 에이전트는 독립된 GitHub 리포지토리에 호스팅된다. `setup.sh`가 자동으로 클론하거나, 개발 중에는 `agents/` 하위에 심볼릭 링크를 만든다. **오케스트레이터는 하위 에이전트의 `CLAUDE.md`를 절대 수정하지 않는다** — 이것이 "100% 재활용"의 실천이다.

> 브리핑 계열 에이전트 2개(`game-legal-briefing`, `game-policy-briefing`)는 독립 Python 앱으로 존재하며 이 오케스트레이터의 스코프 바깥이라 의도적으로 위 목록에서 제외했다.

---

## 샘플 케이스 완주기

위 [실제 케이스 한눈에 보기](#실제-케이스-한눈에-보기)와 같은 케이스를 이번엔 제대로 풀어본다. 언급되는 파일은 전부 [`samples/20260410-012238-391f/`](samples/20260410-012238-391f/) 아래 실재하므로 직접 `cat`해서 볼 수 있다.

### 질문

> "한국 게임산업법의 확률형 아이템(가챠) 규제에 대한 법률 의견서를 작성해줘"

한국 게임회사가 한국의 가챠 규제 전반에 관한 의견서를 원하는 상황. 실제로 한국 중견 로펌이 게임 퍼블리셔 클라이언트로부터 받는 전형적인 질문이다.

### 분류

오케스트레이터가 질문을 분석해서 다음을 emit했다:

```json
{
  "jurisdiction": ["KR"],
  "domain": "game_regulation",
  "task": "drafting",
  "complexity": "compound",
  "pipeline": ["general-legal-research", "legal-writing-agent", "second-review-agent"]
}
```

Pattern 2 (순차 핸드오프). 관할권이 하나뿐이라 Pattern 1은 필요 없었고, 다관할권 의견 충돌이 없어 Pattern 3도 발동 안 함.

### Stage 1 — 리서치 (김재식, general-legal-research)

`korean-law` MCP로 가져온 1차 소스 14건, 주요한 것:

- 게임산업법 §2 xi ("확률형 아이템"의 정의)
- 게임산업법 §33 ② (표시의무, 법률 제19877호, 2024-03-22 시행)
- 시행령 §19조의2 + 별표 3의2 (7 카테고리 × 3 영역 표시 규정)
- 게임산업법 §38 ⑨⑩⑪ (시정권고 → 시정명령 집행 체인)
- 게임산업법 §45 xi (시정명령 불이행 시 2년 이하 징역 / 2천만원 이하 벌금)
- 게임산업법 §48 (과태료 — **§33② 위반은 열거 대상에 포함되지 않음**, 즉 집행은 §38 시정명령 경로를 반드시 거쳐야 함)
- 게임산업법 §31조의2 (해외 사업자 국내대리인 지정 의무)
- 전자상거래법 §21 ①i (거짓·기만적 소비자 유인 금지)
- **공정위 전원회의 의결 2024-01-05, 사건번호 2021전자1052** — 넥슨 메이플스토리 큐브 사건, 과징금 **116억 4,200만원** (전자상거래법 위반 역대 최대 규모)
- 공정위 제3소회의 결정 2018-05-14, 넥슨 선행 사건

11개 key finding 중 load-bearing한 발견 하나: **§33② 위반이 §48 과태료 직접 부과 조항의 열거 대상에서 빠져 있어서 집행이 §38 시정명령 → §45 형사처벌 2단 구조를 반드시 거쳐야 한다**는 구조적 디테일. 이 한 줄이 클라이언트의 리스크 그림 전체를 바꾼다.

[`research-result.md`](samples/20260410-012238-391f/research-result.md) (37 KB) + [`research-meta.json`](samples/20260410-012238-391f/research-meta.json) (10 KB) 참조.

### Stage 2 — 드래프팅 (한석봉, legal-writing-agent)

한석봉이 한국 로펌 표준 의견서를 작성했다:

- MEMORANDUM 헤더 + 수신/참조/발신/제목 표
- 결론 요약 — 실질적 3 문단
- 면책조항 (Disclaimer)
- 5개 항목의 사실관계 가정 블록
- 7개 쟁점 검토의견 (클라이언트의 7개 질의에 대응)
- 리스크 매트릭스 (高/中/低 grading)
- 8개 항목 권고사항
- 결론 + 서명 블록

리뷰 전 v1 초안은 [`opinion-v1.md`](samples/20260410-012238-391f/opinion-v1.md) (39 KB)에서 확인할 수 있다.

### Stage 3 — 리뷰 (반성문, 파트너) — 잡아낸 것들

파트너가 `approved_with_revisions`를 리턴하면서 **9개 코멘트 — Critical 2건, Major 3건, Minor 4건** 달았다. 일반적인 스타일 지적이 아니다. 그중 두 건을 [`review-meta.json`](samples/20260410-012238-391f/review-meta.json)에서 그대로 인용:

> **[Critical #1]** 의견서 본문 블록 인용구 중 게임산업법 §38 ⑩⑪이 현행 법률 제19877호 원문과 불일치. 수범자 범위 `제9항` vs `제7항부터 제9항까지`, 용어 `이행·보고` vs `조치 완료·통보`, 수신자 `문체부장관만` vs `게임물관리위원회위원장 또는 문체부장관`, 제11항 단서 형식 2개 서술형 vs 3개 항목 열거형. **블록 인용은 verbatim이 필수다.**

> **[Critical #2]** 게임산업법 §31조의2 국내대리인 지정의무를 '모든 해외 사업자'에게 적용되는 것처럼 기술. 실제 조문은 '게임 이용자 수, 매출액 등을 고려하여 대통령령으로 정하는 기준에 해당하는 자'로 한정됨. 소규모 해외 인디 개발자·Steam 유통 사업자까지 의무 대상으로 오해 유발.

이건 주니어 어소시엇이 놓치고 시니어 파트너가 잡는 정확히 그 종류의 catch다. 이 시스템이 이걸 잡아낸 이유는 **`second-review-agent`가 초안에 나온 인용구 각각을 `korean-law` MCP에 쿼리해서 verbatim 대조를 돌리기 때문**이다. "LLM이 이상해 보인다고 판단함"이 아니라 "§38⑩의 1차 소스 원문과 초안 블록 인용구가 다른 토큰들이 여기 있다"라는 구체 수준이다.

파트너의 9개 코멘트에는 이런 것도 있었다:

- **[Major]** §47 양벌규정을 "일반적으로 이런 규제법 벌칙에는 양벌규정이 수반됨"이라는 일반론으로 처리. §47을 직접 인용할 수 있는 사안인데 하향 처리했다고 지적.
- **[Major]** 리스크 매트릭스는 전자상거래법 과징금을 유일한 "高"로 평가했는데, 권고사항은 여전히 게임산업법 대응을 앞에 배치했다. 리스크 평가와 권고 우선순위 역순.
- **[Major]** 메이플스토리 서울중앙지법 민사 집단소송 건이 리서치에서 `[Unverified]`로 태그됐는데 리스크 매트릭스에는 "中" 등급이 부여됨. 미확인 사실에 정량 리스크 등급을 주면 안 된다는 지적.
- **[Minor]** 시행령 시행일 3개가 병기되어(2024-03-22 / 2025-10-23 / 2026-03-24) 독자 혼선. 파트너는 단일 기준일로 정리할 것을 요청.
- **[Minor]** 8개 권고사항에 "즉시 / 단기 / 중기" 시한 표기가 없어 실무 우선순위 판단이 어려웠다.

전체 코멘트 세트는 라인 레벨 참조까지 포함된 [`review-result.md`](samples/20260410-012238-391f/review-result.md) (23 KB)에서 볼 수 있다.

### Stage 4 — 리비전 + 메타 검증 rescue

오케스트레이터가 `revision_requested` (사이클 1/2)를 emit하고 한석봉을 다시 디스패치했다. 리비전 도중:

```
evt_044  error  rate_limit  "Anthropic usage limit hit, reset 6am Asia/Seoul"
```

Fallback이 없다면 이 케이스는 내일 아침까지 멈춘다. 오케스트레이터는 대신 원래 설계 문서에 없던 동작을 했다:

```
evt_045  verbatim_verified  verifier=orchestrator_meta
         reason: "review-agent token limit hit; meta verification via korean-law MCP"
         critical_pass: 2
         major_pass: 1
         minor_diffs: 1
         final_status: approved
```

오케스트레이터가 직접 수정본을 읽고, `korean-law` MCP로 §38, §31-2, §47 1차 소스 원문을 쿼리한 뒤 verbatim diff를 돌렸다. 전체 rescue 로그는 [`verbatim-verification.md`](samples/20260410-012238-391f/verbatim-verification.md) (5 KB)에 있다.

이 패턴은 원래 설계 문서에 없었다. E2E 테스트 중 압박 상황에서 자연 발생했다. 이제는 이 시스템이 rate-limited 서브에이전트를 처리하는 방식의 일부가 되었고, Phase 2.3 토론 구현에서도 load-bearing fallback으로 쓰일 예정이다 — 토론 중 전문가 한쪽이 죽으면 예전엔 fatal이었기 때문.

### Stage 5 — DOCX 생성

```
evt_046  docx_generated  opinion.docx  (56519 bytes, 138 paragraphs, 5 tables)
                          fonts: latin=Times New Roman 11pt, cjk=맑은 고딕 11pt
```

[`scripts/md-to-docx.py`](scripts/md-to-docx.py)로 [`docs/ko-legal-opinion-style-guide.md`](docs/ko-legal-opinion-style-guide.md) §11을 그대로 따라 이중 폰트 출력. 한국 법률 업계는 인쇄되는 의견서에 특정 타이포그래피를 기대한다 (Latin은 Times New Roman, Hangul은 맑은 고딕, 명시적 `eastAsia` XML 속성으로 Word on Windows가 CJK run을 다시 reshape하지 않도록). 이건 장식이 아니라 deliverable 계약의 일부다.

### 최종 숫자

- `events.jsonl`에 이벤트 **47건**
- 총 **33 소스** (Grade A 29 + Grade B 4 + C 0 + D 0)
- 최종 의견서에는 **14건**만 인용 (33건은 리서치 단계에서 후보였다가 드래프팅에서 걸러진 것 포함)
- 리비전 사이클 **1회** (최대 2회 중)
- 메타 검증 rescue **1회**
- **최종 승인**: approved

---

## 측정된 성능

마케팅 문구가 아니라, `output/` 폴더에서 직접 읽어볼 수 있는 실제 숫자다.

### Phase 1 E2E (Pattern 2 순차, 리비전 포함)

| 항목 | 값 |
|------|-----|
| 케이스 | [`20260410-012238-391f`](samples/20260410-012238-391f/) |
| 파이프라인 | `general-legal-research → legal-writing → second-review → revision 1` |
| 이벤트 | 47 |
| 총 소스 | 33 (Grade A 29 / B 4 / C 0 / D 0) |
| 리비전 사이클 | 1/2 |
| 특이사항 | Rate-limit 상황을 오케스트레이터 메타 검증으로 돌파 (`evt_045`) |
| 최종 deliverable | `opinion.docx` (56 KB, 138 문단, 5 표) |
| 승인 | approved |

### Phase 2.2 mini E2E

| Test | 파이프라인 | 패턴 | 소스 | Grade A/B/C | 토큰 | Wall time | 비고 |
|------|-----------|------|------|-------------|------|-----------|------|
| **T1** | `PIPA-expert` 단독 | direct | 9 | 8 / 1 / 0 | ~60K | 582초 | [`test-T1-20260410-121640/`](samples/test-T1-20260410-121640/). `library/grade-b/` KB gap 발견, 이후 해소. |
| **Regression** | `game-legal-research` 단독 | direct | 32 | 25 / 0 / 7 | ~170K | 797초 | [`test-regression-20260410-121640/`](samples/test-regression-20260410-121640/). 전문가 vs v1 범용 baseline: −3% comparable, 11/11 주제 coverage. |
| **T2** | `[PIPA ∥ GDPR]` 병렬 | Pattern 1 | 26 | 26 / 0 / 0 | ~124K | 334초 | [`test-T2-20260410-121640/`](samples/test-T2-20260410-121640/). 양 브랜치 실제 병렬 실행, 5-dimension 다관할권 태깅 정상. |

### Phase 2.1 전문가 라우팅 — [`skills/route-case.md`](skills/route-case.md) v2

- 153줄 → 637줄로 확장: 8 에이전트 로스터, multi-domain 3-way 매트릭스, 공통 주입 블록, 이벤트 스키마 부록, 토큰 예산표.
- `/plan-eng-review`에서 나온 13 issues + 4 critical FM gap 전면 해결.

### Phase 2.2 후속 작업: PIPA-expert `library/grade-b/` KB 보강 — 완료

- 6 토픽(동의·제3자 제공·안전조치/유출·국외이전·가명정보·민감/고유식별) 전반에 걸쳐 **landmark 30건** 수록.
- 법제처 법령해석례 20건 + 대법원 판례 10건 (예: 2013두2945, 2015다24904, 2022두68923, 2024다210554).
- **원안 대비 스코프 변경:** 원래 계획은 PIPC 결정 20 + 판례 10이었으나 `get_pipc_decision_text` MCP endpoint 장애로 법제처 해석례 20건으로 대체. `pipc-decisions/`는 endpoint 복구 시 재개 대상으로 `source-registry.json`에 사유 기록.
- 모든 파일 `verification_status: VERIFIED`, MCP 원문 verbatim 인용. [kipeum86/PIPA-expert@6b8137c](https://github.com/kipeum86/PIPA-expert/commit/6b8137c) 참조.

### 진행 중 · 대기

- **[`skills/manage-debate.md`](skills/manage-debate.md) 실제 로직** (Pattern 3) — 현재 skeleton 상태.
- **멀티라운드 토론 E2E** (킬러 피처 증명) — 후보 시나리오는 위 [Pattern 3 walkthrough](#pattern-3-walkthrough--구체-시나리오)의 EU 서버 한국 게임사.
- **Case Replay MVP** (Next.js 정적 뷰어) — 독립 트랙, 샘플 데이터 풍부 (Phase 1 E2E 케이스 + 3 mini E2E).
- **PIPC 결정문 재수집** — `get_pipc_decision_text` MCP endpoint 복구 대기.

---

## 이벤트 분류체계

`events.jsonl`은 append-only JSONL 스트림이다. 한 줄에 이벤트 하나. 현재 사용 중인 주요 타입:

| Type | Emit 주체 | 언제 | Key data |
|------|----------|------|----------|
| `case_received` | 오케스트레이터 | 사건 접수 시 | `query`, `case_id` |
| `case_classified` | 오케스트레이터 | 라우팅 결정 후 | `jurisdiction`, `domain`, `task`, `complexity`, `pipeline` |
| `agent_assigned` | 오케스트레이터 | 각 디스패치 전 | `agent_id`, `name`, `role` |
| `source_graded` | 서브에이전트 | 소스를 인용할 때 | `source`, `grade` (A/B/C/D), `citation` |
| `research_completed` | 리서치 에이전트 | 리서치 단계 종료 | `output_file`, `sources_count`, `key_findings_count` |
| `writing_completed` | 작성 에이전트 | 드래프팅 종료 | `output_file`, `sources_count` |
| `review_completed` | 리뷰 에이전트 | 리뷰 종료 | `approval` (approved / approved_with_revisions / rejected), `comments_count` |
| `revision_requested` | 오케스트레이터 | 리뷰가 `approved_with_revisions`를 리턴했을 때 | `cycle`, `max_cycles`, `critical`, `major`, `minor` |
| `error` | 모든 에이전트 | 실패 시 | `error_type`, `message`, `attempt`, `max_attempts` |
| `verbatim_verified` | 오케스트레이터 | 메타 검증 fallback | `verifier`, `reason`, `critical_pass`, `final_status` |
| `debate_round_start` / `debate_round_end` | 오케스트레이터 | Phase 2.3 — 토론 라운드별 | `round`, `participants` |
| `docx_generated` | 오케스트레이터 | 최종 어셈블 후 | `output`, `size_bytes`, `tables`, `paragraphs`, `fonts` |
| `final_output` | 오케스트레이터 | 마지막 이벤트 | `total_sources`, `grade_distribution`, `final_approval`, `agents_invoked` |

실제 라인 샘플 (Phase 1 E2E 케이스의 넥슨 소스 grading):

```json
{"id":"evt_014","ts":"2026-04-09T16:53:26Z","agent":"general-legal-research","type":"source_graded","data":{"source":"공정거래위원회 2024.1.5. 전원회의 의결 ㈜넥슨코리아의 전자상거래소비자보호법 위반행위에 대한 건 (메이플스토리 큐브·블랙큐브·버블파이터 매직바늘 확률 조작·은폐 4건, 과징금 116억 4,200만원)","grade":"A","citation":"공정위 전원회의 의결 사건번호 2021전자1052, 2024.1.5. (결정문 ID 17235)"}}
```

append-only JSONL이라서 `tail -f`로 돌아가는 케이스를 실시간 볼 수 있고, 두 케이스를 라인 단위로 diff할 수 있다. 이 스트림이 Phase 3 Case Replay 뷰어의 입력 형식이다.

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
│   ├── route-case.md                   # 분류 + 파이프라인 선택 (v2, 637줄)
│   ├── deliver-output.md               # 최종 어셈블리
│   └── manage-debate.md                # Phase 2.3 토론 로직 (skeleton)
├── scripts/
│   └── md-to-docx.py                   # DOCX 변환 (스타일 가이드 §11)
├── agents/                             # 8 하위 에이전트 (심볼릭 링크 또는 클론, gitignore)
├── output/                             # 런타임 케이스 아티팩트 ({case-id}/, gitignore)
├── samples/                            # 포트폴리오 증거용 frozen 샘플 (git 추적)
│   ├── README.md                       # 4개 샘플 케이스의 에이전트별 작업 분해
│   ├── 20260410-012238-391f/           # Phase 1 E2E 샘플 케이스 (47 events, 33 sources)
│   ├── test-T1-20260410-121640/        # Phase 2.2 T1 (PIPA 단독)
│   ├── test-T2-20260410-121640/        # Phase 2.2 T2 (PIPA ∥ GDPR)
│   └── test-regression-20260410-121640/
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
  - `korean-law` — 법제처 공개 API 래퍼. Grade A 1차 소스 (법령·판례·해석례·헌법재판소 결정)
  - `kordoc` — 대한민국 법원 판결문 조회
- **스킬 시스템**: markdown 기반 절차 문서 (`skills/*.md`)를 오케스트레이터가 서브루틴처럼 실행
- **이벤트 로깅**: JSONL (append-only, replayable)
- **결과물 포맷**: Markdown → DOCX (python-docx, 이중 폰트: Times New Roman + 맑은 고딕)

---

## 로드맵

- [x] **Phase 0** — 기술 스파이크 (`Agent` tool / MCP / 병렬 실행 검증, 6/8 PASS)
- [x] **Phase 1** — 3 에이전트 기본 파이프라인 (research → writing → review) + E2E
- [x] **Phase 2.1** — 전문가 라우팅 (8 에이전트 로스터, multi-domain 매트릭스, 이벤트 스키마)
- [x] **Phase 2.2** — Pattern 1 병렬 디스패치 (3 mini E2E 검증 완료)
- [x] **Phase 2.2 후속** — PIPA-expert `library/grade-b/` 보강 (30건)
- [ ] **Phase 2.3** — Pattern 3 멀티라운드 토론 (킬러 피처)
- [ ] **Phase 3** — Case Replay (Next.js 정적 뷰어, 다크 테마 워룸 UI)
- [ ] 8 하위 에이전트 public 배포 + 라이선스 정리
- [ ] Classification regression 테스트 하네스 (route-case.md few-shot 자동 검증)

---

## FAQ

**프로덕션에 쓸 수 있나요?**
아니요. 이건 흔치 않은 아키텍처가 E2E로 돌아간다는 걸 보여주는 포트폴리오 / 연구 프로젝트입니다. Phase 1 E2E 케이스는 진짜이고, 그 의견서 초안은 한국 변호사가 편집해서 넘길 수 있을 법한 실제 MEMORANDUM입니다. 하지만 실제 클라이언트 업무에 쓰려면 (a) AI 시스템이 드래프트했다는 명시적 고지, (b) 자격 있는 변호사의 검토, (c) 관할권별 면책조항, (d) 소속 로펌의 엔게이지먼트 정책에 따른 특권 정보 취급이 필요합니다.

**클라이언트 기밀은 어떻게 보호하나요?**
오케스트레이터와 서브에이전트는 모두 사용자의 로컬 머신에서, 사용자 본인의 Claude Code 세션에서 실행됩니다. Anthropic API 경계 바깥으로 데이터가 나가지 않습니다 — 중간 SaaS가 없습니다. 다만: Claude Code 자체는 추론을 위해 Anthropic에 프롬프트를 보냅니다. 특정 사안에 그게 허용되는지는 소속 로펌의 엔게이지먼트 정책에 따라 다릅니다. 민감한 사안은 IT / 컴플라이언스 팀에 먼저 확인하세요. 이 리포는 `output/`, `agents/`, `.env`를 의도적으로 gitignore해서 케이스 파일과 API 키가 커밋에 새어나가지 않도록 합니다.

**왜 Harvey / Casetext / 상용 법률 AI를 안 쓰나요?**
상용 도구는 닫혀 있습니다. 어떤 소스가 인용됐는지 볼 수 없고, 답이 어떻게 구성됐는지 재생할 수 없고, 직접 쓴 전문 에이전트를 swap-in할 수 없습니다. 이 프로젝트는 광택을 투명성과 맞바꿨습니다. 오늘 당장 battle-tested된 제품이 필요하면 Harvey를 쓰세요. 멀티에이전트 법률 추론이 어떻게 작동하는지 이해하고, 수정하고, 감사하고 싶다면 여기서 시작하세요.

**한국 / EU 외 다른 관할권에서도 작동하나요?**
네, 다만 에이전트는 직접 제공해야 합니다. 오케스트레이터 자체는 관할권 중립입니다. 현재 세팅이 한국/EU 중심인 이유는 하위 전문 에이전트들(`PIPA-expert`, `GDPR-expert`, `game-legal-research`, `korean-law` MCP)이 그 관할권을 커버하기 때문입니다. `US-privacy-expert`나 `Japan-corporate-expert`를 추가하려면 그 에이전트를 독립된 Claude Code 프로젝트(자체 CLAUDE.md, skills, KB, MCP 포함)로 작성하고, [`skills/route-case.md`](skills/route-case.md)에 한 행을 추가하면 됩니다. 오케스트레이터 계약은 의도적으로 얇게 설계되어 있습니다.

**파이프라인 중간에 에이전트가 실패하면 어떻게 되나요?**
실패 종류에 따라 다릅니다. 리서치 에이전트의 rate limit 에러: 1회 재시도. 작성/리뷰의 rate limit: 오케스트레이터가 MCP로 직접 메타 검증 시도 (Phase 1 E2E에서 실제 발생 — `evt_044` / `evt_045` 참조). 복구 불가능한 에러: 케이스 파일을 보존하고, `events.jsonl`에 실패 지점 기록, 사용자에게 부분 출력 보고. 조용한 drop은 없습니다.

**의견서 한 건에 얼마 드나요?**
Claude Code Max ($100/월 무제한) 기준: 추가 비용 없음. Phase 1 E2E 케이스는 서브에이전트 합산 200K 토큰을 넘었지만 marginal dollar cost는 0이었습니다. 종량제 API 기준: 복잡도와 리비전 사이클에 따라 대략 $3~10/건. 진짜 비용은 벽시계 시간입니다 — 병렬 없이 파이프라인당 5~15분, Pattern 1을 쓰면 그보다 짧음.

**제 전문 에이전트를 추가할 수 있나요?**
네. 독립된 Claude Code 에이전트로 작성하고 (원하는 구조 아무거나 — CLAUDE.md, skills, KB, MCP), (a) `agents/` 아래에 git submodule로 drop하거나 (b) 자기 위치에서 심볼릭 링크 걸면 됩니다. 라우터가 언제 그 에이전트를 부를지 알도록 [`skills/route-case.md`](skills/route-case.md)에 한 행 추가하세요. 오케스트레이터 변경은 필요 없습니다. 의도적으로 plugin 모양으로 설계되어 있습니다.

---

## 참고 문서

| 문서 | 설명 |
|------|------|
| [docs/design.md](docs/design.md) | 디자인 문서 (office-hours 6라운드 adversarial review, APPROVED 9/10) |
| [docs/notes/architecture-defense.md](docs/notes/architecture-defense.md) | 이 README의 원재료 — 확장된 "왜 이 아키텍처인가" 방어 노트 |
| [docs/ko-legal-opinion-style-guide.md](docs/ko-legal-opinion-style-guide.md) | 한국어 법률 의견서 스타일 정본 (한국어 에이전트 호출 시 강제 주입) |
| [skills/route-case.md](skills/route-case.md) | 분류 + 파이프라인 선택 로직 (v2, 637줄) |
| [skills/deliver-output.md](skills/deliver-output.md) | 최종 어셈블 절차 |
| [skills/manage-debate.md](skills/manage-debate.md) | Phase 2.3 토론 로직 (skeleton) |
| [resume.md](resume.md) | 개발 진행 상태 (세션 간 핸드오프 문서) |
| [samples/README.md](samples/README.md) | **4개 샘플 케이스의 에이전트별 작업 분해** — 누가 뭘 했고 각 artifact가 뭘 담고 있는지 |
| [samples/20260410-012238-391f/](samples/20260410-012238-391f/) | 이 README 전반에 걸쳐 참조된 샘플 케이스 |

---

## 라이선스

**Apache License 2.0** — [LICENSE](LICENSE) 참조.

하위 에이전트는 각자 리포지토리에서 별도의 라이선스를 따른다. 법률 데이터는 법제처 공개 API와 대한민국 법원 판결문(공공저작물)에서 수집한다.
