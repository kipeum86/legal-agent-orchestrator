# 다음 세션 시작 프롬프트 (PIPA-expert grade-b 작업)

아래 프롬프트를 새 Claude Code 세션에 **복사·붙여넣기**하여 시작.

**세션 시작 전 체크:**
```bash
cd "/Users/kpsfamily/코딩 프로젝트/legal-agent-orchestrator"
export LAW_OC=kipeum86
echo $LAW_OC  # kipeum86 확인
claude        # Claude Code 시작
```

---

## 복사용 프롬프트 (아래부터 끝까지 복사)

```
PIPA-expert library/grade-b/ 보강 작업을 이어서 수행하겠다.

## 1. 컨텍스트 복원

다음 문서를 순서대로 Read로 읽어서 컨텍스트 복원:
1. docs/todo/pipa-expert-grade-b-collection.md (이 작업의 완전한 핸드오프 — 스코프, 3 phase 계획, 주제 매트릭스, subagent 프롬프트 템플릿, 스키마)
2. docs/session-log-20260410.md Phase 8 (배경 — T1 테스트에서 grade-b 디렉토리가 완전히 빈 상태로 발견된 경위)
3. resume.md (프로젝트 전체 상태)

## 2. 환경 확인

```bash
git log --oneline | head -5
# 최신: 0f1248f docs: 세션 4 종료 핸드오프
echo $LAW_OC
# kipeum86 출력돼야 함
```

korean-law MCP tools가 deferred 상태라면 ToolSearch로 로드:
- mcp__claude_ai_Korean-law__search_pipc_decisions
- mcp__claude_ai_Korean-law__get_pipc_decision_text
- mcp__claude_ai_Korean-law__search_precedents
- mcp__claude_ai_Korean-law__get_precedent_text
- mcp__claude_ai_Korean-law__find_similar_precedents (옵션)

## 3. 작업 스코프 (확정됨)

- Option B: 30건 = PIPC 결정 20 + 대법원 판례 10
- 6 core topics: 수집·이용 동의 / 제3자 제공 vs 처리위탁 / 안전조치·유출 / 국외이전 / 가명정보 / 민감·고유식별정보
- 예상 2-3시간, ~150k 토큰
- 이 작업은 /Users/kpsfamily/코딩 프로젝트/PIPA-expert 레포에서 수행 (심볼릭 링크)
- 오케스트레이터 레포(legal-agent-orchestrator)는 건드리지 않음

## 4. 실행 절차 (핸드오프 doc의 3 Phase 따름)

### Phase A — 큐레이션 (직접 수행, ~30분)
주제별로 search_pipc_decisions/search_precedents 쿼리 → 각 주제 5-8개 후보 → 중요도 기준 30건 curated list 확정.

핸드오프 doc의 "검색 쿼리 예시" 표와 "주요 landmark 후보" 참조 (내 기억 기반이므로 실제 MCP 검색으로 재검증 필수).

### Phase B — Fetch + Format + Save (subagent 위임)
큐레이션된 30 ID를 subagent에 일괄 위임. 핸드오프 doc의 "Subagent 프롬프트 구조" 템플릿 그대로 사용하되, 큐레이션된 실제 ID 리스트를 주입.

Subagent가 각 결정문/판례문을 fetch → YAML frontmatter 생성 → markdown 변환 → library/grade-b/{pipc-decisions,court-precedents}/ 에 저장.

주의: subagent에 "DO NOT commit — 오케스트레이터가 검증 후 커밋" 지시 필수.

### Phase C — 검증 + Commit (직접 수행, ~15분)
1. ls로 30 파일 존재 확인
2. 랜덤 샘플 2-3개 읽어서 schema 준수 확인
3. source-registry.json 업데이트: grade-b 두 카테고리를 pending → partial, count=20/10, retrieved_at 기록
4. PIPA-expert 레포 내부에서 commit:
   ```bash
   cd "/Users/kpsfamily/코딩 프로젝트/PIPA-expert"
   git add library/grade-b/pipc-decisions/ library/grade-b/court-precedents/ index/source-registry.json
   git commit -m "feat(grade-b): landmark 30건 초기 수집 (PIPC 20 + 판례 10)"
   ```
5. Push는 사용자 명시적 승인 후 (public repo)

## 5. 완료 후

- 오케스트레이터 레포 resume.md §8 "알려진 이슈" 항목에서 이 항목 체크 또는 제거
- (선택) T1 질문 재실행하여 grade-b에서 실제로 소스가 나오는지 regression 확인

## 주의사항

- 세션 4 Mini E2E에서 Pattern 1 Subagent 3건 연속 실행 시 rate_limit 근접했음 → 30건 fetch는 subagent 하나로 일괄 처리하되, 중간에 실패하면 이어서 재개 가능한 체크포인트 전략 고려
- korean-law MCP의 search/get 호출이 30+ 건 연속되면 MCP 서버 쪽 rate_limit 가능 → 필요 시 간격 두기
- 결정문 원문이 10-30KB 수준이라 subagent 컨텍스트 관리 주의

시작한다.
```

---

## 이 프롬프트의 설계 의도

- **컨텍스트 복원 먼저**: Read 3개 문서로 다음 세션 Claude가 세션 4 상태를 완전히 이해
- **환경 체크 명시**: LAW_OC 환경변수가 매 세션 재설정 필요 (resume.md §11에 기록된 제약)
- **스코프 재확인**: 세션 4에서 확정된 Option B를 명시적으로 재확인하여 scope creep 방지
- **Subagent 위임 전략**: Phase B를 subagent에 위임하여 메인 세션 컨텍스트 보존 (세션 4에서도 같은 전략)
- **완료 조건 명시**: "PIPA-expert 레포에서 commit, 오케스트레이터 레포는 안 건드림" — 세션 4에서 명확히 정리된 아키텍처 전제 유지
- **Push 승인 게이트**: public repo이므로 push는 사용자 승인 후

## 대체 프롬프트 (grade-b 작업 아닌 다른 걸 할 경우)

세션 4 종료 시점의 다른 가능한 다음 세션 옵션:

**A. Case Replay MVP (Next.js 뷰어)**
```
Case Replay MVP를 시작한다.
resume.md와 docs/session-log-20260410.md §6의 3개 테스트 결과 경로를 읽어서
events.jsonl 샘플 데이터로 Next.js 정적 뷰어 MVP를 설계하겠다.
타임라인 + 이벤트 카드 + 소스 grade A/B/C 컬러 코딩.
docs/design.md와 docs/notes/architecture-defense.md도 읽어서 컨셉 정합성 확인.
```

**B. README 작성**
```
legal-agent-orchestrator README.md를 작성한다.
원재료는 docs/notes/architecture-defense.md + docs/session-log-20260410.md.
킬러 포인트 4개 (컨텍스트 격리, LangGraph 대비, Harvey 대비 투명성, Case Replay).
현재 상태는 resume.md 참조.
```

**C. manage-debate.md 실제 로직 (Pattern 3)**
```
세션 4에서 skip 결정했던 2.3 Pattern 3 (멀티라운드 토론) 구현을 재개한다.
skills/manage-debate.md 현재 skeleton을 실제 로직으로 확장.
docs/design.md §Pattern 3 + skills/route-case.md Step 6 fallback 경로 참조.
docs/session-log-20260410.md D2에서 skip 이유 확인 (token 비용) — 재검토.
```

**D. route-case.md v3 (game-legal-research 자체 제안 반영)**
```
route-case.md v3 확장: Regression 테스트에서 game-legal-research가 자체 제안한 패턴 반영.
"국제 비교 primary-source가 중요한 KR 게임법 질문은 [game-legal-research ∥ general-legal-research] 병렬이 더 나을 수 있음"
docs/session-log-20260410.md Phase 6 Regression 섹션 참조.
skills/route-case.md Step 4 중복 범위 해결 규칙에 새 항목 추가.
```
