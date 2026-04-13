# 최종 결과물 전달 (deliver-output)

모든 에이전트 작업이 완료된 후, 최종 결과물을 어셈블하고 클라이언트에게 전달합니다.

---

## Step 1: 결과물 확인

output/{CASE_ID}/ 디렉토리의 파일을 확인하세요:

```bash
ls -la "$PROJECT_ROOT/output/$CASE_ID/"
```

**필수 파일:**
- `events.jsonl` — 이벤트 로그
- `opinion.md` 또는 `debate-opinion.md` 또는 `*-result.md` — 최종 결과물
- `*-meta.json` — 각 에이전트의 메타데이터

---

## Step 2: sources.json 병합 생성

각 에이전트의 meta.json에서 sources를 추출하여 통합 sources.json을 생성하세요:

```bash
# sources.json 생성은 수동으로: 각 *-meta.json을 Read하여 sources 배열을 추출하고 병합
```

**sources.json 형식:**
```json
{
  "case_id": "{CASE_ID}",
  "total_sources": 0,
  "grade_distribution": { "A": 0, "B": 0, "C": 0, "D": 0 },
  "agents": [
    {
      "agent_id": "general-legal-research",
      "agent_name": "김재식",
      "sources": []
    }
  ]
}
```

각 meta.json을 Read하여 sources 배열을 추출하고, 위 형식으로 병합한 뒤 파일로 저장:
```bash
# Write tool로 $PROJECT_ROOT/output/$CASE_ID/sources.json에 저장
```

---

## Step 3: events.jsonl 마감

파이프라인 완료 이벤트를 기록하세요:

```bash
echo '{"id":"evt_final","ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","agent":"orchestrator","type":"final_output","data":{"file_path":"output/'"$CASE_ID"'/opinion.md","format":"markdown","summary":"FINAL_SUMMARY","total_sources":N,"grade_distribution":{"A":0,"B":0,"C":0,"D":0}}}' >> "$PROJECT_ROOT/output/$CASE_ID/events.jsonl"
```

<!-- IF pattern == pattern_3 (토론) -->
```bash
echo '{"id":"evt_final","ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","agent":"orchestrator","type":"final_output","data":{"case_id":"'"$CASE_ID"'","pattern":"pattern_3","primary_deliverable":"debate-opinion.docx","deliverables":["debate-opinion.docx","debate-transcript.docx","sources.json"],"summary":"VERDICT_SUMMARY","total_sources":N,"grade_distribution":{"A":0,"B":0,"C":0,"D":0}}}' >> "$PROJECT_ROOT/output/$CASE_ID/events.jsonl"
```
<!-- END IF -->

---

## Step 4: case-report.md 생성

최종 전달 직전에 반드시 `case-report.md`를 생성하세요.

```bash
python3 "$PROJECT_ROOT/scripts/generate-case-report.py" "$PROJECT_ROOT/output/$CASE_ID"
```

생성 후 확인:

```bash
[ -f "$PROJECT_ROOT/output/$CASE_ID/case-report.md" ]
```

`events.jsonl`이 없는 smoke test 디렉토리라면 생성이 skip될 수 있습니다. 이 경우에도 파이프라인 자체를 실패로 처리하지는 않습니다.

---

## Step 5: 클라이언트에게 전달

최종 결과를 클라이언트에게 보고하세요:

```
📋 사건 {CASE_ID} 처리 완료

📄 **최종 결과물:**
- 의견서: output/{CASE_ID}/opinion.md
- 사건 리포트: output/{CASE_ID}/case-report.md
- 참조 소스: output/{CASE_ID}/sources.json ({N}개 소스, Grade A: {n}개)

👥 **참여 변호사:**
- 김재식 (리서치)
- 한석봉 (작성)
- 반성문 파트너 (검토: {approved/revision_needed})

📊 **파이프라인 이벤트 로그:** output/{CASE_ID}/events.jsonl
```

파트너 검토에서 `revision_needed`가 반환된 경우:
- 검토 코멘트를 legal-writing-agent에 전달하여 수정 요청
- 수정 후 다시 second-review-agent에 재검토 요청
- 최대 2회 수정 사이클 후 현재 상태로 전달

<!-- IF pattern == pattern_3 (토론) -->

📋 사건 {CASE_ID} 처리 완료 — 멀티라운드 토론

📄 **최종 결과물:**
- 토론 종합 판단 보고서: `output/{CASE_ID}/debate-opinion.docx`
- 토론 트랜스크립트: `output/{CASE_ID}/debate-transcript.docx`
- 사건 리포트: `output/{CASE_ID}/case-report.md`

⚖️ **토론 개요:**
- 주제: {TOPIC}
- {AGENT_A_NAME} ({JURISDICTION_A}) vs {AGENT_B_NAME} ({JURISDICTION_B})
- 라운드: {N_ROUNDS}
- 결론: {VERDICT_SUMMARY}

👥 **참여 변호사:**
- {AGENT_A_NAME} (토론자)
- {AGENT_B_NAME} (토론자)
- 한석봉 (종합 판단 작성)
- 반성문 파트너 (검토: {approval status})

📊 참조 소스: `output/{CASE_ID}/sources.json` ({N}개 소스)
📊 이벤트 로그: `output/{CASE_ID}/events.jsonl`

<!-- END IF -->
