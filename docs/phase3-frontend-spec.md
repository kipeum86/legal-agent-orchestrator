# Phase 3 Frontend Spec — Jinju Legal Orchestrator Case Replay
> [DEPRECATED 2026-04-14] 이 문서는 Vercel 기반 정적 뷰어 접근을 전제로 작성되었으나, case-report.md 단일 파일 출력 방식으로 방향이 변경되었습니다. skills/generate-case-report.md 를 참조하세요.

**작성일:** 2026-04-14
**대상 리포지토리:** `legal-agent-orchestrator`
**상태:** 구현 스펙 (Codex 핸드오프용)
**배포 타깃:** Vercel (static export)
**선행 문서:** `docs/phase3-case-replay-design.md` (데이터 파이프라인/아키텍처 설계는 여기 참조)

---

## 0. 이 문서의 역할

`phase3-case-replay-design.md`는 **무엇을 데이터로 보여줄지**를 정의한 아키텍처 문서다.
이 문서는 **그 데이터를 어떻게 생긴 화면으로 만들지**를 정의한 프론트엔드 스펙이다.

Codex는 이 스펙만 보고 구현이 가능해야 한다. 디자인 시스템(타이포/컬러/스페이싱), 페이지 구조,
컴포넌트 목록, 상태 매트릭스, 반응형/접근성, Vercel 배포 설정이 모두 포함되어 있다.

**범위:**
- 랜딩 페이지 (`/`)
- 케이스 상세 페이지 (`/cases/[caseId]`)
- MVP는 `samples/20260410-012238-391f` 한 케이스만 하드코딩. 정규화 파이프라인은 Phase 3 후속 작업.

**범위 밖:**
- 다중 케이스 목록 UI (Phase 3B)
- `build-replays.ts` 정규화 스크립트 (Phase 3A, 별도 작업)
- Pattern 3 debate UI (Phase 3C)
- DOCX inline 렌더링
- 검색 / 필터링

---

## 1. 프로덕트 포지셔닝

### 1.1 한 줄 정의

**"8명의 AI 스페셜리스트가 실제로 협업한 법률 사건 기록을 재생하는 정적 웹사이트."**

### 1.2 이것이 아닌 것

- AI 챗봇 인터페이스가 아님
- 대시보드가 아님
- SaaS 랜딩 페이지가 아님
- Generic "AI 포트폴리오" 페이지가 아님

### 1.3 톤 & 무드

**전문 법률 워크플로우 제품의 진지함 + Linear의 타이포그래피적 샤프함.**

- 참조군: Ropes & Gray, Paul Weiss 같은 법률 조직 웹 + Linear changelog + Stripe docs + Pitchfork review
- 피할 것: 보라/인디고 그라디언트, 카드 그리드, 이모지, 3-col feature grid, 도넛 차트, stock photo, floating blobs, centered everything

**핵심:** 방문자가 "AI 포트폴리오"가 아니라 **"실제 법률 사건 기록 아카이브"**처럼 느껴야 한다.
그래야 "이거 진짜 돌아간 거야?"라는 신뢰 신호가 선다.

### 1.4 주요 방문자와 감정 arc

| 방문자 | 첫 5초 질문 | 5분 후 떠야 할 확신 |
|---|---|---|
| **포트폴리오 평가자** (채용/투자자) | "이게 뭐하는 프로젝트지?" | "실제 돌아가는 시스템이고, 로그까지 남긴다" |
| **법률 전문가** | "이 AI가 쓴 의견서 수준이 어느 정도야?" | "리뷰어가 실제로 잡아낸다, roleplay가 아니다" |
| **개발자** | "어떻게 구현했어?" | "이벤트 기반, 멀티에이전트, 실제 이벤트 로그 있음" |

세 사람 모두를 위한 UI여야 한다. 우선순위는 위에서 아래.

---

## 2. 기술 스택 결정

| 레이어 | 선택 | 이유 |
|---|---|---|
| 프레임워크 | **Next.js 16 App Router** | Vercel 배포 최적화, RSC로 빌드 타임 데이터 주입 |
| 렌더링 | **Static export** (`output: 'export'`) | 완전 정적, API 불필요, CDN만으로 동작 |
| 언어 | **TypeScript** (strict) | |
| 스타일 | **CSS Modules + CSS 변수** | Tailwind 선택 시 AI slop 디폴트로 빠지기 쉬움. 커스텀 디자인 토큰을 강제하려면 CSS 변수 |
| 폰트 | **`next/font/google`** | self-hosted, layout shift 없음 |
| 마크다운 | **`react-markdown` + `remark-gfm`** | `opinion.md`, `review-result.md` 렌더링 |
| 코드 하이라이트 | 없음 | 법률 문서에 코드 블록 거의 없음. 필요 시만 `rehype-highlight` 추가 |
| 설정 | **`vercel.json` (MVP)** | `vercel.ts`는 동적 config 필요 시 전환 |
| 노드 런타임 | Node.js 24 LTS (Vercel 기본) | |
| 아이콘 | **Lucide React** (선택적, 최소한만) | 이모지 금지. 아이콘은 status 배지 등 기능적 용도로만 |

**의도적으로 쓰지 않는 것:**
- Tailwind (이유: 디자인 토큰을 강제하는 CSS 변수 체계가 더 깔끔함. Codex 재량으로 Tailwind v4 선택 가능하되, 아래 디자인 토큰을 tailwind config로 1:1 포팅할 것)
- shadcn/ui (같은 이유)
- client-side 상태 관리 라이브러리 (정적 사이트에 불필요)
- Framer Motion (모션은 CSS transition으로 충분)

---

## 3. 디자인 시스템

### 3.1 타이포그래피

**폰트 페어링:** 이중 serif/sans 시스템. 법률 문서의 격식 + 현대 UI의 가독성.

| 역할 | 폰트 | Weights |
|---|---|---|
| Display / H1-H2 | **Noto Serif KR** | 400, 700 |
| Body / UI / H3-H6 | **Inter** | 400, 500, 600 |
| Numerals / case-id / event type | **JetBrains Mono** | 400, 500 |

**중요:**
- Inter는 **variable font**로, `font-feature-settings: 'tnum', 'cv11'` 적용 (tabular figures, alternate 1)
- Noto Serif KR은 한글에서만 진가가 나옴. 영문이 섞이면 Inter로 fallback (CSS `unicode-range`)
- 시스템 폰트 fallback 금지. `font-family: Inter, sans-serif`가 아니라 `font-family: Inter, 'Noto Sans KR', sans-serif` (한영 fallback 체인 명시)

**Type scale** (1.250 ratio, 16px base):

| 토큰 | px | rem | 용도 |
|---|---|---|---|
| `--text-xs` | 12 | 0.75 | 캡션, 배지, 메타데이터 |
| `--text-sm` | 14 | 0.875 | UI small, secondary |
| `--text-base` | 16 | 1.0 | 본문 |
| `--text-lg` | 18 | 1.125 | 본문 강조, sub-heading |
| `--text-xl` | 20 | 1.25 | H4 |
| `--text-2xl` | 24 | 1.5 | H3 |
| `--text-3xl` | 32 | 2.0 | H2 |
| `--text-4xl` | 44 | 2.75 | H1 |
| `--text-5xl` | 64 | 4.0 | Hero display (랜딩 only) |

**Line height 규칙:**
- Display (2xl 이상): `1.15`
- Body (base, lg): `1.7` (한글 본문은 1.7 이상이어야 숨통 트임)
- UI (sm, xs): `1.4`

**letter-spacing:**
- Display: `-0.02em` (꽉 묶기)
- Body: `0`
- Mono/uppercase 라벨: `0.04em`

### 3.2 컬러 시스템

**철학:** 베이스는 3색(ink, paper, rule)으로 수렴. 액센트는 1색(deep legal green). 상태/등급만 별도.

```css
:root {
  /* neutrals — warm off-white 베이스 (순수 흰색 금지) */
  --ink: #111111;          /* 본문 텍스트, 강조 */
  --ink-soft: #3a3633;     /* 보조 텍스트, 긴 본문 */
  --mute: #6b6760;         /* 메타데이터, 타임스탬프 */
  --rule: #e5e2db;         /* hairline 구분선, 테두리 */
  --paper: #fafaf7;        /* 페이지 배경 */
  --surface: #ffffff;      /* 카드/패널 (paper 위에 살짝 뜬 느낌) */

  /* accent — single color, deep legal green */
  --accent: #1f4d3f;       /* 링크, CTA, 브랜드 */
  --accent-hover: #173a30;
  --accent-tint: #eef3f1;  /* 배경 하이라이트 */

  /* semantic — grade (소스 등급) */
  --grade-a: #1f4d3f;      /* green — primary source */
  --grade-b: #8a6d1e;      /* mustard — secondary */
  --grade-c: #9c4a1a;      /* burnt — tertiary */
  --grade-d: #6b2c2c;      /* burgundy — unverified */

  /* semantic — status */
  --ok: #1f4d3f;
  --warn: #8a6d1e;
  --err: #6b2c2c;
  --info: #2a4a6b;         /* blue/slate, 드물게만 */

  /* dark mode (Phase 3C, 지금은 정의만) */
}

@media (prefers-color-scheme: dark) {
  :root {
    --ink: #f2ede4;
    --ink-soft: #c9c2b6;
    --mute: #8a857c;
    --rule: #2a2722;
    --paper: #141210;
    --surface: #1a1815;
    --accent: #6db29a;
    --accent-hover: #8fc7b3;
    --accent-tint: #1d2a25;
    /* grade/status는 live 조절 */
  }
}
```

**규칙:**
- 순수 `#000`, `#fff` 금지. 항상 위 토큰에서 꺼내쓸 것.
- 보라/인디고/Tailwind 디폴트 색 **절대 금지**.
- 그림자는 최소. `box-shadow`가 필요하면 `0 1px 0 var(--rule)` 수준의 hairline만. 드롭 섀도우/블러 섀도우 금지.
- 그라디언트 금지 (단, 랜딩 hero 아래 paper→surface 미세 전환 1회 허용).

### 3.3 스페이싱 & 레이아웃

**Spacing scale** (4px base):

| 토큰 | px |
|---|---|
| `--space-1` | 4 |
| `--space-2` | 8 |
| `--space-3` | 12 |
| `--space-4` | 16 |
| `--space-5` | 24 |
| `--space-6` | 32 |
| `--space-7` | 48 |
| `--space-8` | 64 |
| `--space-9` | 96 |
| `--space-10` | 128 |

**Container widths:**

| 토큰 | px | 용도 |
|---|---|---|
| `--container-prose` | 720 | 본문 읽기 폭 (opinion.md 등) |
| `--container-content` | 1080 | 일반 콘텐츠 |
| `--container-wide` | 1280 | hero, footer, max |

**Breakpoints:**

| 이름 | min-width |
|---|---|
| `sm` | 640 |
| `md` | 768 |
| `lg` | 1024 |
| `xl` | 1280 |

**Grid:** 모바일 1-col, ≥lg에서 12-col.

**Border radius:**
- 기본: `0` (carpet bombing rounded corners 금지)
- 허용: 배지/버튼 `4px`, 코드 블록 `6px`
- 카드/패널에 radius 주지 않음 — 법률 문서는 각진 것이 어울림

### 3.4 Border / Rule 스타일

법률 문서의 시각 모티프로 **hairline** 적극 사용.

- 섹션 구분: `border-top: 1px solid var(--rule)` + 상단 `--space-7` 여백
- 표 구분: 1px rule만. vertical rule 금지
- 카드 테두리: 기본 없음. hover/focus 시만 `var(--accent)`

### 3.5 모션

**원칙:** 모션은 계층(hierarchy)을 지원할 때만. 장식 금지.

허용:
- Link/button `transition: color 120ms ease`
- Collapsible expand/collapse `max-height 200ms ease`
- Page-load fade-in (100ms, opacity만) — 없어도 무방

금지:
- Scroll-triggered animation
- Parallax
- Floating elements
- Infinite animations (spinner 제외)

### 3.6 아이코노그래피

- Lucide React 중 **최소한**만 사용
- 사이즈: 16px (UI), 20px (섹션 헤더)
- `stroke-width: 1.5` (기본 2는 너무 굵음)
- 기능적 용도에 한함: status 배지, 외부 링크 표시, copy 버튼, chevron

이모지 사용 금지 (배지, 아이콘, 강조 어디에도).

### 3.7 키보드 포커스

```css
:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
  border-radius: 2px;
}
```

모든 interactive element에 적용. 기본 `outline: none` 금지.

---

## 4. 정보 아키텍처

### 4.1 라우트

| Path | 역할 | 상태 |
|---|---|---|
| `/` | 랜딩 | MVP 필수 |
| `/cases/20260410-012238-391f` | 하드코딩된 단일 케이스 상세 | MVP 필수 |
| `/cases` | 케이스 인덱스 | Phase 3B (MVP에서 `/` → 케이스로 직접 CTA) |
| `/about` | 프로젝트 소개 | Phase 3C. MVP는 `/`에 통합 |

### 4.2 글로벌 네비게이션

**Header (모든 페이지):**
- 좌측: 워드마크 "**Jinju Legal Orchestrator**" (Noto Serif KR 700, 20px) — `/`로 링크
- 우측: `Case` (현재 케이스 shortcut), `GitHub` (외부 링크 아이콘 포함)
- 높이: 64px
- 스타일: paper 배경, 하단 `border-bottom: 1px solid var(--rule)`, sticky
- 모바일 (<640): 우측 링크는 그대로 노출 (햄버거 금지, 2개뿐이라 공간 있음)

**Footer (모든 페이지):**
- 좌측: `Jinju Legal Orchestrator · 2026 · an AI legal orchestrator`
- 우측: GitHub, MIT License
- 높이: 96px
- 스타일: `--mute` 색, 12px, 상단 hairline

---

## 5. `/` 랜딩 페이지 스펙

### 5.1 전체 구조 (위에서 아래)

```
┌──────────────────────────────────────────┐
│ HEADER                                    │
├──────────────────────────────────────────┤
│ § HERO                                    │
│   - Kicker (소속 라벨)                    │
│   - Display headline (한글)               │
│   - Sub (1문장 설명)                      │
│   - Stats row (팩트 3개)                  │
│   - CTA × 2                              │
├──────────────────────────────────────────┤
│ § 어떻게 돌아가나 (How it works)         │
│   - 3단계 수직 다이어그램                │
├──────────────────────────────────────────┤
│ § 8명의 스페셜리스트 (Meet the Team)     │
│   - 8명 table-style 리스트               │
├──────────────────────────────────────────┤
│ § 실제 처리한 케이스 (Featured case)     │
│   - 단일 케이스 프리뷰 + CTA             │
├──────────────────────────────────────────┤
│ § 왜 만들었나 (Why / Philosophy)         │
│   - 2문단 prose                          │
├──────────────────────────────────────────┤
│ FOOTER                                    │
└──────────────────────────────────────────┘
```

### 5.2 Hero 상세

**레이아웃:** 단일 composition. 카드 없음. 좌측 정렬.

```
[Kicker] ─────────────────────────────────────
AI 스페셜리스트 8명이 실제로 협업한
법률 사건 기록 아카이브

규칙 기반 워크플로우로 리서치 → 작성 → 리뷰를
자동화하고, 모든 이벤트를 사건 폴더에 남깁니다.

┌─────────┐  ┌─────────┐  ┌─────────┐
│ 8명     │  │ 1 케이스 │  │ 33 소스 │
│ 전문 AI │  │ 공개     │  │ 중 A등급 │
│ specialist │ │        │  │ 29건    │
└─────────┘  └─────────┘  └─────────┘

[케이스 기록 보기 →]  [GitHub ↗]
```

**구체 스펙:**

| 요소 | 값 |
|---|---|
| Kicker | Inter 500, 12px, uppercase, letter-spacing 0.08em, `--mute` 색, 위에 24px `─` |
| Kicker 문구 | `Jinju Legal Orchestrator · AN AI LEGAL ORCHESTRATOR` |
| Display | Noto Serif KR 700, `--text-5xl` (64px), `--ink`, line-height 1.1, letter-spacing -0.02em. 모바일 `--text-4xl` (44px) |
| Display 문구 | "AI 스페셜리스트 8명이 실제로 협업한<br />법률 사건 기록 아카이브" (2줄 강제) |
| Sub | Inter 400, `--text-lg` (18px), `--ink-soft`, line-height 1.7, 최대 폭 560px |
| Sub 문구 | "규칙 기반 워크플로우로 법률 리서치, 의견서 작성, 시니어 리뷰를 자동화하고, 모든 이벤트를 사건 폴더에 남깁니다." |
| Stats row | 3개 셀, flex gap 48px. 각 셀 = 숫자(JetBrains Mono 500, 32px, `--ink`) + 라벨(Inter 400, 12px, `--mute`, uppercase). 숫자 tabular-nums 강제 |
| Stats 값 | `8` 전문 AI 스페셜리스트 · `1` 공개 케이스 · `29 / 33` A등급 소스 |
| CTA primary | "케이스 기록 보기 →" — Inter 500, 15px, `--accent` 배경, paper 글자, padding 12/20, radius 4, hover `--accent-hover` |
| CTA secondary | "GitHub ↗" — ghost 버튼. 투명 배경, `--accent` 글자 + border 1px `--accent` |
| 수직 여백 | hero top `--space-10` (128px), hero bottom `--space-9` (96px) |

**Hero 배경:**
- `--paper` 솔리드. 이미지/그라디언트 없음.
- 페이지 바닥에서 아주 미세하게 `--paper` → `--surface` 수직 전환 허용 (선택).

### 5.3 How it works (§어떻게 돌아가나)

**레이아웃:** 3-col 그리드 금지. 세로 3단계.

```
§ 어떻게 돌아가나
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  01   라우팅
       ─────────────────────
       클라이언트 질문을 분석해 8명의
       전문 스페셜리스트 중 담당자를 배정합니다.
       질문 유형에 따라 Pattern 1~3 중
       협업 패턴이 결정됩니다.

  02   리서치 · 작성 · 검토
       ─────────────────────
       담당 스페셜리스트가 법령·판례를 A/B/C/D
       등급으로 리서치하고, 법률문서를
       작성합니다. 시니어 리뷰 담당자가 critical
       findings를 다시 잡아냅니다.

  03   배포
       ─────────────────────
       최종 의견서를 Markdown과 DOCX로
       내보내고, 전 과정을 events.jsonl로
       남깁니다. 이 사이트가 그 기록을
       재생합니다.
```

**스펙:**
- 섹션 제목 `§ 어떻게 돌아가나` — Noto Serif KR 700, 32px, 위 `border-top: 1px solid var(--rule)` + `--space-7` padding-top
- 각 단계 번호 `01 02 03` — JetBrains Mono 500, 24px, `--mute`
- 단계 제목 — Inter 600, 20px, `--ink`
- 단계 본문 — Inter 400, 16px, `--ink-soft`, line-height 1.7, 최대 폭 640px
- 단계 사이 `--space-7` 여백
- 아이콘/일러스트 금지

### 5.4 Meet the Team (§8명의 스페셜리스트)

**레이아웃:** 아바타 카드 그리드 금지. 법률 디렉토리 스타일의 table-like list.

```
§ 8명의 스페셜리스트
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  #01   김재식          범용 법률 리서치              PHASE 1
        ─────────────────────────────────────────
        general-legal-research

  #02   한석봉          법률문서 작성                 PHASE 1
        ─────────────────────────────────────────
        legal-writing-agent

  #03   반성문  시니어 리뷰   품질 검토, 최종 승인          PHASE 1
        ─────────────────────────────────────────
        second-review-agent

  #04   김덕배          EU 데이터보호법 (GDPR)        PHASE 2
  ...
```

**스펙:**
- 각 row: grid-template-columns `56px 120px 1fr 80px` (번호, 이름, 역할, phase)
- 번호 `#01` — JetBrains Mono 500, `--mute`
- 이름 — Noto Serif KR 700, 18px, `--ink`. 시니어 리뷰 담당자는 옆에 작은 `시니어 리뷰` 배지
- 역할 — Inter 400, 16px, `--ink-soft`
- agent_id — Inter 400, 13px, `--mute`, row 아래 작게
- Phase 배지 — Inter 500, 11px, uppercase, letter-spacing 0.06em, 오른쪽 정렬
  - Phase 1 배지: `--accent` 글자 + `--accent-tint` 배경
  - Phase 2 배지: `--mute` 글자 + `--rule` 테두리
- row 사이 `border-bottom: 1px solid var(--rule)`

### 5.5 Featured case (§실제 처리한 케이스)

**목적:** 단일 케이스 하나를 미리보기로 놓고 CTA로 상세 페이지로 보냄.

```
§ 실제 처리한 케이스
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  CASE 20260410-012238-391f
  PATTERN 2 · APPROVED · 2026.04.09

  ─────────────────────────────────────────

  "한국 게임산업법의 확률형 아이템(가챠)
   규제에 대한 법률 의견서를 작성해줘"

  ─────────────────────────────────────────

  김재식 → 한석봉 → 반성문
  33 소스 (A 29 / B 4 / C 0 / D 0)
  리뷰 1회, critical 2건 지적 → 수정 후 승인

  [전체 기록 재생하기 →]
```

**스펙:**
- 상단 라인: `CASE` + case-id (JetBrains Mono 500, 13px, `--mute`) / 다음 줄: Pattern, 승인 상태 배지, 날짜
- 질문 원문: Noto Serif KR 400 italic, `--text-2xl` (24px), line-height 1.5, 양쪽 인용부호. 60ch 이상이면 줄바꿈
- 메타: agent flow 화살표는 `→` 유니코드, `--mute` 색. Grade 분포는 텍스트 (도넛 금지)
- CTA: "전체 기록 재생하기 →" — primary button 스타일
- 배경: `--surface`, 상하 `--space-8` padding

### 5.6 Why / Philosophy (§왜 만들었나)

**레이아웃:** 2문단 prose. 최대 폭 720px, 좌측 정렬.

**문구 (작성 시 Codex가 이 초안을 존중):**

> 법률 업무는 높은 정확성과 검증이 필요하다. 판례를 정확히 인용하는지, 리뷰어가 빠뜨린 쟁점을 잡아내는지, 어디에서 근거가 흔들렸는지를 모르면 결과물을 신뢰할 수 없다.
>
> Jinju Legal Orchestrator는 그 과정 전체를 기록한다. 질문이 어떻게 분류됐는지, 어떤 법령이 A등급으로 인용됐는지, 시니어 리뷰 담당자가 무엇을 critical로 지적했는지, 수정이 어떻게 반영됐는지가 모두 `events.jsonl`에 남는다. 이 사이트는 그 기록을 사람이 읽을 수 있게 재생한다.

**스펙:**
- 섹션 제목 스타일 동일
- 본문: Noto Serif KR 400, `--text-lg` (18px), line-height 1.8, `--ink`
- 첫 글자 드롭캡 금지 (AI slop)

---

## 6. `/cases/[caseId]` 케이스 상세 페이지 스펙

### 6.1 페이지 구조 (위계)

```
PRIMARY (above fold, 첫 5초)
├── Case metadata line
├── Question verbatim (핵심)
└── Status badge + key stats

SECONDARY (메인 콘텐츠, 첫 스크롤)
├── Overview — summary + key findings
├── Timeline — 이벤트 시각화
├── Agents — 누가 무엇을 했나
└── Review — findings by severity

TERTIARY (상세 참조, 스크롤)
├── Sources — grade 분포 + 인용 리스트
└── Documents — opinion.md 리더 + 다운로드

DEVELOPER (접힘, footer 바로 위)
└── Raw events (collapsible)
```

### 6.2 레이아웃 (데스크톱 ≥lg)

```
┌───────────────────┬──────────┐
│                   │          │
│   메인 콘텐츠      │   TOC    │
│   (max 720px)     │  (sticky)│
│                   │          │
└───────────────────┴──────────┘
     grid-cols: 1fr 220px, gap 64px
     max-width: 1080px, centered
```

**모바일:** TOC 숨김. 메인 1-col.

### 6.3 Hero (상세 페이지)

```
CASE 20260410-012238-391f          ✓ APPROVED
PATTERN 2 · 2026.04.09 · 12분 13초

"한국 게임산업법의 확률형 아이템
 (가챠) 규제에 대한 법률 의견서를
 작성해줘"

김재식 · 한석봉 · 반성문
33 소스 · 리뷰 1회
```

**스펙:**
- 상단 라인 좌/우 분리:
  - 좌: `CASE` + case-id (mono, 13px, `--mute`)
  - 우: status 배지 (6.5 참조)
- 두 번째 라인: pattern, 날짜, 실행 시간 — mono 13px, `--mute`, `·` 구분
- 질문 원문:
  - Noto Serif KR 400 italic, `--text-4xl` (44px) desktop / `--text-2xl` mobile
  - line-height 1.3, letter-spacing -0.02em
  - 최대 폭 640px
  - 앞뒤 "" 한글 큰따옴표 사용
- 에이전트 라인 & 메타: Inter 400, 15px, `--mute`
- 여백: top `--space-8`, bottom `--space-8`, 하단 `border-bottom: 1px solid var(--rule)`

### 6.4 Overview 섹션

**내용:**
- H2 `§ 요약`
- `research-meta.json`의 `summary` 또는 derived (200-300자)
- Key findings 3~5개 (bullet list)

**스펙:**
- summary: Inter 400, `--text-lg` (18px), line-height 1.7
- key findings: serial 번호 `01. 02. 03.` (mono, `--mute`, 24px) + 본문 (Inter 400, 16px)
- bullet 점/대시 금지. 번호만 사용

### 6.5 Status 배지 시스템

**규칙: 색 + 기호 + 라벨 3중 표기** (색맹 대응)

| 상태 | 기호 | 라벨 | 배경 | 글자 |
|---|---|---|---|---|
| approved | `✓` | APPROVED | `--accent-tint` | `--accent` |
| approved_with_revisions | `✓` | APPROVED W/ REVISIONS | `--accent-tint` | `--accent` (라벨에 "W/ REVISIONS") |
| revision_needed | `↻` | REVISION NEEDED | `#fef6e4` | `--warn` |
| partial | `◐` | PARTIAL | `#f5f1ea` | `--mute` |
| failed | `✕` | FAILED | `#f8ece8` | `--err` |

**스펙:**
- Inter 500, 11px, uppercase, letter-spacing 0.06em
- padding 4/10, radius 4
- 기호는 inline, 0.5ch 앞 여백
- role="status", aria-label에 full label

### 6.6 Timeline 섹션

**레이아웃:** 수직 타임라인. 좌측 세로 rule + 이벤트 마커.

```
§ 타임라인
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  16:22:38  ●  CASE RECEIVED
  evt_001  │   orchestrator
           │   → "한국 게임산업법의 확률형..."
           │
  16:22:38  ●  CASE CLASSIFIED
  evt_002  │   orchestrator
           │   → pipeline: research → writing → review
           │
  16:34:51  ●  김재식 ASSIGNED
  evt_003  │   general-legal-research
           │
  16:53:26  ◈  14 SOURCES GRADED
  evt_004  │   김재식 · A: 12, B: 2
  ~017    │   [expand]
           │
  16:53:26  ●  RESEARCH COMPLETED
  evt_018  │   김재식 · 11 key findings
           │
  ...
           │
  18:07:12  ✓  APPROVED
  evt_NNN  │   반성문 · 2 critical findings resolved
```

**구체 스펙:**
- 좌측 타임스탬프 열: mono, 13px, `--mute`, 고정 폭 80px
- 이벤트 ID 열: mono, 11px, `--mute`, 고정 폭 60px
- 마커 열: 16px 원형 또는 다각형, 고정 폭 32px
  - `●` 일반 이벤트: 꽉 찬 원, `--accent`
  - `◈` 집계 이벤트 (source 그룹핑): 다이아몬드, `--accent`
  - `⚠` 에러: `--warn`
  - `✓` 완료/승인: `--ok`
  - `✕` 실패: `--err`
- 세로 연결선: `border-left: 1px solid var(--rule)`, 마커 사이
- 이벤트 타입 라벨: Inter 500, 12px, uppercase, `--ink`
- 본문: Inter 400, 14px, `--ink-soft`, line-height 1.5
- 페이로드: `→` 시작, mono 14px 본문 혼용 가능
- row 사이 `--space-4` (16px)

**source_graded 이벤트 집계:**
- 연속된 `source_graded` 이벤트는 1개로 집계해서 보여준다.
- 집계 row: "14 sources graded" + "A: 12, B: 2"
- `[expand]` 버튼 클릭 시 개별 소스 리스트가 펼쳐진다 (collapsible, CSS only with `<details>`).

**접근성:**
- `<ol role="list">` 전체 감싸고 각 이벤트는 `<li>`
- 타임스탬프는 `<time datetime="2026-04-09T16:22:38Z">`
- 마커는 `aria-hidden="true"` (스크린리더는 라벨만 읽음)

### 6.7 Agents 섹션

**레이아웃:** 참여 에이전트별 활동 요약.

```
§ 참여 에이전트
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  김재식              범용 법률 리서치         PHASE 1
  general-legal-research
  ─────────────────────────────────────────────────
  18분 35초 · 14 sources (A 12 · B 2) · 11 findings

  핵심 기여:
  01. 게임산업법 §2 xi 확률형 아이템 정의 조항 확보
  02. 시행령 §19의2 + 별표 3의2 조합으로 표시의무 구체화
  03. 공정위 넥슨 의결 사건번호 확보 (2021전자1052)


  한석봉              법률문서 작성           PHASE 1
  legal-writing-agent
  ─────────────────────────────────────────────────
  8분 51초 · 2 drafts
  ...
```

**데이터 소스:**
- 에이전트 정보 & 소요 시간 → events.jsonl에서 계산
- 핵심 기여 → `{agent}-meta.json`의 `key_findings`

**스펙:**
- 각 에이전트 블록 간 `border-top: 1px solid var(--rule)` + `--space-7`
- 이름 + 역할 줄은 Meet the Team과 동일 스타일

### 6.8 Review 섹션 (가장 중요)

**이 섹션이 이 프로젝트의 설득 핵심.** 실제로 리뷰어가 뭘 잡아냈는지를 보여줘야 한다.

**레이아웃:** severity별로 그룹.

```
§ 시니어 리뷰 (반성문)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  최종 판정      ✓ APPROVED (1회 수정 후)
  리뷰어         반성문 (Senior Review Specialist)
  소요 시간       24분 17초


  CRITICAL  (2 findings · 모두 반영)
  ─────────────────────────────────────────────────

  01. 게임산업법 §33② 시행일 오기재
      INITIAL DRAFT — "2023.3.21. 시행"
      FINDING       — 실제는 2024.3.22. 시행. 1년 차이.
      FIX           — "2024.3.22. 시행"으로 수정
      EVIDENCE      — opinion.md §2.1 참조

  02. 공정위 과징금 금액 단위 오류
      INITIAL DRAFT — "과징금 116억 4,200만원"
      FINDING       — 의결서 원문은 116억 4,200만원 맞음.
                     다만 본문 타 위치에서 "11억"으로 오기.
      FIX           — 모든 위치 "116억 4,200만원"으로 통일


  MAJOR  (0 findings)
  ─────────────────────────────────────────────────
  발견 없음


  MINOR  (3 findings · 반영)
  ─────────────────────────────────────────────────
  01. 조문 번호 표기 일관성 ...
  02. ...
  03. ...
```

**스펙:**
- Severity 헤더: Inter 600, 14px, uppercase, letter-spacing 0.04em
  - CRITICAL: `--err`
  - MAJOR: `--warn`
  - MINOR: `--mute`
- Finding row: grid-template-columns `24px 1fr`, 번호 + 본문
- Sub-label (`INITIAL DRAFT`, `FINDING`, `FIX`, `EVIDENCE`): Inter 500, 11px, uppercase, `--mute`, letter-spacing 0.06em
- 본문: Inter 400, 14px, `--ink-soft`, line-height 1.6
- finding 간 `--space-5` 여백, `border-top: 1px dashed var(--rule)` 구분

**데이터 매핑:**
- `review-meta.json` → severity별 findings
- 필드명 정규화는 `phase3-case-replay-design.md` §17 fallback 규칙 따름

### 6.9 Sources 섹션

**레이아웃:**
- 상단: grade 분포 (가로 스택 바, 도넛 금지)
- 하단: 전체 소스 리스트 (테이블)

```
§ 소스
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  총 33건
  ████████████████████████████████░░░░░░░░░░
   A  29건 (87.9%)                B 4 (12.1%)

  ─────────────────────────────────────────────────

  #01   A   게임산업법 §2 xi (확률형 아이템 정의)
            법률 제19877호, 2024.10.22. 개정
            김재식 · 한석봉

  #02   A   게임산업법 §33② (표시의무)
            법률 제19877호
            김재식

  ...
```

**Grade 스택 바 스펙:**
- 높이 24px, 전체 폭 `max-width: 480px`
- 각 grade 구획: 해당 색 (`--grade-a` 등), 구획 끝에 1px `--paper` 구분선
- 텍스트 레이블: 바 아래 줄에 `A 29건 (87.9%)` 식으로 표시. 바 안쪽 텍스트 없음 (가독성 이유)

**소스 리스트 스펙:**
- `<table>` semantic HTML
- 컬럼: # (mono 40px), Grade (배지 40px), 제목/인용 (1fr), 인용한 에이전트 (160px)
- row 사이 `border-bottom: 1px solid var(--rule)`
- 인용 citation: mono 13px, `--mute`, 두 번째 줄

### 6.10 Documents 섹션

**레이아웃:** Tab 또는 세로 스택. MVP는 세로 스택 권장.

```
§ 문서
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  [opinion.md]  [review-result.md]  [research-result.md]

  ─────────────────────────────────────────────────

  (선택된 문서 inline 렌더링, prose 컨테이너)

  ─────────────────────────────────────────────────

  다운로드
  · opinion.docx  (42 KB)  [Download ↓]
  · opinion.md    (18 KB)  [Download ↓]
```

**Tab 스펙:**
- Inter 500, 14px
- 활성 탭: `--ink` 색 + 하단 2px `--accent` underline
- 비활성: `--mute` 색, hover 시 `--ink`

**Markdown 렌더링 (`react-markdown`):**
- 컨테이너 `.prose`:
  - max-width: 720px
  - font: Noto Serif KR 400, 17px, line-height 1.8
  - H1: Noto Serif KR 700, 32px, `--space-7` top
  - H2: Noto Serif KR 700, 24px, `--space-6` top
  - H3: Inter 600, 18px, `--space-5` top
  - ul/ol: padding-left 24px, li 사이 8px
  - blockquote: border-left 2px `--accent`, padding-left 16px, italic, `--ink-soft`
  - a: `--accent`, underline on hover only
  - code (inline): JetBrains Mono, 14px, bg `--accent-tint`, padding 2/6, radius 2
  - pre: bg `--surface`, border 1px `--rule`, padding 16, radius 6, overflow-x auto
  - table: border-collapse, th/td padding 8/12, border-bottom 1px `--rule`

**Download 링크:**
- Inter 400, 14px
- 파일 크기는 `--mute` 색, 괄호 안
- 아이콘 `↓` 우측

### 6.11 Raw events (개발자용)

**위치:** Documents 섹션 아래, footer 바로 위.

**스펙:**
- `<details>` 기본 접힘
- summary: "Raw events (개발자용)" + chevron 아이콘
- 펼침 시: `<pre>`에 `events.jsonl` 원문 표시
- 배경 `--surface`, 글자 JetBrains Mono 12px
- 복사 버튼 우상단

### 6.12 TOC (우측 sticky)

**스펙:**
- 데스크톱 ≥lg에서만 노출. `position: sticky; top: 96px;`
- 섹션 리스트: 요약, 타임라인, 에이전트, 리뷰, 소스, 문서
- Inter 400, 13px, `--mute`
- active 항목: `--ink` + 좌측 2px `--accent` border
- scroll-spy로 active 토글 (IntersectionObserver 사용, client component 하나만)
- 클릭 시 smooth scroll (`scroll-behavior: smooth`)

---

## 7. 상태 매트릭스

**모든 상태를 UI로 정의한다. MVP에서도 생략 금지.**

### 7.1 케이스 상세 페이지 상태

| 상태 | 트리거 | UI 처리 |
|---|---|---|
| **Full case** | events.jsonl 있음 + opinion.md 있음 + review-meta.json 있음 | 전체 섹션 렌더 (기본) |
| **Partial — no review** | review-meta.json 없음 | Review 섹션을 "이 케이스는 리뷰 단계를 거치지 않았습니다" 공백 상태로 표시 |
| **Partial — no opinion** | opinion.md 없음 | Documents 섹션에 "최종 의견서가 생성되지 않았습니다" |
| **Agent smoke test** | events.jsonl 없음, 단일 agent 산출물만 | 전체 페이지 대신 축약 뷰: metadata + 단일 result.md 렌더만. 배너 "이 케이스는 단일 에이전트 스모크 테스트입니다" |
| **Rescued** | events.jsonl에 error 이벤트 + rescue 성공 | Timeline에 error 마커 `⚠` → 이어서 `✓` 복구 마커. Overview에 "rescued after 1 error" 배지 |
| **Failed** | events.jsonl에 error + rescue 없음 | status 배지 `✕ FAILED`. Timeline error 이후 아무것도 없음. "최종 산출물이 생성되지 않았습니다" |
| **Missing artifact** | 특정 문서 파일 없음 | Documents 탭에서 해당 문서 disable + "파일 없음" 툴팁 |

### 7.2 랜딩 페이지 상태

| 상태 | UI |
|---|---|
| **Default** | MVP에서는 유일한 상태 |
| **Future: no featured case** | Featured case 섹션 자리에 "곧 공개됩니다" placeholder |

### 7.3 마크다운 렌더링 상태

| 상태 | UI |
|---|---|
| **Loading** | 정적이므로 N/A (빌드 시 inline) |
| **Empty** | "이 문서는 비어 있습니다" |
| **Oversized (>100KB)** | 상단에 "문서가 깁니다. [원본 보기 ↗]" 배너 |

---

## 8. 반응형 스펙

### 8.1 Breakpoint별 레이아웃

| Breakpoint | Layout |
|---|---|
| < 640 (mobile) | 1-col. Hero display 44px. Stats row 세로 쌓임. TOC 숨김. Timeline 좌측 80px 컬럼 → 60px 축소. Table은 가로 스크롤 허용 |
| 640 - 1023 (tablet) | 1-col. Hero display 56px. Stats row 가로 유지. TOC 숨김 |
| ≥ 1024 (desktop) | 상세 페이지 2-col (main + TOC). 랜딩 1-col 유지 (의도적) |
| ≥ 1280 (xl) | 컨테이너 1280px 최대. 양옆 여백 자동 |

### 8.2 긴 콘텐츠 처리

| 케이스 | 처리 |
|---|---|
| 질문 원문 > 120자 | 그대로 전체 노출. 줄바꿈은 `word-break: keep-all` (한글 단어 중간 안 끊김) |
| agent 이름 길이 | 정해져 있음 — 자동 줄바꿈 필요 없음 |
| source citation > 100자 | `word-break: break-word`, overflow 허용 |
| opinion.md 분량 | 항상 inline 전체 렌더. 스크롤은 페이지 자체 스크롤 |
| events.jsonl 행 수 많음 (>200) | Timeline에서 source_graded 자동 집계로 축약 |

### 8.3 터치 타깃

- 모든 interactive element ≥ 44 × 44 px (Apple HIG 기준)
- Footer 링크도 44px 높이 확보 (padding으로)

---

## 9. 접근성 (A11y)

법률 콘텐츠에 A11y는 프로 시그널이다. 명시적으로 구현.

### 9.1 Semantic HTML

- 랜딩: `<header>` `<main>` `<footer>` + 섹션별 `<section aria-labelledby="...">`
- 케이스 상세: hero는 `<header>`, 각 섹션 `<section>`
- 타임라인: `<ol role="list">` + `<li>` + `<time datetime="...">`
- 소스 테이블: `<table>` with `<thead>`, `<tbody>`, `<caption>`
- 배지: `<span role="status" aria-label="...">`

### 9.2 Skip link

```html
<a href="#main" class="skip-link">본문으로 건너뛰기</a>
```

기본 숨김, `:focus` 시 좌상단 노출.

### 9.3 색 + 기호 + 라벨 3중 표기

- Grade 배지: 색 + 글자 (`A`, `B` 등) + aria-label
- Status 배지: 색 + 기호 (`✓`, `⚠`, `✕`) + 라벨 텍스트 + aria-label
- Timeline 마커: 색 + shape + aria-hidden (라벨로 대신 읽음)

### 9.4 키보드 내비게이션

- Tab 순서: header → main → footer
- 상세 페이지에서 Tab으로 문서 Tab 선택 가능 (`role="tablist"`)
- Raw events `<details>` Enter/Space로 토글
- Focus ring 항상 visible (3.7 참조)

### 9.5 모션 감소

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

### 9.6 Contrast

모든 텍스트 ≥ WCAG AA (4.5:1).
- `--ink` on `--paper`: 약 16:1 ✓
- `--ink-soft` on `--paper`: 약 9:1 ✓
- `--mute` on `--paper`: 약 5.5:1 ✓
- `--accent` on `--paper`: 약 8:1 ✓
- White on `--accent`: 약 6:1 ✓ (CTA 버튼)

Grade 색은 텍스트가 아닌 배지 배경에만 사용하며, 반드시 글자(`A`/`B`/`C`/`D`)와 aria-label 병기.

---

## 10. SEO & 메타데이터

### 10.1 `<head>` (랜딩)

```
<title>Jinju Legal Orchestrator · AI Legal Case Archive</title>
<meta name="description" content="8명의 전문 AI 스페셜리스트가 실제로 협업한 법률 사건 기록 아카이브. 리서치 → 작성 → 시니어 리뷰의 전 과정을 이벤트 로그로 재생합니다.">
<meta property="og:title" content="Jinju Legal Orchestrator">
<meta property="og:description" content="...">
<meta property="og:type" content="website">
<meta property="og:image" content="/og-landing.png">
<meta name="twitter:card" content="summary_large_image">
```

### 10.2 `<head>` (케이스 상세)

```
<title>{case.question_short} · Jinju Legal Orchestrator</title>
<meta name="description" content="Pattern {N} · {agents_joined} · {total_sources} 소스 · {status}">
```

### 10.3 OG 이미지

- MVP: 정적 이미지 2개 (`/og-landing.png`, `/og-case.png`)
- 1200 × 630
- Noto Serif KR 700 + Inter + 하단 케이스 메타
- Phase 3C: 동적 OG 생성 (`@vercel/og`) 고려

### 10.4 Sitemap & robots

- `app/sitemap.ts` — `/`, `/cases/20260410-012238-391f` 두 route
- `app/robots.ts` — 전체 allow

---

## 11. Vercel 배포 설정

### 11.1 `vercel.json`

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "framework": "nextjs",
  "buildCommand": "next build",
  "outputDirectory": ".next",
  "cleanUrls": true,
  "trailingSlash": false,
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "X-Frame-Options", "value": "DENY" },
        { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" }
      ]
    },
    {
      "source": "/fonts/(.*)",
      "headers": [
        { "key": "Cache-Control", "value": "public, max-age=31536000, immutable" }
      ]
    }
  ]
}
```

### 11.2 `next.config.ts`

```ts
import type { NextConfig } from 'next';

const config: NextConfig = {
  output: 'export',
  images: { unoptimized: true },
  trailingSlash: false,
};

export default config;
```

### 11.3 도메인

- 프로덕션: (선택) `pearlpartners.law` 또는 `jinju-law.vercel.app`
- 프리뷰: Vercel 기본 preview URL

### 11.4 환경 변수

MVP는 없음. 추후 `@vercel/og` 도입 시 등 필요하면 `vercel env` 사용.

---

## 12. 디렉토리 구조

```
legal-agent-orchestrator/
├── apps/
│   └── web/                              # 프론트엔드 (Next.js)
│       ├── app/
│       │   ├── layout.tsx
│       │   ├── page.tsx                  # 랜딩
│       │   ├── cases/
│       │   │   └── [caseId]/
│       │   │       ├── page.tsx
│       │   │       └── case-data.ts      # 빌드 타임 데이터 로더
│       │   ├── sitemap.ts
│       │   ├── robots.ts
│       │   ├── not-found.tsx
│       │   ├── og/
│       │   │   ├── landing.png
│       │   │   └── case.png
│       │   └── styles/
│       │       ├── tokens.css            # 디자인 토큰 (CSS 변수)
│       │       ├── globals.css
│       │       └── prose.css             # markdown prose
│       ├── components/
│       │   ├── layout/
│       │   │   ├── header.tsx
│       │   │   └── footer.tsx
│       │   ├── landing/
│       │   │   ├── hero.tsx
│       │   │   ├── how-it-works.tsx
│       │   │   ├── team-list.tsx
│       │   │   ├── featured-case.tsx
│       │   │   └── philosophy.tsx
│       │   ├── case/
│       │   │   ├── case-hero.tsx
│       │   │   ├── overview.tsx
│       │   │   ├── timeline/
│       │   │   │   ├── timeline.tsx
│       │   │   │   ├── event-row.tsx
│       │   │   │   └── source-group.tsx
│       │   │   ├── agents.tsx
│       │   │   ├── review.tsx
│       │   │   ├── sources.tsx
│       │   │   ├── documents.tsx
│       │   │   ├── raw-events.tsx
│       │   │   └── toc.tsx
│       │   ├── primitives/
│       │   │   ├── status-badge.tsx
│       │   │   ├── grade-badge.tsx
│       │   │   ├── phase-badge.tsx
│       │   │   ├── stat.tsx
│       │   │   ├── button.tsx
│       │   │   ├── section-heading.tsx
│       │   │   └── kicker.tsx
│       │   └── md/
│       │       └── prose.tsx             # react-markdown 래퍼
│       ├── lib/
│       │   ├── case-loader.ts            # samples/ 읽어 CaseData 반환
│       │   ├── events.ts                 # event type alias + 집계
│       │   ├── types.ts                  # CaseData, Event, Source, Finding 등
│       │   ├── team.ts                   # 8명 스페셜리스트 정적 데이터
│       │   └── format.ts                 # 날짜, 시간 포매팅
│       ├── public/
│       │   ├── fonts/                    # (next/font 쓰면 자동)
│       │   └── favicon.ico
│       ├── next.config.ts
│       ├── package.json
│       ├── tsconfig.json
│       └── vercel.json
├── samples/                              # 기존 그대로 (데이터 소스)
├── docs/
│   ├── phase3-case-replay-design.md     # 데이터 파이프라인 설계 (기존)
│   └── phase3-frontend-spec.md          # 이 문서 (프론트엔드)
└── ...
```

**이유:**
- `apps/web/` 서브디렉토리 — 향후 다른 앱(예: `apps/admin/`)이 생길 여지 + 루트를 깔끔히
- `components/primitives/` — 배지/버튼 등 원자 컴포넌트
- `lib/case-loader.ts` — samples/에서 파일 읽어 타입 안전 객체 반환. Codex의 정규화 스크립트를 나중에 이 자리에 plug-in 가능
- `lib/team.ts` — 스페셜리스트 8명 정적 데이터 (README에서 도출)

---

## 13. 데이터 레이어 (MVP)

### 13.1 `lib/types.ts` (핵심 타입)

```ts
export type Grade = 'A' | 'B' | 'C' | 'D';
export type Severity = 'critical' | 'major' | 'minor';
export type CaseStatus =
  | 'approved'
  | 'approved_with_revisions'
  | 'revision_needed'
  | 'partial'
  | 'failed';

export type CaseData = {
  caseId: string;
  query: string;
  pattern: 1 | 2 | 3;
  status: CaseStatus;
  startedAt: string;   // ISO
  endedAt: string;     // ISO
  durationSec: number;

  overview: {
    summary: string;
    keyFindings: string[];
  };

  agents: AgentSummary[];
  timeline: TimelineEvent[];
  review: ReviewSummary | null;
  sources: SourceEntry[];
  gradeDistribution: Record<Grade, number>;
  documents: DocumentEntry[];
  rawEventsPath: string;
};

export type AgentSummary = {
  id: string;           // e.g. "general-legal-research"
  name: string;         // e.g. "김재식"
  role: string;
  phase: 1 | 2;
  durationSec: number;
  sourceCount: number;
  gradeBreakdown: Partial<Record<Grade, number>>;
  keyFindings: string[];
};

export type TimelineEvent =
  | { kind: 'single'; id: string; ts: string; agent: string; type: string; data: unknown; marker: 'dot' | 'warn' | 'ok' | 'err' }
  | { kind: 'source_group'; idRange: [string, string]; ts: string; agent: string; count: number; gradeBreakdown: Partial<Record<Grade, number>>; sources: SourceEntry[] };

export type ReviewSummary = {
  reviewer: string;
  verdict: CaseStatus;
  durationSec: number;
  findings: Record<Severity, Finding[]>;
};

export type Finding = {
  id: string;
  title: string;
  initialDraft?: string;
  finding: string;
  fix: string;
  evidence?: string;
  resolved: boolean;
};

export type SourceEntry = {
  title: string;
  citation: string;
  grade: Grade;
  citingAgents: string[];
};

export type DocumentEntry = {
  filename: string;       // e.g. "opinion.md"
  kind: 'markdown' | 'docx';
  label: string;          // UI 라벨 (e.g. "의견서")
  sizeBytes: number;
  bodyMarkdown?: string;  // md인 경우 인라인 본문
  downloadUrl: string;    // 빌드 시 public/으로 복사된 URL
};
```

### 13.2 `lib/case-loader.ts` (빌드 타임 로더)

**역할:** 빌드 시 `samples/{caseId}/` 폴더 읽어 `CaseData`를 반환.

**구체 동작:**

1. `events.jsonl`을 줄 단위로 읽어 raw events 배열
2. `research-meta.json`, `writing-meta.json`, `review-meta.json` 개별 로드 (없으면 null)
3. `sources.json` 로드 (없으면 meta의 sources 병합)
4. `opinion.md`, `review-result.md`, `research-result.md` 로드 (문서)
5. `opinion.docx` 바이너리는 `public/downloads/{caseId}/opinion.docx`로 복사
6. event type alias 매핑 (phase3-case-replay-design.md §9.3):
   - `research_completed` / `writing_completed` / `review_completed` → `agent_completed`
7. 연속 `source_graded` 이벤트는 `source_group`으로 집계
8. Review findings는 `review-meta.json`의 `critical_findings`, `major_findings`, `minor_findings` 필드를 정규화

**불변식:**
- 빌드 실패가 나면 안 된다. 누락 필드는 `null` 또는 빈 배열로 fallback.
- 에러 발생 시 `console.warn`은 허용하지만 throw 금지.

### 13.3 `lib/team.ts` (정적 팀 데이터)

```ts
export const TEAM: Array<{
  id: string;
  name: string;
  role: string;
  phase: 1 | 2;
  isSeniorReview?: boolean;
}> = [
  { id: 'general-legal-research', name: '김재식', role: '범용 법률 리서치', phase: 1 },
  { id: 'legal-writing-agent',   name: '한석봉', role: '법률문서 작성',     phase: 1 },
  { id: 'second-review-agent',   name: '반성문', role: '품질 검토, 최종 승인', phase: 1, isSeniorReview: true },
  { id: 'GDPR-expert',           name: '김덕배', role: 'EU 데이터보호법 (GDPR)', phase: 2 },
  { id: 'PIPA-expert',           name: '정보호', role: '한국 개인정보보호법',    phase: 2 },
  { id: 'game-legal-research',   name: '심진주', role: '게임산업 국제법',       phase: 2 },
  { id: 'contract-review-agent', name: '고덕수', role: '계약서 검토',          phase: 2 },
  { id: 'legal-translation-agent', name: '변혁기', role: '법률문서 번역',       phase: 2 },
];
```

---

## 14. 컴포넌트 인벤토리

| 카테고리 | 컴포넌트 | 역할 |
|---|---|---|
| Layout | `Header` | 전역 상단 |
| Layout | `Footer` | 전역 하단 |
| Primitive | `Kicker` | `§` 섹션 위 작은 라벨 (uppercase, mono) |
| Primitive | `SectionHeading` | `§` prefix + serif 제목 + 상단 rule |
| Primitive | `Button` | primary / ghost 2 variant |
| Primitive | `StatusBadge` | approved/revision/failed (3중 표기) |
| Primitive | `GradeBadge` | A/B/C/D 배지 (문자 + aria-label) |
| Primitive | `PhaseBadge` | Phase 1 / Phase 2 |
| Primitive | `Stat` | 숫자 + 라벨 (hero stats row) |
| Primitive | `DownloadLink` | 아이콘 + 파일명 + 크기 |
| Landing | `Hero` | |
| Landing | `HowItWorks` | |
| Landing | `TeamList` | |
| Landing | `FeaturedCase` | |
| Landing | `Philosophy` | |
| Case | `CaseHero` | |
| Case | `Overview` | |
| Case | `Timeline` | 전체 타임라인 컨테이너 |
| Case | `EventRow` | 단일 이벤트 row |
| Case | `SourceGroup` | source_graded 집계 row (collapsible) |
| Case | `AgentsSection` | |
| Case | `ReviewSection` | |
| Case | `FindingRow` | 단일 finding |
| Case | `SourcesSection` | |
| Case | `GradeDistributionBar` | 가로 스택 바 |
| Case | `DocumentsSection` | tabs + prose |
| Case | `RawEvents` | collapsible |
| Case | `Toc` | 우측 sticky, scroll-spy |
| Md | `Prose` | react-markdown 래퍼 with custom renderers |

---

## 15. 구현 순서 (Codex 체크리스트)

### Phase 3-FE-1: 골격 (1-2시간)

- [ ] Next.js 16 App Router 프로젝트 `apps/web/`에 초기화
- [ ] `next.config.ts`에 `output: 'export'` 설정
- [ ] `tokens.css` 디자인 토큰 CSS 변수 정의 (3.2, 3.3)
- [ ] `globals.css` 기본 리셋 + typography 설정
- [ ] `next/font/google`로 Noto Serif KR, Inter, JetBrains Mono 로드
- [ ] `layout.tsx`에 Header + Footer 배치
- [ ] `/` 빈 페이지로 배포 테스트 (Vercel)

### Phase 3-FE-2: 데이터 로더 (1-2시간)

- [ ] `lib/types.ts` 타입 전체 정의
- [ ] `lib/case-loader.ts` 작성
  - events.jsonl 파싱
  - meta 파일 3종 로드
  - source 집계
  - review findings 정규화
  - docx 파일 public/ 복사
- [ ] 빌드 시 `20260410-012238-391f` 한 케이스를 `CaseData`로 변환 성공
- [ ] `lib/team.ts` 작성

### Phase 3-FE-3: Primitives (1-2시간)

- [ ] Button, Badge 3종 (Status/Grade/Phase), Kicker, SectionHeading, Stat, DownloadLink
- [ ] 각 컴포넌트 스토리북/테스트 페이지(`/_dev/primitives`)에서 시각 확인

### Phase 3-FE-4: 랜딩 (2-3시간)

- [ ] Hero
- [ ] HowItWorks
- [ ] TeamList
- [ ] FeaturedCase
- [ ] Philosophy
- [ ] 모바일/데스크톱 확인
- [ ] OG 이미지 정적 생성 (Figma/Sketch 또는 HTML → screenshot)

### Phase 3-FE-5: 케이스 상세 (4-6시간)

- [ ] CaseHero
- [ ] Overview
- [ ] Timeline + EventRow + SourceGroup
- [ ] AgentsSection
- [ ] ReviewSection + FindingRow
- [ ] SourcesSection + GradeDistributionBar
- [ ] DocumentsSection + Prose (react-markdown)
- [ ] RawEvents
- [ ] TOC (scroll-spy client component)

### Phase 3-FE-6: 상태 & 마감 (1-2시간)

- [ ] 상태 매트릭스 (§7) 처리 확인
- [ ] A11y 감사 (§9)
- [ ] Lighthouse 감사 (모든 페이지 90+ 목표)
- [ ] Vercel 프로덕션 배포
- [ ] 도메인 연결 (선택)

**총 예상 시간: 10-17시간.**

---

## 16. 수용 기준 (Acceptance Criteria)

MVP "됐다"고 말하려면:

### 16.1 기능

- [ ] `/` 정적 export 빌드 성공 (`next build` 에러 0)
- [ ] `/cases/20260410-012238-391f` 빌드 성공
- [ ] Vercel 배포 후 두 페이지 모두 200 응답
- [ ] JS 비활성 브라우저에서도 핵심 콘텐츠 전부 읽힘 (TOC scroll-spy와 collapsible 제외)
- [ ] `opinion.md` 본문이 prose 스타일로 정확히 렌더링
- [ ] `opinion.docx` 다운로드 링크가 실제 파일을 반환
- [ ] events.jsonl 이벤트가 모두 timeline에 표현됨 (집계 포함)
- [ ] review-meta.json의 findings가 severity별로 렌더링

### 16.2 디자인

- [ ] 3-column feature grid 0개
- [ ] 보라/인디고/퍼플 색 사용 0곳
- [ ] 이모지 사용 0개 (본문, UI 어디에도)
- [ ] 시스템 폰트 디폴트 fallback이 화면에 노출되는 순간 없음 (FOUT 방지)
- [ ] 랜딩 hero의 display 제목이 Noto Serif KR로 정확히 렌더
- [ ] 그라디언트 배경 0곳 (미세한 paper→surface 허용)
- [ ] 드롭/블러 섀도우 0곳
- [ ] 모든 카드/패널 radius 0 (배지/버튼 제외)

### 16.3 성능

- [ ] Lighthouse Performance ≥ 95 (`/`, `/cases/...` 둘 다)
- [ ] Lighthouse Accessibility ≥ 95
- [ ] Lighthouse Best Practices ≥ 95
- [ ] Lighthouse SEO ≥ 95
- [ ] 첫 화면 JS 번들 < 100KB gzipped
- [ ] CLS < 0.01
- [ ] LCP < 1.2s (4G mobile)

### 16.4 접근성

- [ ] 키보드만으로 모든 CTA, 문서 탭, collapsible 조작 가능
- [ ] 모든 interactive element에 visible focus
- [ ] 색 없이도 status/grade 구분 가능 (기호 + 라벨)
- [ ] 스크린리더에서 timeline 전체 의미 전달 (VoiceOver/NVDA 둘 다 테스트)
- [ ] WCAG AA contrast 전부 통과

### 16.5 반응형

- [ ] 320px 폭에서 가로 스크롤 0 (테이블 제외)
- [ ] 375px (iPhone SE)에서 hero display 잘림 없음
- [ ] 768px (iPad)에서 TOC 숨김 확인
- [ ] 1024px에서 TOC 노출 확인

---

## 17. 의도적으로 하지 않는 것

| 기능 | 이유 |
|---|---|
| 케이스 목록 페이지 (`/cases`) | MVP는 단일 케이스. 2번째 케이스 공개 시 추가 |
| 검색 / 필터 | 데이터 규모 너무 작음 |
| 케이스 간 비교 | 단일 케이스 |
| Pattern 3 Debate UI | 현재 샘플에 없음. Phase 3C |
| 다국어 (i18n) | 프로젝트 자체가 한국어 우선 |
| 다크 모드 | 토큰만 정의. 토글 UI는 Phase 3C |
| 동적 OG 이미지 | 정적 2장으로 충분 |
| 애널리틱스 | 필요 시 Vercel Analytics 활성화 (코드 변경 없음) |
| 댓글/공유 | 법률 문서 성격상 불필요 |
| 로그인 / 권한 | 정적 사이트 |

---

## 18. 참고 / 결정 근거

### 18.1 왜 Tailwind를 안 쓰나?

Tailwind는 유틸리티 클래스의 편의성이 크지만, **디폴트 설정이 AI slop 미학으로 가기 쉽다** (rounded-lg, shadow-md, gradient-to-br 등). 이 프로젝트는 법률 문서의 진지함이 중요하므로, CSS 변수로 디자인 토큰을 명시 강제하는 게 안전하다.

Codex가 Tailwind를 강하게 선호한다면, 허용. 단 아래를 반드시 준수:
- `borderRadius`는 0, 2px, 4px, 6px 4개만 허용
- `boxShadow` 프리셋 전부 제거
- 폰트는 Noto Serif KR / Inter / JetBrains Mono 3개로 고정
- 색 팔레트는 §3.2 토큰으로 교체 (Tailwind 디폴트 slate/gray/zinc 등 제거)

### 18.2 왜 static export인가?

- 콘텐츠가 완전히 빌드 타임에 확정됨
- API / 런타임 필요 없음
- CDN 캐싱 극대화
- Vercel Functions 의존 없어 배포가 단순

### 18.3 왜 아이콘 라이브러리를 최소화하나?

이모지 금지 외에, 아이콘도 과하면 산만해진다. Lucide만 선택적으로 쓰되 "이 요소가 텍스트만으로도 성립하는가?"를 먼저 본다. 성립하면 아이콘 없이 가는 게 디폴트.

### 18.4 왜 CSS Modules + CSS 변수?

- 스코프 격리 (Tailwind 스타일 충돌 없음)
- 토큰 변경 시 런타임 반영 (dark mode 쉬움)
- 번들 크기 작음
- RSC와 잘 섞임

---

## 19. Codex에게 보내는 노트

이 문서는 설계 문서가 아니라 **구현 지시서**다. 자유도를 주는 부분과 고정된 부분을 구분해서 읽어라.

**고정 (바꾸지 말 것):**
- §1 포지셔닝, 피할 것 목록
- §3 디자인 토큰 값 (색, 폰트, 스페이싱)
- §5, §6 페이지 구조와 상단 계층
- §7 상태 매트릭스
- §9 접근성 3중 표기 규칙
- §16 수용 기준

**자유 (판단으로 결정 가능):**
- §12 디렉토리 구조의 세부 배치
- §13 `case-loader.ts`의 내부 구현
- §14 컴포넌트 분할 경계
- §11 `vercel.json`의 추가 헤더
- Tailwind 선택 여부 (§18.1 조건부)

**의심스러우면:**
- `samples/20260410-012238-391f/`의 실제 파일을 Read로 확인할 것
- `docs/phase3-case-replay-design.md`의 §17 fallback 규칙을 따를 것
- 한국어 마이크로카피는 이 문서의 예시 톤을 유지할 것 (합니다/~다 혼용 금지, 합니다체 일관)

**질문이 필요한 지점에서는 구현을 멈추고 보고할 것.** 가짜 data mock을 채워 넣지 말 것. 샘플 케이스 1개를 정확히 재현하는 것이 목표.
