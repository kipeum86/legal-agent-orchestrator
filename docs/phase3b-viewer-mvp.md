# Phase 3B: Case Replay Viewer MVP
> [DEPRECATED 2026-04-14] 이 문서는 Vercel 기반 정적 뷰어 접근을 전제로 작성되었으나, case-report.md 단일 파일 출력 방식으로 방향이 변경되었습니다. skills/generate-case-report.md 를 참조하세요.

**작성일:** 2026-04-13  
**상위 문서:** [phase3-case-replay-design.md](./phase3-case-replay-design.md)  
**선행 조건:** [phase3a-data-pipeline.md](./phase3a-data-pipeline.md) 완료  
**목적:** 3A가 생성한 정적 replay JSON을 읽어 목록/상세 페이지를 렌더링하는 Case Replay viewer MVP 구현

---

## 1. 3B의 역할

3B는 **이미 만들어진 replay JSON을 읽어 사람이 이해하기 쉬운 화면으로 그리는 단계**다.

입력:

- `public/replays/index.json`
- `public/replays/<case-id>.json`
- `public/replays/artifacts/<case-id>/*`

출력:

- `/` 목록 페이지
- `/cases/[caseId]` 상세 페이지

즉:

> 3A가 데이터를 만든다면, 3B는 그 데이터를 설명 가능한 UI로 바꾼다.

---

## 2. MVP 범위

### 2.1 포함

- 정적 export 가능한 Next.js viewer
- 목록 페이지
- 케이스 상세 페이지
- timeline
- review findings
- source breakdown
- artifact links

### 2.2 제외

- raw event inspector
- full-text search
- 복잡한 애니메이션
- 다국어 UI
- smoke test minimal view
- Pattern 3 전용 시각 요소

---

## 3. 기술 제약

3B는 정적 export를 전제로 한다.

권장 `next.config.mjs`:

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

- API route 없음
- SSR 의존 없음
- 데이터는 전부 `public/replays/`에서 읽음

---

## 4. 파일 구조

```text
case-replay/viewer/
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   └── cases/[caseId]/page.tsx
├── components/
│   ├── case-card.tsx
│   ├── case-hero.tsx
│   ├── process-summary.tsx
│   ├── stage-cards.tsx
│   ├── timeline.tsx
│   ├── review-findings.tsx
│   ├── source-breakdown.tsx
│   └── artifact-panel.tsx
├── lib/
│   ├── replay-types.ts
│   └── load-replay.ts
├── public/
│   └── replays/
└── package.json
```

MVP에서는 이것보다 더 쪼갤 필요는 없다.

---

## 5. 페이지 설계

### 5.1 `/` 목록 페이지

목적:

- “이 프로젝트에 어떤 케이스들이 공개되어 있는가”를 한눈에 보여주기

필수 요소:

- 케이스 카드 목록
- title
- query 요약 1~2줄
- pattern badge
- status badge
- total source count
- Grade A 비율
- error/rescue badge

권장 상단 헤더:

- 페이지 제목: `Case Replay`
- 짧은 설명: “실제 처리된 법률 케이스의 협업 과정을 정적 replay로 탐색”

### 5.2 `/cases/[caseId]` 상세 페이지

목적:

- 한 케이스를 “사건 재구성” 관점에서 읽게 하기

섹션 순서:

1. Hero
2. Process Summary
3. Stage Cards
4. Timeline
5. Review Findings
6. Source Breakdown
7. Documents & Artifacts

이 순서를 유지하는 이유는, 사용자가 사건을 이해하는 흐름과 일치하기 때문이다.

---

## 6. 목록 페이지 상세 스펙

### 6.1 CaseCard 컴포넌트

표시 필드:

- `title`
- `caseId`
- `query`
- `pattern`
- `status`
- `totalSources`
- `gradeDistribution`
- `hasErrors`
- `hasRescue`

권장 카드 구조:

1. 상단: title + pattern/status badge
2. 중단: query 요약
3. 하단: sources / events / error-rescue badge

### 6.2 필터

MVP에서는 복잡한 검색 대신 아래 정도면 충분하다.

- pattern filter
- status filter

텍스트 검색은 후순위다.

### 6.3 empty state

manifest에 public case가 없으면:

```text
No public replay cases available yet.
```

정도로 간단히 처리.

---

## 7. 상세 페이지 상세 스펙

### 7.1 Hero

표시:

- title
- query 원문
- caseId
- pattern
- status
- startedAt / endedAt
- wallClockSeconds
- totalSources
- totalEvents

Hero 목표:

- 사용자가 “무슨 사건인지” 5초 안에 이해

### 7.2 Process Summary

표시:

- agents invoked
- approval label
- 3~5줄 요약

요약 소스:

- `overview.summary`
- 없으면 `writing-meta.summary` 또는 `review-meta.summary`

### 7.3 Stage Cards

stage별 카드 표시:

- label
- agents
- startedAt / endedAt
- summary
- linked artifacts

카드는 timeline 전체를 읽기 전에 큰 그림을 잡는 역할이다.

### 7.4 Timeline

정렬 기준:

- `ts` ascending

표시:

- 시간
- agent
- label
- summary
- severity

강조:

- `error`는 빨간 계열
- `verbatim_verified` 같은 rescue는 강조 배지

### 7.5 Review Findings

이 섹션은 매우 중요하다.

표시:

- approval
- comments count
- severity별 그룹
- 각 comment의 `location`, `issue`, `recommendation`

그룹 순서:

1. Critical
2. Major
3. Minor

### 7.6 Source Breakdown

표시:

- grade distribution
- agent별 source count
- citation list

MVP에서는 막대 차트보다 텍스트/배지 조합이 더 안정적이다.

예:

- Grade A: 29
- Grade B: 4
- Grade C: 0
- Grade D: 0

### 7.7 Documents & Artifacts

표시:

- primary document
- previous versions
- review markdown
- research markdown
- event log
- docx download

artifact는 inline preview보다 링크 중심이 낫다.

---

## 8. 데이터 로딩 방식

### 8.1 목록 페이지

`/replays/index.json`을 읽는다.

권장 방식:

- build-time import 또는 fetch
- static export에 걸리지 않는 단순 방식 사용

### 8.2 상세 페이지

`/replays/<case-id>.json`을 읽는다.

주의:

- 존재하지 않는 caseId면 404 처리 필요
- static export이므로 가능한 caseId는 build 시점에 알아야 한다

권장:

- `generateStaticParams`에서 `index.json` 또는 local data source 기반으로 caseId 목록 생성

---

## 9. 컴포넌트 책임

### `case-card.tsx`

- 목록 카드 UI

### `case-hero.tsx`

- 제목 / query / badge / top metrics

### `process-summary.tsx`

- overview summary + agents

### `stage-cards.tsx`

- stage list 렌더링

### `timeline.tsx`

- canonical timeline 렌더링

### `review-findings.tsx`

- severity별 코멘트 그룹

### `source-breakdown.tsx`

- grade counts + citation list

### `artifact-panel.tsx`

- markdown / jsonl / docx 링크 모음

---

## 10. UI 톤과 시각 원칙

MVP의 우선순위는 화려함이 아니라 신뢰감이다.

권장 방향:

- 밝은 배경
- 문서형 레이아웃
- 상태 배지는 분명하게
- 카드 그림자 최소화
- 표와 로그는 읽기 우선

피해야 할 것:

- 너무 스타트업 대시보드 같은 과한 그래디언트
- 의미 없는 애니메이션
- 정보보다 장식이 앞서는 카드 디자인

이 viewer는 “AI showreel”보다 “감사 가능한 사건 리플레이어”에 가깝다.

---

## 11. 모바일 대응

필수:

- 카드 세로 스택
- timeline 가로 넘침 방지
- 긴 query 줄바꿈
- code / citation overflow 처리

모바일에서 가장 먼저 무너지는 부분:

- 긴 caseId
- 긴 법률 citation
- review comment 본문

따라서:

- `word-break`
- `overflow-x: auto`
- 적당한 line clamp

가 필요하다.

---

## 12. artifact UX 규칙

### 12.1 markdown

가능하면 viewer 내 새 페이지보다 같은 상세 화면 안의 링크/펼침 구조가 낫다.

MVP 선택지:

- 가장 단순: 새 탭 링크
- 한 단계 더 나은 형태: `details` / collapse preview

첫 구현은 새 탭 링크로 충분하다.

### 12.2 docx

항상 다운로드 링크로 처리한다.

### 12.3 events.jsonl

MVP에서는 raw inspector 대신 아래 두 가지면 충분하다.

- `events.jsonl` 다운로드 링크
- timeline에 canonical summary 표시

---

## 13. 상태/배지 규칙

### 13.1 pattern badge

- `pattern_1`
- `pattern_2`
- `pattern_3`
- `unknown`

### 13.2 status badge

- approved
- approved_with_revisions
- revision_needed
- partial
- failed

### 13.3 event severity color

- info: neutral
- warning: amber
- error: red

`verbatim_verified`는 error가 아니라 rescue success이므로 별도 success badge가 좋다.

---

## 14. 3B 구현 순서

### Step 1

Next.js viewer 앱을 초기화한다.

### Step 2

`next.config.mjs`에 `output: "export"`를 넣는다.

### Step 3

`lib/replay-types.ts`를 3A와 공유한다.

### Step 4

`lib/load-replay.ts`에 `loadIndex()`, `loadCase(caseId)`를 만든다.

### Step 5

`/` 목록 페이지를 먼저 구현한다.

### Step 6

`/cases/[caseId]` 상세 페이지 골격을 구현한다.

### Step 7

timeline, review, artifacts 섹션을 붙인다.

### Step 8

정적 export가 실제로 깨지지 않는지 확인한다.

---

## 15. 권장 package.json scripts

```json
{
  "scripts": {
    "replay:build-data": "tsx ../scripts/build-replays.ts",
    "replay:dev": "next dev",
    "replay:build": "next build",
    "replay:export": "next build"
  }
}
```

정적 export 환경에서는 `next build` 자체가 export 결과를 내게 구성하면 된다.

---

## 16. 로컬 개발 루프

매우 중요하다. 구현 중에는 아래 순서를 반복한다.

1. `samples/manifest.json` 또는 `samples/` 수정
2. `pnpm replay:build-data`
3. `pnpm replay:dev`
4. 브라우저에서 `/`와 `/cases/20260410-012238-391f` 확인
5. 마지막에 `pnpm replay:export`

이 루프가 문서에 명시돼 있어야, 나중에 viewer와 data pipeline이 따로 놀지 않는다.

---

## 17. 수용 기준

3B가 끝났다고 말하려면 최소한 다음을 만족해야 한다.

1. `/`에서 manifest 기반 public case 카드가 보인다.
2. 카드에서 `20260410-012238-391f` 상세 페이지로 이동 가능하다.
3. 상세 페이지에서 query, status, pattern, source count가 보인다.
4. timeline이 시간순으로 렌더링된다.
5. `review-meta.json` 기반 Critical / Major / Minor 코멘트가 보인다.
6. `opinion.md`, `review-result.md`, `research-result.md`, `events.jsonl`, `opinion.docx` 링크가 보인다.
7. 모바일 폭에서도 레이아웃이 깨지지 않는다.
8. `pnpm replay:export`가 성공한다.

---

## 18. 이번 단계에서 하지 말 것

- 검색 기능부터 만들지 말 것
- chart library부터 넣지 말 것
- Pattern 3 전용 탭 UI를 먼저 만들지 말 것
- raw event inspector를 MVP에 억지로 넣지 말 것
- smoke test 화면까지 한 번에 해결하려고 하지 말 것

---

## 19. 3B 완료 후 3C로 넘길 것

3C로 넘길 후속 과제:

- raw event inspector
- Pattern 3 round tabs
- richer source charts
- OG image
- 공유 링크 polish
- smoke test minimal replay view

즉 3B는 “읽을 수 있는 viewer”까지만 책임진다.
