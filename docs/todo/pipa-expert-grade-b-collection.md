# TODO: PIPA-expert library/grade-b/ 보강 (Option B, 30건)

**작성일**: 2026-04-10 (세션 4 종료 시)
**배경**: 세션 4 T1 테스트에서 KB gap 발견 — PIPA-expert의 `library/grade-b/pipc-decisions/` 및 `library/grade-b/court-precedents/` 두 디렉토리가 완전히 빈 상태. `source-registry.json`에 `"pending — 추후 수집"`으로 기록된 planned work.

**관련 문서**:
- 세션 4 로그: [docs/session-log-20260410.md](../session-log-20260410.md) Phase 8 참조
- PIPA-expert ingest 스킬: `/Users/kpsfamily/코딩 프로젝트/PIPA-expert/.claude/skills/ingest/SKILL.md`
- Grade A 예시 파일: `/Users/kpsfamily/코딩 프로젝트/PIPA-expert/library/grade-a/pipa/art22.md`

---

## 중요: 아키텍처 전제

**이 작업은 `legal-agent-orchestrator` 레포가 아닌 `/Users/kpsfamily/코딩 프로젝트/PIPA-expert` 레포에서 수행한다.**

- `legal-agent-orchestrator/agents/PIPA-expert`는 **심볼릭 링크** → `/Users/kpsfamily/코딩 프로젝트/PIPA-expert/`
- 실제 데이터는 PIPA-expert 자체 레포에 저장
- PIPA-expert 레포에서 git commit + GitHub push (public repo, 다른 사용자 `setup.sh clone` 경로)
- 오케스트레이터 레포는 이 작업에서 **건드리지 않음**
- 심볼릭 링크로 오케스트레이터가 자동 접근

---

## 스코프: Option B (30건)

### 분배 (PIPC 20 + 판례 10)

| # | 주제 | PIPA 조문 | PIPC | 판례 | 총 |
|---|------|-----------|------|------|-----|
| 1 | 수집·이용 동의 | §15, §22 | 3 | 2 | 5 |
| 2 | 제3자 제공 vs 처리위탁 | §17, §26 | 3 | 2 | 5 |
| 3 | 안전조치의무·유출 | §29, §34 | 4 | 1 | 5 |
| 4 | 국외이전 | §28조의8~11 | 4 | 1 | 5 |
| 5 | 가명정보 | §28조의2~7 | 3 | 1 | 4 |
| 6 | 민감·고유식별정보 | §23, §24 | 3 | 2 | 5 |
| 보너스 | 헌재결정/자기결정권 | — | 0 | 1 | 1 |
| **합계** |  |  | **20** | **10** | **30** |

**PIPC 쪽을 더 채우는 이유**: 개인정보 분야는 PIPC 결정례가 압도적으로 많고, landmark 대법원 판례는 상대적으로 적음.

---

## 실행 계획 (3 Phase)

### Phase A: 큐레이션 (직접 수행, ~30분)

MCP tools 필요:
- `mcp__claude_ai_Korean-law__search_pipc_decisions`
- `mcp__claude_ai_Korean-law__search_precedents`
- (fetch는 Phase B에서 subagent가 사용: `get_pipc_decision_text`, `get_precedent_text`)

**ToolSearch로 위 tool schema 먼저 로드한 뒤 진행.**

주제별로 검색 → 각 주제 약 5-8개 후보 수집 → 중요도/최신성 기준으로 curated list 확정.

**검색 쿼리 예시:**

| 주제 | PIPC 검색 쿼리 | 판례 검색 쿼리 |
|------|---------------|---------------|
| 1. 동의 | "수집 동의 위반", "포괄 동의" | "개인정보 동의 범위", "동의 유효성" |
| 2. 제3자 제공/위탁 | "제3자 제공 고지", "처리위탁 구분" | "제3자 제공 vs 처리위탁" |
| 3. 안전조치/유출 | "안전조치 의무 위반", "개인정보 유출" | "개인정보 유출 손해배상" |
| 4. 국외이전 | "국외이전", "해외사업자 동의" | "국외이전 적정성" |
| 5. 가명정보 | "가명정보", "가명처리" | "가명정보" |
| 6. 민감/고유식별 | "민감정보", "주민등록번호 수집" | "주민등록번호 처리" |
| 보너스 | — | "개인정보 자기결정권" |

**주요 landmark 후보 (검색 시작점):**
- PIPC 결정: 넥슨 메이플스토리 (2024.1.5., 116억 — 세션 4 E2E 참조됨), 구글·메타 맞춤형 광고 (2022.9.14.), LG U+ 유출 (2023), 카카오 판교 데이터센터 (2023), 홈플러스 경품 응모
- 대법원 판례: 로앤비 개인정보자기결정권, CJ올리브네트웍스, 정보주체 열람권 관련, 손해배상 인정 기준
- 헌재결정: 주민등록번호 관련 헌법불합치 결정 등

**⚠️ 위 landmark는 내 기억 기반이라 실제 MCP 검색에서 사건명/사건번호 재검증 필수.** 일부는 다른 선례로 대체될 수 있음.

**Phase A 결과물**: 30개 ID + 메타 요약의 curated list (내부 메모, 파일화 불필요).

### Phase B: Fetch + Format + Save (subagent 위임)

**왜 subagent 위임**: 30 × 10-30KB 결정문 fetch는 mechanical 작업 + 내 context 보존 + rate_limit 격리.

**Subagent 프롬프트 구조** (다음 세션에서 작성):

```
You are dispatched to populate PIPA-expert's library/grade-b/ with {30} curated items.

INPUT:
- Curated list of {PIPC_IDs} PIPC decisions + {COURT_IDs} court precedents
- Schema template (below)
- Save paths (below)
- korean-law MCP access

SCHEMA TEMPLATE (frontmatter — ingest SKILL.md Step 4 참조):
---
# === 식별 정보 ===
source_id: "b-{pipc|court}-{year}-{slug}"
slug: "..."
title_kr: "..."
title_en: ""  # 있으면
document_type: "decision" | "precedent"

# === 소스 정보 ===
source_grade: "B"
publisher: "개인정보보호위원회" | "대법원" | "헌법재판소"
case_number: "..."  # 예: "제2024-001-001호", "2020다12345"
decision_date: "YYYY-MM-DD"
source_url: "https://www.pipc.go.kr/..." | "https://glaw.scourt.go.kr/..."
original_format: "json" (MCP 반환)
ingested_at: "{YYYY-MM-DD}"

# === 검색 메타 ===
keywords: [5-10개 키워드]
topics: ["consent" | "third_party_provision" | "outsourcing" | "safety_measures" | 
         "data_breach" | "cross_border_transfer" | "pseudonymized_data" |
         "sensitive_info" | "unique_identifier" | "self_determination"]
pipa_articles: ["15", "17", "22", ...]  # 인용된 조문
char_count: {글자수}

# === 검증 ===
verification_status: "VERIFIED"  # MCP 원문 직접 fetch
grade_confidence: "high"
---

CONTENT STRUCTURE:
# {title_kr}

## 사건 개요
- 사건번호: ...
- 처분일/선고일: ...
- 당사자: ...

## 주요 쟁점
- ...

## 결정/판시 사항
(verbatim 인용 위주)

## PIPA 조문 매핑
- 제X조: ...

## 관련 결정/판례
- ...

SAVE PATHS:
- PIPC: /Users/kpsfamily/코딩 프로젝트/PIPA-expert/library/grade-b/pipc-decisions/{slug}.md
- Court: /Users/kpsfamily/코딩 프로젝트/PIPA-expert/library/grade-b/court-precedents/{slug}.md

REPORT BACK:
- Files saved (count + paths)
- Errors or gaps
- DO NOT commit — orchestrator will commit after verification
```

**Phase B 결과물**: 30 파일 생성. 내 검증 대기.

### Phase C: 검증 + Registry 업데이트 + Commit (직접 수행, ~15분)

1. **검증**
   - `ls` 로 파일 30개 존재 확인
   - 랜덤 sample 2-3개 읽어서 schema 준수 확인
   - 주제 분포 확인 (30건이 6주제에 걸쳐 있는지)

2. **source-registry.json 업데이트**
   ```json
   "grade-b": {
     "pipc-decisions": {
       "status": "partial",  // pending → partial (30건 중 20건이므로)
       "count": 20,
       "target": null,  // 미정, 향후 확장
       "retrieved_at": "2026-MM-DDTHH:MM:SSZ",
       "note": "Initial landmark collection (Option B, 6 topics × ~3-4 decisions)"
     },
     "court-precedents": {
       "status": "partial",
       "count": 10,
       "target": null,
       "retrieved_at": "2026-MM-DDTHH:MM:SSZ",
       "note": "Initial landmark collection (Option B, 6 topics + constitutional court)"
     }
   }
   ```

3. **Commit (PIPA-expert 레포 내부)**
   ```bash
   cd "/Users/kpsfamily/코딩 프로젝트/PIPA-expert"
   git status  # 30개 신규 파일 + registry 변경 확인
   git add library/grade-b/pipc-decisions/*.md library/grade-b/court-precedents/*.md index/source-registry.json
   git commit -m "feat(grade-b): landmark 30건 초기 수집 (PIPC 20 + 판례 10)"
   # git push origin main  ← 사용자 확인 후
   ```

4. **Push 확인**
   - PIPA-expert는 public repo → `setup.sh clone` 경로이므로 push 중요
   - 사용자 명시적 승인 후 push

5. **오케스트레이터 측 검증 (선택)**
   - 오케스트레이터에서 `agents/PIPA-expert/library/grade-b/` 경유로 파일 접근 확인 (심볼릭 링크 검증)
   - T1 질문 재실행하여 grade-b에서 소스가 나오는지 확인 (regression)

---

## 예상 비용 및 리스크

| 항목 | 추정치 | 리스크 |
|------|--------|--------|
| 시간 | 2-3시간 | Phase A 검색이 예상보다 길어질 수 있음 |
| 토큰 (내 context) | ~30-50k | Phase C 검증 단계에서 파일 샘플 읽기 |
| 토큰 (subagent) | ~100-150k | 30 × (검색 + fetch + format) |
| Rate limit | 중 | 30 MCP 호출 연속 → 세션 4에서도 발생했던 이슈 |
| KB 중복 | 저 | grade-b 완전 빈 상태라 충돌 없음 |
| 소스 정확성 | 중 | korean-law MCP 원문 직접 fetch이므로 high confidence. 단 기존 PIPC 결정 번호 체계 변경 시 주의. |

---

## 시작 시 체크리스트 (다음 세션)

- [ ] 이 문서 읽기
- [ ] `docs/session-log-20260410.md` Phase 8 참조 (배경)
- [ ] `agents/PIPA-expert/.claude/skills/ingest/SKILL.md` 읽기 (schema 원본)
- [ ] `agents/PIPA-expert/library/grade-a/pipa/art22.md` 읽기 (frontmatter 예시)
- [ ] `agents/PIPA-expert/index/source-registry.json` 읽기 (update 대상)
- [ ] ToolSearch로 `search_pipc_decisions`, `search_precedents` 등 MCP tools 로드
- [ ] Phase A 시작 (주제별 검색 + 큐레이션)
- [ ] Phase B 시작 (subagent 위임, 프롬프트 위 템플릿 참조)
- [ ] Phase C 시작 (검증 + registry + commit + push)
- [ ] 완료 후 resume.md §8 "알려진 이슈" 항목에서 제거
- [ ] 완료 후 T1 재실행 (optional regression) — grade-b 소스가 실제로 나오는지 확인

---

## 후속 작업 (별건)

이 작업 완료 후에도 남는 일:

1. **Option C로 확장** (필요 시): 100건+ 포괄 수집. 이 30건이 landmark이면 나머지는 주제 내 세부 사례.
2. **PIPA-expert library/grade-c/** (law-firm, academic) 보강 — registry에도 `pending` 상태
3. **GDPR-expert KB gap 확인** — 유사한 gap이 있는지 검증 필요
4. **game-legal-research KB** — T2/Regression에서 이미 활용됨, gap 없을 가능성 높지만 확인 가능
