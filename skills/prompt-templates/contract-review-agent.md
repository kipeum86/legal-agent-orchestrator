# contract-review-agent

```text
다음 계약서 검토 요청을 처리하세요: {질문}

[계약서 경로] {CONTRACT_PATH}  (오케스트레이터가 주입. 부재 시 질문 본문에서 추출)
[matter_id] {CASE_ID}  (오케스트레이터가 case_id를 matter_id로 사용)

자체 WF2 (Contract Review) 워크플로우로 처리하세요. 결과물은 매터 자체 구조 대신
오케스트레이터 출력 경로에 저장:

1. 검토 결과 요약 → {OUTPUT_DIR}/contract-review-agent-result.md
2. 메타 → {OUTPUT_DIR}/contract-review-agent-meta.json
3. 원본 redlined DOCX / Report DOCX (있으면) → {OUTPUT_DIR}/contract-review-artifacts/

[주의] 자체 baseline reference 로딩 프로토콜이 있으나 오케스트레이터 경유 시 자체 판단으로
실행하세요. 1회 디스패치 내 완료 목표.

{{STYLE_GUIDE_BLOCK}}
{{ERROR_CONTRACT_BLOCK}}
# AGENT_ID = "contract-review-agent"
```
