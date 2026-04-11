# Sample Cases — Who did what, and what they produced

This directory contains **four real cases** that were processed by the orchestrator, frozen and committed as portfolio evidence. The main README references these files throughout — in particular, the [Quick Look](../README.md#quick-look-a-real-case), [Process Is the Product](../README.md#3-the-process-is-the-product), [Sample Case Walkthrough](../README.md#sample-case-walkthrough), and [Measured Performance](../README.md#measured-performance) sections.

These cases are **not synthetic demos**. They were produced by actually running the system end-to-end. Every `events.jsonl`, every `{agent}-result.md`, every `{agent}-meta.json` is the untouched output of a real subagent dispatch.

> ⚠️ **Snapshot, not live output.** New cases processed by the orchestrator land under `output/` (which is gitignored). Files under `samples/` are an immutable frozen copy kept in git so anyone cloning the repo can inspect real data without having to run the system themselves.

---

## 1. Phase 1 E2E Case — Loot Box Regulation Opinion

**Directory:** [`20260410-012238-391f/`](20260410-012238-391f/)
**Query:** "한국 게임산업법의 확률형 아이템(가챠) 규제에 대한 법률 의견서를 작성해줘"
**Pattern:** 2 — sequential handoff (with revision cycle)
**Total events:** 47 · **Sources:** 33 (29 Grade A + 4 Grade B) · **Revision:** 1 cycle · **Approval:** approved

### Agents involved and their assignments

| # | Agent | Lawyer | Stage | What this subagent actually did | Artifact |
|---|-------|--------|-------|----------------------------------|----------|
| 1 | `general-legal-research` | 김재식 | Research | Queried `korean-law` MCP and pulled **14 primary sources** from the Korean statute database: 게임산업법 §2 xi (loot-box definition), §33 ② (disclosure duty), §38 ⑨~⑪ (corrective-order chain), §45 xi (criminal penalty), §48 (administrative fines — **noted that §33② violations are NOT listed**, a load-bearing structural finding), §31조의2 (domestic representative duty), 시행령 §19-2 + 별표 3-2, 전자상거래법 §21 ①i, 표시광고법 §3, KFTC 2024-01-05 en-banc decision on Nexon (₩11.642B fine, the largest in e-commerce law history), KFTC 2018-05-14 precedent, industry self-regulation history. Produced an 11-point key-finding summary. | [`research-result.md`](20260410-012238-391f/research-result.md) (37 KB) + [`research-meta.json`](20260410-012238-391f/research-meta.json) (10 KB) |
| 2 | `legal-writing-agent` | 한석봉 | Drafting | Took the 14 sources + 11 findings and drafted a full Korean law-firm memorandum: MEMORANDUM header → 수신/참조/발신/제목 table → 결론 요약 (3 substantive paragraphs) → Disclaimer → 사실관계 가정 (5 items) → 검토의견 (7 issue headings corresponding to the client's 7 questions) → 리스크 매트릭스 (High/Medium/Low) → 권고사항 (8 items) → 종결 disclaimer → signature block. Enforced tone conventions from `docs/ko-legal-opinion-style-guide.md` (합니다체, 사료됩니다, 가사, etc.). | [`opinion-v1.md`](20260410-012238-391f/opinion-v1.md) (39 KB) |
| 3 | `second-review-agent` | 반성문 (Partner) | QA review | **This is where the system earns its keep.** Ran verbatim checks on every block quote in the draft against the primary statute text via `korean-law` MCP. Returned `approved_with_revisions` with **9 comments: 2 Critical + 3 Major + 4 Minor**. Two specific catches worth highlighting: <br/> **[Critical #1]** Block quote of §38 ⑩⑪ did not match the current statute (receiver scope `제9항` vs the actual `제7항부터 제9항까지`; verb phrases `이행·보고` vs `조치 완료·통보`; recipient `문체부장관만` vs `게임물관리위원회위원장 또는 문체부장관`; §11 proviso format 2 descriptive clauses vs 3 enumerated items). Block quotes must be verbatim. <br/> **[Critical #2]** §31-2 domestic representative duty was over-generalized as applying to "all overseas operators" when the statute limits it to those meeting a Presidential-Decree threshold. Would mislead small overseas indie developers. <br/> Plus: §47 양벌규정 was hand-waved instead of cited directly (Major); risk matrix priority inversion vs recommendations (Major); `[Unverified]` civil suit got a quantitative risk grade (Major); three enforcement dates caused confusion (Minor); recommendations lacked time markers (Minor). | [`review-result.md`](20260410-012238-391f/review-result.md) (23 KB) + [`review-meta.json`](20260410-012238-391f/review-meta.json) (16 KB) |
| 4 | `legal-writing-agent` (revision 1) | 한석봉 | Revision | Dispatched again to apply all 9 comments. Mid-revision, **hit the Anthropic rate limit** (`"Anthropic usage limit hit, reset 6am Asia/Seoul"`). In a normal pipeline that would stall the case until tomorrow. | logged in [`events.jsonl`](20260410-012238-391f/events.jsonl) (`evt_042` ~ `evt_044`) |
| 5 | `orchestrator` (meta-verification) | — | Rescue | Instead of giving up, the orchestrator itself read the revised draft, called `korean-law` MCP directly for §38, §31-2, §47 primary-source text, and ran the verbatim diff in-process (`verifier=orchestrator_meta`). Result: 2 Critical + 1 Major + 1 Minor passed, revision approved. **This pattern was not in the original design** — it emerged under pressure during this E2E test and is now treated as a first-class fallback for Pattern 3 debates where a specialist going down mid-argument used to be fatal. | [`verbatim-verification.md`](20260410-012238-391f/verbatim-verification.md) (5 KB) + [`events.jsonl`](20260410-012238-391f/events.jsonl) `evt_045` |
| 6 | `orchestrator` (assembly) | — | Final delivery | Converted the revised `opinion.md` to DOCX via `scripts/md-to-docx.py`, producing a 56 KB file with 138 paragraphs, 5 tables, and dual-font typography (Times New Roman 11pt for Latin runs, 맑은 고딕 11pt for CJK runs, explicit XML `eastAsia` attribute so Word on Windows doesn't re-shape CJK). Styling follows `docs/ko-legal-opinion-style-guide.md` §11 to the letter. | [`opinion.md`](20260410-012238-391f/opinion.md) (47 KB) + [`opinion.docx`](20260410-012238-391f/opinion.docx) (123 KB) + [`events.jsonl`](20260410-012238-391f/events.jsonl) `evt_046` |

### Recommended reading order for visitors

1. **Start with the timeline:** [`events.jsonl`](20260410-012238-391f/events.jsonl) — 47 lines, under 2 minutes to skim. Each line is one atomic event. `evt_001` (the query) → `evt_final` (summary).
2. **See what the partner caught:** [`review-meta.json`](20260410-012238-391f/review-meta.json) → the `comments` array with severity-ranked findings. This is the single most impressive piece of evidence in this repository for "the fact-checker is real."
3. **See the final deliverable:** [`opinion.md`](20260410-012238-391f/opinion.md) — the post-revision memorandum that would actually go to a client.
4. **See the rescue:** [`verbatim-verification.md`](20260410-012238-391f/verbatim-verification.md) — the orchestrator's in-process meta-verification log when the writing agent died mid-revision.

---

## 2. Phase 2.2 T1 — PIPA-expert Solo Sanity Check

**Directory:** [`test-T1-20260410-121640/`](test-T1-20260410-121640/)
**Query:** PIPA §28-2 (가명정보의 처리) + §28-3 (결합) deep interpretation, including PIPC precedents
**Pattern:** direct single-specialist (no writing/review wrapper — specialist output only)
**Sources:** 9 (8 Grade A + 1 Grade B) · **Tokens:** ~60K · **Wall time:** 582s

### What happened

This was a **specialist routing sanity test**: does `PIPA-expert` correctly handle a question entirely within its jurisdiction without the generalist pipeline getting in the way?

| # | Agent | Lawyer | Stage | What this subagent actually did | Artifact |
|---|-------|--------|-------|----------------------------------|----------|
| 1 | `PIPA-expert` | 정보호 | Solo research | Loaded its own KB (`library/grade-a/pipa/art28-2.md`, related articles, PIPC guidelines) and interpreted §28-2 (pseudonymization consent exemption for statistical/scientific/public-interest purposes) + §28-3 (combination of pseudonymized data by different controllers must go through a PIPC-designated combination institution) + §28-4/5/7 interactions + 시행령 §29-2/3 (institution designation criteria and export review). Key finding: the consent exemption under §28-2 ① only applies to the listed purposes; `§28-4` (safety measures), `§28-5` (re-identification prohibition), `§28-3` (combination restrictions) remain as parallel obligations. Also attempted to pull the PIPC 2022-04-27 Korean Medicine Association case (ID 667) but couldn't retrieve the full decision text — honestly flagged the limit and declined to use it as sole support. | [`PIPA-expert-result.md`](test-T1-20260410-121640/PIPA-expert-result.md) + [`PIPA-expert-meta.json`](test-T1-20260410-121640/PIPA-expert-meta.json) |

### What this test surfaced

**KB gap discovery.** During the run, `PIPA-expert` reported that its `library/grade-b/pipc-decisions/` and `library/grade-b/court-precedents/` directories were **empty**. The agent compensated by calling `korean-law` MCP live, but the integrity of the result depended on how much the agent could pull per query — not ideal.

This finding **drove a follow-up effort** (see [Measured Performance → Phase 2.2 follow-up](../README.md#phase-22-follow-up-pipa-expert-librarygrade-b-expansion--complete) in the main README): in a separate session, 30 landmark items (20 legal interpretations + 10 Supreme Court precedents) were collected and committed to `PIPA-expert/library/grade-b/` as [kipeum86/PIPA-expert@6b8137c](https://github.com/kipeum86/PIPA-expert/commit/6b8137c). The original plan was 20 PIPC decisions + 10 precedents, but the `get_pipc_decision_text` MCP endpoint was down, so the plan pivoted to legal interpretations — a scope-change decision made visible in the grade-b commit message for portfolio transparency.

**Takeaway:** a sanity test found a real KB gap, and the gap got fixed. The fact that we can point at the exact commit that fixed it (`6b8137c`) is part of the same "process is the product" story as `evt_045` in case #1.

---

## 3. Phase 2.2 T2 — PIPA ∥ GDPR Parallel Dispatch

**Directory:** [`test-T2-20260410-121640/`](test-T2-20260410-121640/)
**Query:** Cross-jurisdictional data transfer analysis — how K-PIPA Chapter 28-8/9/10/11 and GDPR Chapter V (Arts. 44-50) compare along 5 dimensions: legal basis, consent, accountability, enforcement, suspension order
**Pattern:** 1 — parallel dispatch (two specialists run simultaneously, then results merged)
**Sources:** 26 (all Grade A) · **Tokens:** ~124K total · **Wall time:** 334s

### What happened

This was the **Pattern 1 validation test**: can the orchestrator dispatch `PIPA-expert` and `GDPR-expert` in parallel (not sequentially), have each produce their own jurisdiction-specific analysis along a 5-dimension common frame, and then mechanically align the results?

| # | Agent | Lawyer | Stage | What this subagent actually did | Artifact |
|---|-------|--------|-------|----------------------------------|----------|
| 1 | `PIPA-expert` | 정보호 | Parallel research (branch A) | Analyzed K-PIPA §28-8 (5-basis closed list: separate consent / law-treaty / contract-performance outsourcing / PIPC-designated certification / PIPC adequacy decision), §28-9 (PIPC's standalone suspension-order power, functionally analogous to GDPR Art. 58(2)(j)), §28-10 (cumulative application of Chapters §17-19 + Chapter 5 data-subject rights), §28-11 (onward-transfer mutatis mutandis). Produced findings tagged against the 5 common dimensions. Key structural observation: Korea's "flexible adequacy" under §28-8 ①5 + 시행령 §29-9 lets PIPC set country-specific scope/duration/conditions — unlike the EU's binary adequacy model. | [`PIPA-expert-result.md`](test-T2-20260410-121640/PIPA-expert-result.md) + [`PIPA-expert-meta.json`](test-T2-20260410-121640/PIPA-expert-meta.json) |
| 2 | `GDPR-expert` | 김덕배 | Parallel research (branch B) | Analyzed GDPR Arts. 44 (non-undermining principle) / 45 (adequacy decisions, including Korea's 2021-12-17 commercial adequacy) / 46 (SCCs under Implementing Decision 2021/914, BCRs under Art. 47, codes, certifications) / 47 (BCR consistency mechanism) / 48 (blocking of third-country judicial orders absent MLAT) / 49 (narrow derogations interpreted restrictively per EDPB Guidelines 2/2018). Anchored in **Schrems II (CJEU C-311/18, 2020-07-16)**: "essentially equivalent" protection standard, Privacy Shield invalidated under Charter Arts. 7/8/47 due to FISA 702 surveillance and ineffective Ombudsperson. Operationalized via EDPB Recommendations 01/2020 v2.0 six-step Transfer Impact Assessment methodology. Ran in its own Claude instance, with its own KB, without reading anything PIPA-expert produced. | [`GDPR-expert-result.md`](test-T2-20260410-121640/GDPR-expert-result.md) + [`GDPR-expert-meta.json`](test-T2-20260410-121640/GDPR-expert-meta.json) |

### Why this is not the same as "one LLM playing both sides"

The important thing about Pattern 1 is not that two agents ran in parallel in wall-clock time. It's that **they could not see each other's context**. `PIPA-expert` has its own CLAUDE.md (Korean personal information law specialist persona, Korean legal tone conventions, PIPA/PIPC knowledge base), and `GDPR-expert` has its own CLAUDE.md (EU data protection law specialist, English legal tone, GDPR/CJEU/EDPB knowledge base). Neither agent's prompts, sources, or reasoning were visible to the other until the orchestrator merged summaries at the end.

This is the minimum structural precondition for any real cross-jurisdiction analysis. A single LLM "role-playing" both sides shares one set of priors. These two agents genuinely don't.

The 5-dimension common frame (legal basis / consent / accountability / enforcement / suspension order) was injected into both prompts so their findings could be aligned post-hoc. Both branches produced structurally comparable outputs — look at the two `{agent}-meta.json` `key_findings` arrays side by side to see it.

---

## 4. Phase 2.2 Regression — game-legal-research on Korean Gaming Law

**Directory:** [`test-regression-20260410-121640/`](test-regression-20260410-121640/)
**Query:** The same Korean loot-box regulation question as case #1, but routed to the specialist `game-legal-research` agent instead of the generalist `general-legal-research` agent — to compare specialist depth against the v1 generalist baseline.
**Pattern:** direct single-specialist (regression comparison)
**Sources:** 32 (25 Grade A + 0 B + 7 C) · **Tokens:** ~170K · **Wall time:** 797s

### What happened

This was the **v1 vs v2 baseline comparison**. Case #1 had already produced a great result using `general-legal-research`. The question for this test was: does routing the same query to `game-legal-research` (the gaming-domain specialist, with its own library of international gaming law materials and its own `game-legal-mcp`) produce a noticeably better result — justifying the cost of maintaining a specialist?

| # | Agent | Lawyer | Stage | What this subagent actually did | Artifact |
|---|-------|--------|-------|----------------------------------|----------|
| 1 | `game-legal-research` | 심진주 | Specialist research | Did the same 게임산업법 verbatim walkthrough as case #1, but hit harder on: (a) the §45 xi criminal-penalty structure — confirming that §33 ② violations themselves are NOT criminal; only non-compliance with a §38 ⑨ corrective order is, (b) §48 fine-structure gap — the explicit observation that §33 ② is absent from the administrative fine enumeration, meaning there is no direct-fine enforcement route, (c) domestic-representative duty under §31-2 with explicit attribution-to-parent clause under §31-2 ④ (plugging the exact over-generalization hole that the partner caught in case #1's review stage), (d) international comparison: Belgium's outright paid-loot-box ban, Japan's complete gacha (コンプガチャ) prohibition + self-regulation, China's 2017 disclosure mandate. Pulled KFTC decision 17235 full text including ¶110-111 ("현행법상 확률 고지 의무 존부는 전자상거래법 위반 판단 기준이 아니다") and ¶39-41 (Supreme Court doctrine on deceptive inducement). Used the agent's own `library/cache/` for faster citation retrieval. | [`game-legal-research-result.md`](test-regression-20260410-121640/game-legal-research-result.md) + [`game-legal-research-meta.json`](test-regression-20260410-121640/game-legal-research-meta.json) |

### The measured comparison

Setting `general-legal-research`'s case #1 research output as the baseline:

- **Source count:** 32 vs 14 (+129%) — this is partly because the specialist pulls more background context (KFTC, Nexon decision full text, international comparators) than the generalist
- **Comparable topic coverage:** 11/11 of the same substantive topics covered, −3% on overall legal accuracy in the narrow overlap (the specialist slightly under-performed on two minor points the generalist got right — likely a function of the specialist agent trading some Korean-law generalist breadth for international-gaming-law depth)
- **Unique specialist contributions:** the international comparison (Belgium / Japan / China) was entirely absent from the generalist output; the §31-2 ④ attribution clause was explicitly cited, which is exactly the point the generalist's draft got dinged for in case #1's review stage

**Conclusion:** the specialist is worth keeping for gaming-law questions, but the win is specifically in **structural/comparative depth** (international framing, statutory-structure observations), not raw primary-source count. This is the kind of finding that calibrates the router in `skills/route-case.md` — for gaming questions, prefer `game-legal-research`; for pure Korean statutory questions outside gaming, the generalist is fine.

---

## About grade distribution in source citations

Throughout these samples you'll see a `grade_distribution` on each case's final output:

- **Grade A** — Primary sources. Statutes (with specific article/paragraph numbers), Supreme Court judgments, constitutional court decisions, KFTC/PIPC formal decisions, EU regulations/CJEU judgments. Verifiable verbatim against the government database.
- **Grade B** — Secondary but authoritative. Published administrative interpretations (법제처 법령해석례), regulator guidelines (PIPC guidelines, EDPB guidelines), official commentary.
- **Grade C** — Tertiary. Industry self-regulation, academic commentary, law-firm memoranda, news reports citing verified facts.
- **Grade D** — Unverified or speculative. Flagged with `[Unverified]` in the draft; the reviewer will demote any risk grade tied to these.

Case #1 (`20260410-012238-391f`) has 29A + 4B + 0C + 0D — an unusually high primary-source ratio because the question was about recent Korean statutes with fresh KFTC enforcement action. Case #4 (regression) has 25A + 0B + 7C because the international comparison required pulling from academic sources and foreign-law commentary where primary-source text wasn't available in `korean-law` MCP.

---

## About PII and sensitivity

These samples cover **publicly available regulatory topics**: Korean loot-box regulation (a matter of public KFTC enforcement action against a publicly listed game company), PIPA Chapter 28 pseudonymization interpretation (statutory and published-guideline territory), and a cross-jurisdictional K-PIPA / GDPR framework comparison. **No client PII is involved.** The sample opinions would be appropriate to share with any Korean game company as a general regulatory briefing.

This is different from the `PIPA-expert` repository itself, which does have a `.gitignore *.docx` rule to block accidental inclusion of actual client-work files that live in the developer's local working copy. The orchestrator repository has never had tracked `.docx` files other than the dual-font sample opinion in case #1 above.
