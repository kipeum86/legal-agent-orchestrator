# 최종 결과물 전달 (deliver-output)

모든 에이전트 작업이 완료된 후, 최종 결과물을 어셈블하고 클라이언트에게 전달합니다.

이 스킬의 모든 orchestrator bash 예시는 `PRIVATE_DIR="${LEGAL_ORCHESTRATOR_PRIVATE_DIR:-$PROJECT_ROOT/output}"`가 이미 설정되어 있다고 가정합니다. (`CLAUDE.md` Step 1)

---

## Step 1: 결과물 확인

기본 work-product 디렉토리(`$OUTPUT_DIR`; env 미설정 시 `output/{CASE_ID}`와 동일)의 파일을 확인하세요:

```bash
ls -la "$OUTPUT_DIR/"
```

**필수 파일:**
- `events.jsonl` — 이벤트 로그
- `opinion.md` 또는 `debate-opinion.md` 또는 `*-result.md` — 최종 결과물
- `*-meta.json` — 각 에이전트의 메타데이터

---

## Step 2: sources.json 병합 생성

각 에이전트의 meta.json에서 sources를 추출하여 통합 sources.json을 생성하세요:

```bash
python3 "$PROJECT_ROOT/scripts/merge-sources.py" "$OUTPUT_DIR"
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
      "agent_name": "범용 법률 리서치 스페셜리스트",
      "sources": []
    }
  ]
}
```

`merge-sources.py`는 모든 `*-meta.json`과 `events.jsonl`의 `source_graded` 이벤트를 함께 읽고, 같은 agent 안에서 `(title, citation)` 기준으로 중복을 제거합니다. 수동 작성 대신 이 스크립트를 사용해야 `agent_id`, grade 분포, citation 필드가 일관됩니다.

---

## Step 3: events.jsonl 마감

파이프라인 완료 이벤트를 기록하세요:

```bash
python3 "$PROJECT_ROOT/scripts/log-event.py" "$OUTPUT_DIR/events.jsonl" \
  --agent orchestrator \
  --type final_output \
  --final \
  --data-json "$(python3 -c 'import json, sys; sources=json.load(open(sys.argv[1], encoding="utf-8")); print(json.dumps({"case_id":sys.argv[2],"file_path":sys.argv[3],"format":"markdown","summary":"FINAL_SUMMARY","total_sources":sources.get("total_sources",0),"grade_distribution":sources.get("grade_distribution",{})}, ensure_ascii=False))' "$OUTPUT_DIR/sources.json" "$CASE_ID" "$OUTPUT_DIR/opinion.md")"
```

<!-- IF pattern == pattern_3 (토론) -->
```bash
python3 "$PROJECT_ROOT/scripts/log-event.py" "$OUTPUT_DIR/events.jsonl" \
  --agent orchestrator \
  --type final_output \
  --final \
  --data-json "$(python3 -c 'import json, sys; sources=json.load(open(sys.argv[1], encoding="utf-8")); print(json.dumps({"case_id":sys.argv[2],"pattern":"pattern_3","primary_deliverable":sys.argv[3],"deliverables":[sys.argv[3],sys.argv[4],sys.argv[5]],"summary":"VERDICT_SUMMARY","total_sources":sources.get("total_sources",0),"grade_distribution":sources.get("grade_distribution",{})}, ensure_ascii=False))' "$OUTPUT_DIR/sources.json" "$CASE_ID" "$OUTPUT_DIR/debate-opinion.docx" "$OUTPUT_DIR/debate-transcript.docx" "$OUTPUT_DIR/sources.json")"
```
<!-- END IF -->

---

## Step 4: 산출물 계약 검증

최종 전달 전에 case directory의 구조적 오류를 점검하세요. `warn` 모드는 경고와 오류를 모두 보고하지만 파이프라인을 즉시 중단하지 않습니다.

```bash
python3 "$PROJECT_ROOT/scripts/validate-case.py" "$OUTPUT_DIR" --mode warn \
  > "$OUTPUT_DIR/case-validation.json"
```

`case-validation.json`의 `errors`가 비어 있지 않다면:
- 누락된 필수 필드(`citation`, `summary`, `sources`, review comment object 등)를 가능한 경우 보정합니다.
- 보정할 수 없는 경우 최종 전달 메시지에 구조적 오류를 명시합니다.

---

## Step 5: case-report.md 생성

최종 전달 직전에 반드시 `case-report.md`를 생성하세요.

```bash
python3 "$PROJECT_ROOT/scripts/generate-case-report.py" "$OUTPUT_DIR"
```

생성 후 확인:

```bash
[ -f "$OUTPUT_DIR/case-report.md" ]
```

`events.jsonl`이 없는 smoke test 디렉토리라면 생성이 skip될 수 있습니다. 이 경우에도 파이프라인 자체를 실패로 처리하지는 않습니다.

---

## Step 6: 최종 인젝션 잔여물 스캔

DOCX 생성 또는 최종 전달 직전에, 최종 opinion/transcript markdown에 injection 잔여물이 남아있지 않은지 확인합니다.

```bash
for f in "$OUTPUT_DIR"/opinion.md \
         "$OUTPUT_DIR"/debate-opinion.md \
         "$OUTPUT_DIR"/debate-transcript.md; do
  [ -f "$f" ] || continue
  AUDIT="${f%.md}.deliverable.audit.json"
  python3 "$PROJECT_ROOT/scripts/sanitize-check.py" \
    --in "$f" --out /dev/null \
    --audit "$AUDIT" \
    --source "deliverable:$(basename "$f")"
  COUNT=$(python3 -c "import json; print(len(json.load(open('$AUDIT', encoding='utf-8'))['matches']))")
  if [ "$COUNT" -gt 0 ]; then
    python3 "$PROJECT_ROOT/scripts/log-event.py" "$OUTPUT_DIR/events.jsonl" \
      --agent orchestrator \
      --type deliverable_injection_residue \
      --data-json "$(python3 -c 'import json, sys; print(json.dumps({"file":sys.argv[1],"match_count":int(sys.argv[2]),"audit":sys.argv[3]}, ensure_ascii=False))' "$(basename "$f")" "$COUNT" "$(basename "$AUDIT")")"
  fi
done
```

매치가 발견되면:
- 모든 매치가 이미 `<escape>...</escape>` 태그 안에 있는 경우, 이는 Task 6에서 정상적으로 sanitize된 잔여물입니다. `scripts/md-to-docx.py`가 렌더 직전에 `<escape>` 프레임만 제거하므로 DOCX 생성은 계속할 수 있습니다.
- `<escape>` 태그 밖의 문구가 매치되면 sanitizer 우회 가능성이 있으므로 사고로 취급합니다. `deliverable_injection_residue` 이벤트를 남기고, DOCX 생성 및 최종 전달을 중단한 뒤 사용자에게 보고합니다.

## Step 7: 클라이언트에게 전달

최종 결과를 클라이언트에게 보고하세요. 아래 `output/{CASE_ID}` 표기는 실제로는 `$OUTPUT_DIR`를 뜻합니다. env 미설정 시 두 경로는 같습니다:

```
📋 사건 {CASE_ID} 처리 완료

📄 **최종 결과물:**
- 의견서: output/{CASE_ID}/opinion.md
- 사건 리포트: output/{CASE_ID}/case-report.md
- 참조 소스: output/{CASE_ID}/sources.json ({N}개 소스, Grade A: {n}개)

👥 **참여 에이전트:**
- 범용 법률 리서치 스페셜리스트 (리서치)
- 법률문서 작성 스페셜리스트 (작성)
- 시니어 리뷰 스페셜리스트 (검토: {approved/revision_needed})

📊 **파이프라인 이벤트 로그:** output/{CASE_ID}/events.jsonl
```

시니어 리뷰에서 `revision_needed`가 반환된 경우:
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

👥 **참여 에이전트:**
- {AGENT_A_NAME} (토론자)
- {AGENT_B_NAME} (토론자)
- 법률문서 작성 스페셜리스트 (종합 판단 작성)
- 시니어 리뷰 스페셜리스트 (검토: {approval status})

📊 참조 소스: `output/{CASE_ID}/sources.json` ({N}개 소스)
📊 이벤트 로그: `output/{CASE_ID}/events.jsonl`

<!-- END IF -->
