# 사건 분류 및 파이프라인 실행 (route-case)

이 스킬은 클라이언트의 법률 질문을 분석하여 적절한 에이전트 조합과 실행 패턴을 결정합니다.

---

## Step 1: 질문 분류

클라이언트의 질문을 다음 4개 차원으로 분류하세요:

```json
{
  "jurisdiction": ["KR", "EU", "US", "international", "multi"],
  "domain": "general | data_protection | game_regulation | contract | translation | briefing",
  "task": "research | drafting | review | translation | briefing | debate",
  "complexity": "simple | compound | multi_domain | adversarial"
}
```

### 분류 예시 (few-shot)

| 질문 | jurisdiction | domain | task | complexity |
|------|-------------|--------|------|-----------|
| "한국 게임산업법의 확률형 아이템 규제" | KR | game_regulation | research | simple |
| "개인정보보호법 제28조의2 해석" | KR | data_protection | research | simple |
| "한국과 EU의 국외이전 규제 비교" | KR, EU | data_protection | research | multi_domain |
| "이 계약서 검토해줘" | — | contract | review | simple |
| "법률 의견서를 작성해줘" | — | general | drafting | compound |
| "양측 의견을 들려줘" | multi | data_protection | debate | adversarial |
| "이 문서를 영어로 번역해줘" | — | translation | translation | simple |
| "게임규제 최신 뉴스" | — | game_regulation | briefing | simple |

---

## Step 2: 에이전트 조합 결정

### Phase 1 라우팅 (현재 활성)

Phase 1에서는 다음 3개 에이전트만 사용합니다:
- **general-legal-research** (김재식) — 모든 리서치
- **legal-writing-agent** (한석봉) — 문서 작성
- **second-review-agent** (반성문) — 파트너 검토

**라우팅 트리:**

```
질문 입력
  ├─ task == "research" (리서치 요청)
  │   → general-legal-research → (필요 시) legal-writing → second-review
  │
  ├─ task == "drafting" (문서 작성 요청)
  │   → general-legal-research → legal-writing → second-review
  │
  ├─ task == "review" (검토 요청)
  │   → second-review (단독)
  │
  ├─ task == "translation" (번역 요청)
  │   → [Phase 2] legal-translation-agent
  │   → [Phase 1 fallback] "번역 에이전트는 Phase 2에서 활성화됩니다" 안내
  │
  ├─ task == "briefing" (뉴스/브리핑)
  │   → [Phase 2] game-legal-briefing / game-policy-briefing
  │   → [Phase 1 fallback] "브리핑 에이전트는 Phase 2에서 활성화됩니다" 안내
  │
  └─ 분류 모호
      → general-legal-research (기본 라우트)
```

### Phase 2 라우팅 (나중에 활성화)

```
질문 입력
  ├─ domain == "data_protection" + jurisdiction includes "EU"
  │   → GDPR-expert → legal-writing → second-review
  │
  ├─ domain == "data_protection" + jurisdiction includes "KR"
  │   → PIPA-expert → legal-writing → second-review
  │
  ├─ domain == "data_protection" + complexity == "multi_domain"
  │   → [PIPA-expert ∥ GDPR-expert] → legal-writing → second-review  (Pattern 1)
  │
  ├─ domain == "game_regulation"
  │   → game-legal-research → legal-writing → second-review
  │
  ├─ domain == "contract"
  │   → contract-review-agent → second-review
  │
  ├─ complexity == "adversarial" (토론 요청)
  │   → skills/manage-debate.md 참조  (Pattern 3)
  │
  └─ 기본
      → general-legal-research → legal-writing → second-review
```

---

## Step 3: 파이프라인 실행

분류 결과를 events.jsonl에 기록하세요:

```bash
echo '{"id":"evt_002","ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","agent":"orchestrator","type":"case_received","data":{"query":"QUERY_SUMMARY","jurisdiction":["KR"],"domain":"DOMAIN","task":"TASK","complexity":"COMPLEXITY","pipeline":["AGENT1","AGENT2","AGENT3"]}}' >> "$PROJECT_ROOT/output/$CASE_ID/events.jsonl"
```

그런 다음 CLAUDE.md의 Step 3(에이전트 디스패치)으로 돌아가서 파이프라인의 각 에이전트를 순서대로 호출하세요.

### 에이전트별 프롬프트 가이드

**general-legal-research (김재식):**
```
다음 법률 질문을 리서치하세요: {질문}

리서치 완료 후 반드시:
1. 전체 분석 결과를 {PROJECT_ROOT}/output/{CASE_ID}/research-result.md에 저장
2. 메타데이터를 {PROJECT_ROOT}/output/{CASE_ID}/research-meta.json에 저장:
   {"summary": "...", "key_findings": [...], "sources": [...]}
```

**legal-writing-agent (한석봉):**
```
다음 리서치 결과를 바탕으로 법률 의견서를 작성하세요.

[리서치 요약]: {이전 에이전트의 summary}
[주요 발견]: {이전 에이전트의 key_findings}
[상세 리서치 참조]: {PROJECT_ROOT}/output/{CASE_ID}/research-result.md를 Read하세요.

[필수] 한국어 의견서 작성 전, 반드시 다음 스타일 가이드를 Read하고 준수하세요:
{PROJECT_ROOT}/docs/ko-legal-opinion-style-guide.md
이 가이드가 문서 구조, 인용 형식, 어조, 확신도 언어, 번호 매기기, 타이포그래피의 정본(canonical source)입니다.

의견서 작성 완료 후 반드시:
1. 완성된 의견서를 {PROJECT_ROOT}/output/{CASE_ID}/opinion.md에 저장
2. 메타데이터를 {PROJECT_ROOT}/output/{CASE_ID}/writing-meta.json에 저장:
   {"summary": "...", "key_findings": [...], "sources": [...]}
```

**second-review-agent (반성문 파트너):**
```
다음 법률 의견서를 파트너 검토하세요.

[의견서 경로]: {PROJECT_ROOT}/output/{CASE_ID}/opinion.md를 Read하세요.
[리서치 요약]: {research summary}

[필수] 한국어 의견서 검토 전, 반드시 다음 스타일 가이드를 Read하고 이를 기준으로 검토하세요:
{PROJECT_ROOT}/docs/ko-legal-opinion-style-guide.md
스타일 가이드 위반 사항도 review comment에 포함하세요.

검토 완료 후 반드시:
1. 검토 결과를 {PROJECT_ROOT}/output/{CASE_ID}/review-result.md에 저장
2. 메타데이터를 {PROJECT_ROOT}/output/{CASE_ID}/review-meta.json에 저장:
   {"summary": "...", "key_findings": [...], "sources": [...], "approval": "approved|revision_needed", "comments": [...]}
```
