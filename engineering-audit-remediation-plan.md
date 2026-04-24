# Legal Agent Orchestrator 엔지니어링 감사 개선 기획서

작성일: 2026-04-24

이 문서는 직전 엔지니어링/프롬프트 감사에서 지적된 문제를 하나씩 수정 가능한 작업 단위로 쪼갠 실행 계획이다. 목표는 새로운 기능을 늘리는 것이 아니라, 현재 오케스트레이터가 이미 약속한 품질, 감사 가능성, 재현성, 토큰 효율을 실제 런타임에서 보장하게 만드는 것이다.

## 실행 완료 상태

상태: **완료**

최종 acceptance gate:
- `python3 scripts/acceptance-check.py --json`
- 결과: `engineering-audit-acceptance-report.md` 기준 **12/12 PASS**

운영 smoke:
- `python3 -m unittest`
- `python3 scripts/sanitize-check.py --self-test`
- `python3 scripts/smoke-check.py`

구현 추적:

| 범위 | 주요 산출물 | 검증 |
|---|---|---|
| Phase 0-1 기반 계약 | `OUTPUT_DIR` 계약, tracked `legal-writing-formatting-guide.md`, public fixtures | `scripts/smoke-check.py`, `tests/test_generate_case_report.py` |
| Phase 2 이벤트/schema | `scripts/log-event.py`, `schemas/*.schema.json`, `scripts/validate-case.py` | `tests/test_log_event.py`, `tests/test_validate_case.py` |
| Phase 3 결정적 조립 | `scripts/merge-sources.py`, `scripts/finalize-case.py`, case-report meta discovery | `tests/test_merge_sources.py`, `tests/test_finalize_case.py`, `tests/test_generate_case_report.py` |
| Phase 4 라우팅 안정화 | `schemas/routing.schema.json`, `scripts/select-route.py`, `scripts/lib/routing.py` | `tests/test_routing.py` |
| Phase 5 토큰/토론 효율 | `skills/prompt-templates/`, `scripts/build-debate-transcript.py`, `scripts/decide-debate-round3.py` | `tests/test_prompt_templates.py`, `tests/test_build_debate_transcript.py`, `tests/test_decide_debate_round3.py` |
| Phase 6 안전성 강화 | `sanitize-check.py --fail-on-unescaped`, DOCX escape omission policy | `tests/test_sanitize.py`, `tests/test_md_to_docx_escape_policy.py` |
| Phase 7 재현성 | `agents.lock`, `scripts/agent-lock.py`, pinned `.mcp.json`, MCP monitor workflow | `tests/test_agent_lock.py`, `tests/test_mcp_pins.py` |
| 최종 수락 | `scripts/acceptance-check.py`, `engineering-audit-acceptance-report.md` | `tests/test_acceptance_check.py` |

이 문서의 아래 섹션들은 원래 실행 계획을 보존한다. 향후 회귀나 scope 변경이 생기면 위 acceptance gate를 먼저 갱신한 뒤 해당 Phase 항목을 수정한다.

## 원칙

1. 하위 agent 레포의 `CLAUDE.md`, skills, KB는 수정하지 않는다.
2. 오케스트레이터 레포는 control plane만 책임진다: 라우팅, 파일 계약, 이벤트, 검증, 최종 조립.
3. 모델에게 “반드시”라고 지시하는 부분은 가능하면 스크립트와 schema validation으로 강제한다.
4. 먼저 파일/스키마/경로 계약을 안정화한다. 다만 `summary` payload 축소처럼 rate-limit와 직결되는 토큰 효율 작업은 schema 정리 직후 앞당겨 처리한다.
5. 각 단계는 독립적으로 merge 가능해야 하며, 회귀 테스트가 있어야 한다.

## 우선순위 요약

| 우선순위 | 작업 묶음 | 이유 |
|---|---|---|
| P0 | 경로 계약, tracked style guide, event writer, 회귀 fixture | 런타임 파일 누락과 감사 로그 손상을 막는 기반 |
| P1 | schema validation, token payload 축소, deterministic `sources.json`, `case-report` meta discovery, review cycle 정렬 | 최종 산출물의 신뢰성과 rate-limit 안정성 개선 |
| P2 | prompt 정리, routing schema 정규화 | 비용 절감과 라우팅 안정성 개선 |
| P3 | Pattern 3 transcript 재설계, agent/MCP lockfile | 대형 케이스 토큰 폭증과 재현성 문제 해결 |

## Phase 0: 현재 상태 고정과 회귀 기준 만들기

### 0.1 기준 테스트 케이스 fixture 추가

문제:
현재 테스트는 sanitizer 중심이며, 라우팅/이벤트/리포트 조립 문제를 잡지 못한다.

중요성:
앞으로 경로 계약과 meta 파일 탐색을 고치면 회귀 가능성이 높다. 실제 케이스와 유사한 fixture가 없으면 `case-report.md`가 조용히 부정확해져도 알 수 없다.

수정안:
- `tests/fixtures/cases/pattern2-basic/` 추가
- `tests/fixtures/cases/pattern1-multi-agent/` 추가
- `tests/fixtures/cases/path-resolution/` 추가
  - `output/CASE_ID` 또는 bare `CASE_ID` 입력이 private dir로 resolve되는지 확인
  - `samples/CASE_ID` legacy 입력이 계속 작동하는지 확인
- 각 fixture에는 최소 파일을 둔다:
  - `events.jsonl`
  - `general-legal-research-meta.json` 또는 `PIPA-expert-meta.json`, `GDPR-expert-meta.json`
  - `writing-meta.json`
  - `review-meta.json`
  - `opinion.md`
- 공개 레포 fixture는 합성 minimal 데이터만 사용한다. 실제 사건 기반 회귀 fixture는 `tests/fixtures-private/`에 두고 gitignore한다.
- 합성 fixture에도 `PIPA-expert`, `GDPR-expert`처럼 대소문자가 섞인 agent id를 반드시 포함한다.

대상 파일:
- `tests/fixtures/cases/...`
- `tests/test_generate_case_report.py`

검증:
- `python3 -m unittest`
- pattern1 fixture에서 PIPA/GDPR sources가 모두 `case-report.md`에 나타나는지 확인
- macOS와 Linux 양쪽에서 `PIPA-expert-meta.json`의 대소문자가 보존되어 agent id로 인식되는지 확인
- `tests/fixtures-private/`가 git에 올라가지 않는지 `git check-ignore -v tests/fixtures-private/example`로 확인

### 0.2 smoke command 문서화

문제:
현재 검증 명령이 sanitizer 테스트에 치우쳐 있다.

수정안:
- `README.md` 또는 새 `CONTRIBUTING.md`에 다음 최소 검증 명령을 추가한다:
  - `python3 -m unittest`
  - `python3 scripts/sanitize-check.py --self-test`
  - `python3 scripts/generate-case-report.py tests/fixtures/cases/pattern2-basic`

검증:
- fresh clone 기준으로 문서 명령이 성공해야 한다.

## Phase 1: 파일 경로와 배포 누락 수정

### 1.1 단일 출력 디렉토리 계약 도입

문제:
`CLAUDE.md`와 `skills/route-case.md`는 agent에게 `{PROJECT_ROOT}/output/{CASE_ID}`에 쓰라고 지시하지만, 런타임은 `$PRIVATE_DIR/$CASE_ID`를 사용한다. `LEGAL_ORCHESTRATOR_PRIVATE_DIR`가 설정되면 agent 출력과 orchestrator 탐색 경로가 어긋난다.

중요성:
meta/result 파일을 못 찾으면 fallback 요약으로 진행되어 품질과 감사성이 급락한다.

수정안:
1. `CLAUDE.md` Step 1에 다음 변수를 명시한다:
   ```bash
   OUTPUT_DIR="$PRIVATE_DIR/$CASE_ID"
   mkdir -p "$OUTPUT_DIR"
   ```
2. 모든 prompt template에서 출력 경로를 `{OUTPUT_DIR}/...`로 통일한다.
3. 하위 agent prompt에는 `PROJECT_ROOT`, `PRIVATE_DIR`, `OUTPUT_DIR`, `CASE_ID`를 모두 전달한다.
4. 문서의 `output/{CASE_ID}` 표기는 사용자 안내용 예시로만 남기고, 실제 작업 계약에서는 제거한다.
5. 기존 `output` 또는 `samples`가 private 디렉토리로 향하는 symlink인 환경을 하위 호환한다.
   - `scripts/generate-case-report.py`의 bare `CASE_ID`, `output/CASE_ID`, `samples/CASE_ID` resolution 테스트를 유지한다.
   - 새 `OUTPUT_DIR` 계약은 agent write path만 통일하고, 과거 case replay 입력 형식은 깨지 않도록 한다.

대상 파일:
- `CLAUDE.md`
- `skills/route-case.md`
- `skills/manage-debate.md`
- `skills/deliver-output.md`
- `README.md`
- `README.ko.md`

검증:
- `rg -n "PROJECT_ROOT}/output|output/\\{CASE_ID\\}" CLAUDE.md skills`
- 실제 작업 계약에 남은 `{PROJECT_ROOT}/output/{CASE_ID}`가 없어야 한다.
- `python3 scripts/generate-case-report.py output/<fixture-case-id>`와 `python3 scripts/generate-case-report.py samples/<fixture-case-id>` resolution 테스트가 통과해야 한다.

### 1.2 canonical style guide를 tracked 파일로 복구

문제:
`legal-writing-formatting-guide.md`는 runtime prompt에서 필수 파일로 주입되지만, `.gitignore`가 `docs/**/*`를 전부 무시한다.

중요성:
fresh clone에서는 한국어 의견서 품질을 결정하는 정본 파일이 누락된다.

수정안:
선택지 A를 기본안으로 채택한다.

선택지 A:
- `.gitignore`에 예외 추가:
  ```gitignore
  !docs/
  !legal-writing-formatting-guide.md
  ```
- 해당 파일을 git tracked 상태로 추가한다.

선택지 B:
- 파일을 루트 `legal-writing-formatting-guide.md`로 이동한다.
- prompt template의 경로도 루트 파일로 바꾼다.

권장:
선택지 A. README의 프로젝트 구조와 기존 prompt가 이미 `docs/`를 가리킨다.

검증:
- `git check-ignore -v legal-writing-formatting-guide.md`가 아무것도 출력하지 않아야 한다.
- `git ls-files legal-writing-formatting-guide.md`에 파일이 나타나야 한다.
- 루트 `legal-writing-formatting-guide.md`의 역할도 결정한다.
  - prompt에서 직접 참조하지 않는 참고 문서라면 README의 Project Structure에 명시하거나 제거한다.
  - canonical guide와 중복이면 canonical guide로 병합한 뒤 루트 파일은 삭제한다.
  - 계속 유지한다면 tracked 상태인지 확인한다: `git ls-files legal-writing-formatting-guide.md`.

### 1.3 잘못 남은 generic skill routing 제거

문제:
`CLAUDE.md` 말미에 이 프로젝트와 무관한 `office-hours`, `investigate`, `ship`, `qa` 등 generic skill routing 규칙이 남아 있다.

중요성:
법률 라우팅과 무관한 지시가 모델의 첫 행동을 오염시킬 수 있다.

수정안:
- `CLAUDE.md`의 `## Skill routing` 블록 전체를 삭제한다.
- 필요한 경우 아래 한 문장만 남긴다:
  - “이 레포의 오케스트레이션 스킬은 `skills/route-case.md`, `skills/manage-debate.md`, `skills/deliver-output.md`, `skills/generate-case-report.md`로 한정한다.”

검증:
- `rg -n "office-hours|investigate|ship|design-review|plan-eng-review" CLAUDE.md`가 결과를 내지 않아야 한다.

## Phase 2: 이벤트와 메타데이터를 코드로 강제

### 2.1 JSON event writer 추가

문제:
현재 이벤트는 shell string interpolation으로 생성한다. 사용자 질의에 따옴표, 개행, 역슬래시가 있으면 `events.jsonl`이 깨질 수 있다.

중요성:
감사 추적의 원장이 손상되면 `case-report`, source audit, replay가 모두 불안정해진다.

수정안:
1. `scripts/log-event.py` 추가
2. 입력 방식:
   ```bash
   python3 scripts/log-event.py "$OUTPUT_DIR/events.jsonl" \
     --agent orchestrator \
     --type case_received \
     --data-json '{"query": "...", "case_id": "..."}'
   ```
3. `--id auto` 기본값으로 다음 `evt_NNN`을 자동 부여한다.
4. `evt_final`은 `--final` 옵션으로만 허용한다.
5. JSON invalid 시 non-zero exit.
6. `evt_NNN` 자동 부여는 파일 락 안에서 수행한다.
   - macOS/Linux 기준 `fcntl.flock`으로 `$OUTPUT_DIR/events.jsonl.lock`을 잠근다.
   - lock 획득 후 기존 이벤트를 읽어 다음 번호를 계산하고 append까지 같은 critical section에서 수행한다.
   - lock 실패 또는 timeout 시 non-zero exit로 실패한다.
7. 병렬 dispatch 중 이벤트 충돌을 피하기 위해 하위 agent가 직접 `events.jsonl`에 쓰지 않는 원칙을 유지한다. 모든 이벤트 기록은 오케스트레이터 또는 deterministic script가 `log-event.py`를 통해 수행한다.

대상 파일:
- `scripts/log-event.py`
- `tests/test_log_event.py`
- `CLAUDE.md`
- `skills/*.md`

검증:
- 따옴표와 개행이 포함된 query를 기록해도 `parse_jsonl()`이 1개 이벤트로 읽어야 한다.
- multiprocessing 테스트로 20개 이벤트를 동시에 기록해도 `evt_001`부터 `evt_020`까지 중복/누락 없이 생성되어야 한다.

### 2.2 events/meta JSON Schema 추가

문제:
이벤트 스키마와 meta schema가 문서에만 있고 검증되지 않는다.

중요성:
하위 agent가 `comments`를 문자열 배열로 내거나 `source_graded`에서 `citation`을 누락해도 최종 리포트까지 통과한다.

수정안:
1. `schemas/events.schema.json` 추가
2. `schemas/agent-meta.schema.json` 추가
3. `schemas/review-meta.schema.json` 추가
4. `scripts/validate-case.py CASE_DIR` 추가
   - `--mode warn|strict` 옵션을 둔다.
   - 초기 rollout에서는 `warn`을 기본으로 두고, fixture와 prompt 정리가 끝난 뒤 `strict`를 deliver gate로 승격한다.
   - `strict`에서는 schema violation이 non-zero exit를 반환한다.
   - `warn`에서는 JSON 리포트와 stderr warning을 남기되 파이프라인을 중단하지 않는다.
5. `deliver-output.md` Step 1 직후 validation 실행:
   ```bash
   python3 "$PROJECT_ROOT/scripts/validate-case.py" "$OUTPUT_DIR" --mode warn
   ```

필수 schema 규칙:
- 모든 event: `id`, `ts`, `agent`, `type`, `data`
- `source_graded.data`: `agent_id`, `source`, `grade`, `citation`
- meta: `summary`, `key_findings`, `sources`, `error`
- review meta: `approval`, `comments[]`
- `comments[]`: `{severity, location, issue, recommendation, status?}`

검증:
- fixture에 `citation` 없는 `source_graded`를 넣으면 validation 실패해야 한다.
- `--mode warn`은 exit 0 + warning, `--mode strict`는 non-zero exit를 반환해야 한다.

### 2.3 `source_graded` 이벤트 payload 수정

문제:
현재 `CLAUDE.md` 예시는 `citation` 대신 `relevance`를 기록한다.

수정안:
- 모든 예시를 다음 형태로 교체:
  ```json
  {
    "agent_id": "AGENT_ID",
    "source": "SOURCE_TITLE",
    "grade": "A",
    "citation": "ARTICLE_OR_PINPOINT",
    "relevance": "optional short note"
  }
  ```

대상 파일:
- `CLAUDE.md`
- `skills/route-case.md`
- `skills/manage-debate.md`

검증:
- `rg -n '"relevance":"RELEVANCE"' CLAUDE.md skills`가 없어야 한다.

### 2.4 meta summary payload 축소

문제:
각 agent summary가 2000 tokens까지 허용되어 병렬 3-agent 케이스에서 writing prompt가 비대해진다. 이 문제는 단순 비용 문제가 아니라 rate-limit와 context 압박으로 이어지므로 schema 도입 직후 앞당겨 처리한다.

수정안:
meta schema를 다음 구조로 변경한다:
```json
{
  "summary": "500 tokens 이내",
  "issue_map": [
    {
      "issue": "...",
      "answer": "...",
      "authority_ids": ["src_001"],
      "confidence": "high|medium|low"
    }
  ],
  "key_findings": ["최대 8개"],
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
```

프롬프트 수정:
- “summary + key_findings만으로 90% 작성” 대신 “`issue_map`을 기본 근거 구조로 사용하고, 직접 인용이 필요한 경우에만 result.md를 Read”라고 지시한다.
- 기존 하위 agent가 즉시 새 schema를 완벽히 따르지 못할 수 있으므로 `validate-case.py --mode warn`에서는 legacy shape를 허용하되 migration warning을 낸다.

검증:
- meta fixture가 500 token을 크게 넘는 경우 validation warning 또는 strict failure를 내도록 한다.
- Pattern 1 3-agent fixture의 writing prompt 예상 payload가 기존 대비 줄어드는지 snapshot으로 확인한다.

## Phase 3: 결정적 산출물 조립

### 3.1 `merge-sources.py` 추가

문제:
`deliver-output.md`는 `sources.json` 생성을 모델/사람에게 수동으로 맡긴다.

중요성:
인용 소스 병합은 감사 산출물의 핵심인데 재현성이 없다.

수정안:
1. `scripts/merge-sources.py CASE_DIR` 추가
2. 입력:
   - 모든 `*-meta.json`
   - `events.jsonl`의 `source_graded`
3. 출력:
   - `sources.json`
   - 중복 제거 기준: normalized `(title, citation)`
   - `agents[]`와 `grade_distribution` 자동 계산
4. `deliver-output.md` Step 2를 스크립트 호출로 교체한다.

검증:
- pattern1 fixture에서 PIPA/GDPR/general 소스가 모두 병합되어야 한다.

### 3.2 `generate-case-report.py` meta discovery 개선

문제:
현재 생성기는 `research-meta.json`, `writing-meta.json`, `review-meta.json`만 고정으로 읽는다. 실제 계약인 `{agent-id}-meta.json`을 놓친다.

수정안:
1. `load_meta_bundle()`를 glob 기반으로 변경:
   - `*-meta.json` 전체 로드
   - `writing-meta.json`, `review-meta.json`은 특수 별칭 유지
2. 파일명에서 agent id 추출:
   - `PIPA-expert-meta.json` -> `PIPA-expert`
   - `general-legal-research-meta.json` -> `general-legal-research`
   - 대소문자를 보존한다. `pipa-expert`로 소문자 normalize하지 않는다.
3. `research-meta.json` legacy alias는 계속 지원하되 우선순위는 현재 계약에 둔다.

대상 파일:
- `scripts/generate-case-report.py`
- `tests/test_generate_case_report.py`

검증:
- pattern1 fixture에서 참여 agent별 핵심 발견이 `## 참여 에이전트`에 나타나야 한다.
- `sources.json`이 없어도 모든 `*-meta.json` source가 `## 인용 소스`에 나타나야 한다.
- Linux case-sensitive filesystem에서 `PIPA-expert-meta.json`과 `pipa-expert-meta.json`을 혼동하지 않는지 테스트한다.

### 3.3 `revision_needed` 흐름을 finalization 전에 강제

문제:
현재 `deliver-output.md`는 `final_output` 기록 후 revision cycle을 언급한다.

중요성:
미승인 문서가 최종본으로 확정될 수 있다.

수정안:
1. `deliver-output.md` 순서 변경:
   - 결과 확인
   - review approval 확인
   - 필요 시 revision cycle
   - validation
   - sources merge
   - injection scan
   - DOCX/case-report 생성
   - `final_output` 기록
2. `review-meta.json.approval` 값이 다음이면:
   - `approved`: 진행
   - `approved_with_revisions`: revision 적용 여부 확인 후 진행
   - `revision_needed`: 최대 2회 수정, 실패 시 `final_output` 대신 `pipeline_aborted` 또는 `final_output.status = "not_approved"` 명시

검증:
- review fixture가 `revision_needed`이면 `final_output`이 생성되지 않거나 `not_approved`로 기록되어야 한다.

## Phase 4: Prompt 정규화와 라우팅 안정화

### 4.1 routing schema를 배열 기반으로 정규화

문제:
`domain`과 `task`는 scalar처럼 정의됐지만 예시는 `contract+translation`, `game_regulation+data_protection`처럼 복수값을 쓴다.

중요성:
모델이 임의 문자열을 만들면 routing tree가 조건을 잘못 평가한다.

수정안:
분류 결과를 다음 schema로 바꾼다:
```json
{
  "jurisdictions": ["KR", "EU"],
  "domains": ["game_regulation", "data_protection"],
  "tasks": ["research", "drafting"],
  "complexity": "multi_domain",
  "confidence": 0.0,
  "ambiguity": []
}
```

라우팅 조건도 다음처럼 변경:
- `if "translation" in tasks`
- `if "contract" in domains and "drafting" in tasks`
- `if len(domains) > 1 or len(jurisdictions) > 1`

검증:
- 기존 few-shot 16개를 classification fixture로 만들고 expected pipeline을 테스트한다.

### 4.2 contract drafting unreachable branch 수정

문제:
`domain == contract` 분기가 `task == drafting && domain == contract`보다 먼저 있어 NDA 초안 요청이 contract review로 갈 수 있다.

수정안:
- contract drafting branch를 contract review branch보다 위로 이동한다.
- 또는 배열 schema 도입 후:
  ```text
  if "contract" in domains and "drafting" in tasks
      -> contract-review-agent(WF5 drafting mode) -> second-review
  elif "contract_review" in tasks or "contract" in domains
      -> contract-review-agent -> second-review
  ```

검증:
- “NDA 초안 작성해줘” fixture가 WF5 drafting mode로 분류되어야 한다.

### 4.3 review comments schema를 prompt와 code에 동시에 고정

문제:
review prompt는 `comments: [...]`만 제시하지만 report generator는 dict comment를 기대한다.

수정안:
review prompt의 meta 계약을 다음처럼 구체화:
```json
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
```

검증:
- `comments`가 문자열 배열이면 `validate-case.py`가 실패해야 한다.

### 4.4 오케스트레이터 직접 검증 예외 범위 명시

문제:
`CLAUDE.md`는 직접 법률 리서치를 금지하지만 `manage-debate.md`는 rate-limit 시 직접 MCP 검증을 지시한다.

수정안:
`CLAUDE.md` 제약사항을 다음처럼 수정:
- 금지: 새로운 법률 분석, 결론 도출, 문서 작성
- 허용: 이미 산출된 claim/citation의 존재 여부, 조문 원문, 핀포인트 일치 여부 확인
- 허용 산출물: `verbatim-verification.md`, `mcp_fallback_verification` 이벤트

검증:
- prompt 내 “직접 MCP” 문구가 모두 “citation/verbatim verification only” 문맥을 갖도록 수정한다.

## Phase 5: Token 효율 후속 개선

### 5.1 prompt template 분리

문제:
`route-case.md` 하나가 라우팅, 템플릿, schema, 토큰 예산을 모두 포함한다.

수정안:
다음 파일 구조로 분리한다:
```text
skills/
  route-case.md
  prompt-templates/
    common-blocks.md
    general-legal-research.md
    pipa-expert.md
    gdpr-expert.md
    game-legal-research.md
    contract-review-agent.md
    legal-translation-agent.md
    legal-writing-agent.md
    second-review-agent.md
schemas/
  routing.schema.json
  events.schema.json
  agent-meta.schema.json
```

검증:
- `route-case.md`는 라우팅 판단만 담당하고 250줄 이하를 목표로 한다.

### 5.2 Pattern 3 transcript deterministic concat

문제:
`debate-transcript.md` 생성을 위해 writing agent가 모든 라운드 result를 읽고 verbatim 복사한다.

수정안:
1. `scripts/build-debate-transcript.py CASE_DIR` 추가
2. 입력:
   - `debate-round-*-*-result.md`
   - `debate-round-*-*-meta.json`
3. 동작:
   - 각 result를 sanitize scan
   - 정해진 heading 아래 그대로 concat
   - `debate-transcript.md` 생성
4. writing agent는 `debate-opinion.md`만 작성한다.

검증:
- transcript 생성에 LLM 호출이 필요 없어야 한다.
- 파일 순서가 round, agent 순으로 안정적이어야 한다.

### 5.3 Pattern 3 round 진행 판단 자동화 범위 결정

문제:
`debate_round3_decision`은 현재 `conceded_points` 비율을 이용한다고 되어 있지만, 그 판단을 모델이 하는지 deterministic script가 하는지 불명확하다.

중요성:
Round 3 진행 여부는 비용과 산출물 구조를 바꾼다. 같은 meta로 재실행했을 때 판단이 달라지면 replay와 비용 예측이 흔들린다.

수정안:
1. `scripts/decide-debate-round3.py CASE_DIR` 추가 여부를 결정한다.
2. 기본안:
   - `debate-round-2-*-meta.json`의 `conceded_points`와 상대 `key_claims` 개수를 읽는다.
   - 기존 문서의 `conceded_ratio >= 0.5` 규칙을 그대로 적용한다.
   - 결과 JSON을 stdout으로 출력하고 `log-event.py`로 `debate_round3_decision`을 기록한다.
3. 예외:
   - meta 누락 또는 malformed면 deterministic 판단을 보류하고 `debate_round3_decision.data.reason = "insufficient_meta"`로 기록한 뒤 Round 3 진행을 기본값으로 둔다.
4. LLM은 contested claim 요약을 보조할 수 있지만, `proceed` boolean은 script 결과를 우선한다.

검증:
- 같은 Round 1/2 meta fixture를 두 번 실행하면 동일한 `proceed` 값이 나와야 한다.
- malformed meta fixture에서는 `insufficient_meta`가 기록되고 Round 3 진행으로 fallback해야 한다.

## Phase 6: Safety hardening

### 6.1 `sanitize-check.py --fail-on-unescaped` 추가

문제:
최종 injection scan은 match가 `<escape>` 내부인지 외부인지 코드로 판정하지 않는다.

수정안:
1. sanitizer audit match에 `escaped: true|false`를 추가한다.
2. `--fail-on-unescaped` 옵션을 추가한다.
3. unescaped match가 있으면 exit code 3.
4. `deliver-output.md`에서 이 옵션을 사용한다.

검증:
- `<escape>[SYSTEM]</escape>`은 통과
- `[SYSTEM]`은 exit 3

### 6.2 DOCX 렌더 시 escape 내부 원문 처리 정책 변경

문제:
`md-to-docx.py`는 `<escape>` 태그만 제거하고 내부 prompt-injection 문구를 그대로 DOCX에 남긴다.

수정안:
정책을 두 모드로 나눈다:
- 기본: escape 내부 텍스트를 `[Sanitized instruction-like text omitted]`로 치환
- 감사용: `--preserve-escaped-text` 옵션을 명시한 경우에만 원문 보존

대상 파일:
- `scripts/md-to-docx.py`
- `tests/test_md_to_docx_escape_policy.py`

검증:
- 기본 변환 결과 DOCX text에 `[SYSTEM]`이 없어야 한다.

## Phase 7: 재현성과 dependency pinning

### 7.1 `agents.lock` 도입

문제:
`setup.sh update`는 각 agent 최신 commit을 가져온다.

중요성:
동일 케이스 재실행 결과가 agent 업데이트에 따라 달라진다.

수정안:
1. `agents.lock` 추가:
   ```json
   {
     "general-legal-research": {"repo": "...", "commit": "..."},
     "legal-writing-agent": {"repo": "...", "commit": "..."}
   }
   ```
2. `setup.sh setup`은 lock commit checkout
3. `setup.sh update-lock`은 최신 commit으로 lock 갱신
4. `setup.sh status`는 lock 대비 dirty/ahead/behind 표시

검증:
- fresh clone 후 `./setup.sh`가 lock commit을 checkout해야 한다.

### 7.2 MCP package version pinning

문제:
`.mcp.json`이 `korean-law-mcp@latest`, `kordoc`를 사용한다.

수정안:
- 동작 확인된 version으로 pinning:
  ```json
  "args": ["-y", "korean-law-mcp@x.y.z"]
  ```
- 버전 업그레이드는 별도 changelog로 관리한다.
- 보안/호환성 패치 누락을 막기 위해 dependency monitoring을 둔다.
  - GitHub Actions cron 또는 Renovate 설정으로 `korean-law-mcp`, `kordoc` 최신 버전을 주기적으로 확인한다.
  - 새 버전 감지 시 자동 PR 또는 issue를 생성하고 smoke test 결과를 첨부한다.
  - pin bump는 `MCP_VERSION_CHANGELOG.md`에 이유와 smoke 결과를 남긴다.

검증:
- `.mcp.json`에 `@latest`가 없어야 한다.
- dependency monitoring workflow 또는 Renovate config가 존재해야 한다.

## 작업 순서 제안

1. Phase 0.1 fixture 정책과 합성 fixture 추가
2. Phase 1.3 generic routing 제거
3. Phase 1.2 style guide tracking 복구 및 `legal-writing-formatting-guide.md` 역할 결정
4. Phase 1.1 `OUTPUT_DIR` 계약 통일 및 symlink 하위 호환 테스트
5. Phase 2.1 `log-event.py` 구현 (`flock` 기반 race 방지 포함)
6. Phase 2.2 schema + `validate-case.py --mode warn|strict`
7. Phase 2.3 `source_graded` payload 정리
8. Phase 2.4 token payload 축소
9. Phase 3.1 `merge-sources.py`
10. Phase 3.2 `case-report` meta discovery
11. Phase 3.3 revision/finalization 순서 정리
12. Phase 4 routing schema 정규화
13. Phase 5.1 prompt template 분리
14. Phase 6 sanitizer/DOCX hardening
15. Phase 7 lockfile/pinning 및 MCP monitoring
16. Phase 5.2 Pattern 3 transcript deterministic concat
17. Phase 5.3 Pattern 3 round 진행 판단 자동화

## 완료 기준

이 기획의 핵심 완료 조건은 다음이다.

1. fresh clone에서 style guide 경로가 실제로 존재한다.
2. `LEGAL_ORCHESTRATOR_PRIVATE_DIR` 설정 여부와 무관하게 모든 agent 출력이 같은 case dir에 모인다.
3. 모든 이벤트는 JSON writer를 통해 기록된다.
4. `validate-case.py`가 이벤트와 meta schema를 검증한다.
   - event 공통 필드: `id`, `ts`, `agent`, `type`, `data`
   - `source_graded`: `agent_id`, `source`, `grade`, `citation`
   - agent meta: `summary`, `key_findings`, `sources`, `error`
   - review meta: `approval`, `comments[].severity/location/issue/recommendation`
   - `--mode warn|strict`가 모두 테스트된다.
5. `sources.json`은 deterministic script로 생성된다.
6. `case-report.md`는 모든 `*-meta.json`을 반영한다.
7. review 미승인 상태에서는 최종 승인 산출물처럼 기록되지 않는다.
8. Pattern 3 transcript는 LLM copy가 아니라 deterministic concat으로 생성된다.
9. Pattern 3 Round 3 진행 여부는 동일 meta에 대해 재현 가능하게 결정된다.
10. 최종 DOCX에는 unescaped prompt-injection marker가 남지 않는다.
11. agent와 MCP dependency version이 lock 또는 pin으로 재현 가능하다.
12. MCP pinning에는 업데이트 알림 또는 자동 PR 경로가 있다.
