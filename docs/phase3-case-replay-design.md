# Phase 3 Design: Case Replay
> [DEPRECATED 2026-04-14] 이 문서는 Vercel 기반 정적 뷰어 접근을 전제로 작성되었으나, case-report.md 단일 파일 출력 방식으로 방향이 변경되었습니다. skills/generate-case-report.md 를 참조하세요.

**작성일:** 2026-04-13  
**대상 리포지토리:** `legal-agent-orchestrator`  
**상태:** 설계안 (구현 전)  
**목적:** Phase 3 "Case Replay"를 실제 구현 가능한 수준으로 구체화

---

## 1. 한 줄 정의

Case Replay는 **오케스트레이터가 실제로 처리한 케이스 폴더(`events.jsonl`, `sources.json`, `*-meta.json`, `*.md`, `*.docx`)를 정규화하여, API 키 없이도 브라우저에서 전체 협업 과정을 재생하듯 탐색할 수 있게 하는 정적 뷰어**다.

핵심은 "에이전트를 웹으로 옮긴다"가 아니다.  
핵심은 **이미 끝난 케이스를 설명 가능한 산출물로 보여준다**는 것이다.

---

## 2. 왜 필요한가

이 프로젝트의 강점은 단순히 최종 의견서가 아니라:

- 어떤 에이전트가 배정되었는지
- 어떤 1차 소스를 썼는지
- 어디서 오류가 났는지
- 리뷰어가 무엇을 잡아냈는지
- 수정 사이클이 어떻게 끝났는지

가 모두 남는다는 점이다.

그런데 지금은 이것을 보려면 방문자가 직접:

1. `samples/<case-id>/` 폴더를 열고
2. `events.jsonl`을 읽고
3. `research-meta.json`, `review-meta.json`, `sources.json`을 따로 열고
4. `opinion.md`와 `review-result.md`를 왔다 갔다 해야 한다.

이건 개발자에게는 가능하지만, 포트폴리오 방문자에게는 진입장벽이 높다.

Phase 3의 목적은 이 폴더 구조를 **읽기 좋은 하나의 스토리 UI**로 바꾸는 것이다.

---

## 3. 목표와 비목표

### 3.1 목표

1. `samples/manifest.json`에 등록된 공개 대상 케이스를 정적 사이트에서 탐색 가능하게 만든다.
2. 케이스 하나의 진행 흐름을 타임라인으로 보여준다.
3. 어떤 에이전트가 어떤 단계에서 무엇을 했는지 요약한다.
4. 리뷰 결과, 에러, rescue, 승인 상태를 한눈에 보이게 만든다.
5. 소스 등급 분포(Grade A/B/C/D)와 인용 목록을 탐색 가능하게 만든다.
6. 최종 deliverable과 중간 산출물을 다운로드하거나 읽을 수 있게 한다.
7. API 서버 없이 `next build` + 정적 배포만으로 동작하게 한다.

### 3.2 비목표

1. Claude Code 실행을 브라우저로 옮기지 않는다.
2. Agent tool 호출을 웹에서 live로 재생하지 않는다.
3. `output/`의 민감한 로컬 케이스를 자동으로 public 배포하지 않는다.
4. DOCX를 브라우저에서 완벽 렌더링하려고 하지 않는다.
5. 로그 스키마를 Phase 3 구현 중에 크게 뒤엎지 않는다.

---

## 4. 추천 구현 방향

Phase 3은 **별도 정적 뷰어 + 빌드 시점 정규화 파이프라인**으로 구현하는 것이 가장 적합하다.

### 4.1 왜 이 방식이 맞는가

이 프로젝트의 실행 환경은 Claude Code다. 실행과 시각화를 섞으면 다시 웹앱 중심 아키텍처가 된다.

그래서 Phase 3은 다음처럼 분리하는 게 좋다:

- 실행계: 기존 오케스트레이터 그대로
- 표시계: 이미 생성된 케이스 폴더를 읽어 정적 JSON으로 변환
- 뷰어: 그 JSON을 렌더링하는 Next.js 정적 사이트

즉, **Case Replay는 runtime이 아니라 publishing layer**다.

### 4.2 권장 스택

- 프레임워크: Next.js App Router
- 배포 형태: static export
- 언어: TypeScript
- 변환 스크립트: `tsx` 또는 Node.js
- 마크다운 렌더링: `react-markdown`
- 차트: 아주 가벼운 수준만 사용
- 스타일: CSS Modules 또는 Tailwind 중 하나로 단순하게

여기서 중요한 건 프론트엔드 기술 선택보다 **정규화 계층을 먼저 두는 것**이다.

### 4.3 정적 export 제약

Case Replay는 서버 없이 배포하는 것이 전제이므로, viewer는 처음부터 정적 export 제약을 깔고 설계하는 편이 좋다.

권장 `next.config`:

```ts
const nextConfig = {
  output: "export",
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
```

의미:

- 서버 사이드 API route 전제 금지
- 이미지 최적화 서버 의존 금지
- replay 데이터는 모두 build 시점에 `public/replays/`로 내려와 있어야 함

---

## 5. 가장 중요한 설계 원칙

### 5.1 원본 로그를 뷰어가 직접 해석하지 않는다

실제 샘플을 보면 이벤트 타입이 완전히 균일하지 않다.

예:

- 스키마 문서에는 `agent_completed`
- 실제 샘플에는 `research_completed`, `writing_completed`, `review_completed`

즉, Phase 3 뷰어가 `events.jsonl` 원문에 직접 강하게 결합되면 쉽게 깨진다.

그래서 중간에 반드시 한 단계가 더 필요하다:

1. 원본 케이스 폴더 읽기
2. 이벤트/메타/아티팩트 정규화
3. 정규화된 replay JSON 생성
4. 뷰어는 replay JSON만 읽기

이게 이번 설계의 핵심이다.

### 5.2 public 입력과 private 입력을 분리한다

- public viewer 빌드는 기본적으로 `samples/manifest.json`에 등록된 케이스만 읽는다
- `output/`는 로컬 개발자 모드에서만 읽게 한다

이렇게 해야 Phase 3가 생기더라도 민감 케이스를 실수로 publish하지 않는다.

### 5.3 "케이스 폴더"가 곧 데이터베이스다

별도 DB는 필요 없다. 이미 케이스 폴더가 append-only 사건 기록이다.

Phase 3는 그것을 DB처럼 읽어, 검색/정렬/시각화에 적합한 파생 JSON으로 바꾸는 계층일 뿐이다.

---

## 6. 시스템 전체 흐름

```mermaid
flowchart LR
    A[Claude Code orchestrator run]
    B[output/{case-id} or samples/{case-id}]
    C[Replay build script]
    D[Normalized replay JSON]
    E[Next.js static viewer]
    F[Visitor browser]

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
```

조금 더 풀어 쓰면:

1. 오케스트레이터가 케이스를 처리한다.
2. 결과가 `output/<case-id>/`에 쌓인다.
3. 공개 가능한 케이스는 `samples/<case-id>/`로 freeze하고 `samples/manifest.json`에 등록한다.
4. Replay 빌드 스크립트가 manifest를 읽고 대상 케이스만 처리한다.
5. `events.jsonl`, `sources.json`, `*-meta.json`, `*.md`, `*.docx`를 분석한다.
6. 정규화된 `index.json`, `<case-id>.json`을 만든다.
7. Next.js 정적 뷰어는 이 JSON을 읽어 화면을 그린다.
8. 최종 결과는 정적 파일이므로 API 없이 배포 가능하다.

---

## 7. 권장 디렉토리 구조

```text
legal-agent-orchestrator/
├── case-replay/
│   ├── viewer/
│   │   ├── app/
│   │   │   ├── page.tsx
│   │   │   ├── cases/[caseId]/page.tsx
│   │   │   └── layout.tsx
│   │   ├── components/
│   │   │   ├── case-hero.tsx
│   │   │   ├── timeline.tsx
│   │   │   ├── stage-cards.tsx
│   │   │   ├── source-breakdown.tsx
│   │   │   ├── review-findings.tsx
│   │   │   └── artifact-panel.tsx
│   │   ├── lib/
│   │   │   ├── replay-types.ts
│   │   │   └── load-replay.ts
│   │   ├── public/
│   │   │   └── replays/
│   │   │       ├── index.json
│   │   │       ├── 20260410-012238-391f.json
│   │   │       └── artifacts/
│   │   ├── next.config.mjs
│   │   ├── package.json
│   │   └── tsconfig.json
│   └── scripts/
│       └── build-replays.ts
├── samples/
│   ├── manifest.json
│   └── 20260410-012238-391f/
├── output/
└── docs/
    └── phase3-case-replay-design.md
```

포인트는 세 가지다:

- `viewer/`는 프론트엔드
- `scripts/`는 빌드 시점 데이터 변환기
- `public/replays/`는 정적 산출물

MVP에서는 `build-replays.ts` 하나로 시작하는 편이 좋다.  
`parseEvents()`, `normalizeCase()`, `copyArtifacts()` 같은 함수는 파일 내부 private helper로 두고, 파일이 비대해질 때만 분리한다.

---

## 8. 입력 데이터

Case Replay의 입력은 이미 리포에 존재한다.

### 8.1 공개 대상 선정: `samples/manifest.json`

MVP에서는 `samples/`의 모든 폴더를 자동 공개하지 않는다.  
반드시 `samples/manifest.json`에 등록된 케이스만 public viewer에 포함한다.

권장 형식:

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

빌드 규칙:

- manifest에 없는 폴더는 무시
- `include: false`인 케이스는 무시
- public viewer MVP는 `kind: "full_case"`만 지원

### 8.2 현재 `samples/`의 실제 상태

현재 리포의 샘플은 4개지만, 성격이 서로 다르다.

- `20260410-012238-391f`: full case
- `test-T1-20260410-121640`: 단일 에이전트 smoke test
- `test-T2-20260410-121640`: 병렬 전문가 smoke test
- `test-regression-20260410-121640`: 회귀 비교용 smoke test

즉, `test-*` 3개는:

- `events.jsonl` 없음
- `sources.json` 없음
- `review-meta.json` 없음
- 최종 `opinion.md` 없음

대신 `*-result.md`, `*-meta.json`만 존재한다.

따라서 public viewer MVP는 **manifest로 공개 대상 full case만 포함**하는 것이 맞다.  
`test-*` 케이스는 향후 minimal card view가 필요해질 때 다시 포함 여부를 판단한다.

### 8.3 full case 기준 필수 입력

- `events.jsonl`
- `sources.json`
- `*-meta.json`
- 최종 결과물 `opinion.md` 또는 `debate-opinion.md` 또는 `*-result.md`

### 8.4 선택 입력

- `review-result.md`
- `research-result.md`
- `verbatim-verification.md`
- `debate-transcript.md`
- `*.docx`

### 8.5 실제 케이스에서 추출 가능한 핵심 정보

`events.jsonl`에서:

- 케이스 시작/종료 시각
- 전체 이벤트 수
- pipeline 순서
- 에이전트 배정
- 소스 수집
- 에러/재시도
- 리뷰 승인 상태
- 최종 산출물 목록

`sources.json`에서:

- 총 소스 수
- Grade 분포
- 에이전트별 인용 목록

`*-meta.json`에서:

- summary
- key findings
- review comments
- approval

`*.md`에서:

- 사람이 읽을 수 있는 본문

---

## 9. 정규화 계층 설계

Phase 3의 실질적인 핵심은 `normalize-case.ts`다.

이 스크립트는 한 케이스 폴더를 읽어 아래 구조의 canonical JSON으로 바꾼다.

### 9.1 정규화 후 대표 타입

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
  overview: {
    summary: string;
    totalEvents: number;
    totalSources: number;
    gradeDistribution: { A: number; B: number; C: number; D: number };
    agentsInvoked: string[];
    approval: string | null;
    reviewCycle: number | null;
  };
  stages: ReplayStage[];
  timeline: ReplayTimelineEvent[];
  agents: ReplayAgentSummary[];
  artifacts: ReplayArtifact[];
  documents: ReplayDocument[];
  review: ReplayReview | null;
  sourceCatalog: ReplaySourceCatalog;
  rawEventPath: string;
};
```

### 9.2 정규화가 해야 하는 일

1. `events.jsonl` 한 줄씩 파싱
2. 이벤트 타입 alias 처리
3. 시작/종료 시각 계산
4. stage 묶음 생성
5. 에이전트별 활동 요약 생성
6. review 상태 추출
7. 최종 산출물 목록 정리
8. markdown 문서를 viewer-friendly 구조로 변환
9. 누락 필드가 있으면 fallback 적용

### 9.3 이벤트 타입 alias 매핑

실제 로그 편차를 흡수하기 위해 alias 레이어를 둔다.

예:

```ts
const EVENT_TYPE_ALIASES = {
  research_completed: "agent_completed",
  writing_completed: "agent_completed",
  review_completed: "agent_completed",
};
```

단, 원문은 버리지 않는다.

- `rawType`: 실제 로그 타입
- `canonicalType`: 정규화 후 타입

둘 다 유지해야 디버깅이 쉽다.

### 9.4 stage 분류 규칙

MVP에서는 이벤트를 6개 stage로 분류하면 충분하다.

1. Intake
2. Classification
3. Research / Specialist Work
4. Drafting / Verdict
5. Review / Revision
6. Delivery

Pattern 3은 다음처럼 확장한다.

1. Intake
2. Classification
3. Debate Round 1
4. Debate Round 2
5. Debate Round 3 (optional)
6. Verdict Writing
7. Partner Review
8. Delivery

---

## 10. replay JSON을 두 단계로 나눈다

한 파일에 모든 걸 몰아넣기보다 index와 detail을 분리하는 게 좋다.

### 10.1 `index.json`

목록 페이지에서 쓸 최소 정보만 담는다.

```json
{
  "schemaVersion": "1.0",
  "generatedAt": "2026-04-13T09:00:00Z",
  "cases": [
    {
      "caseId": "20260410-012238-391f",
      "title": "KR loot box regulation opinion",
      "query": "한국 게임산업법의 확률형 아이템(가챠) 규제에 대한 법률 의견서를 작성해줘",
      "pattern": "pattern_2",
      "status": "approved",
      "totalSources": 33,
      "gradeDistribution": { "A": 29, "B": 4, "C": 0, "D": 0 }
    }
  ]
}
```

### 10.2 `<case-id>.json`

케이스 상세 페이지에서 쓸 전체 normalized data를 담는다.

이렇게 분리하면 목록 화면은 빠르고, 상세 화면만 무거운 데이터를 읽으면 된다.

### 10.3 URL 규칙

MVP에서는 케이스 폴더명 자체를 URL slug로 그대로 사용한다.

예:

- `/cases/20260410-012238-391f`

장점:

- 폴더명과 URL이 1:1 대응
- 추가 매핑 테이블 불필요
- 케이스 재현과 디버깅이 쉬움

슬러그가 예쁘지는 않지만, Phase 3의 우선순위는 branding보다 traceability다.

---

## 11. Artifact 처리 원칙

Case Replay가 보여줘야 하는 건 세 종류다.

### 11.1 바로 렌더링할 것

- `*.md`
- `*.json`
- `events.jsonl`

### 11.2 다운로드 링크만 제공할 것

- `*.docx`

DOCX를 브라우저에서 완벽하게 보여주려 하면 복잡도만 커진다.  
이 프로젝트의 본질은 문서 뷰어를 만드는 것이 아니라 **프로세스 replay**다.

### 11.3 빌드 시 복사 규칙

공개용 build에서는:

- `samples/` 아래 artifact만 복사
- `output/`는 기본 무시
- 허용 확장자 whitelist 사용

예:

```ts
const PUBLIC_ARTIFACT_EXTENSIONS = [".md", ".json", ".jsonl", ".docx"];
```

### 11.4 버전 파일 처리 규칙

실제 샘플에는 `opinion.md`와 `opinion-v1.md`, `writing-meta.json`과 `writing-meta-v1.json`이 함께 존재한다.

MVP 규칙:

- primary document 우선순위:
  1. `debate-opinion.md`
  2. `opinion.md`
  3. `*-result.md`
- `*-v1`, `*-v2` 같은 버전 파일은 "Previous versions" 섹션으로 묶어 collapse 처리
- 목록 카드에는 최신 primary document만 노출
- 상세 페이지에서만 이전 버전을 보여준다

---

## 12. Viewer UI 설계

MVP 기준으로 페이지는 2개면 충분하다.

### 12.1 `/` 목록 페이지

보여줄 정보:

- 케이스 카드 목록
- 패턴별 필터 (`pattern_1`, `pattern_2`, `pattern_3`)
- 승인 상태 필터
- 총 소스 수 / Grade A 비율
- 에러 또는 rescue 있었는지 배지

이 페이지의 목표는 "어떤 케이스를 볼지 고르기"다.

### 12.2 `/cases/[caseId]` 상세 페이지

상세 페이지는 아래 섹션으로 구성하는 것이 좋다.

#### A. Hero

- 질문 원문
- 패턴
- 승인 상태
- 총 소스 수
- 이벤트 수
- 실행 시간

#### B. Process Summary

- 어떤 파이프라인이 돌았는지
- 참여 에이전트 목록
- 핵심 결론 3~5줄

#### C. Stage Cards

- Research
- Drafting
- Review
- Delivery

또는 Pattern 3이면 Debate Round별 카드

#### D. Timeline

`events.jsonl`을 시간순으로 시각화

- event type
- agent
- 핵심 내용
- error / rescue 강조

#### E. Review Findings

`review-meta.json`의 코멘트를 severity별로 정리

- Critical
- Major
- Minor

이 섹션은 이 프로젝트의 설득력 핵심이다.

#### F. Source Breakdown

- Grade 분포 막대
- 에이전트별 source count
- citation list

#### G. Documents & Artifacts

- `opinion.md`
- `review-result.md`
- `research-result.md`
- `verbatim-verification.md`
- `opinion.docx`

---

## 13. UI에서 강조해야 할 것

Case Replay는 화려한 모션보다 **법률 프로세스의 설명 가능성**이 중요하다.

그래서 아래 순서를 강조하는 편이 좋다.

1. 질문이 무엇이었는가
2. 누구에게 배정되었는가
3. 무엇을 근거로 답했는가
4. 어디서 문제가 생겼는가
5. 누가 무엇을 고쳤는가
6. 최종 승인되었는가

즉, "예쁜 대시보드"보다 **사건 재구성 도구**에 가까워야 한다.

---

## 14. Pattern 3를 위해 미리 고려해야 할 UI

Phase 3 뷰어는 Pattern 2뿐 아니라 Pattern 3를 받아낼 수 있어야 한다.

그래서 data model에 처음부터 다음 개념이 있어야 한다.

- `round`
- `position` (`opinion`, `rebuttal`, `surrebuttal`)
- `participants`
- `concededPoints`
- `consensusAreas`
- `disagreementAreas`

UI에서는 Pattern 3일 때만:

- Debate header
- Round tabs
- A vs B 비교 카드
- convergence / disagreement 배지

를 보이게 하면 된다.

중요한 점은 Pattern 3용으로 별도 앱을 만들지 말고, **같은 상세 페이지 안에서 pattern-aware rendering**으로 처리하는 것이다.

---

## 15. 구현 순서 추천

Phase 3은 한 번에 크게 만들기보다 세 단계로 끊는 게 좋다.

### 15.1 Phase 3A: 데이터 파이프라인

상세 구현 문서: [phase3a-data-pipeline.md](./phase3a-data-pipeline.md)

먼저 만들 것:

- `build-replays.ts`
- `replay-types.ts`

완료 조건:

- manifest에 포함된 모든 public full case가 JSON으로 변환 가능
- schema drift가 있어도 실패하지 않음
- `index.json` + `<case-id>.json` 생성됨

이 단계에서는 UI가 없어도 된다.

### 15.2 Phase 3B: Viewer MVP

상세 구현 문서: [phase3b-viewer-mvp.md](./phase3b-viewer-mvp.md)

그 다음 만들 것:

- 목록 페이지
- 상세 페이지
- timeline
- source breakdown
- document links

완료 조건:

- manifest에 포함된 모든 public case 탐색 가능
- 최종 결과와 review가 잘 보임
- 모바일에서도 읽을 수 있음

### 15.3 Phase 3C: Product polish

마지막에 추가할 것:

- severity 색상 시스템
- 에러/rescue 강조
- Pattern 3 전용 round UI
- deep-link
- 공유용 OG 이미지
- raw event inspector

### 15.4 로컬 미리보기 워크플로우

구현 문서에는 이 흐름을 명시해야 한다.

권장 개발 루프:

1. `samples/` 또는 `samples/manifest.json` 수정
2. replay JSON 재생성
3. viewer dev server 실행
4. static export 검증

권장 스크립트 이름:

```bash
pnpm replay:build-data
pnpm replay:dev
pnpm replay:export
```

의미:

- `replay:build-data`: `samples/manifest.json` 기준으로 `public/replays/` 갱신
- `replay:dev`: viewer 로컬 개발 서버
- `replay:export`: 정적 export 결과 검증

---

## 16. 구현 파일별 책임

MVP에서는 파일을 최소화한다.

### `case-replay/scripts/build-replays.ts`

책임:

- `samples/manifest.json` 읽기
- 대상 케이스 순회
- `events.jsonl` 파싱
- 이벤트 alias 정규화
- stage / overview / artifacts 계산
- `index.json` 및 케이스별 detail JSON 생성
- public artifact 복사

내부 helper 함수 예시:

```ts
parseEvents()
normalizeCase()
collectArtifacts()
copyPublicArtifacts()
buildIndex()
```

파일이 300~400줄 이상으로 커질 때만 `parse-events.ts`, `normalize-case.ts` 등으로 분리한다.

### `case-replay/viewer/app/page.tsx`

책임:

- 케이스 목록 렌더링

### `case-replay/viewer/app/cases/[caseId]/page.tsx`

책임:

- 케이스 상세 렌더링

---

## 17. fallback 전략

실제 로그는 항상 깔끔하지 않다. 그래서 아래 fallback이 필요하다.

### 17.1 `sources.json`이 없을 때

- 각 `*-meta.json`의 `sources`를 병합해서 대체 생성

### 17.2 `review-meta.json`이 없을 때

- `events.jsonl`의 `review_completed` 또는 `final_output`에서 approval 유추

### 17.3 최종 markdown이 없을 때

- `final_output.deliverables` 기준으로 artifact 링크만 표시

### 17.4 event type이 문서 스키마와 다를 때

- alias 매핑 후 canonical type으로 처리

### 17.5 duration 계산이 불가능할 때

- `startedAt`만 보여주고 wall-clock time은 숨김

---

## 18. 보안 및 공개 정책

이 문서는 public viewer를 전제로 한다.

따라서 반드시 다음 원칙을 지킨다.

1. 기본 입력은 `samples/`만 허용
2. `output/`는 명시적 로컬 모드에서만 허용
3. public build 전에 artifact whitelist 적용
4. 필요 시 `redaction-manifest.json`을 도입할 수 있게 설계
5. public build에서는 `samples/manifest.json`에 등록된 케이스만 포함

향후 private case replay가 필요하면:

- `samples/`용 public pipeline
- `output/`용 local-only pipeline

을 분리하면 된다.

---

## 19. 예상 사용자 흐름

### 19.1 포트폴리오 방문자

1. 목록 화면에서 케이스를 고른다
2. "질문 → 에이전트 배정 → 리뷰 → 승인" 흐름을 본다
3. 리뷰어가 실제로 뭘 잡아냈는지 확인한다
4. 최종 의견서와 소스 목록을 열어본다

### 19.2 개발자/평가자

1. 타임라인과 stage 묶음을 본다
2. 필요 시 원본 JSON 다운로드 링크를 연다
3. rescue / error handling을 본다
4. 이 시스템이 단순 roleplay가 아니라 실제 프로세스 엔진이라는 점을 이해한다

---

## 20. MVP에서 꼭 들어가야 하는 화면 요소

정말 최소로 줄이면 아래 8개면 충분하다.

1. 케이스 목록
2. 질문 원문
3. pipeline / agents
4. 승인 상태
5. timeline
6. review findings
7. source distribution
8. artifact links

이 8개만 있어도 Phase 3는 이미 의미가 있다.

반대로 아래는 후순위다.

- fancy animation
- live filtering on every field
- docx inline rendering
- full-text search across all markdown

---

## 21. 수용 기준

Phase 3 MVP가 "됐다"고 말하려면 최소한 아래를 만족해야 한다.

1. `samples/manifest.json`에 포함된 모든 public case가 viewer에서 열린다
2. 각 케이스의 질문, pattern, agents, sources, approval이 보인다
3. `events.jsonl` 기반 timeline이 시간순으로 보인다
4. review findings가 severity별로 보인다
5. 최종 결과물 링크가 열린다
6. 정적 빌드 결과가 API 없이 동작한다
7. schema drift가 있어도 build가 중단되지 않는다
8. manifest에 없는 케이스는 public output에 포함되지 않는다

---

## 22. 구현 전에 먼저 고쳐두면 좋은 것

Case Replay 구현 전에 아래 문서/데이터 정리는 도움이 된다.

### 22.1 `events-schema.json` 신설

`skills/route-case.md`의 부록 설명만으로는 기계 검증이 어렵다.  
정식 JSON Schema 파일이 있으면 빌드 스크립트에서 validation하기 쉬워진다.

다만 이것은 **MVP 전제조건은 아니다**.  
alias 레이어만 잘 두면 Phase 3A를 먼저 진행할 수 있고, 정식 schema 파일은 후속 작업으로 분리해도 된다.

### 22.2 이벤트 타입 일관화

앞으로 생성되는 로그부터는 가능하면:

- `agent_completed`
- `review_completed`
- `docx_generated`
- `final_output`

같은 canonical naming을 유지하는 편이 좋다.

기존 샘플은 alias로 흡수하면 된다.

### 22.3 `sources.json` 생성 규칙 고정

현재 일부 샘플은 `final_output.total_sources`와 `sources.json.total_sources`가 다를 수 있다.  
Phase 3에서는 어느 값을 화면에 표준으로 보여줄지 정해야 한다.

권장:

- summary badge: `final_output.total_sources`
- 상세 catalog count: 실제 deduplicated source count

이렇게 둘을 구분 표기한다.

---

## 23. "이게 실제로 어떻게 돌아가나?"를 한 문단으로 설명하면

오케스트레이터가 케이스를 처리하면 `output/<case-id>/` 폴더 하나가 생긴다.  
그 안에는 사건 접수부터 최종 DOCX 생성까지의 모든 이벤트 로그와, 각 에이전트가 남긴 요약 JSON, 중간 문서, 최종 결과물이 들어 있다.  
Phase 3는 이 폴더를 읽어 사람이 보기 쉬운 구조로 다시 묶는다.  
즉, **실행 중인 AI를 보여주는 게 아니라, 이미 끝난 케이스를 재구성해서 보여주는 정적 퍼블리싱 레이어**다.

---

## 24. 최종 권고

Phase 3는 다음 순서로 구현하는 것이 가장 좋다.

1. **`samples/manifest.json`부터 도입한다**
2. **정규화 스크립트부터 만든다**
3. 그다음 **정적 viewer MVP**를 만든다
4. 마지막에 **Pattern 3와 디자인 polish**를 얹는다

가장 피해야 할 접근은:

- 뷰어가 원본 `events.jsonl`에 직접 강결합되는 것
- `output/`를 그대로 public asset으로 노출하는 것
- DOCX 렌더링 문제를 Phase 3 핵심으로 오해하는 것

Case Replay의 본질은 문서 뷰어가 아니라 **법률 협업 프로세스의 설명 가능한 재생**이다.
