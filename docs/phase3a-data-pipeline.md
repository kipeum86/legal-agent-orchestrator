# Phase 3A: Case Replay Data Pipeline
> [DEPRECATED 2026-04-14] 이 문서는 Vercel 기반 정적 뷰어 접근을 전제로 작성되었으나, case-report.md 단일 파일 출력 방식으로 방향이 변경되었습니다. skills/generate-case-report.md 를 참조하세요.

**작성일:** 2026-04-13  
**상위 문서:** [phase3-case-replay-design.md](./phase3-case-replay-design.md)  
**목적:** `samples/manifest.json`에 등록된 full case를 viewer가 읽을 수 있는 정적 replay JSON으로 변환하는 데이터 파이프라인 구현

---

## 1. 3A의 역할

3A는 화면을 만드는 단계가 아니다.  
3A는 **케이스 폴더를 화면용 데이터로 바꾸는 단계**다.

입력:

- `samples/manifest.json`
- `samples/<case-id>/events.jsonl`
- `samples/<case-id>/sources.json`
- `samples/<case-id>/*-meta.json`
- `samples/<case-id>/*.md`
- `samples/<case-id>/*.docx`

출력:

- `case-replay/viewer/public/replays/index.json`
- `case-replay/viewer/public/replays/<case-id>.json`
- `case-replay/viewer/public/replays/artifacts/<case-id>/*`

한 줄로 말하면:

> 3A는 `samples/<case-id>/`를 읽어서 `public/replays/` 아래의 정적 소비용 JSON + artifact set으로 변환한다.

---

## 2. 이번 단계의 범위

### 2.1 포함

- `samples/manifest.json` 파싱
- `kind: "full_case"`만 처리
- 이벤트 로그 파싱 및 alias 정규화
- 케이스 overview 계산
- stage 카드 데이터 생성
- artifact 목록 생성
- public artifact 복사
- `index.json` / `<case-id>.json` 생성

### 2.2 제외

- Next.js UI 구현
- Pattern 3 전용 round UI
- smoke test용 minimal replay
- full-text search
- raw event inspector
- JSON Schema 파일 강제 validation

---

## 3. 전제

MVP에서는 `samples/manifest.json`이 public viewer의 단일 진입점이다.

현재 manifest 예시:

```json
{
  "schemaVersion": "1.0",
  "cases": [
    {
      "caseId": "20260410-012238-391f",
      "title": "KR loot box regulation opinion",
      "kind": "full_case",
      "include": true
    }
  ]
}
```

현재 `samples/` 실제 상태:

- `20260410-012238-391f`: full case
- `test-T1-20260410-121640`: smoke test
- `test-T2-20260410-121640`: smoke test
- `test-regression-20260410-121640`: smoke test

즉, 3A MVP는 사실상 현재 `20260410-012238-391f` 1건을 안정적으로 변환하는 것이 1차 목표다.

---

## 4. 구현 산출물

### 4.1 파일 구조

```text
case-replay/
├── scripts/
│   └── build-replays.ts
└── viewer/
    ├── public/
    │   └── replays/
    │       ├── index.json
    │       ├── 20260410-012238-391f.json
    │       └── artifacts/
    │           └── 20260410-012238-391f/
    └── lib/
        └── replay-types.ts
```

### 4.2 생성해야 하는 JSON

1. `index.json`
2. `<case-id>.json`

### 4.3 복사해야 하는 artifact

허용 확장자:

- `.md`
- `.json`
- `.jsonl`
- `.docx`

단, 원본 케이스 폴더 전체를 통째로 복사하지 말고 whitelist 기준으로만 복사한다.

---

## 5. build-replays.ts 책임

`build-replays.ts` 하나로 시작한다.  
파일 내부 helper 함수 분리는 허용하되, 초기에는 별도 파일 쪼개기를 하지 않는다.

이 스크립트가 해야 할 일:

1. manifest 읽기
2. `include: true` + `kind: "full_case"` 케이스만 선택
3. 케이스 디렉토리 존재 여부 검증
4. 필수 파일 존재 여부 검증
5. `events.jsonl` 파싱
6. 이벤트 alias 정규화
7. overview 계산
8. stage 계산
9. artifact 목록 계산
10. source catalog 계산
11. `index.json` 생성
12. `<case-id>.json` 생성
13. public artifact 복사

권장 helper 함수:

```ts
readManifest()
loadCaseDirectory()
parseJsonl()
canonicalizeEvent()
collectArtifacts()
buildOverview()
buildStages()
buildTimeline()
buildReplayCase()
buildReplayIndex()
copyArtifacts()
```

---

## 6. 입력 파일 계약

### 6.1 manifest 계약

필수 필드:

- `schemaVersion`
- `cases[]`
- `cases[].caseId`
- `cases[].title`
- `cases[].kind`
- `cases[].include`

MVP에서 허용하는 `kind`:

- `full_case`

허용하지 않는 `kind`:

- `agent_smoke_test`
- 기타 미래 타입

허용하지 않는 타입은 무시하거나 warning을 출력한다.

### 6.2 full case 필수 파일

케이스 디렉토리 내부에 아래 파일이 있어야 한다.

- `events.jsonl`
- `sources.json`
- 최소 1개 이상의 `*-meta.json`
- primary document 후보 중 하나:
  - `opinion.md`
  - `debate-opinion.md`
  - `*-result.md`

### 6.3 누락 허용 파일

없어도 build를 깨지 않게 처리:

- `review-result.md`
- `verbatim-verification.md`
- `opinion.docx`
- `debate-transcript.md`

---

## 7. 데이터 모델

3A는 아래 두 타입을 생성한다고 생각하면 된다.

### 7.1 ReplayIndexEntry

```ts
type ReplayIndexEntry = {
  caseId: string;
  title: string;
  query: string;
  pattern: "pattern_1" | "pattern_2" | "pattern_3" | "unknown";
  status: "approved" | "approved_with_revisions" | "revision_needed" | "partial" | "failed";
  totalEvents: number;
  totalSources: number;
  gradeDistribution: { A: number; B: number; C: number; D: number };
  agentsInvoked: string[];
  hasErrors: boolean;
  hasRescue: boolean;
};
```

### 7.2 ReplayCase

```ts
type ReplayCase = {
  schemaVersion: "1.0";
  caseId: string;
  title: string;
  query: string;
  pattern: "pattern_1" | "pattern_2" | "pattern_3" | "unknown";
  status: "approved" | "approved_with_revisions" | "revision_needed" | "partial" | "failed";
  startedAt: string;
  endedAt: string | null;
  wallClockSeconds: number | null;
  overview: ReplayOverview;
  timeline: ReplayTimelineEvent[];
  stages: ReplayStage[];
  agents: ReplayAgentSummary[];
  sourceCatalog: ReplaySourceCatalog;
  artifacts: ReplayArtifact[];
  primaryDocument: ReplayDocumentRef | null;
  previousVersions: ReplayDocumentRef[];
  review: ReplayReview | null;
  raw: {
    eventsPath: string;
    sourcePath: string | null;
  };
};
```

이 타입은 3A에서 안정적으로 만들어져야 3B가 쉬워진다.

---

## 8. 이벤트 파싱 규칙

### 8.1 JSONL 파싱

`events.jsonl`은 한 줄에 이벤트 하나다.

파서 규칙:

1. 파일 전체를 line split
2. 빈 줄 제거
3. 각 줄 `JSON.parse`
4. parse 실패 시 파일 전체 build를 죽이지 말고 해당 케이스 실패 처리

권장 에러 메시지:

```text
[replay] Failed to parse events.jsonl for case 20260410-012238-391f at line 23
```

### 8.2 최소 필드

각 이벤트에서 최소 기대 필드:

- `id`
- `ts`
- `agent`
- `type`
- `data`

누락 시:

- event 자체는 유지
- canonicalization 시 warning 남김

### 8.3 canonical type alias

실제 샘플과 문서 스키마가 어긋날 수 있으므로 alias 레이어를 둔다.

```ts
const EVENT_TYPE_ALIASES = {
  research_completed: "agent_completed",
  writing_completed: "agent_completed",
  review_completed: "agent_completed",
};
```

정규화된 이벤트에는 둘 다 보존한다.

```ts
type ReplayTimelineEvent = {
  id: string;
  ts: string;
  agent: string;
  rawType: string;
  canonicalType: string;
  label: string;
  severity: "info" | "warning" | "error";
  summary: string;
  data: Record<string, unknown>;
};
```

---

## 9. 케이스 요약 계산 규칙

overview는 여러 파일에서 끌어와야 한다.

### 9.1 query

우선순위:

1. `case_received.data.query`
2. manifest title만 있고 query가 없으면 빈 문자열

### 9.2 pattern

우선순위:

1. `case_classified.data.pattern`
2. `final_output.data.pattern`
3. fallback `"unknown"`

현재 샘플 `20260410-012238-391f`는 `pattern`이 이벤트에 명시되지 않았을 수 있으므로 fallback 허용이 필요하다.

권장 fallback:

- `pipeline` 길이와 deliverables 기준으로 `pattern_2` 추론 가능하면 추론
- 아니면 `unknown`

### 9.3 status

우선순위:

1. `review-meta.json.approval`
2. `final_output.data.final_approval`
3. `pipeline_aborted`
4. fallback `"partial"`

주의:

- `approved_with_revisions`는 최종 승인 상태가 아니라 중간 리뷰 상태일 수 있다
- 최종 `final_output.data.final_approval`가 있으면 그 값을 사람이 읽는 badge용으로 따로 보존한다

즉:

- machine-friendly `status`
- display-friendly `approvalLabel`

를 분리하는 편이 좋다.

### 9.4 totalSources

우선순위:

1. `final_output.data.total_sources`
2. `sources.json.total_sources`
3. deduped catalog count

### 9.5 gradeDistribution

우선순위:

1. `final_output.data.grade_distribution`
2. `sources.json.grade_distribution`
3. sources 집계

### 9.6 hasErrors / hasRescue

다음 이벤트가 있으면 true:

- `error` → `hasErrors`
- `verbatim_verified`, `mcp_fallback_verification` → `hasRescue`

---

## 10. stage 계산 규칙

MVP stage는 6개 고정으로 충분하다.

1. Intake
2. Classification
3. Research / Specialist Work
4. Drafting / Verdict
5. Review / Revision
6. Delivery

### 10.1 이벤트별 stage 분류 예시

| canonicalType | stage |
|---|---|
| `case_received` | Intake |
| `case_classified` | Classification |
| `agent_assigned` | Research 또는 Drafting 또는 Review |
| `source_graded` | 현재 활성 stage 유지 |
| `agent_completed` | 현재 활성 stage 유지 |
| `error` | 직전 stage 유지 |
| `verbatim_verified` | Review / Revision |
| `docx_generated` | Delivery |
| `final_output` | Delivery |

### 10.2 실제 분류 방법

이벤트 타입만으로 부족하므로 `agent`도 함께 본다.

예:

- `general-legal-research`, `PIPA-expert`, `GDPR-expert`, `game-legal-research` → Research / Specialist
- `legal-writing-agent` → Drafting / Verdict
- `second-review-agent` → Review / Revision
- `orchestrator` + `docx_generated` / `final_output` → Delivery

### 10.3 Stage 구조

```ts
type ReplayStage = {
  id: string;
  label: string;
  startedAt: string | null;
  endedAt: string | null;
  agents: string[];
  summary: string;
  eventIds: string[];
  artifactIds: string[];
};
```

3A에서 stage summary는 자동 요약이 아니라 규칙 기반 문장으로 충분하다.

예:

- `"general-legal-research가 14개 소스를 수집하고 research-result.md를 생성"`
- `"second-review-agent가 approved_with_revisions 판단과 9개 코멘트를 반환"`

---

## 11. artifact 규칙

### 11.1 artifact 분류

artifact는 아래 4종류면 충분하다.

- `event_log`
- `meta`
- `markdown`
- `docx`

### 11.2 primary document 선정

우선순위:

1. `debate-opinion.md`
2. `opinion.md`
3. `*-result.md`

### 11.3 previous versions

`opinion-v1.md`, `writing-meta-v1.json` 같은 파일은 previous versions로 분리한다.

정규식 예:

- `/-v\d+\./`

### 11.4 artifact 복사 경로

원본:

```text
samples/20260410-012238-391f/opinion.md
```

복사 대상:

```text
case-replay/viewer/public/replays/artifacts/20260410-012238-391f/opinion.md
```

JSON에는 public 경로만 넣는다.

예:

```json
{
  "label": "Final opinion (Markdown)",
  "kind": "markdown",
  "path": "/replays/artifacts/20260410-012238-391f/opinion.md"
}
```

---

## 12. meta 파일별 처리 규칙

### 12.1 `research-meta.json`

주로:

- summary
- key_findings
- sources

를 읽는다.

### 12.2 `writing-meta.json`

주로:

- summary
- key_findings
- revision_cycle
- sources

를 읽는다.

### 12.3 `review-meta.json`

주로:

- approval
- comments
- summary
- key_findings

를 읽는다.

이 파일은 3B의 Review Findings 섹션 핵심 데이터다.

### 12.4 메타 파일 자동 발견

MVP 규칙:

- `review-meta*.json` 중 최신 우선
- `writing-meta*.json` 중 최신 우선
- `research-meta*.json` 우선

버전 판별:

- `-vN` 없는 파일 우선
- 있으면 가장 큰 `N`

---

## 13. 에이전트 요약 생성

`agents[]`는 화면에서 “누가 일했는가”를 보여주는 요약이다.

필드 예:

```ts
type ReplayAgentSummary = {
  agentId: string;
  displayName: string;
  role: string | null;
  stages: string[];
  sourcesCount: number;
  artifactIds: string[];
};
```

데이터 추출:

- `agent_assigned.data.name`
- `agent_assigned.data.role`
- `source_graded` 개수
- agent 관련 artifact

---

## 14. index.json 생성 규칙

`index.json`은 목록 페이지용으로 가볍게 유지한다.

포함:

- title
- query
- caseId
- pattern
- status
- totalSources
- gradeDistribution
- totalEvents
- agentsInvoked
- hasErrors
- hasRescue

포함하지 않을 것:

- 긴 summary 본문
- 리뷰 코멘트 전문
- 전체 타임라인

---

## 15. 로깅과 warning 원칙

3A 스크립트는 완벽한 데이터만 받는다고 가정하면 안 된다.

권장 원칙:

- 잘못된 케이스 1건 때문에 전체 build를 무조건 죽이지 않는다
- 단, manifest에 포함된 full case가 실패하면 마지막에 non-zero exit 가능

권장 출력 예:

```text
[replay] Loaded manifest: 1 public case
[replay] Building case 20260410-012238-391f
[replay] Copied 12 artifacts
[replay] Wrote index.json
[replay] Done
```

warning 예:

```text
[replay][warn] Missing review-result.md for case 20260410-012238-391f
[replay][warn] Unknown event type "revision_requested"; kept as rawType
```

---

## 16. 구현 순서

### Step 1

`case-replay/` 디렉토리와 최소 `viewer/public/replays/` 경로를 만든다.

### Step 2

`viewer/lib/replay-types.ts`에 타입을 정의한다.

### Step 3

`build-replays.ts`에서 manifest 파싱을 구현한다.

### Step 4

single case load + validation을 구현한다.

### Step 5

`events.jsonl` 파싱 + alias 정규화를 구현한다.

### Step 6

overview / stages / timeline / agents / artifacts 계산을 구현한다.

### Step 7

artifact copy를 구현한다.

### Step 8

`index.json`, `<case-id>.json` 쓰기를 구현한다.

### Step 9

샘플 1건 기준으로 결과를 사람이 읽어 검증한다.

---

## 17. 권장 npm 스크립트

viewer `package.json` 기준:

```json
{
  "scripts": {
    "replay:build-data": "tsx ../scripts/build-replays.ts"
  }
}
```

실제 경로는 workspace 구조에 맞춰 조정하면 된다.

핵심은 이름을 일관되게 두는 것이다.

---

## 18. 수용 기준

3A가 끝났다고 말하려면 최소한 다음을 만족해야 한다.

1. `samples/manifest.json`을 읽는다.
2. manifest에 등록된 `20260410-012238-391f`를 정상 처리한다.
3. `index.json`이 생성된다.
4. `20260410-012238-391f.json`이 생성된다.
5. final opinion, review, research, event log 경로가 JSON에 포함된다.
6. artifact가 `public/replays/artifacts/20260410-012238-391f/` 아래 복사된다.
7. `error`와 `verbatim_verified`가 timeline에 각각 error/rescue 성격으로 반영된다.
8. `opinion-v1.md`는 previous version으로 분리된다.

---

## 19. 이번 단계에서 하지 말 것

- `test-*` smoke test를 억지로 viewer에 넣지 말 것
- Pattern 3 전용 데이터 모델을 먼저 과하게 최적화하지 말 것
- UI 필요를 이유로 3A JSON을 과하게 뷰 전용으로 찢지 말 것
- DOCX inline rendering 문제를 해결하려 들지 말 것

---

## 20. 3A 완료 후 3B로 넘길 것

3B에 넘길 최소 확정물:

1. `ReplayIndexEntry` 타입
2. `ReplayCase` 타입
3. `index.json`
4. case detail JSON 1건
5. public artifact 경로 체계

3B는 이 다섯 개가 안정화되면 바로 붙일 수 있다.
