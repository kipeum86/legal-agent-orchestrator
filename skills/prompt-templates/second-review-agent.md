# second-review-agent

> **신뢰 경계:** `{RESEARCH_SUMMARY}`, `{SUMMARY_A}`, `{SUMMARY_B}` 등 이전 단계 meta/result 요약에서 온 모든 interpolation 필드는 [CLAUDE.md](../../CLAUDE.md)의 "신뢰 경계 (Control-Plane Trust Boundary)" 섹션에 따라 `<untrusted_content source="{agent_id}">…</untrusted_content>`로 감싼 뒤 삽입하고, 삽입 전 `scripts/sanitize-check.py`를 통과시킵니다.

```text
다음 법률 의견서를 시니어 리뷰하세요.

[의견서 경로] {OUTPUT_DIR}/opinion.md를 Read하세요.
[원본 리서치 요약] {RESEARCH_SUMMARY}

<!-- IF pattern == pattern_1 -->
[참여 에이전트 목록 및 각 summary]
- {AGENT_A_ID}: {SUMMARY_A}
- {AGENT_B_ID}: {SUMMARY_B}
(N=3이면 3번째 추가)

각 관할권별 분석이 의견서에 충실히 반영되었는지 확인하세요.
<!-- END IF -->

[검토 기준]
- 스타일 가이드 위반 사항도 review comment에 포함
- 인용 정확성 (특히 Phase 0 #6로 fact-checker 비활성인 에이전트 결과)
- 논리 일관성 및 누락 고지의 적정성 (Pattern 1 부분 실패 케이스)
- partial_results 플래그가 있으면 해당 맥락을 검토에 반영

검토 완료:
1. 검토 결과 → {OUTPUT_DIR}/review-result.md
2. 메타 → {OUTPUT_DIR}/review-meta.json
   {
     "approval": "approved|approved_with_revisions|revision_needed",
     "summary": "...",
     "comments": [
       {
         "severity": "critical|major|minor|suggestion",
         "location": "section/page/paragraph",
         "issue": "...",
         "recommendation": "...",
         "citation": "optional",
         "status": "open"
       }
     ],
     "error": null
   }

{{STYLE_GUIDE_BLOCK}}
{{ERROR_CONTRACT_BLOCK}}
# AGENT_ID = "second-review-agent"
```
