# Generate Single-File Case Report (generate-case-report)

For a completed case directory (`output/{CASE_ID}/` or `samples/{CASE_ID}/`), bundle the scattered work-products into a single readable `case-report.md`.

The goal of this skill is **not** to build a web viewer, but to produce a single markdown report so that opening one folder on GitHub immediately conveys the full case context.

---

## Input

- A single case directory path
  - e.g., `output/20260410-012238-391f`
  - e.g., `samples/20260410-012238-391f`

## Output

- `case-report.md` written to the same directory.

---

## Generation rules

1. Reconstruct the case timeline from `events.jsonl`.
2. Collapse consecutive `source_graded` events into a single aggregated entry.
3. Read `research-meta.json`, `writing-meta.json`, `review-meta.json`, `sources.json`, `opinion.md`, and `review-result.md`, and stitch them into a narrative report.
4. Missing files do not abort generation:
   - `review-meta.json` missing: leave the review section blank.
   - `sources.json` missing: merge `sources` from each `*-meta.json`.
   - `opinion.md` missing: keep only the attachment link; skip the inline body.
   - `events.jsonl` missing: skip generation entirely.
5. Korean microcopy must use the 합니다체 register.
6. Treat only the following event aliases as canonical:
   - `research_completed` → `agent_completed`
   - `writing_completed` → `agent_completed`
   - `review_completed` → `agent_completed`

---

## Recommended invocation

```bash
PRIVATE_DIR="${LEGAL_ORCHESTRATOR_PRIVATE_DIR:-$PROJECT_ROOT/output}"
python3 "$PROJECT_ROOT/scripts/generate-case-report.py" "$OUTPUT_DIR"
```

When backfilling a sample case:

```bash
python3 scripts/generate-case-report.py samples/20260410-012238-391f
```

Right after generation, run the same injection scan against `case-report.md`:

```bash
ROOT="${PROJECT_ROOT:-.}"
CASE_DIR="${CASE_DIR:-${LEGAL_ORCHESTRATOR_PRIVATE_DIR:-$ROOT/output}/$CASE_ID}"  # for sample regeneration set CASE_DIR=samples/<CASE_ID>
CR="$CASE_DIR/case-report.md"
if [ -f "$CR" ]; then
  python3 "$ROOT/scripts/sanitize-check.py" \
    --in "$CR" --out /dev/null \
    --audit "${CR%.md}.audit.json" \
    --source "case-report"
  COUNT=$(python3 -c "import json; print(len(json.load(open('${CR%.md}.audit.json', encoding='utf-8'))['matches']))")
  if [ -f "$CASE_DIR/events.jsonl" ] && [ "$COUNT" -gt 0 ]; then
    python3 "$ROOT/scripts/log-event.py" "$CASE_DIR/events.jsonl" \
      --agent orchestrator \
      --type deliverable_injection_residue \
      --data-json "$(python3 -c 'import json, sys; print(json.dumps({"file":"case-report.md","match_count":int(sys.argv[1]),"audit":"case-report.audit.json"}, ensure_ascii=False))' "$COUNT")"
  fi
fi
```

---

## Verification points

After generation, verify:

1. `case-report.md` was written to the same directory.
2. The top metadata block contains pattern, status, timestamps, participants, and source distribution.
3. `## 처리 과정` contains a human-readable timeline.
4. `## 최종 의견서` inlines the body of `opinion.md`.
5. `## 첨부` contains live relative-path links.

---

## Caveats

- Smoke-test folders without `events.jsonl` (e.g., `samples/test-T1`, `samples/test-T2`, `samples/test-regression`) are excluded.
- This skill never modifies the source artifacts (`events.jsonl`, `*-meta.json`, `opinion.md`, etc.).
- `case-report.md` is treated only as a derived artifact.
