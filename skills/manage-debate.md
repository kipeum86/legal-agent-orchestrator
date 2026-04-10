# 멀티라운드 토론 (manage-debate) — Phase 2

> **이 스킬은 Phase 2에서 활성화됩니다.** Phase 1에서는 사용하지 않습니다.
> 토론 요청이 들어오면: "멀티라운드 토론은 Phase 2에서 활성화됩니다. 현재는 일반 리서치로 처리합니다."

---

## 토론 트리거 조건

다음 키워드가 포함된 질문에서 토론 패턴을 사용합니다:
- "양측 의견", "논쟁", "반론", "토론", "상충", "갈등", "debate"
- 두 관할권의 법적 입장이 상충(conflicting)할 때

## 토론 흐름 (Phase 2 구현 시)

```
Round 1: Agent A → 의견 제시 (opinion)
Round 2: Agent B → 결과 A에 대해 반론 (rebuttal)  
Round 3: Agent A → 결과 B에 대해 재반론 (surrebuttal)
Verdict: legal-writing-agent → A, B, C 종합하여 verdict 작성
Review:  second-review-agent → 최종 판단
```

**라운드 제한:** 최대 3라운드. 무한 루프 방지.

## 이벤트 로깅

각 라운드마다 debate_round 이벤트를 기록:
```json
{"type": "debate_round", "data": {"agent_id": "...", "round": 1, "position": "opinion|rebuttal|surrebuttal", "summary": "..."}}
```

토론 시작/종결:
```json
{"type": "debate_initiated", "data": {"topic": "...", "participants": [...], "max_rounds": 3}}
{"type": "debate_concluded", "data": {"verdict_summary": "...", "consensus_areas": [...], "disagreement_areas": [...]}}
```
