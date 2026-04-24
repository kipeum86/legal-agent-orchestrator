# Common Prompt Blocks

Use these blocks when rendering any agent prompt from `skills/route-case.md`.

## `{{STYLE_GUIDE_BLOCK}}`

한국어 결과물 작성/검토 에이전트에만 주입합니다.

```text
[필수] 한국어 결과물 작성/검토 시 스타일 가이드 준수:
{PROJECT_ROOT}/legal-writing-formatting-guide.md

이 가이드가 문서 구조, 인용 형식, 어조, 확신도 언어 척도, 번호 매김,
타이포그래피(이중 폰트 Times New Roman + 맑은 고딕)의 정본(canonical source)입니다.
에이전트 자체에 유사한 스타일 가이드가 있더라도 위 절대 경로를 정본으로 사용하세요.
```

적용 대상: `PIPA-expert`, `GDPR-expert`, `game-legal-research`, `contract-review-agent`, `legal-writing-agent`, `second-review-agent`.

`general-legal-research`는 리서치 단계이므로 선택적입니다. `legal-translation-agent`에는 주입하지 않습니다.

## `{{ERROR_CONTRACT_BLOCK}}`

모든 에이전트에 주입합니다.

```text
[에러 처리 계약]
- MCP 실패/타임아웃: 사용 가능한 범위에서 부분 결과를 저장하고 meta.json에 `error` 필드 기록:
  {"error": {"type": "mcp_timeout|mcp_error|rate_limit|source_not_found|out_of_scope",
             "message": "...", "recoverable": true|false}}
- 소스 부재: result.md에 "관련 1차 소스를 찾지 못함" 명시, meta.json sources는 빈 배열이되
  key_findings에 사유 기록.
- 관할권/도메인 범위 외 질문: 거부하지 말고 result.md에 "이 질문은 에이전트 전문 범위
  밖입니다: {사유}"를 기록하고 meta.error.type = "out_of_scope". 오케스트레이터가 감지하여
  fallback 라우트로 전환합니다.
- Rate limit: meta.error.type = "rate_limit". 오케스트레이터가 1회 재시도 판단.
```

## `{{OUTPUT_CONTRACT_BLOCK}}`

모든 에이전트에 주입합니다. `{AGENT_ID}`는 렌더 시 대상 에이전트 id로 치환합니다.

```text
[출력 계약 (필수)]
1. 상세 결과물 → {OUTPUT_DIR}/{AGENT_ID}-result.md
2. 메타데이터 → {OUTPUT_DIR}/{AGENT_ID}-meta.json

meta.json 스키마:
{
  "summary": "500 tokens 이내 핵심 요약",
  "issue_map": [
    {
      "issue": "쟁점",
      "answer": "핵심 답변",
      "authority_ids": ["src_001"],
      "confidence": "high|medium|low"
    }
  ],
  "key_findings": ["발견 1", "발견 2", ...],
  "sources": [
    {
      "id": "src_001",
      "title": "...",
      "grade": "A|B|C|D",
      "citation": "...",
      "pinpoint": "...",
      "url_or_access": "optional"
    }
  ],
  "error": null
}

오케스트레이터는 meta.json 존재 → summary/sources 파싱, 부재 → 반환 텍스트에서
fallback 추출합니다. meta.json을 저장하지 않으면 fallback 경로로 진행되어 데이터 손실
가능성이 있으므로 반드시 저장하세요.
```
