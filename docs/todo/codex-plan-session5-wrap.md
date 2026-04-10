# Codex 작업 지시서 — 세션 5 wrap-up (A + B + C)

**작성일:** 2026-04-10
**대상 에이전트:** Codex CLI (또는 이 파일을 읽을 수 있는 모든 코딩 에이전트)
**실행 환경:** macOS, zsh, git
**작업 공간 루트:** `/Users/kpsfamily/코딩 프로젝트/legal-agent-orchestrator`
**소요 추정:** 기계적 작업 (약 15~20분). 모든 수정 위치가 이 문서에 명시되어 있음.

---

## 0. 이 문서를 읽는 방법

이 문서는 **self-contained**합니다. 이전 대화 맥락 없이도 바로 실행할 수 있도록 필요한 사실, 파일 경로, 정정 전/후 텍스트, 커밋 메시지가 모두 포함되어 있습니다.

- §1 **배경**을 먼저 읽어 맥락을 파악하세요.
- §2 **팩트 박스**는 정정할 때 기준이 되는 확정 사실입니다. 이 사실과 다른 내용이 파일에 있으면 파일이 틀린 것입니다.
- §3~§5는 Task **A / B / C** 각각의 실행 지시입니다. 순서대로 진행하세요.
- §6 **검증 체크리스트**는 커밋 직전에 반드시 통과해야 합니다.
- §7 **가드레일**은 절대 어기지 마세요. 특히 PIPA-expert 레포는 건드리지 마세요 — 해당 작업은 별도 세션에서 이미 완료되었습니다.

---

## 1. 배경

이 프로젝트는 **"법무법인 진주 오케스트레이터"**(Jinju Law Firm Orchestrator), Claude Code 위에서 돌아가는 멀티에이전트 법률 시스템입니다. 세션 5에서 포트폴리오 공개를 준비하며 `README.md`, `README.ko.md`, `LICENSE`, `CLAUDE.md` 4개 파일을 작성/수정했으나 **아직 커밋되지 않았습니다**.

세션 5 도중 두 가지 이슈가 발견되어 이 작업 지시서가 작성되었습니다:

1. **회사명 오기록** — 하위 레포 `PIPA-expert`의 git status에서 untracked로 발견된 클라이언트 문서를 orchestrator 쪽 기록물(`resume.md`, `docs/session-log-20260410-pt2.md`, memory 파일)에 적을 때, 파일명이 인코딩 깨진 상태였고 **"루킨엑스"**로 잘못 읽어 기록했습니다. 실제 회사명은 **"룰루랩"**입니다 (LuskinX는 같은 회사의 영문 브랜드명).

2. **PIPA-expert grade-b 보강 완료** — 세션 5 기록 당시 "대기 중"으로 적었던 PIPA-expert의 `library/grade-b/` 보강 작업이 별도 세션에서 실제로 완료되었고 원격까지 push됐습니다. 그리고 원안이 변경되었습니다 — 원래 계획은 PIPC 결정 20 + 판례 10이었으나, `get_pipc_decision_text` MCP endpoint 장애로 **법제처 법령해석례 20 + 판례 10**으로 대체되었습니다. 이 사실이 orchestrator 측 문서에 전혀 반영되어 있지 않습니다.

그리고 이 이슈들과 별개로, 세션 5 변경사항 **4개 파일이 아직 미커밋**입니다.

이 문서의 목적은 이 세 가지를 한꺼번에 정리하고 세션 5를 깔끔히 종료하는 것입니다.

---

## 2. 팩트 박스 (정정·반영의 기준)

**모든 수정 작업은 이 사실을 기준으로 합니다.** 만약 파일에 이와 다른 내용이 적혀 있으면 파일이 잘못된 것입니다.

### 2.1 회사명

| 틀린 표기 | 올바른 표기 |
|----------|------------|
| 루킨엑스 | **룰루랩** |

- LuskinX는 영문 브랜드, 룰루랩은 한국어 회사명, **같은 회사**입니다.
- 파일명 안에 들어있는 `LuskinX` 토큰은 그대로 두세요 (실제 파일명의 일부). 본문 서술에서 "루킨엑스"를 "룰루랩"으로 정정합니다.
- 참고용 파일명 (실제 PIPA-expert 로컬에 있었던 `.docx` 3개, 이미 `*.docx` gitignore로 차단됨):
  ```
  (환자용) [룰루랩] 개인정보 처리방침_LuskinX_260119_clean_룰루랩.docx
  (환자용) [룰루랩] 개인정보수집동의서_LuskinX_260119_clean_룰루랩.docx
  룰루랩_LuskinX_개인정보_AI학습_검토의견.docx
  ```

### 2.2 PIPA-expert grade-b 완료 상태

**레포:** `/Users/kpsfamily/코딩 프로젝트/PIPA-expert` (원격: `github.com/kipeum86/PIPA-expert.git`, public)
**이 Codex 세션에서 건드리지 마세요. 이미 다른 세션에서 commit + push 완료됨.**

실제 push된 커밋 (최신순):

```
e163dd7 chore(gitignore): block all .docx files (client confidentiality)
174c2af docs(readme): add Grade B section (30 landmark cases + interpretations)
6b8137c feat(grade-b): landmark 30건 초기 수집 (해석례 20 + 판례 10)
```

구체 사실:

- `library/grade-b/legal-interpretations/` 20건 추가 (법제처 법령해석례)
- `library/grade-b/court-precedents/` 10건 추가 (대법원 판례: 2013두2945, 2014다235080, 2015다24904, 2017다219232, 2018다262103, 2020도14713, 2022두68923, 2023다311184, 2024다210554, 2024도8121)
- `library/grade-b/pipc-decisions/` **0건 (pending)** — `get_pipc_decision_text` endpoint 장애로 해석례로 대체됨. endpoint 복구 시 재개 대상으로 `source-registry.json`에 사유 기록됨.
- 모든 파일 `verification_status: VERIFIED`, MCP 원문 verbatim 인용.
- 6 주제(동의·제3자제공·안전조치/유출·국외이전·가명정보·민감정보/고유식별) 전반 커버.

**의의:** 세션 5 당시 README가 "In Progress / Pending"에 올려뒀던 `library/grade-b/` 보강 작업이 **완료**되었습니다. 단, 원안(PIPC 결정)이 아닌 법제처 해석례로 구성되었다는 사실을 반영해야 합니다.

### 2.3 `.docx` 보안 조치

PIPA-expert 레포에는 별도 세션에서 `.gitignore`에 `*.docx` 전역 차단 패턴이 추가되어 commit + push 완료됨 (`e163dd7`). orchestrator 레포에는 이 조치가 **불필요**합니다 (orchestrator 레포는 자체 `.docx` 파일을 만들지 않음). orchestrator 쪽에서는 **문서 정정만** 하면 됩니다.

### 2.4 세션 5 미커밋 파일 (orchestrator 레포)

이 문서 작업 시작 시점 기준:

```
On branch main
Changes not staged for commit:
  modified:   CLAUDE.md
  modified:   resume.md
Untracked files:
  LICENSE
  README.ko.md
  README.md
  docs/session-log-20260410-pt2.md
```

Task A와 B의 결과로 `resume.md`, `docs/session-log-20260410-pt2.md`, `README.md`, `README.ko.md`가 추가로 수정될 것입니다. Task C에서 이 모두를 한 번에 commit합니다.

---

## 3. Task A — "루킨엑스" → "룰루랩" 정정

### 3.1 작업 범위

orchestrator 레포 내부의 기록물 3곳에서 "루킨엑스" 표기를 **모두** "룰루랩"으로 정정합니다. 아래는 `grep -rn` 결과로 확인된 **현재 출현 위치**입니다. 에디팅 도중 라인 번호가 미세하게 바뀔 수 있으므로, 라인 번호에 의존하기보다 문자열 매칭으로 수정하세요.

### 3.2 대상 파일 1 — `resume.md`

**절대경로:** `/Users/kpsfamily/코딩 프로젝트/legal-agent-orchestrator/resume.md`

#### 수정 #1 (line 4 근방, 세션 5 상태 라인)

**Before:**
```
**상태:** ✅ Phase 1 E2E 통과 + ✅ Phase 2 2.1/2.2 검증 완료 + ✅ 세션 5 포트폴리오 공개 준비 (README 영/한 + LICENSE Apache 2.0 + CLAUDE.md 8-에이전트 동기화). ⚠️ **세션 5 변경사항 모두 미커밋.** ⏸️ PIPA-expert grade-b 보강 + 루킨엑스 .docx 처리는 별도 세션.
```

**After:**
```
**상태:** ✅ Phase 1 E2E 통과 + ✅ Phase 2 2.1/2.2 검증 완료 + ✅ 세션 5 포트폴리오 공개 준비 (README 영/한 + LICENSE Apache 2.0 + CLAUDE.md 8-에이전트 동기화) + ✅ PIPA-expert grade-b 보강 완료 (해석례 20 + 판례 10) + ✅ 룰루랩 .docx 보안 조치 완료 (PIPA-expert `.gitignore` `*.docx` 차단).
```

(주: `⚠️ 미커밋`과 `⏸️ 별도 세션` 표기는 제거합니다. 둘 다 해소되었기 때문.)

#### 수정 #2 (line 8 근방, 세션 5 요약 블록 — 긴 줄)

`resume.md` line 8에 "루킨엑스"가 포함된 세션 5 요약 라인이 있습니다. 해당 라인은 다음 부분을 포함합니다:

**Before (부분):**
```
**루킨엑스 .docx 3개 발견** (PIPA-expert untracked, GitHub 미공개 확인, 처리 방안 결정 대기)
```

**After (부분):**
```
**룰루랩 .docx 3개 발견 및 차단 조치 완료** (PIPA-expert에 `*.docx` gitignore 패턴 추가 + commit/push `e163dd7`)
```

#### 수정 #3 (line 258 근방, Part 3 세션 로그 부분)

**Before:**
```
- git status 점검 중 **루킨엑스 .docx 3개 untracked 발견**: `(환자용) [루킨엑스] 개인정보 처리방침_...docx`, `개인정보수집동의서_...docx`, `개인정보_AI학습_검토의견.docx`
```

**After:**
```
- git status 점검 중 **룰루랩 .docx 3개 untracked 발견**: `(환자용) [룰루랩] 개인정보 처리방침_...docx`, `개인정보수집동의서_...docx`, `개인정보_AI학습_검토의견.docx` (당초 세션 중 인코딩 깨진 상태로 "루킨엑스"로 오기록했으나 실제 회사명은 "룰루랩", LuskinX는 영문 브랜드)
```

#### 수정 #4 (line 276 근방, 다음 세션 체크리스트)

**Before:**
```
2. **루킨엑스 .docx 3개 처리** (PIPA-expert 레포) — A(레포 밖 이동) / B(`.gitignore` 추가) / C(현상 유지) 중 사용자 선택. 현재 GitHub 미공개는 확인됨.
```

**After:**
```
2. ~~**룰루랩 .docx 3개 처리**~~ ✅ 완료 (별도 세션에서 Option B 채택: PIPA-expert `.gitignore`에 `*.docx` 전역 차단 패턴 추가, commit `e163dd7` + push 완료).
```

### 3.3 대상 파일 2 — `docs/session-log-20260410-pt2.md`

**절대경로:** `/Users/kpsfamily/코딩 프로젝트/legal-agent-orchestrator/docs/session-log-20260410-pt2.md`

**전략:** 이 파일에는 "루킨엑스" 출현이 다수입니다 (아래 확인된 목록 참조). 단순 find/replace로는 주의가 필요합니다 — 파일명 안의 `LuskinX`는 그대로 두고, 본문 서술의 "루킨엑스"만 "룰루랩"으로 바꿔야 합니다. 그리고 "루킨엑스(LuskinX)" 같은 bilingual 표기는 "룰루랩(LuskinX)"으로 정정.

확인된 출현 위치:

```
line 75: ## 3. 루킨엑스(LuskinX) 민감 파일 이슈 (세션 5에서 발견)
line 82: (환자용) [루킨엑스] 개인정보 처리방침_LuskinX_260119_clean_루킨엑스.docx
line 83: (환자용) [루킨엑스] 개인정보수집동의서_LuskinX_260119_clean_루킨엑스.docx
line 84: 루킨엑스_LuskinX_개인정보_AI학습_검토의견.docx
line 88: - 실제 클라이언트(LuskinX) 문서로 추정 (헬스케어/환자 대상?)
line 105: **결론: 루킨엑스 .docx 3개는 GitHub에 올라간 적 없음. 로컬 워킹 디렉터리에만 존재.**
line 152: 2. ⭐⭐ **루킨엑스 .docx 3개 처리 결정 + 실행** (PIPA-expert 레포) — A/B/C 중 선택
line 159: - PIPA-expert 레포에서 절대 `git add .` / `git add -A` 사용 금지. 루킨엑스 파일 노출 위험.
```

**구체 수정 지시:**

1. **Line 75 (섹션 헤더):**
   - Before: `## 3. 루킨엑스(LuskinX) 민감 파일 이슈 (세션 5에서 발견)`
   - After: `## 3. 룰루랩(LuskinX) 민감 파일 이슈 (세션 5에서 발견, 세션 wrap-up에서 해소)`

2. **Line 82~84 (파일명 표기):**
   - "루킨엑스" 토큰만 "룰루랩"으로 치환. 파일명 내부의 `LuskinX`는 건드리지 않음.
   - Before: `(환자용) [루킨엑스] 개인정보 처리방침_LuskinX_260119_clean_루킨엑스.docx`
   - After: `(환자용) [룰루랩] 개인정보 처리방침_LuskinX_260119_clean_룰루랩.docx`
   - (수집동의서 라인, 검토의견 라인도 같은 방식)

3. **Line 88:** 변경 없음. `LuskinX`는 영문 브랜드명이므로 그대로 유지. 단, 정확성을 위해 다음과 같이 보완:
   - Before: `- 실제 클라이언트(LuskinX) 문서로 추정 (헬스케어/환자 대상?)`
   - After: `- 실제 클라이언트(룰루랩 / LuskinX) 문서로 추정 (헬스케어/환자 대상)`
   - (물음표도 제거 — 확인됨)

4. **Line 105 (결론 블록):**
   - Before: `**결론: 루킨엑스 .docx 3개는 GitHub에 올라간 적 없음. 로컬 워킹 디렉터리에만 존재.**`
   - After: `**결론: 룰루랩 .docx 3개는 GitHub에 올라간 적 없음. 로컬 워킹 디렉터리에만 존재.**`

5. **Line 152 (체크리스트 항목):**
   - Before: `2. ⭐⭐ **루킨엑스 .docx 3개 처리 결정 + 실행** (PIPA-expert 레포) — A/B/C 중 선택`
   - After: `2. ~~**룰루랩 .docx 3개 처리**~~ ✅ 완료 — 별도 세션에서 Option B 채택: PIPA-expert \`.gitignore\`에 \`*.docx\` 전역 차단 패턴 추가, commit \`e163dd7\` + push 완료.`

6. **Line 159 (주의사항):**
   - Before: `- PIPA-expert 레포에서 절대 \`git add .\` / \`git add -A\` 사용 금지. 루킨엑스 파일 노출 위험.`
   - After: `- PIPA-expert 레포에서는 \`.gitignore\`에 \`*.docx\` 전역 차단이 이미 적용되어 broad staging도 안전. 단 `git add -f <파일>`로 강제 추가는 여전히 가능하므로 클라이언트 .docx에는 절대 `-f` 쓰지 말 것.`

7. **추가 — 세션 종료 상태 섹션 업데이트:** 이 문서 상단(파일 시작 부근)에 "세션 중단점" 문구가 있으면 "세션 wrap-up 완료 (Codex `YYYY-MM-DD`)"로 갱신. 파일 상단에 정확히 어떤 상태 문구가 있는지는 Codex가 직접 읽어서 판단하고 자연스럽게 갱신.

8. **공통 회사명 오기록 주석 추가 (선택, 권장):** 파일 상단 메타 근처에 한 줄 주석으로
   > **[Codex wrap-up 정정]** 이 문서 작성 당시 git status 인코딩 깨짐으로 회사명을 "루킨엑스"로 오기록했으나, 실제 회사명은 "룰루랩"(LuskinX는 영문 브랜드). 세션 wrap-up에서 전면 정정.

   을 추가하여 히스토리 보존. 한 줄이면 충분.

### 3.4 대상 파일 3 — memory (외부 파일)

**절대경로:**
- `/Users/kpsfamily/.claude/projects/-Users-kpsfamily---------legal-agent-orchestrator/memory/MEMORY.md`
- `/Users/kpsfamily/.claude/projects/-Users-kpsfamily---------legal-agent-orchestrator/memory/project_status.md`

**이 파일들은 orchestrator 레포 바깥에 있는 Claude Code 자동 메모리입니다. git 추적 대상이 아닙니다. 수정은 하되 commit 대상은 아닙니다.**

확인된 출현 위치:

- `MEMORY.md:1` — `- [Project Status](project_status.md) — Phase 1 ✅ + Phase 2.1/2.2 ✅ + 세션 5 포트폴리오(README/LICENSE) ✅ 미커밋, 루킨엑스 .docx 처리 대기`
- `project_status.md:3` (frontmatter description)
- `project_status.md:30` (대기 항목)
- `project_status.md:40` 근방 (긴 라인, 보안 이슈 블록)

#### 수정 지시

1. **`MEMORY.md` line 1:** 전체 대체
   - Before: `- [Project Status](project_status.md) — Phase 1 ✅ + Phase 2.1/2.2 ✅ + 세션 5 포트폴리오(README/LICENSE) ✅ 미커밋, 루킨엑스 .docx 처리 대기`
   - After: `- [Project Status](project_status.md) — Phase 1 ✅ + Phase 2.1/2.2 ✅ + 세션 5 포트폴리오(README/LICENSE) ✅ + PIPA-expert grade-b ✅ + 룰루랩 .docx 차단 ✅`

2. **`project_status.md`:** 파일 전체를 읽고, 다음 변경사항을 자연스럽게 반영하여 다시 쓰세요 (machine edit보다 전면 재작성이 더 깔끔):
   - "루킨엑스" → "룰루랩" 전면 교체
   - "미커밋" 상태 표현 제거 (Codex가 Task C에서 commit할 것이므로, 이 메모리 갱신은 Task C commit **직후**에 수행)
   - PIPA-expert grade-b 완료 사실 반영: `status: complete`, 30건(해석례 20 + 판례 10), PIPC 결정 pending 사유 기록
   - PIPA-expert `.gitignore` `*.docx` 차단 완료 (`e163dd7`) 반영 — 보안 이슈 해소
   - "대기" 섹션에서 "세션 5 변경사항 commit" 항목 제거 (완료)
   - "대기" 섹션에서 "룰루랩 .docx 처리" 항목 제거 (완료)
   - 남는 대기 항목: Phase 2.3 토론, 멀티라운드 토론 E2E, Phase 3 Case Replay, PIPC 결정문 재수집 (endpoint 복구 대기)
   - frontmatter `description` 라인도 갱신

---

## 4. Task B — PIPA-expert grade-b 완료 사실 반영

### 4.1 README.md (영어)

**절대경로:** `/Users/kpsfamily/코딩 프로젝트/legal-agent-orchestrator/README.md`

#### 수정 #1 — `## Current Status` 섹션

현재 파일 line 175~186 영역을 다음과 같이 수정:

**Before (line 180~186):**
```markdown
### In Progress / Pending

- **PIPA-expert `library/grade-b/` KB expansion** (Option B scope: 30 items across 6 topics) — [docs/todo/pipa-expert-grade-b-collection.md](docs/todo/pipa-expert-grade-b-collection.md)
- **Real debate logic in `skills/manage-debate.md`** (Pattern 3) — currently a skeleton
- **Multi-round debate E2E** (to prove the killer feature) — candidate scenario: "A Korean game company with EU servers transferring Korean user PII to the EU" (GDPR ↔ PIPA ↔ game-legal-research three-way debate)
- **Case Replay MVP** (Next.js static viewer) — independent track; sample data ready (case `20260410-012238-391f` + 3 mini E2E runs)
```

**After:**
```markdown
**Phase 2.2 follow-up: PIPA-expert `library/grade-b/` KB expansion** — complete
- 30 landmark items across 6 topics (consent, third-party provision, safety measures/breach, cross-border transfer, pseudonymization, sensitive/unique identifiers)
- 20 legal interpretations (법제처 법령해석례) + 10 Supreme Court precedents (e.g., 2013두2945, 2015다24904, 2022두68923, 2024다210554)
- **Scope change from original plan:** the original plan was 20 PIPC decisions + 10 precedents, but `get_pipc_decision_text` MCP endpoint outage forced substitution with 20 legal interpretations. `pipc-decisions/` remains pending for endpoint recovery (`source-registry.json` documents the reason).
- All files `verification_status: VERIFIED` with verbatim MCP source text. See [kipeum86/PIPA-expert@6b8137c](https://github.com/kipeum86/PIPA-expert/commit/6b8137c).

### In Progress / Pending

- **Real debate logic in `skills/manage-debate.md`** (Pattern 3) — currently a skeleton
- **Multi-round debate E2E** (to prove the killer feature) — candidate scenario: "A Korean game company with EU servers transferring Korean user PII to the EU" (GDPR ↔ PIPA ↔ game-legal-research three-way debate)
- **Case Replay MVP** (Next.js static viewer) — independent track; sample data ready (case `20260410-012238-391f` + 3 mini E2E runs)
- **PIPC decision re-collection** — blocked on `get_pipc_decision_text` MCP endpoint recovery
```

#### 수정 #2 — T1 mini E2E 부연설명 갱신

**Before (line 176):**
```markdown
- **T1** — PIPA-expert solo: 9 sources (8A + 1B), 60k tokens, 582s. Surfaced a KB gap in `library/grade-b/` (tracked as follow-up)
```

**After:**
```markdown
- **T1** — PIPA-expert solo: 9 sources (8A + 1B), 60k tokens, 582s. Surfaced a KB gap in `library/grade-b/` — **since resolved** (see Phase 2.2 follow-up below)
```

### 4.2 README.ko.md (한국어)

**절대경로:** `/Users/kpsfamily/코딩 프로젝트/legal-agent-orchestrator/README.ko.md`

#### 수정 #1 — `## 현재 상태` 섹션

**Before (line 180~186):**
```markdown
### 진행 중 · 대기

- **PIPA-expert `library/grade-b/` KB 보강** (Option B 스코프: 6 토픽에 걸쳐 30건) — [docs/todo/pipa-expert-grade-b-collection.md](docs/todo/pipa-expert-grade-b-collection.md)
- **`skills/manage-debate.md` 실제 로직** (Pattern 3) — 현재는 skeleton 상태
- **멀티라운드 토론 E2E** (킬러 피처 증명) — 후보 시나리오: "EU에 서버 둔 한국 게임사가 한국 이용자 개인정보를 EU로 국외이전할 때 법적 쟁점" (GDPR ↔ PIPA ↔ game-legal-research 3자 토론)
- **Case Replay MVP** (Next.js 정적 뷰어) — 독립 트랙, 샘플 데이터 풍부 (케이스 `20260410-012238-391f` + 3 mini E2E)
```

**After:**
```markdown
**Phase 2.2 후속 작업: PIPA-expert `library/grade-b/` KB 보강** — 완료
- 6 토픽(동의·제3자 제공·안전조치/유출·국외이전·가명정보·민감/고유식별) 전반에 걸쳐 landmark 30건 수록
- 법제처 법령해석례 20건 + 대법원 판례 10건 (예: 2013두2945, 2015다24904, 2022두68923, 2024다210554 등)
- **원안 대비 스코프 변경:** 원래 계획은 PIPC 결정 20 + 판례 10이었으나 `get_pipc_decision_text` MCP endpoint 장애로 법제처 해석례 20건으로 대체. `pipc-decisions/`는 endpoint 복구 시 재개 대상으로 `source-registry.json`에 사유 기록.
- 모든 파일 `verification_status: VERIFIED`, MCP 원문 verbatim 인용. [kipeum86/PIPA-expert@6b8137c](https://github.com/kipeum86/PIPA-expert/commit/6b8137c) 참조.

### 진행 중 · 대기

- **`skills/manage-debate.md` 실제 로직** (Pattern 3) — 현재는 skeleton 상태
- **멀티라운드 토론 E2E** (킬러 피처 증명) — 후보 시나리오: "EU에 서버 둔 한국 게임사가 한국 이용자 개인정보를 EU로 국외이전할 때 법적 쟁점" (GDPR ↔ PIPA ↔ game-legal-research 3자 토론)
- **Case Replay MVP** (Next.js 정적 뷰어) — 독립 트랙, 샘플 데이터 풍부 (케이스 `20260410-012238-391f` + 3 mini E2E)
- **PIPC 결정문 재수집** — `get_pipc_decision_text` MCP endpoint 복구 대기
```

#### 수정 #2 — T1 mini E2E 부연설명 갱신

**Before (line 176):**
```markdown
- **T1** — PIPA-expert 단독: 9 sources (8A + 1B), 60k tokens, 582s. `library/grade-b/`에서 KB gap 발견 (후속 과제로 추적 중)
```

**After:**
```markdown
- **T1** — PIPA-expert 단독: 9 sources (8A + 1B), 60k tokens, 582s. `library/grade-b/`에서 KB gap 발견 — **이후 해소** (아래 Phase 2.2 후속 작업 참조)
```

### 4.3 resume.md

**절대경로:** `/Users/kpsfamily/코딩 프로젝트/legal-agent-orchestrator/resume.md`

#### 수정 — `### ⏸️ 대기 중 (우선순위)` 테이블에서 grade-b 항목 제거

**Before (line 79):**
```markdown
| **PIPA-expert library/grade-b/ 보강** (Option B, 30건) | ⭐ 다음 세션 즉시 시작 가능 | [docs/todo/pipa-expert-grade-b-collection.md](docs/todo/pipa-expert-grade-b-collection.md) |
```

**조치:** 이 행을 삭제하고, 대신 `### ✅ 세션 4 추가 완료` 테이블 또는 별도로 `### ✅ 세션 5 wrap-up 완료` 블록 아래 적절한 위치에 다음 항목을 추가:

```markdown
| **PIPA-expert library/grade-b/ 보강** | ✅ 완료 (별도 세션, 커밋 `6b8137c`) | 해석례 20 + 판례 10 = 30건. 원안 PIPC 결정은 endpoint 장애로 해석례 대체. pipc-decisions 재개는 endpoint 복구 대기. |
```

(Codex가 resume.md 구조를 읽고 적절한 위치에 삽입하세요. 문서 흐름 유지가 우선.)

### 4.4 `docs/todo/pipa-expert-grade-b-collection.md`

이 파일은 **원본 핸드오프 문서**입니다. 내용을 그대로 둬도 되지만, 문서 상단 근처에 **완료 마크**를 추가하는 것이 유용합니다.

**수정 지시:** 파일 상단(frontmatter/제목 근방)에 다음 블록을 추가:

```markdown
> ✅ **완료됨** — 2026-04-10 별도 세션에서 실행. 커밋 [kipeum86/PIPA-expert@6b8137c](https://github.com/kipeum86/PIPA-expert/commit/6b8137c). 단, **원안 변경**: `get_pipc_decision_text` MCP endpoint 장애로 PIPC 결정 20건이 법제처 법령해석례 20건으로 대체됨. `library/grade-b/pipc-decisions/`는 endpoint 복구 시 재개 대상으로 남음. 자세한 내용은 `PIPA-expert/index/source-registry.json` 참조.
```

---

## 5. Task C — Commit (orchestrator 레포)

### 5.1 사전 확인 (commit 전 필수)

다음 명령을 실행하여 상태 확인:

```bash
cd "/Users/kpsfamily/코딩 프로젝트/legal-agent-orchestrator"
git status
git diff --stat
```

**예상 상태:**
- Modified: `CLAUDE.md`, `resume.md`, `README.md`, `README.ko.md`, `docs/session-log-20260410-pt2.md`, `docs/todo/pipa-expert-grade-b-collection.md`
- Untracked: `LICENSE`, `README.md`(처음), `README.ko.md`(처음), `docs/session-log-20260410-pt2.md`(처음), `docs/todo/codex-plan-session5-wrap.md` (이 문서 자체)

만약 **예상과 다른 modified/untracked 파일**이 나타나면 **commit 중단하고 사용자에게 확인 요청**하세요. 특히 `agents/`, `output/`, `.env`, `.mcp.json` 같은 파일이 변경 상태로 잡히면 잘못된 것입니다.

### 5.2 Staging 전략

**절대 `git add .` 또는 `git add -A`를 사용하지 마세요.** 파일을 개별 경로로 명시 추가:

```bash
cd "/Users/kpsfamily/코딩 프로젝트/legal-agent-orchestrator"

git add \
  CLAUDE.md \
  README.md \
  README.ko.md \
  LICENSE \
  resume.md \
  docs/session-log-20260410-pt2.md \
  docs/todo/pipa-expert-grade-b-collection.md \
  docs/todo/codex-plan-session5-wrap.md
```

`.gitignore`가 orchestrator 레포에 `output/`, `agents/`, `.env`를 이미 차단하고 있지만, 그래도 broad staging은 금지.

### 5.3 Commit 메시지

heredoc으로 다음 메시지 사용:

```bash
git commit -m "$(cat <<'EOF'
docs: 세션 5 wrap-up — 포트폴리오 README(영/한) + LICENSE + grade-b 완료 반영

세션 5에서 작성했으나 미커밋이던 변경사항을 일괄 정리.

- README.md: 영어 portfolio README 신규 (250줄, 4 killer points + §5
  토큰 정직성 섹션). 상단에 한국어판 링크.
- README.ko.md: 자연스러운 한국어판 (직역 아님). 영어판과 1:1 섹션 대응.
- LICENSE: Apache License 2.0 공식 본문 + Copyright 2026 kipeum86.
- CLAUDE.md: 에이전트 목록 10 → 8 동기화 (briefing 2개는 독립 Python
  앱으로 스코프 외, route-case.md v2와 일치).

추가로 wrap-up 정정 2건:

- 회사명 정정 (루킨엑스 → 룰루랩): 세션 5 기록 당시 PIPA-expert git
  status 인코딩 깨짐으로 "루킨엑스"로 오기록했던 부분을 정정. 실제
  회사명은 "룰루랩"(LuskinX는 영문 브랜드). resume.md,
  docs/session-log-20260410-pt2.md 전면 교체.

- PIPA-expert grade-b 완료 사실 반영: 별도 세션에서 30건(해석례 20 +
  판례 10) 수집 완료 및 push (kipeum86/PIPA-expert@6b8137c). 원안의
  PIPC 결정 20건은 get_pipc_decision_text MCP endpoint 장애로 법제처
  법령해석례 20건으로 대체. README(영/한) Current Status 섹션과
  resume.md 대기 테이블에 완료 사실 반영.

또한 PIPA-expert 레포에는 `.gitignore`에 `*.docx` 전역 차단 패턴 추가
commit (kipeum86/PIPA-expert@e163dd7)으로 룰루랩 클라이언트 문서 공개
리스크 해소됨 — 이 orchestrator 레포에는 별도 조치 불요.

Co-Authored-By: Codex
EOF
)"
```

**중요:**
- `--amend` 금지 (기존 커밋 수정 X). 항상 새 커밋.
- `--no-verify` 금지. pre-commit hook이 돌면 그대로 두고, 실패하면 원인을 조사한 뒤 별도 수정으로 처리.
- Co-Authored-By 라인은 Codex 세션이 실제로 수행했을 때만 추가. 사용자가 수동으로 편집한 경우는 제거.

### 5.4 Push는 하지 마세요

**Codex는 `git push`를 실행하지 마세요.** 사용자가 직접 확인한 후 push할 것입니다. 이 작업은 local commit에서 종료됩니다.

---

## 6. 검증 체크리스트 (Task C 전에 반드시 통과)

다음을 순서대로 확인:

### 6.1 "루킨엑스" 잔존 확인 (0건이어야 함)

```bash
cd "/Users/kpsfamily/코딩 프로젝트/legal-agent-orchestrator"
grep -rn "루킨엑스" . --include="*.md" 2>/dev/null | grep -v "\.git/"
```

**기대 출력:** 빈 문자열 (이 plan 파일 `codex-plan-session5-wrap.md` 자체에는 "루킨엑스"가 팩트박스와 지시부에 등장할 수 있음 — 문서의 역사적 설명이므로 유지. grep 시 `--exclude="codex-plan-session5-wrap.md"` 추가하거나, 결과가 이 plan 파일만 나오면 OK.)

memory 파일도 확인:
```bash
grep -n "루킨엑스" \
  "/Users/kpsfamily/.claude/projects/-Users-kpsfamily---------legal-agent-orchestrator/memory/"*.md
```
**기대 출력:** 빈 문자열.

### 6.2 grade-b "in progress" 잔존 확인

```bash
cd "/Users/kpsfamily/코딩 프로젝트/legal-agent-orchestrator"
grep -n "grade-b.*in progress\|grade-b.*Pending\|grade-b.*대기\|library/grade-b/.*KB expansion" README.md README.ko.md resume.md
```
**기대 출력:** 빈 문자열 또는 "complete"/"완료"를 포함한 라인만.

### 6.3 새 작성한 grade-b 완료 블록 존재 확인

```bash
grep -n "Phase 2.2 follow-up" README.md
grep -n "Phase 2.2 후속 작업" README.ko.md
grep -n "해석례 20" resume.md
```
**기대 출력:** 각 명령마다 최소 1개 매치.

### 6.4 git status 확인

```bash
git status
```
**기대:** §5.1의 예상 파일만 modified/untracked로 나타나야 함.

### 6.5 staging 내용 확인 (commit 전)

```bash
git diff --cached --stat
```
**기대:** 8개 파일 + insertions/deletions 수치가 합리적 (총 500~1500줄 범위).

### 6.6 diff 샘플 육안 검증

```bash
git diff --cached README.md | head -80
git diff --cached resume.md | head -60
```
의도치 않은 라인이 섞여 있지 않은지 확인.

---

## 7. 가드레일 (절대 금지 사항)

1. **PIPA-expert 레포에 손대지 마세요.** 별도 세션에서 이미 commit + push 완료됨. Codex는 orchestrator 레포만 건드립니다.
   ```
   /Users/kpsfamily/코딩 프로젝트/PIPA-expert    ← 절대 건드리지 마세요
   /Users/kpsfamily/코딩 프로젝트/legal-agent-orchestrator    ← 작업 대상
   ```

2. **`git add .` / `git add -A` / `git add *` 금지.** 파일을 개별 경로로 명시 추가.

3. **`git push` 금지.** local commit까지만.

4. **`git commit --amend` 금지.** 새 커밋만.

5. **`--no-verify` / `--no-gpg-sign` 금지.** Pre-commit hook이 걸리면 hook 실패 원인을 보고 별도 수정.

6. **`git reset --hard` / `git clean -f` / `git restore` 금지.** 이 작업 중에는 destructive 명령 사용하지 않습니다. 실수 발생 시 사용자에게 보고.

7. **`.env` / `.mcp.json` / `agents/` / `output/`을 staging하지 마세요.** `.gitignore`가 대부분 막고 있지만 명시 add로도 우회하지 마세요.

8. **`docs/todo/pipa-expert-grade-b-collection.md` 내용 대부분은 유지.** 완료 마크만 상단에 추가. 실행 계획 본문은 히스토리 보존용으로 그대로 남깁니다.

9. **`docs/design.md` / `docs/ko-legal-opinion-style-guide.md` / `skills/*.md` / `.mcp.json` / `scripts/*` 건드리지 마세요.** 이 wrap-up과 무관.

10. **의심스러울 때 멈추고 보고하세요.** 기대와 다른 상태, 예상 못한 modified 파일, grep 결과 불일치가 발생하면 commit 전에 사용자에게 보고.

---

## 8. 예상 결과물

이 작업이 완료되면:

- orchestrator 레포에 새 커밋 1개 (local only, unpushed)
- 8개 파일 수정/생성
- "루킨엑스" 표기 0건 (이 plan 파일 제외)
- README(영/한)의 Current Status에 PIPA-expert grade-b 완료 사실 반영
- resume.md에서 grade-b 대기 항목 제거, 완료 항목 추가
- memory 파일(MEMORY.md, project_status.md)에 wrap-up 반영
- 사용자가 `git log -1`과 `git diff HEAD~1 HEAD --stat`만 보고 바로 push 여부 판단 가능한 상태

---

## 9. 이 plan 문서 자체의 처리

이 `codex-plan-session5-wrap.md` 파일은:

- **이번 Task C 커밋에 포함합니다** (히스토리 보존용).
- 나중에 불필요해지면 별도 커밋으로 삭제하거나 `docs/todo/archive/`로 이동.
- Codex는 이 파일 자체는 수정하지 마세요. 오직 참조 문서입니다.

---

## 10. 완료 보고 포맷

작업이 끝나면 다음과 같이 보고:

```
✅ Task A (회사명 정정) — N 라인 수정 (파일: X, Y, Z)
✅ Task B (grade-b 완료 반영) — N 라인 추가/수정 (파일: README.md, README.ko.md, resume.md, pipa-expert-grade-b-collection.md)
✅ Task C (commit) — 커밋 해시: <hash>, 파일 N개, +X/-Y 라인

검증:
✅ "루킨엑스" grep → 0건 (이 plan 파일 제외)
✅ "grade-b ... pending" grep → 0건
✅ git status → clean (commit 후)

다음 단계: 사용자 확인 후 `git push origin main`
```

끝.
