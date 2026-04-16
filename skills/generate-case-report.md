# 사건 단일 리포트 생성 (generate-case-report)

처리 완료된 케이스 디렉토리(`output/{CASE_ID}/` 또는 `samples/{CASE_ID}/`)의 흩어진 산출물을 하나의 읽기 좋은 `case-report.md`로 묶습니다.

이 스킬의 목표는 웹 뷰어를 만드는 것이 아니라, GitHub에서 폴더 하나만 열어도 사건 전체 맥락이 바로 읽히는 단일 마크다운 리포트를 만드는 것입니다.

---

## 입력

- 케이스 디렉토리 경로 1개
  - 예: `output/20260410-012238-391f`
  - 예: `samples/20260410-012238-391f`

## 출력

- 같은 디렉토리에 `case-report.md` 생성

---

## 생성 규칙

1. `events.jsonl`을 기준으로 사건 타임라인을 재구성합니다.
2. 연속된 `source_graded` 이벤트는 하나로 집계합니다.
3. `research-meta.json`, `writing-meta.json`, `review-meta.json`, `sources.json`, `opinion.md`, `review-result.md`를 읽어 narrative report로 합칩니다.
4. 누락 파일이 있어도 중단하지 않습니다.
   - `review-meta.json` 없음: 리뷰 섹션은 공백 상태로 남깁니다.
   - `sources.json` 없음: 각 `*-meta.json`의 `sources`를 병합합니다.
   - `opinion.md` 없음: 첨부 링크만 남기고 본문 삽입은 생략합니다.
   - `events.jsonl` 없음: `case-report.md` 생성 없이 skip 합니다.
5. 한국어 마이크로카피는 합니다체로 유지합니다.
6. 이벤트 alias는 다음만 canonical로 취급합니다.
   - `research_completed` → `agent_completed`
   - `writing_completed` → `agent_completed`
   - `review_completed` → `agent_completed`

---

## 권장 실행

```bash
PRIVATE_DIR="${LEGAL_ORCHESTRATOR_PRIVATE_DIR:-$PROJECT_ROOT/output}"
python3 "$PROJECT_ROOT/scripts/generate-case-report.py" "$PRIVATE_DIR/$CASE_ID"
```

샘플 케이스에 소급 적용할 때:

```bash
python3 scripts/generate-case-report.py samples/20260410-012238-391f
```

생성 직후 `case-report.md`에도 동일한 인젝션 스캔을 수행합니다:

```bash
ROOT="${PROJECT_ROOT:-.}"
CASE_DIR="${CASE_DIR:-${LEGAL_ORCHESTRATOR_PRIVATE_DIR:-$ROOT/output}/$CASE_ID}"  # 샘플 재생성 시 CASE_DIR=samples/<CASE_ID>
CR="$CASE_DIR/case-report.md"
if [ -f "$CR" ]; then
  python3 "$ROOT/scripts/sanitize-check.py" \
    --in "$CR" --out /dev/null \
    --audit "${CR%.md}.audit.json" \
    --source "case-report"
  COUNT=$(python3 -c "import json; print(len(json.load(open('${CR%.md}.audit.json', encoding='utf-8'))['matches']))")
  if [ -f "$CASE_DIR/events.jsonl" ] && [ "$COUNT" -gt 0 ]; then
    echo '{"id":"evt_NNN","ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","agent":"orchestrator","type":"deliverable_injection_residue","data":{"file":"case-report.md","match_count":'"$COUNT"',"audit":"case-report.audit.json"}}' \
      >> "$CASE_DIR/events.jsonl"
  fi
fi
```

---

## 검증 포인트

생성 후 다음을 확인합니다:

1. `case-report.md`가 같은 디렉토리에 생겼는지
2. 상단 메타데이터에 패턴, 상태, 시간, 참여자, 소스 분포가 들어갔는지
3. `## 처리 과정`에 사람이 읽는 타임라인이 생성됐는지
4. `## 최종 의견서`에 `opinion.md` 본문이 인라인 삽입됐는지
5. `## 첨부`에 상대 경로 링크가 살아 있는지

---

## 주의

- `samples/test-T1`, `samples/test-T2`, `samples/test-regression`처럼 `events.jsonl`이 없는 smoke test 폴더는 생성 대상에서 제외합니다.
- 이 스킬은 원본 산출물(`events.jsonl`, `*-meta.json`, `opinion.md` 등)을 수정하지 않습니다.
- `case-report.md`는 항상 derived artifact로만 취급합니다.
