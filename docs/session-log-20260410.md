# Session Log — 2026-04-10 (Session 4)

## Session Overview

- **프로젝트**: legal-agent-orchestrator
- **날짜**: 2026-04-10 (KST 오전 ~ 오후)
- **시작 상태**: Phase 1 파일 작성 완료, E2E 테스트 대기 (resume.md v1 기준)
- **종료 상태**: ✅ Phase 1 E2E 검증 완료 + ✅ route-case.md v2 (Phase 2 2.1 + 2.2) 구현 및 검증 + ⏸️ PIPA-expert grade-b 보강 작업 다음 세션 이관
- **주요 결과**: 3개 git commit (`f4a5582`, `6d8a9a7`, `1a71b9d`), 3개 mini E2E PASS, plan-eng-review 클리어

---

## Phase 1: 세션 시작 및 상태 파악

### 발견 사항
- resume.md가 "Phase 1 E2E 대기" 상태로 기록돼 있었으나, **실제로는 이전 세션(4 시작 전)에 E2E가 이미 완료됨**
- 케이스 `20260410-012238-391f` 존재 — 확률형 아이템 의견서, 47 events, 33 sources (29A/4B)
- Phase 1 E2E가 `opinion.docx`까지 생성하여 final_output 이벤트로 마무리된 상태
- 메모리(`project_status.md`)가 3일 스테일 — "Phase 0 gate" 단계로 기록돼 있음

### 새로 발견된 패턴 (디자인 문서 미반영)
**Meta-verification fallback**: `legal-writing-agent`가 revision cycle 1 중 `rate_limit` 히트 → 오케스트레이터가 `korean-law` MCP로 **직접 verbatim 대조**해서 revision 승인. evt_045 (`type=verbatim_verified`, `verifier=orchestrator_meta`) 참조. design.md 원안에는 없던 fallback이며, 이후 Phase 2 `manage-debate.md` 설계에 반영 필요.

### 발견된 새 파일
`scripts/md-to-docx.py` (10KB) — 스타일 가이드 §11 구현 (Times New Roman + 맑은 고딕 이중 폰트, A4, 인용 블록 테이블). opinion.docx 생성용. resume.md의 "확인 필요" 항목이 이걸로 해결.

---

## Phase 2: 하우스키핑 (빚 청산)

### Commit `f4a5582` — 초기 커밋
- 15 files, 3016 insertions
- `.gitignore`에 `.claude/settings.local.json` 추가 (사용자 로컬 설정 제외)
- 포함: CLAUDE.md, 3 skills, setup.sh, .mcp.json, scripts/md-to-docx.py, docs/design.md, docs/ko-legal-opinion-style-guide.md, docs/notes/architecture-defense.md, resume.md

### Commit `6d8a9a7` — resume.md 세션 4 반영 (v2)
- +68/-54
- 상태: "Phase 1 E2E 대기" → "Phase 1 E2E 통과, Phase 2 진입 준비"
- 세션 4 히스토리 섹션 추가
- 주요 아키텍처 결정 #9 추가: meta-verification fallback 패턴
- Phase 2 진입점 (route-case.md 확장) 상세화

### 메모리 업데이트
`~/.claude/projects/-Users-kpsfamily---------legal-agent-orchestrator/memory/project_status.md` 갱신:
- "Phase 0 gate" → "Phase 1 E2E PASSED (2026-04-10)"
- meta-verification fallback 패턴 기록
- E2E 결과 수치 포함

---

## Phase 3: route-case.md v2 확장 (Phase 2 2.1 + 2.2)

### 3.1 스코프 결정 — 2개 핵심 질문

**Q1: briefing 2개 에이전트(game-legal-briefing, game-policy-briefing)를 라우팅에 포함?**
- 발견: 둘 다 CLAUDE.md 없는 **독립 Python 앱** (RSS 피드 모니터링, 뉴스 아카이빙). Agent tool로 호출 불가.
- 사용자: "얘들은 안 불러도 되.. 다른 용도야"
- **결정: 제외.** route-case.md는 8 Claude 에이전트만 다룸.

**Q2: 이 확장의 1차 목적 (실용 vs 데모 vs 둘 다)?**
- 사용자: "잠만..우리 지금 뭐하고 있는거지?"
- 전환점: 브레인스토밍 스킬이 과하게 무겁다는 피드백 (Q1 스코프 → Q2 목적 → Q3... 형식적 문답)
- 사용자: "페이즈2 하면 뭔가 show-off용으로 좋은데 토큰은 녹겠네? 퀄리티 개선에도 의미있는 개선이 있을까?"

### 3.2 Phase 2 가치 분석 (숨은 퀄리티 개선)

Phase 2는 단일 "멀티라운드 토론" 피처가 아니라 **세 가지 다른 메커니즘**:

| Sub-phase | 메커니즘 | 토큰 | 퀄리티 | Show-off |
|-----------|---------|------|--------|----------|
| **2.1** | 전문가 라우팅 (5 specialist 활성화) | ≈Phase 1 | ★★★ | ★ |
| **2.2** | Pattern 1 병렬 멀티 전문가 | ≈2x (조건부) | ★★★★ | ★★ |
| **2.3** | Pattern 3 멀티라운드 토론 | ≈3-4x | ★★ (좁은 범위) | ★★★★★ |

**핵심 통찰**: 실질 퀄리티 개선은 2.1 + 2.2에 있고 상대적으로 저렴. 토큰 녹는 2.3은 순수 show-off + conflict-of-law 전용. "전부 or 아무것도"가 아닌 단계적 선택 가능.

**사용자 질문**: "2.2는 항상 트리거되는 건 아니겠지?"
- 답: 아니, `complexity == "multi_domain"`일 때만 조건부 트리거. 단일 관할권 질문은 2x 비용 부담 없음.

### 3.3 최종 스코프 결정
- ✅ **2.1** 전문가 라우팅 (5 에이전트 활성화)
- ✅ **2.2** Pattern 1 병렬 멀티 전문가
- ❌ **2.3** Pattern 3 토론 (skip, `manage-debate.md` skeleton 유지)

### 3.4 중요 설계 결정: KR 게임법 라우팅 (Option b)

**문제**: KR 게임법 질문(예: 확률형 아이템)을 `game-legal-research`(국제 게임 전문)와 `general-legal-research` 중 어디로 보낼지?

**옵션:**
- a) `general-legal-research` (E2E에서 검증됨, 33 소스)
- b) `game-legal-research` (도메인 특화 일관성)
- c) 명시적 국제 언급 시에만 `game-legal-research`

**사용자 선택: b** — 도메인 특화 규칙 일관성 유지.

### 3.5 route-case.md v2 작성

내용: 153줄 → 637줄 (+572/-87, 이후 eng review 피드백 반영 포함)

**새 섹션:**
- Step 1: 질문 분류 (4차원, 16 few-shot 예시)
- Step 2: 에이전트 로스터 (8 Claude 에이전트, KB 규모, 특기)
- Step 3: 통합 라우팅 트리 (task → contract → debate → multi_domain → single → fallback)
- Step 4: 에이전트 중복 범위 해결 + multi_domain 매트릭스 (3-way 케이스)
- Step 5: Pattern 1 병렬 디스패치 메커니즘 (10단계 절차)
- Step 6: Pattern 3 참조 (manage-debate.md skeleton 상태)
- Step 7: 파이프라인 실행 기록
- Step 8: 8 에이전트 프롬프트 템플릿 전부

---

## Phase 4: plan-eng-review (13 issues + 4 critical gaps)

`/plan-eng-review` 실행. gstack의 플래그(LAKE_INTRO, TEL_PROMPTED 등) 모두 기존 완료 상태 확인 후 바로 리뷰 진입. 사용자가 lighter process 선호한다고 명시해서 per-issue AskUserQuestion 생략, 일괄 리포트 형식으로 진행.

### 리뷰 결과 요약

| 섹션 | 이슈 수 | 핵심 이슈 |
|------|---------|-----------|
| Architecture | 6 | Pattern 1 부분 실패 처리 없음 [P1], 분류 메커니즘 미명세 [P2], 에이전트 수 상한 없음 [P2], multi_domain 공백 [P2], Pattern 3 fallback 의도 손실 [P3], Events 스키마 문서화 없음 [P3] |
| Code Quality | 3 | 스타일 가이드 블록 5번 반복 [P2], Template placeholder 문법 혼재 [P2], 에이전트 에러 처리 계약 없음 [P3] |
| Tests | 36 gap | 라우팅 트리 13규칙 중 1개만 커버됨 (8%). 최소 E2E 4개 권고 (T1~T4) |
| Performance | 3 | Pattern 1 컨텍스트 증폭 [P2], 분류 오버헤드 [P3], 토큰 예산 가드 없음 [P3] |
| Failure modes | 4 critical | FM1 (Pattern 1 부분 실패), FM2 (MCP 실패), FM3 (분류 오류), **FM4 (legal-translation onboarding 블록)** |

### 사용자 선택: Option A (전면 수용)
"권고 전부 수용 → route-case.md 수정 + T1, T2 실행 + 리그레션 체크 → 그 후 커밋"

---

## Phase 5: 이슈 수정 (13개 수정 완료)

### Architecture 수정
- **1.1**: Step 1에 "LLM 추론 + 16 예시 canonical reference" + 모호성 감지 시 `user_prompt` 경로 명시
- **1.2**: Step 5에 부분 실패 처리 (부분 성공/전부 실패/rate_limit 재시도) + `parallel_dispatch_partial` 이벤트
- **1.3**: Pattern 1 최대 3 에이전트 상한 + `multi_domain_truncated` 이벤트
- **1.4**: Step 4에 **multi_domain 매트릭스** (KR+EU+US 3-way 케이스 명시)
- **1.5**: Pattern 3 fallback이 Pattern 1으로 갈 때 writing-agent에 "명시적 충돌점 식별" + "반대 논거 서술" + "'진정한 토론이었다면' 섹션" 주입 지시
- **1.6**: 부록 A (Events 스키마) 신설 — v2 신규 이벤트 8개 문서화

### Code Quality 수정
- **2.1**: Step 8.0 **공통 주입 블록** 신설 (`{{STYLE_GUIDE_BLOCK}}`, `{{ERROR_CONTRACT_BLOCK}}`, `{{OUTPUT_CONTRACT_BLOCK}}`) — 5곳 반복 → 1곳 정의 + 참조
- **2.2**: 템플릿 조건부 섹션을 HTML 주석(`<!-- IF ... -->` / `<!-- END IF -->`)로 명시
- **2.3**: `{{ERROR_CONTRACT_BLOCK}}`에 MCP 실패/소스 부재/out_of_scope/rate_limit 처리 계약 명시

### Performance 수정
- **4.2**: writing-agent Pattern 1 프롬프트에 "summary + key_findings만으로 90% 작성. result.md는 직접 인용 필요 시에만 Read" 지시
- **4.3**: 부록 B (패턴별 토큰 예산) 신설 — Phase 2 simple ~150k부터 Pattern 1 (3-agent) ~570k까지 추정

### Failure Mode 수정
- **FM4**: Step 8.0b **legal-translation-agent preflight 체크** — Agent tool 호출 전 bash 스크립트로 `config.json` 부재 시 기본 config 자동 생성 + `agent_preflight` 이벤트

---

## Phase 6: Mini E2E 검증 (3건 모두 PASS)

토큰/rate_limit 관리를 위해 **research 단계만** 실행 (writing/review 생략).

### Test T1: PIPA-expert 단독 (전문가 라우팅 sanity)

**쿼리**: "개인정보보호법 제28조의2 (가명정보의 처리 등) 해석"

**결과:**
- 파일: `output/test-T1-20260410-121640/PIPA-expert-{result.md,meta.json}`
- Sources: **9개** (8 Grade A 로컬 KB + 1 Grade B via MCP)
- 토큰: ~60k / 시간: 582s (~10분)
- 스타일 가이드 준수, meta.json schema 정확, test_marker 기록

**중요 발견 (KB gap):**
> PIPA-expert의 `library/grade-b/pipc-decisions/` 및 `library/grade-b/court-precedents/` 두 디렉토리가 **완전히 빈 상태**. 가명정보 관련 처분례/판례를 로컬에서 찾을 수 없어 korean-law MCP로 폴백. → **후속 ingest 작업 필요**.

**판정: PASS** — 라우팅 정상 작동, 전문가 KB에서 Grade A 단독 근거 확보 가능.

### Test Regression: game-legal-research (Option b 검증)

**쿼리**: Phase 1 E2E와 동일 (확률형 아이템 규제)

**목적**: Option b (KR 게임법 → game-legal-research) 결정이 v1 (general-legal-research, 33 sources)과 비교해 comparable한지 검증.

**결과:**
- 파일: `output/test-regression-20260410-121640/game-legal-research-{result.md,meta.json}`
- Sources: **32개** (25 Grade A + 0 B + 7 Grade C 국제비교용)
- v1 대비: -3% 소스 (33 → 32), **11/11 required coverage** 달성
- 토큰: ~170k / 시간: 797s (~13분)

**game-legal-research 특장점 입증:**
1. `library/kr-statutes/` cache로 게임산업법·시행령·전자상거래법 즉시 조회 (content_hash verified)
2. `library/domains/loot-boxes-probabilistic-items.md` 9 관할권 비교 프레임
3. MCP `get_annexes(bylSeq=000302)` live fetch로 [별표 3의2] 7유형 전문 확보
4. 공정위 넥슨 결정문을 6 서브섹션으로 구조화 (§39-41, §42-66, §67-82, §83-99, §100-111, §112-128)
5. 6 관할권 국제 비교 (일본/벨기에/중국/영국/독일/네덜란드)

**game-legal-research 자체 제안 (v3 후속):**
> "국제 비교 primary-source가 중요한 KR 게임법 질문은 `[game-legal-research ∥ general-legal-research]` 병렬이 더 나을 수 있음"

**판정: PASS** — Option b 검증 완료. v1 대비 comparable with specialist advantages.

### Test T2: PIPA ∥ GDPR 병렬 (Pattern 1 실전 검증)

**쿼리**: "한국 PIPA와 EU GDPR의 개인정보 국외이전 규제 주요 차이점" — PIPA 브랜치와 GDPR 브랜치로 분할 디스패치

**결과:**

| 브랜치 | Sources | Result.md | 토큰 | 시간 |
|--------|---------|-----------|------|------|
| PIPA (KR branch) | 13 (13A) | 18KB | 63k | 334s |
| GDPR (EU branch) | 13 (13A) | 17KB | 60k | 300s |

**검증된 기능:**
- ✅ 서로 다른 subagent 스레드에서 **독립 병렬 실행** (Phase 0 spike #8 확장 검증)
- ✅ 각 브랜치가 sibling의 파일 존재를 확인 (병렬성 증명)
- ✅ **스코프 분리 철저**: PIPA는 KR만, GDPR은 EU만 (Korea adequacy decision은 EU 관점에서만 언급)
- ✅ `key_findings`가 5개 comparison_dimension 태깅 (`legal_basis`/`consent`/`accountability`/`enforcement`/`suspension_order`) → writing-agent 통합 시 dimension-by-dimension 비교 가능
- ✅ 총 26 Grade A sources (13+13)

**판정: PASS** — Pattern 1 parallel dispatch가 realistic specialist combo에서 완벽 작동.

---

## Phase 7: route-case.md v2 commit

### Commit `1a71b9d` — feat(skills): route-case.md v2
- 1 file, +572/-87
- 메시지 본문에 plan-eng-review 피드백 13건 해결 내역 + 3 mini E2E 결과 수치 전부 포함
- v3 후속 개선 사항 명시 (game-legal-research 자체 제안, PIPA-expert grade-b gap, rate_limit 정책 등)

### 커밋 직후 git 상태
```
1a71b9d feat(skills): route-case.md v2 — Phase 2 전문가 라우팅 + Pattern 1 병렬 디스패치
6d8a9a7 docs: resume.md 세션 4 상태 반영
f4a5582 초기 커밋: 법무법인 진주 오케스트레이터 Phase 1
```

---

## Phase 8: PIPA-expert grade-b 보강 (다음 세션 이관)

### 배경
T1에서 발견한 KB gap — `library/grade-b/pipc-decisions/`, `library/grade-b/court-precedents/` 완전히 빈 상태.

### 탐색 결과
- 두 디렉토리 모두 실제로 비어있음 확인
- `source-registry.json`에 `"status": "pending"`, `"note": "추후 수집"`로 기록된 planned work
- PIPA-expert의 `ingest` 스킬은 inbox drop 워크플로우 (외부 소스 직접 fetch용 아님)
- korean-law MCP의 `search_pipc_decisions`/`get_pipc_decision_text`/`search_precedents`/`get_precedent_text` 활용 가능

### 스코프 결정
사용자가 **Option B (주제별 30건)** 선택:
- PIPC 결정 20건 + 대법원 판례 10건
- 6 core topics: 수집·이용 동의 / 제3자 제공 vs 처리위탁 / 안전조치·유출 / 국외이전 / 가명정보 / 민감·고유식별정보
- 예상: ~2-3시간, ~150k 토큰

### 세션 이관 결정
사용자가 **Y (별도 세션 진행)** 선택. 이유:
- 이 세션 토큰 부담 가중 방지
- fresh context로 시작
- rate_limit 리스크 격리

### 아키텍처 명확화
- `legal-agent-orchestrator/agents/PIPA-expert`는 **심볼릭 링크** → `/Users/kpsfamily/코딩 프로젝트/PIPA-expert/`
- 데이터는 **PIPA-expert 자체 레포**에 저장 + 해당 레포 git commit + GitHub push (public repo, setup.sh clone 경로)
- 오케스트레이터 레포는 건드리지 않음 — 심볼릭 링크가 자동 접근 보장
- 원칙 유지: "에이전트 100% 재활용, 오케스트레이터는 조율 레이어"

**핸드오프 문서:** `docs/todo/pipa-expert-grade-b-collection.md` (다음 세션용 체크리스트)

---

## 세션 4 총 커밋 요약

| 커밋 | 변경 | 의미 |
|------|------|------|
| `f4a5582` | 초기 커밋 (15 파일, +3016) | Phase 1 베이스라인 스냅샷 |
| `6d8a9a7` | resume.md 세션 4 반영 (+68/-54) | E2E 결과 + meta-verification 패턴 기록 |
| `1a71b9d` | route-case.md v2 (+572/-87) | Phase 2 2.1 + 2.2 + eng review 전면 수용 + 3 E2E 검증 |

**+ 세션 4 종료 커밋** (이 문서 + PIPA-expert 핸드오프 + resume.md 업데이트)

---

## 주요 결정 사항 (의사결정 추적)

| # | 결정 | 이유 |
|---|------|------|
| D1 | briefing 2 에이전트 routing 제외 | 독립 Python 앱, Agent tool 불가. 분리 운영. |
| D2 | 2.3 Pattern 3 skip | 토큰 녹음, skeleton 유지로 충분. |
| D3 | KR 게임법 → game-legal-research (Option b) | 도메인 특화 일관성. regression에서 v1 대비 -3% comparable 검증됨. |
| D4 | plan-eng-review 전면 수용 (A) | 필수 + 권장 이슈 전부 수정. E2E 3건 검증. |
| D5 | PIPA-expert grade-b 보강 = Option B (30건) | 주제별 커버리지가 landmark 10보다 실용적. |
| D6 | PIPA-expert 작업 다음 세션 이관 (Y) | 이 세션 부담 분리 + fresh context. |

---

## 알려진 후속 작업 (resume.md §7 업데이트 반영)

### 즉시 다음 세션 가능
1. **PIPA-expert grade-b 보강** (Option B, 30건) — `docs/todo/pipa-expert-grade-b-collection.md` 참조
2. **Case Replay MVP** (Next.js 뷰어) — 이제 3개 E2E 결과물 + Pattern 1 병렬 데이터까지 있어 더 풍부한 데모 가능
3. **README 작성** — `docs/notes/architecture-defense.md` 원재료 + session-log-20260410.md 활용

### Phase 2 후속 (옵션)
1. **manage-debate.md 실제 로직** (Pattern 3) — D2에서 skip 결정, 나중에 결정 변경 시
2. **route-case.md v3**: game-legal-research 자체 제안 반영 — 국제 비교 primary-source 필요 시 `[game-legal-research ∥ general-legal-research]` 병렬 지원
3. **Classification regression test 하네스** — 16 few-shot 예시 모두를 자동 검증

### 별건
1. **rate_limit 공식 재시도 정책** — 세션 4에서 부분 실패 처리로 커버는 했지만 공식 정책 별도 설계 필요
2. **LAW_OC 환경변수 자동 로드** — direnv 또는 Claude Code 세션 시작 스크립트
3. **docs/events-schema.json** — route-case.md 부록 A를 정식 JSON Schema로 추출
4. **퀄리티 비교 정식 측정** — v1 (general) vs v2 (specialist) 의견서 차이 정량화
