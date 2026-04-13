# 아키텍처 방어 노트 — "이거 개발자가 보면 말도 안 되는 구조 아닌가?"

**기록일:** 2026-04-09
**맥락:** Phase 1 E2E 테스트 직전, 사용자가 아키텍처 선택의 정당성에 대해 질문
**용도:** README "Why This Architecture" 섹션의 원재료

---

## 사용자 질문

> "지금 내가 만든 이게 개발자들 보기엔 좀 말도 안 되는 구조인건 아닐까? 이렇게 에이전트를 꾸겨 넣으면 성능이 떨어지는거 아닐까?"

---

## Part 1: "말도 안 되는 구조"인가?

### 반쯤 맞고 반쯤 틀리다

**표준이 아닌 것은 맞다.**
멀티 에이전트 시스템의 업계 표준:
- LangGraph
- CrewAI
- AutoGen
- Claude Agent SDK

Claude Code를 오케스트레이션 런타임으로 쓰는 건 비주류. 개발자 첫 반응은 보통 "왜 Agent SDK 안 썼어?"

**하지만 "틀린" 건 아니다.**
선택 이유가 명확:
1. 10개 에이전트를 100% 그대로 재활용 (Agent SDK로 재구현하면 각각 50-60%만 재현)
2. MCP, skills, KB 전부 살아있음
3. 웹 서버 유지보수 불필요
4. 포트폴리오 프로젝트로 완벽 (실행 가능한 아티팩트 + 단일 파일 아카이브)

**이건 의도된 트레이드오프다.** 디자인 문서 Phase 3.5에서 Approach A vs B 비교로 다뤘고, 엔지니어링 리뷰에서 8개 이슈 발견/해결 후 승인됨.

---

## Part 2: "꾸겨 넣어서 성능 저하"인가?

### 이건 잘못된 멘탈 모델이다 (핵심)

에이전트들이 한 컨텍스트에 꾸겨 넣어지는 게 아니다.
**각 서브에이전트는 완전히 독립된 새 Claude 인스턴스.** 200K 컨텍스트를 처음부터 받는다.

```
오케스트레이터 (200K 컨텍스트)
   ├── Agent tool 호출 → 새 Claude 인스턴스 (200K, CLAUDE.md 로드)
   │                      └── 독립 실행, 결과만 반환
   ├── Agent tool 호출 → 또 다른 새 Claude 인스턴스 (200K)
   │                      └── 독립 실행, 결과만 반환
   └── ...
```

**오케스트레이터는 조율만 한다:**
- 질문 분류 (~2K tokens)
- Agent tool 호출 (~1K 프롬프트)
- 결과 파일에서 summary 읽기 (~2K tokens)
- 다음 에이전트 호출

오케스트레이터 총 컨텍스트 사용: ~25-40K. 여유 충분.

### 성능 저하가 실제로 있는 곳

| 항목 | 영향 | 대책 |
|------|------|------|
| Agent tool 호출당 ~1-3초 초기화 오버헤드 | 있음 | 불가피. 서브에이전트는 fresh Claude라서 매번 로드 필요. |
| 중첩 서브에이전트 비활성 (deep-researcher 등) | 중간 | Phase 0 확인. 영향 낮음 (빈도 낮음). |
| MCP 상속 문제 | 해결됨 | 루트 .mcp.json으로 우회. |
| Pattern 3 토론 시 ~8회 순차 호출 | 있음 | 각 호출 ~30-60초, 총 4-8분. |

---

## Part 3: 진짜 개발자 반응 예측

세 부류로 나뉨:

1. **"오 이거 똑똑한데"** — 기존 에이전트 재활용의 가치를 이해하는 사람. 포트폴리오로는 만점.

2. **"비표준이지만 흥미로움"** — 실용주의자. "LangGraph로 다시 짜는 게 맞다"지만 결과물 퀄리티 인정.

3. **"왜 이렇게 했어? 그냥 LangGraph 써"** — 프레임워크 순수주의자. 설명해도 안 먹힘.

**포트폴리오 관점에서는 1번 반응이 금.** "Harvey AI 안 되는 거 하네" + "기존 전문 에이전트 재활용" 조합이 스토리텔링 강점.

---

## README 킬러 포인트 후보

### 포인트 1: 컨텍스트 격리의 오해

> "Wait, doesn't stuffing 10 agents into one orchestrator kill performance?"
>
> No. That's a misconception about how Claude Code's Agent tool works.
>
> Each subagent gets a **fresh 200K context window**. The orchestrator doesn't carry their weight — it just coordinates. Total orchestrator context usage: ~25-40K tokens. Each specialist lawyer runs at full capacity, with their complete CLAUDE.md, skills, knowledge base, and MCP tools.
>
> This is the opposite of "stuffing" — it's the most context-efficient multi-agent architecture possible.

### 포인트 2: 왜 LangGraph/CrewAI가 아닌가

> "Why not use LangGraph or Agent SDK like everyone else?"
>
> Because wrapping existing Claude Code agents in a web framework loses 40-50% of their capability. The MCP integrations break. The skills system needs reimplementation. The knowledge base browsing changes. You end up with a pretty demo that produces legal opinions at half the quality of the original agents.
>
> We inverted the tradeoff: **use Claude Code as the runtime, preserve 100% of agent capability, and collapse final delivery into a single `case-report.md` artifact instead of a web app.** The result is an architecture that runs real legal work, not a demo.

### 포인트 3: 투명성 vs 블랙박스

> Harvey AI is a black box. You get an answer, you don't know how.
>
> Jinju Law Firm is the opposite:
> - Which specific lawyer was assigned? ✓ visible
> - What sources (Grade A/B/C) were consulted? ✓ visible
> - What did the fact-checker flag? ✓ visible
> - How did the inter-jurisdiction debate play out? ✓ visible
> - What did the partner review comment on? ✓ visible
>
> Because we reuse real specialized agents with their own source grading and fact-checking, **the process itself becomes the product.** Not the answer.

### 포인트 4: Single-File Case Report

> Most AI demos die after 30 seconds. Ours persist.
>
> Every processed case becomes a shareable `case-report.md`. One Markdown file, rendered directly on GitHub, no API key, no separate viewer, no extra deployment surface.
>
> The legal process is the content. The report is how we deliver it.

---

## 진짜 리스크 (이 노트의 핵심)

퀄리티가 아니다. **검증이다.**

이 아키텍처가 잘 돌아간다고 믿고 있지만, **아직 한 번도 end-to-end로 돌려본 적 없다.**
- Phase 1 테스트 성공 → "작동하는 비주류 아키텍처"
- Phase 1 테스트 실패 → "안 되는 실험"

지금 걱정할 것:
- ❌ "이게 말이 되나?"
- ✅ **"이게 실제로 동작하나?"**

---

## 결론

- **비주류 O, 잘못된 설계 X**
- **성능 저하 걱정 불필요** — 컨텍스트는 격리되어 있음
- **진짜 리스크는 untested** — Phase 1 E2E 테스트가 증거

README 작성 시 이 노트의 Part 2 (컨텍스트 격리) + Part 3 (개발자 반응)을 기반으로 "Why this architecture" 섹션 작성 예정.
