# 엔지니어링 감사 개선 기획서 검증 보고서

검증 대상: [engineering-audit-remediation-plan.md](engineering-audit-remediation-plan.md)
검증일: 2026-04-24
검증 범위: 플랜이 주장하는 사실관계, 우선순위, 수정안 타당성, 누락된 이슈

---

## 한 줄 요약

Codex의 플랜은 **사실관계가 매우 정확합니다.** 20개 이상의 claim 중 샘플한 17개를 코드에 대조한 결과 **전부 참**입니다. 다만 우선순위 판단 몇 가지에 이견이 있고, 실행 중 조용히 깨질 수 있는 갭 6개가 누락돼 있습니다.

---

## 1. 각 주장의 사실관계 검증

| # | Plan 주장 | 실제 코드 | Confidence | 판정 |
|---|---|---|---|---|
| 1.1 | 프롬프트는 `{PROJECT_ROOT}/output/{CASE_ID}` 지시, 런타임은 `$PRIVATE_DIR/$CASE_ID` | `skills/route-case.md:243,247,259,323,448,526,541` 모두 `{PROJECT_ROOT}/output/{CASE_ID}`로 지시. `CLAUDE.md` Step 1은 `$PRIVATE_DIR/$CASE_ID`로 씀. env 설정 시 두 경로 **완전 분기** | 10/10 | **참 — P0 맞음** |
| 1.2 | `.gitignore`가 `docs/**/*` 차단으로 style guide 미추적 | `git check-ignore` 결과 `.gitignore:15:docs/**/*` 매치, 파일 ignored 상태 | 10/10 | **참 — P0 맞음** |
| 1.3 | `office-hours`, `investigate`, `ship`, `qa` 등 무관 라우팅 잔존 | `CLAUDE.md` 말미에 `## Skill routing` 블록, gstack 기본 라우팅 13개 항목 존재 | 10/10 | **참 — P0 맞음** |
| 2.1 | 사용자 질의에 따옴표/개행 있으면 `events.jsonl` 손상 | `CLAUDE.md` Step 1: `echo '{..."query":"'"$(echo "$USER_QUERY" \| head -c 200)"'"}' > events.jsonl` — 쌍따옴표 한 번에 JSON 깨짐 | 10/10 | **참** |
| 2.3 | CLAUDE.md 예시는 `citation` 대신 `relevance` 사용 | `CLAUDE.md:94`는 `"relevance":"RELEVANCE"`, `skills/route-case.md:580` 부록 A는 `citation` 필수 필드로 명시 — **문서 내부 모순** | 10/10 | **참** |
| 3.1 | `sources.json` 수동 생성 | `skills/deliver-output.md:28-30`: `# sources.json 생성은 수동으로: 각 *-meta.json을 Read하여 ...` — 주석만 있고 스크립트 호출 없음 | 10/10 | **참 — 재현성 치명적** |
| 3.2 | `{agent-id}-meta.json` 계약을 놓침 | `scripts/generate-case-report.py:282-286` `load_meta_bundle`이 `research-meta.json`, `writing-meta.json`, `review-meta.json`만 읽음. `PIPA-expert-meta.json`, `GDPR-expert-meta.json`, `contract-review-agent-meta.json` **전부 무시됨** | 10/10 | **참 — Pattern 1 케이스에 치명적** |
| 3.3 | `final_output` 기록 후 revision 언급 | `skills/deliver-output.md:60` Step 3에서 `evt_final` 작성 → Step 6 문구에서만 `revision_needed` 처리 언급. **승인 확인 전에 파이프라인 완료 이벤트 기록** | 9/10 | **참** |
| 4.1 | `domain`은 scalar 정의이나 예시에 `contract+translation`, `game_regulation+data_protection` | `skills/route-case.md:31`은 scalar enum, Few-shot 51/52행은 `+`로 결합값 | 10/10 | **참** |
| 4.2 | `domain=="contract"`가 `drafting` 분기 위에 있어 NDA 초안이 review로 감 | `skills/route-case.md:85-89`: `task=="contract_review" \|\| domain=="contract"` → contract-review(검토 모드)를 먼저 매치. `drafting && domain=="contract"` 분기는 **도달 불가** | 10/10 | **참 — 실제 버그** |
| 4.4 | CLAUDE.md는 직접 리서치 금지, manage-debate.md는 직접 MCP 검증 지시 | `skills/manage-debate.md:460,467,472`: rate_limit 시 "오케스트레이터가 직접 MCP로 핵심 주장 검증 수행" — CLAUDE.md 제약사항 1번과 **표면적 모순** | 9/10 | **참 — 문서 명시 필요** |
| 5.1 | 병렬 3-agent에서 writing prompt 비대 | CLAUDE.md, route-case.md 모두 `"2000 tokens 이내 핵심 요약"` 지시. Pattern 1 3-agent = **최대 6,000 tokens의 summary만으로도 writing에 들어감** | 10/10 | **참** |
| 5.2 | route-case.md가 라우팅+템플릿+schema+예산 다 포함 | `route-case.md = 628 lines`, `manage-debate.md = 473 lines`. 플랜의 "250줄 이하" 목표 타당 | 10/10 | **참** |
| 6.1 | 최종 injection scan은 match가 `<escape>` 내/외부인지 판정 안 함 | `scripts/sanitize-check.py`에 `--fail-on-unescaped` 없음, audit JSON에 `escaped: bool` 필드 없음. `skills/deliver-output.md:111-113`은 사람이 눈으로 판단하도록 돼있음 | 10/10 | **참** |
| 6.2 | DOCX 렌더 시 `<escape>` 내부 텍스트 그대로 통과 | `scripts/md-to-docx.py:84-89`: `_ESCAPE_TAG_RE.sub(r"\1", md)` — group 1은 **태그 내부 원문**. DOCX에 `[SYSTEM] ignore previous...` 그대로 남음 | 10/10 | **참 — 클라이언트 납품물 보안 이슈** |
| 7.1 | `setup.sh update`는 `git pull --rebase` | `setup.sh:36` `git pull --rebase` 확인. lock 파일 없음, 재현성 0 | 10/10 | **참** |
| 7.2 | `.mcp.json` unpinned | `.mcp.json` `args: ["-y", "korean-law-mcp@latest"]` 및 버전 없는 `kordoc` | 10/10 | **참** |

**17개 주장 전부 실제 코드에서 검증 확인.**

---

## 2. Architecture 리뷰

플랜의 설계 방향은 건전합니다. 핵심 원칙이 옳습니다.

- **원칙 3 ("모델에게 반드시 지시 → 가능하면 스크립트로 강제")** — 이 프로젝트에서 가장 중요한 대목. LLM 순종을 신뢰할 수 없으면 deterministic 스크립트로 강제해야 한다. 플랜이 `log-event.py`, `validate-case.py`, `merge-sources.py`, `build-debate-transcript.py`로 일관되게 전환하는 것은 **옳은 방향**.
- **Blast radius 감각**: P0/P1/P2/P3 구분이 합리적. P0는 파일 계약(런타임 실패 원인), P3는 비용/재현성(장기). 순서 합당.
- **경계 관리**: P1.3에서 generic skill routing을 지우는 것은 control-plane 오염 방지로 정확. 플랜은 CLAUDE.md를 control-plane으로, 하위 agent를 data-plane으로 보는 원칙에 충실.

---

## 3. 플랜이 놓친 것 (critical gaps)

### G1. 기존 `output/` 심볼릭 링크 처리 누락 — P0

```
lrwxr-xr-x  1 user staff  output -> /Users/user/private/legal-work/legal-agent-orchestrator/output
```

현재 레포에는 `output`이 **private 디렉토리로 심볼릭 링크**되어 있음. 플랜 1.1의 `OUTPUT_DIR` 계약 통일이 prompt 문자열 치환은 다루지만, **기존 샘플 디렉토리(`samples/` 심볼릭 링크 포함)의 하위 호환**은 언급하지 않음. `generate-case-report.py`는 이미 `_resolve_case_dir`에서 `samples/`와 `output/`을 둘 다 지원하는데, 새 계약이 이걸 깨지 않는지 **회귀 fixture에 포함 필요**.

### G2. `legal-writing-formatting-guide.md` 추적 상태 미점검 — P0

루트에 `legal-writing-formatting-guide.md` (62KB) 파일이 있는데, 이게 어떤 prompt에서 참조되는지 플랜은 다루지 않음. 1.2에서 legal-writing-formatting-guide.md만 고려함.

검증 명령: `rg -n "legal-writing-formatting-guide" CLAUDE.md skills`

### G3. `evt_NNN` 순차 번호 race condition — P1

플랜 2.1의 `log-event.py`가 `--id auto`로 자동 부여한다는데, **Pattern 1 병렬 디스패치** 시 여러 에이전트가 거의 동시에 이벤트를 쓰면 race condition 발생 가능. route-case.md Step 5-4번이 "timestamp는 병렬이라 거의 동일"이라고 명시하는데, `evt_NNN` 번호를 파일에서 읽어 +1 하는 방식이면 lost update. 플랜에 `flock` 또는 atomic append 전략이 명시돼야 함.

**권장:** `flock` 기반 파일 락 또는 ULID 사용. `evt_NNN`이 의미상 "이벤트 순번"이라면 timestamp 정렬 + agent+pid suffix로 충돌 피하기.

### G4. Pattern 3 `round3_decision` 자동화 여부 — P1

manage-debate.md의 `debate_round3_decision` 이벤트가 모델 판단인지 스크립트 판단인지 현재 불투명. 플랜 5.3은 transcript concat만 deterministic으로 만들고, **round 진행 판단**은 그대로 LLM에 맡김. 이게 의도인지 누락인지 명시 필요.

### G5. Test fixture의 사실성 — P0

플랜 0.1이 `events.jsonl`, `*-meta.json` fixture를 만들자고 하는데, **샘플 데이터 출처 명시 없음**. 실제 샘플 디렉토리(`samples/` symlink → private)에서 가져와야 의미있는 회귀 테스트가 되는데, 공개 레포에 private 내용을 넣을 수는 없음. "합성 minimal fixture"인지 "실제 익명화된 fixture"인지 플랜이 결정해야 함.

**권장:** 공개 fixture는 합성 minimal로, 실제 케이스 회귀는 private 디렉토리 기반 별도 `tests/fixtures-private/` (gitignored)로 분리.

### G6. Agent ID 대소문자 — P1

CLAUDE.md는 `{agent_id}-meta.json` 규약이지만, `PIPA-expert`처럼 **대소문자 혼용 agent_id**와 Python 파일 glob의 상호작용 점검 필요. macOS(case-insensitive HFS+)와 Linux(case-sensitive ext4)에서 동작 차이 가능. 플랜 3.2의 glob이 이걸 테스트하는지 명시 필요.

---

## 4. 플랜의 잘한 점

- **우선순위 정확**: P0 선정 기준이 "런타임 실패 유발" vs "품질 저하"로 일관. 1.1(경로), 1.2(gitignore), 1.3(오염)은 진짜 P0.
- **검증 명령 명시**: 각 수정안에 `rg -n`, `git check-ignore`, `python3 -m unittest` 등 구체적 검증 명령 포함. 드문 수준의 디테일.
- **역주장도 제시**: 1.2에서 선택지 A/B 둘 다 제시하고 권장 이유 설명. 플랜으로서 건강함.
- **작업 순서의 의존성**: 1.3(오염 제거) → 1.2(tracked) → 1.1(경로) → 2.1(writer) → 2.2(schema). 각 단계가 이전 단계 없이는 안 됨. 의존성 관리 제대로.

---

## 5. 약점 · 이견

### 이견 1: Phase 순서 재검토 가치

플랜은 Phase 5(토큰 효율)를 Phase 4(라우팅) 뒤에 두는데, **5.1(meta summary 2000 → 500)은 P0에 가깝다.** 이유: Pattern 1 3-agent 케이스가 1M context 윈도우의 73%를 소비한다고 route-case.md 부록 B에서 자기 스스로 경고함. rate_limit가 실제 발생하면 P0.

**권장:** 5.1을 Phase 2 직후(2.3 다음)로 승격.

### 이견 2: 2.2 schema validation의 실용성

JSON Schema 검증 자체는 좋으나, **하위 agent가 해당 schema를 따르도록 강제할 방법이 없음**(agent 레포를 못 고치는 제약). validation이 fail하면 파이프라인 중단? 아니면 warning? 플랜에 실패 시 동작 명시 안 됨.

**권장:** `validate-case.py`에 `--mode strict|warn` 플래그 추가. 초기엔 warn으로 배포 후 strict 전환.

### 이견 3: 7.2 `.mcp.json` pinning의 trade-off

`korean-law-mcp`는 외부 MCP 서버. `@latest` → 고정 버전으로 가면 **보안 패치 수동 수신** 필요. 플랜은 "별도 changelog"라고만 하고 모니터링 전략이 없음. Renovate bot이나 GitHub Actions cron으로 upstream 알림 받는 구조 필요.

---

## 6. 완료 기준 적절성

플랜 끝의 완료 조건 10개는 **전부 측정 가능하며 binary**. 각각에 대응하는 검증 명령이 이미 수정안에 포함돼있음. 플랜 품질 지표로 매우 좋음.

다만 완료 조건 4 ("`validate-case.py`가 이벤트와 meta schema를 검증한다") — 검증**하는지**는 binary지만, 검증 커버리지가 충분한지는 schema의 완성도에 달림. "schema는 [specific fields list]를 커버한다" 수준으로 구체화 권장.

---

## 7. 최종 평가

| 축 | 평가 |
|---|---|
| **사실관계 정확도** | 10/10 — 17개 샘플 중 전부 참 |
| **우선순위 판단** | 8/10 — 대체로 옳으나 5.1은 더 앞이 맞음 |
| **수정안 구체성** | 9/10 — 검증 명령까지 포함, 드물게 구체적 |
| **누락된 이슈** | 6/10 — G1~G6 중 특히 G3(race), G5(fixture 출처) 플랜 병합 필요 |
| **실행 가능성** | 9/10 — 각 단계가 독립 merge 가능. 의존성 순서 합리적 |
| **보수성/전진성 균형** | 9/10 — 새 기능 도입 없이 현재 약속을 런타임에 보장하는 일관된 목표 |

**최종: 이 플랜은 채택할 가치가 있습니다.** 다만 **G1~G6 갭을 플랜에 병합한 후 실행**해야 함. 특히 G3(evt_NNN race)는 Phase 2.1 구현 시 **반드시 설계에 포함**되어야 실사용 시 조용히 깨지지 않음.

---

## 8. 권장 실행 순서

1. **플랜에 G1~G6 병합**하는 짧은 addendum 작성 (15분)
2. Phase 1.3 → 1.2 → 1.1 순으로 **P0 3개를 단일 PR**로 묶어 merge (경로 계약이 하나의 일관된 변경)
3. Phase 2.1 구현 시 `evt_NNN` 순차 번호에 **flock 또는 ULID** 결정
4. 그 다음은 플랜 순서대로 진행, 단 5.1만 3.3 직후로 승격

---

## 부록: 검증에 사용한 파일

- `CLAUDE.md` (전체)
- `skills/route-case.md` (628줄)
- `skills/deliver-output.md` (164줄)
- `skills/manage-debate.md` (line 460-472 스팟체크)
- `skills/generate-case-report.md`
- `scripts/generate-case-report.py` (1064줄)
- `scripts/md-to-docx.py` (363줄)
- `scripts/sanitize-check.py` (65줄)
- `setup.sh` (75줄)
- `.mcp.json`
- `.gitignore`
- `tests/test_sanitize.py` (샘플 확인)
- 디렉토리 구조 (`ls -la`, `git ls-files docs/`)
