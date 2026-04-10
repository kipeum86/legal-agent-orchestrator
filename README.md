# Jinju Law Firm Orchestrator · 법무법인 진주

**한국어:** [README.ko.md](README.ko.md)

> An AI law firm running on Claude Code. Eight specialist lawyer agents — each with their own jurisdiction, knowledge base, and MCP tools — collaborate like a real firm to produce legal opinions with full audit trails.

![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)
![Runtime: Claude Code](https://img.shields.io/badge/Runtime-Claude_Code-orange)
![MCP: korean-law](https://img.shields.io/badge/MCP-korean--law-green)
![Status: Phase 2.2 validated](https://img.shields.io/badge/Status-Phase_2.2_validated-brightgreen)

**Status:** Phase 1 E2E passed (2026-04-10) · Phase 2.1/2.2 validated with 3 mini E2E runs · Phase 2.3 (multi-round debate) + Case Replay in progress.

---

## Table of Contents

- [Quick Look: A Real Case](#quick-look-a-real-case)
- [Overview](#overview)
- [Why This Architecture](#why-this-architecture)
- [How It Works](#how-it-works)
- [What You Can Ask](#what-you-can-ask)
- [Agent Roster](#agent-roster)
- [Sample Case Walkthrough](#sample-case-walkthrough)
- [Measured Performance](#measured-performance)
- [Event Taxonomy](#event-taxonomy)
- [Quickstart](#quickstart)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Roadmap](#roadmap)
- [FAQ](#faq)
- [References](#references)
- [License](#license)

---

## Quick Look: A Real Case

Here is one actual case from this repository — no mock data, no hand-wavy demo. Every file referenced below lives under [`output/20260410-012238-391f/`](output/20260410-012238-391f/).

**The query (one sentence from the user):**

> "한국 게임산업법의 확률형 아이템(가챠) 규제에 대한 법률 의견서를 작성해줘"
>
> _"Write a legal opinion on Korea's Game Industry Act loot-box (gacha) regulation."_

**What the orchestrator did, end to end:**

1. **Classified the question** — `jurisdiction=[KR]`, `domain=game_regulation`, `task=drafting`, `complexity=compound`. Router picked pipeline `[general-legal-research → legal-writing-agent → second-review-agent]` (Pattern 2, sequential handoff).
2. **Dispatched `general-legal-research`** (김재식). That subagent pulled **14 primary sources** from the Korean Ministry of Government Legislation (법제처) via the `korean-law` MCP — including 게임산업법 §33② (loot-box disclosure duty), §38 ⑨~⑪ (corrective-order enforcement chain), §45 xi (2-year/₩20M criminal penalty), the 2024-01-05 KFTC en-banc decision fining Nexon **₩11.642 billion** (case 2021전자1052) — and returned 11 key findings.
3. **Dispatched `legal-writing-agent`** (한석봉). That subagent drafted a standard Korean law-firm memorandum: executive summary, disclaimer, factual assumptions, 7 issue headings, risk matrix, 8 recommendations, signature block.
4. **Dispatched `second-review-agent`** (반성문, Partner). Partner returned `approved_with_revisions` with **9 comments: 2 Critical + 3 Major + 4 Minor** — catching, among other things, a real verbatim mismatch in the draft's block quote of §38 ⑩⑪ against the current statute text.
5. **Triggered revision cycle 1.** Mid-revision, `legal-writing-agent` hit `rate_limit` (`"Anthropic usage limit hit, reset 6am Asia/Seoul"`). Instead of bailing, the orchestrator took over: it **cross-checked the revised citations directly against `korean-law` MCP itself** (`verifier=orchestrator_meta`) and passed 2 Critical + 1 Major + 1 Minor verbatim.
6. **Generated `opinion.docx`** — 56 KB, 138 paragraphs, 5 tables, dual-font Times New Roman / 맑은 고딕 per the canonical Korean legal style guide §11.

**What the case file contains, on disk:**

| File | Size | Purpose |
|------|------|---------|
| `events.jsonl` | 17 KB | **47 events** — the full replayable timeline |
| `research-result.md` + `research-meta.json` | 37 KB + 10 KB | Lawyer 1 (김재식) full analysis + 2000-token summary |
| `opinion-v1.md` → `opinion.md` | 39 KB → 47 KB | Draft + final (after revision cycle 1) |
| `review-result.md` + `review-meta.json` | 23 KB + 16 KB | Partner (반성문) comments with line-level citations |
| `verbatim-verification.md` | 5 KB | Orchestrator meta-verification log |
| `opinion.docx` | 123 KB | Final DOCX for client delivery |
| `sources.json` | 8 KB | All 33 graded sources |

**Bottom-line numbers:** 33 sources (29 Grade A primary-source citations + 4 Grade B secondary) · 1 revision cycle · 1 meta-verification rescue · **approved**.

The rest of this README explains why this architecture exists, how it works, and why it burns a lot of tokens on purpose. A [full walkthrough of this same case](#sample-case-walkthrough) — including the actual review comments the partner caught — is further down.

---

## Overview

Most "legal AI" products are a single LLM you throw questions at. This project is different.

An **orchestrator plays the role of managing partner**, classifying each incoming question, routing it to the right specialist lawyer, and choosing the appropriate collaboration pattern (sequential handoff / parallel research / multi-round debate). The eight subordinate agents are real Claude Code agents — each with its own jurisdiction (Korea / EU), domain (privacy / gaming / contracts / translation), and task type (research / drafting / review). **This project reuses them 100% unmodified.**

Every step is logged to `events.jsonl`, producing a replayable artifact. Which lawyer was assigned, which sources (Grade A/B/C) were cited, what the fact-checker flagged, how the inter-jurisdiction debate played out — it's all visible.

---

## Why This Architecture

The standard playbook for multi-agent systems is to wrap a framework (LangGraph, CrewAI, AutoGen, Claude Agent SDK) in a web server. Using Claude Code itself as the orchestration runtime is non-standard — the first reaction from most developers is "why didn't you use Agent SDK?"

The answer starts with clearing up four misconceptions, ends with one honest tradeoff, and is backed up by a comparison table.

### 1. "Doesn't stuffing 8 agents into one orchestrator kill performance?"

No. This is a misconception about how Claude Code's `Agent` tool works.

Each subagent is a **completely independent new Claude instance** with its own fresh 200K context window. The orchestrator doesn't carry their weight — it just coordinates.

```
Orchestrator (200K context, actual usage ~25-40K)
   │
   ├── Agent tool call ──▶ New Claude instance (200K, full CLAUDE.md + skills + MCP)
   │                        └── runs independently → returns result via file
   │
   ├── Agent tool call ──▶ Another new Claude instance (200K)
   │                        └── runs independently → returns result via file
   │
   └── ...
```

The orchestrator itself only spends tokens on classification (~2K), dispatch prompts (~1K), and reading result summaries (~2K). Each specialist runs at full capacity with its complete CLAUDE.md, skills, knowledge base, and MCP tools. **This is the opposite of "stuffing" — it's the most context-efficient multi-agent architecture possible.**

### 2. "Why not LangGraph or Agent SDK like everyone else?"

Because wrapping existing Claude Code agents in a web framework loses 40–50% of their capability:

- MCP integrations break
- The skills system needs reimplementation
- Knowledge base browsing changes
- You end up with a pretty demo that produces legal opinions at half the quality of the originals

So we inverted the tradeoff: **use Claude Code as the runtime, preserve 100% of agent capability, and decouple visualization into static Case Replay**. The result is an architecture that runs real legal work — not a demo.

### 3. The Process Is the Product

Harvey AI is a black box. You get an answer; you don't know how.

Jinju Law Firm is the opposite:

- Which lawyer was assigned? → visible (`events.jsonl` · `agent_assigned`)
- Which sources (Grade A/B/C) were consulted? → visible (`source_graded`)
- What did the fact-checker flag? → visible (`review_completed` with `approval=approved_with_revisions`)
- How did the revision cycle play out? → visible (`revision_requested`, `verbatim_verified`)
- What did the partner comment on? → stored in `review-result.md`, one row per comment with line references

Here are 15 events selected from an actual 47-event case file ([`output/20260410-012238-391f/events.jsonl`](output/20260410-012238-391f/events.jsonl)):

```jsonl
{"id":"evt_001","type":"case_received","data":{"query":"한국 게임산업법의 확률형 아이템(가챠) 규제에 대한 법률 의견서를 작성해줘"}}
{"id":"evt_002","type":"case_classified","data":{"jurisdiction":["KR"],"domain":"game_regulation","task":"drafting","pipeline":["general-legal-research","legal-writing-agent","second-review-agent"]}}
{"id":"evt_003","type":"agent_assigned","agent":"general-legal-research","data":{"name":"김재식","role":"범용 법률 리서치"}}
{"id":"evt_014","type":"source_graded","agent":"general-legal-research","data":{"source":"공정위 2024.1.5. 전원회의 의결 ㈜넥슨코리아... 과징금 116억 4,200만원","grade":"A","citation":"사건번호 2021전자1052"}}
{"id":"evt_018","type":"research_completed","data":{"sources_count":14,"key_findings_count":11}}
{"id":"evt_019","type":"agent_assigned","agent":"legal-writing-agent","data":{"name":"한석봉","role":"법률문서 작성"}}
{"id":"evt_034","type":"writing_completed","data":{"output_file":"opinion.md","sources_count":14}}
{"id":"evt_035","type":"agent_assigned","agent":"second-review-agent","data":{"name":"반성문","role":"품질 검토 / 파트너 최종 승인"}}
{"id":"evt_041","type":"review_completed","data":{"approval":"approved_with_revisions","comments_count":9}}
{"id":"evt_042","type":"revision_requested","data":{"cycle":1,"max_cycles":2,"critical":2,"major":3,"minor":4}}
{"id":"evt_043","type":"agent_assigned","agent":"legal-writing-agent","data":{"role":"법률문서 수정 (revision cycle 1)"}}
{"id":"evt_044","type":"error","agent":"legal-writing-agent","data":{"error_type":"rate_limit","message":"Anthropic usage limit hit, reset 6am Asia/Seoul"}}
{"id":"evt_045","type":"verbatim_verified","agent":"orchestrator","data":{"verifier":"orchestrator_meta","reason":"review-agent token limit hit; meta verification via korean-law MCP","critical_pass":2,"major_pass":1,"final_status":"approved"}}
{"id":"evt_046","type":"docx_generated","data":{"output":"opinion.docx","size_bytes":56519,"tables":5,"paragraphs":138}}
{"id":"evt_final","type":"final_output","data":{"total_sources":33,"grade_distribution":{"A":29,"B":4},"review_cycle":1,"final_approval":"approved"}}
```

Read that stream carefully. `evt_044` is a **real rate-limit failure in production**. A sub-agent died mid-revision. `evt_045` is the rescue — the orchestrator itself cross-checked the revised opinion's verbatim citations against the `korean-law` MCP and passed the revision. In a single-LLM system, that failure would have been "model returned an error" with nothing to learn from. Here, **the failure and its resolution are part of the permanent record**. That is what "the process is the product" actually means.

Because we reuse real specialized agents with their own source grading and fact-checking, this level of observability is free. We did not have to build an audit layer.

### 4. Case Replay — Not a 30-Second Demo

Most AI demos die after 30 seconds. This one doesn't.

Every processed case persists as `events.jsonl` (timeline) + per-agent `{agent}-result.md` and `{agent}-meta.json` + a final `opinion.md/.docx`. Phase 3 turns this data into a static JSON feed plus a static viewer (Case Replay): **no API key required, works offline, shareable and embeddable**. The legal process is the content; the visualization is just delivery.

### 5. Yes, It Burns a Lot of Tokens — On Purpose

A single case can consume 60K–170K tokens per specialist, plus orchestrator handoff overhead. In Phase 2.2 validation, one parallel run (PIPA ∥ GDPR) crossed 124K tokens; the Korean gaming law regression hit 170K. Phase 1 E2E, including the revision cycle, burned north of 200K tokens across all subagents. **That's not a bug — it's the design.**

Every subagent gets its own full 200K context window because we want it to do its actual job:

- Load its complete `CLAUDE.md` (role, principles, tool policies)
- Load every skill it might need
- Browse its full knowledge base
- Run live MCP queries against primary sources
- Have room to think across multiple turns and revisions

Context-sharing, aggressive truncation, or prompt-level shortcuts could cut token usage sharply — and would degrade output quality by roughly the same amount. **Quality-per-case is the objective function; token spend is the price we pay for it.** On Claude Code Max, the marginal dollar cost per call is zero; the real cost is wall-clock time (minutes per pipeline, not milliseconds) — and that is the cost we're choosing to absorb.

If you want a cheap legal chatbot, this is the wrong project. If you want a legal opinion you can defend with a full audit trail, that burn rate is the price of admission.

### Comparison Table

| Aspect | Single LLM | LangGraph / Agent SDK | **Jinju Law Firm** |
|--------|-----------|----------------------|---------------------|
| Multi-specialist reasoning | Simulated via prompt personas | Agents reimplemented inside the framework | **Real Claude Code agents, 100% reused** |
| Knowledge bases | Must be stuffed into context | Must be rebuilt for the framework | Each agent's native KB, untouched |
| MCP tools / live primary sources | Inherits the caller's tools only | Must be rewired server-side | Each agent keeps its own MCP config |
| Dedicated fact-checker | None, or bolted on | Custom implementation | Real agent (`second-review-agent`) with its own CLAUDE.md |
| Audit trail | Chat log | Custom logging layer | Native `events.jsonl` per case |
| Cross-jurisdiction debate | One model role-plays both sides | Sequential state-machine hops | Parallel dispatch + meta-verification fallback |
| Token cost per opinion | Low (10–30K) | Medium (30–80K) | **High (150–400K total across specialists)** |
| Quality ceiling | Limited by one model's "lawyer mode" | Limited by reimplementation fidelity | Limited by each specialist's real capability |
| Demo persistence | Chat dies with the tab | Requires a running server | Static `events.jsonl` + `opinion.md/.docx` files |

---

## How It Works

### System diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                          ORCHESTRATOR                                 │
│                (Claude Code main session, ~25-40K context)            │
│                                                                       │
│  1. Intake ──────────────────────────────────────────────────────────│
│     Generate CASE_ID, create output/{CASE_ID}/, init events.jsonl    │
│                                                                       │
│  2. Classify (skills/route-case.md)                                  │
│     jurisdiction × domain × task → specialist roster + pattern       │
│                                                                       │
│  3. Dispatch (Claude Code Agent tool) ──┐                            │
└──────────────────────────────────────────┼────────────────────────────┘
                                           │
                  ┌────────────────────────┼────────────────────────┐
                  ▼                        ▼                        ▼
        ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
        │   Subagent A     │    │   Subagent B     │    │   Subagent C     │
        │  (new Claude,    │    │  (new Claude,    │    │  (new Claude,    │
        │   fresh 200K)    │    │   fresh 200K)    │    │   fresh 200K)    │
        │                  │    │                  │    │                  │
        │  own CLAUDE.md   │    │  own CLAUDE.md   │    │  own CLAUDE.md   │
        │  own skills      │    │  own skills      │    │  own skills      │
        │  own KB          │    │  own KB          │    │  own KB          │
        │  own MCP tools   │    │  own MCP tools   │    │  own MCP tools   │
        │                  │    │                  │    │                  │
        │  writes:         │    │  writes:         │    │  writes:         │
        │  A-result.md     │    │  B-result.md     │    │  C-result.md     │
        │  A-meta.json     │    │  B-meta.json     │    │  B-meta.json     │
        └────────┬─────────┘    └────────┬─────────┘    └────────┬─────────┘
                 │                       │                       │
                 └───────────────────────┼───────────────────────┘
                                         ▼
┌──────────────────────────────────────────────────────────────────────┐
│                          ORCHESTRATOR                                 │
│                                                                       │
│  4. Handoff: reads only summary + key_findings from each agent       │
│     (full result.md referenced by path → context-efficient)          │
│                                                                       │
│  5. Final assembly (skills/deliver-output.md)                        │
│     opinion.md + opinion.docx + events.jsonl + sources.json          │
└──────────────────────────────────────────────────────────────────────┘
```

### Five-stage workflow

1. **Case intake** — Generate `CASE_ID`, create `output/{CASE_ID}/`, start `events.jsonl`.
2. **Classification** ([`skills/route-case.md`](skills/route-case.md)) — Jurisdiction × domain × task type → agent combination + collaboration pattern.
3. **Agent dispatch** (Claude Code `Agent` tool) — Each agent is an independent Claude instance, loads its own CLAUDE.md + skills + knowledge base + MCP, saves results to `{agent}-result.md` + `{agent}-meta.json`.
4. **Handoff** (if needed) — Only `summary` + `key_findings` are passed to the next agent; full `result.md` is referenced by path only, keeping orchestrator context efficient.
5. **Final assembly** ([`skills/deliver-output.md`](skills/deliver-output.md)) — `opinion.md` + `opinion.docx` + `events.jsonl` + `sources.json`.

### Three collaboration patterns

**Pattern 1 — Independent research → merge (parallel)**
Specialists from different jurisdictions/domains each research, then the writing agent merges. Validated in Phase 2.2.
```
Orchestrator → [PIPA-expert ∥ GDPR-expert] → legal-writing → second-review
```

**Pattern 2 — Sequential handoff** (Phase 1 default)
```
Orchestrator → general-legal-research → legal-writing → second-review
```

**Pattern 3 — Multi-round debate** (Phase 2.3, the killer feature)
For cross-jurisdiction questions where disagreement is likely. Two specialists exchange opinion → rebuttal → counter-rebuttal, then writing drafts a verdict.
```
Orchestrator → Agent A opinion → Agent B rebuttal → Agent A counter → writing verdict → review
```

### Pattern 3 walkthrough — a concrete scenario

Imagine this query lands on the orchestrator:

> "A Korean game company running its live-service servers in Frankfurt (AWS `eu-central-1`) wants to know if transferring Korean users' PII to those servers requires dual compliance under both K-PIPA (국외이전) and GDPR (international transfer), and how the two regimes interact when the same data subject is a Korean national playing from Korea but has their data processed in the EU."

No single LLM can genuinely argue both sides here. "Role-playing a PIPA expert" and "role-playing a GDPR expert" still come from the same underlying priors. A real answer needs two agents who genuinely don't share each other's knowledge bases, plus a third who adjudicates.

Pattern 3 routes it like this:

```
Round 1 ── Opinion
  ├── PIPA-expert    opens: "K-PIPA §28-8 국외이전 applies because the data
  │                          subject is Korean; Frankfurt processing
  │                          triggers cross-border transfer rules."
  │                          → emits ~8 Grade A sources
  │
  └── GDPR-expert    opens: "GDPR Art.3(2) extraterritorial scope kicks in
                             because the controller targets EU users; the
                             data being Korean-national doesn't immunize
                             processing on EU soil."
                             → emits ~7 Grade A sources

Round 2 ── Rebuttal
  ├── PIPA-expert    rebuts GDPR's extraterritorial argument ("targeting EU
  │                  users is not the operative fact — the game's EU servers
  │                  are infrastructure, not a market")
  │
  └── GDPR-expert    rebuts PIPA's scope ("Art.3(1) establishment-based
                     processing still applies if Frankfurt is a real branch,
                     even for non-EU data subjects")

Round 3 ── Verdict (legal-writing-agent)
  Drafts a "Both apply, here's how they interact" memo + a compliance
  checklist that satisfies both regimes.

Final ── second-review-agent signs off.
```

Key design choice: **the orchestrator never argues either side**. It only schedules rounds, records events, and calls the writing agent for the verdict. If one side hits a rate limit mid-debate, the meta-verification fallback (see `evt_045` in the sample case above) takes over that round. Currently [`skills/manage-debate.md`](skills/manage-debate.md) is a skeleton; full logic ships in Phase 2.3.

---

## What You Can Ask

The router in [`skills/route-case.md`](skills/route-case.md) is tuned for eight categories of question. Example queries in each:

**Korean gaming law** → `game-legal-research` (or `general-legal-research`) → writing → review

> "확률형 아이템 공급 확률 정보공개 의무 — 해외 관계회사가 한국 이용자 대상 게임을 운영할 때 국내대리인 지정 요건과 위반 시 리스크는?"

**Korean privacy law (PIPA)** → `PIPA-expert` → writing → review

> "의료기기 스타트업이 환자 음성 데이터를 AI 학습에 사용하려고 합니다. 가명처리만으로 충분한가요, 별도 동의가 필요한가요?"

**EU GDPR** → `GDPR-expert` → writing → review

> "Our SaaS product is based in Seoul but has ~12% EU users. Do we need a GDPR Art.27 representative, and what happens if we don't appoint one?"

**Cross-jurisdiction (parallel, Pattern 1)** → `[PIPA-expert ∥ GDPR-expert]` → writing → review

> "Korean fintech expanding to Germany wants to run KYC with biometric liveness detection. What's the combined K-PIPA + GDPR compliance picture, including DPIA triggers?"

**Cross-jurisdiction (debate, Pattern 3)** → `[PIPA ↔ GDPR ↔ game-legal]` → verdict → review

> "EU-based game publisher with Korean live-service servers — how do international transfer rules interact when the user is German but the data lands in Seoul?"

**Contract review** → `contract-review-agent` → writing (optional) → review

> "이 SaaS 계약서 한번 봐주세요. 한국법 준거에 맞지 않는 조항, 일방적 해지 조항, 자동 갱신 조항 잡아주고 협상 포인트 정리해주세요."

**Legal document translation** → `legal-translation-agent` → review

> "Please translate this Korean opinion letter into English, preserving legal-style tone and citation format."

**Generalist legal research** (when the router can't pin down a specialist) → `general-legal-research` → writing → review

> "상가임대차보호법상 권리금 보호 제외 사유에 대한 최근 3년 대법원 판례를 정리해주세요."

Not every category needs every agent. The router picks the minimal viable pipeline — a simple question may get `research → review` (writing skipped), a complex cross-jurisdiction question gets a three-way debate.

---

## Agent Roster

| # | Agent ID | Lawyer | Role | Phase | Jurisdiction |
|---|----------|--------|------|-------|--------------|
| 1 | `general-legal-research` | 김재식 | Generalist legal research across any Korean law domain | Phase 1 ✓ | KR |
| 2 | `legal-writing-agent` | 한석봉 | Drafts opinions in Korean law-firm memorandum format (style guide enforced) | Phase 1 ✓ | KR (Korean) |
| 3 | `second-review-agent` | 반성문 (Partner) | QA partner — verbatim checks citations against primary sources via MCP, issues Critical/Major/Minor comments | Phase 1 ✓ | KR |
| 4 | `PIPA-expert` | 정보호 | Korean Personal Information Protection Act (개인정보보호법) specialist with dedicated PIPA/PIPC knowledge base | Phase 2 ✓ | KR |
| 5 | `GDPR-expert` | 김덕배 | EU General Data Protection Regulation specialist | Phase 2 ✓ | EU |
| 6 | `game-legal-research` | 심진주 | International gaming law specialist (loot boxes, cross-border live services, content regulation) | Phase 2 ✓ | KR + International |
| 7 | `contract-review-agent` | 고덕수 | Commercial contract review (SaaS, NDA, employment, license) under Korean law | Phase 2 | KR |
| 8 | `legal-translation-agent` | 변혁기 | Legal document translation (KR ↔ EN), tone and citation format preserved | Phase 2 | KR / EN |

Each agent lives in its own GitHub repository. `setup.sh` auto-clones them, or creates local symlinks under `agents/` during development. **The orchestrator never modifies a subordinate agent's `CLAUDE.md`** — that's what "100% reuse" means in practice.

> Two briefing-style agents (`game-legal-briefing`, `game-policy-briefing`) exist as standalone Python apps outside this orchestrator's scope and are intentionally not listed above.

---

## Sample Case Walkthrough

This is the same case as the [Quick Look](#quick-look-a-real-case), unpacked properly. All files referenced are on disk under [`output/20260410-012238-391f/`](output/20260410-012238-391f/) — you can `cat` them yourself.

### The query

> "한국 게임산업법의 확률형 아이템(가챠) 규제에 대한 법률 의견서를 작성해줘"

A Korean gaming company wants an opinion letter on Korea's gacha (loot-box) regulatory regime. This is the kind of question a real mid-size Korean law firm would get from a game publisher client.

### Classification

The orchestrator inspected the question and emitted:

```json
{
  "jurisdiction": ["KR"],
  "domain": "game_regulation",
  "task": "drafting",
  "complexity": "compound",
  "pipeline": ["general-legal-research", "legal-writing-agent", "second-review-agent"]
}
```

Pattern 2 (sequential handoff). Pattern 1 wasn't needed because only one jurisdiction is involved. Pattern 3 wasn't triggered because there's no cross-jurisdiction disagreement to adjudicate.

### Stage 1 — Research (김재식, general-legal-research)

14 primary sources pulled from `korean-law` MCP, including:

- 게임산업법 §2 xi (definition of "확률형 아이템")
- 게임산업법 §33 ② (disclosure duty, 법률 제19877호, in force 2024-03-22)
- 시행령 §19조의2 + 별표 3의2 (7 categories × 3 display areas rule)
- 게임산업법 §38 ⑨⑩⑪ (corrective recommendation → corrective order enforcement chain)
- 게임산업법 §45 xi (2-year imprisonment / ₩20M fine for non-compliance with a corrective order)
- 게임산업법 §48 (administrative fines — **note: §33② violations are NOT listed**, meaning enforcement must route through the §38 corrective-order path)
- 게임산업법 §31조의2 (overseas operator domestic-representative duty)
- 전자상거래법 §21 ①i (false/deceptive consumer inducement prohibition)
- **KFTC en-banc decision 2024-01-05, case 2021전자1052** — Nexon Maplestory Cube case, **₩11.642 billion fine** (the largest e-commerce-law penalty in Korean history)
- KFTC 3rd-commission decision 2018-05-14, Nexon (earlier precedent)

11 key findings, including the load-bearing observation that **§33② violations are not listed in the direct administrative fine provision §48**, meaning enforcement must go through a §38 corrective order → §45 criminal penalty two-step — a structural detail that changes the client's risk picture entirely.

See [`research-result.md`](output/20260410-012238-391f/research-result.md) (37 KB) and [`research-meta.json`](output/20260410-012238-391f/research-meta.json) (10 KB).

### Stage 2 — Drafting (한석봉, legal-writing-agent)

한석봉 drafted a standard Korean law-firm memorandum:

- MEMORANDUM header with 수신 / 참조 / 발신 / 제목 table
- Executive summary (결론 요약) — 3 substantive paragraphs
- Disclaimer
- 5-item factual assumptions block (사실관계 가정)
- 7-item issue analysis (검토의견) corresponding to the client's 7 questions
- Risk matrix (리스크 평가) with High/Medium/Low grading
- 8-item recommendations (권고사항)
- Conclusion + signature block

See [`opinion-v1.md`](output/20260410-012238-391f/opinion-v1.md) (39 KB) for the v1 draft before review.

### Stage 3 — Review (반성문, Partner) — the catch

The partner returned `approved_with_revisions` with **9 comments: 2 Critical, 3 Major, 4 Minor**. These are not generic style nits. Two of them, verbatim from [`review-meta.json`](output/20260410-012238-391f/review-meta.json):

> **[Critical #1]** Block quote of 게임산업법 §38 ⑩⑪ in the draft does not match the current statute text (법률 제19877호). Receiver scope is `제9항` in the draft but `제7항부터 제9항까지` in the actual statute; the verb phrases are `이행·보고` in the draft but `조치 완료·통보` in the actual statute; the recipient is stated as "문화체육관광부장관만" but the actual statute says "게임물관리위원회위원장 또는 문화체육관광부장관"; the §11 proviso is drafted as two descriptive clauses but the statute enumerates three items. **Block quotes must be verbatim.**

> **[Critical #2]** 게임산업법 §31조의2 (overseas operator → domestic representative duty) is described in the draft as applying to "all overseas operators," but the actual statute limits it to "those meeting thresholds defined by Presidential Decree based on user count, revenue, etc." This over-generalization would mislead small overseas indie developers and Steam distributors into thinking they're in scope when they may not be.

That is the kind of catch a junior associate would miss and a senior partner would flag. This system caught it because **`second-review-agent` runs `korean-law` MCP queries against the citations in the draft, verbatim**. It's not "the LLM thinks this looks wrong." It's "the primary-source text in §38⑩ does not match the draft's block quote — here are the exact tokens that differ."

The partner's 9 comments also included:

- **[Major]** §47 양벌규정 was hand-waved as "usually these regulatory statutes have dual liability" instead of citing §47 directly, which the partner flagged as a hedged under-claim.
- **[Major]** Risk matrix rated the 전자상거래법 fine as the only "High" risk but recommendations still led with 게임산업법 compliance — inconsistent priority ordering.
- **[Major]** A civil class-action pending at the Seoul Central District Court was tagged `[Unverified]` in the research but got a "Medium" risk rating in the table — unverified facts shouldn't carry quantitative risk grades.
- **[Minor]** Three different enforcement dates were listed side by side (2024-03-22 / 2025-10-23 / 2026-03-24), which confused readers — the partner wanted a single canonical baseline date.
- **[Minor]** The 8 recommendations lacked "immediate / short-term / medium-term" time markers.

See [`review-result.md`](output/20260410-012238-391f/review-result.md) (23 KB) for the full comment set with line-level references.

### Stage 4 — Revision + the meta-verification rescue

The orchestrator emitted `revision_requested` (cycle 1/2) and dispatched 한석봉 again. Mid-revision:

```
evt_044  error  rate_limit  "Anthropic usage limit hit, reset 6am Asia/Seoul"
```

Without a fallback, the case would now be stuck until tomorrow morning. The orchestrator instead did something the design doc did not anticipate:

```
evt_045  verbatim_verified  verifier=orchestrator_meta
         reason: "review-agent token limit hit; meta verification via korean-law MCP"
         critical_pass: 2
         major_pass: 1
         minor_diffs: 1
         final_status: approved
```

The orchestrator itself read the revised draft, queried `korean-law` MCP for the §38, §31-2, §47 primary-source text, and did the verbatim diff directly. See [`verbatim-verification.md`](output/20260410-012238-391f/verbatim-verification.md) (5 KB) for the full rescue log.

This pattern was not in the original design. It emerged under pressure during the E2E test. It is now part of how the system handles rate-limited sub-agents — and will be a load-bearing fallback for Pattern 3 debates, where a specialist going down mid-argument used to be fatal.

### Stage 5 — DOCX generation

```
evt_046  docx_generated  opinion.docx  (56519 bytes, 138 paragraphs, 5 tables)
                          fonts: latin=Times New Roman 11pt, cjk=맑은 고딕 11pt
```

Dual-font output conforming to [`docs/ko-legal-opinion-style-guide.md`](docs/ko-legal-opinion-style-guide.md) §11 via [`scripts/md-to-docx.py`](scripts/md-to-docx.py). The Korean legal profession expects specific typography on printed opinions (Times New Roman for Latin characters, 맑은 고딕 for Hangul, explicit `eastAsia` XML attribute so Word on Windows doesn't re-shape the CJK runs) — this isn't cosmetic, it's part of the deliverable contract.

### Final numbers

- **47 events** in `events.jsonl`
- **33 sources** total (29 Grade A + 4 Grade B + 0 C + 0 D)
- **14 sources** cited in the final opinion (the 33 total includes research-stage candidates that were cut in drafting)
- **1 revision cycle** (of 2 allowed)
- **1 meta-verification rescue**
- **Final approval:** approved

---

## Measured Performance

Not a marketing claim — these are the actual numbers from `output/` folders you can re-read yourself.

### Phase 1 E2E (Pattern 2 sequential, with revision)

| Metric | Value |
|--------|-------|
| Case | [`20260410-012238-391f`](output/20260410-012238-391f/) |
| Pipeline | `general-legal-research → legal-writing → second-review → revision 1` |
| Events | 47 |
| Total sources | 33 (29 Grade A / 4 Grade B / 0 C / 0 D) |
| Revision cycles | 1 of 2 max |
| Notable | Rate-limit survived via orchestrator meta-verification (`evt_045`) |
| Final deliverable | `opinion.docx` (56 KB, 138 paragraphs, 5 tables) |
| Approval | approved |

### Phase 2.2 mini E2E runs

| Test | Pipeline | Pattern | Sources | Grade A/B/C | Tokens | Wall time | Notes |
|------|----------|---------|---------|-------------|--------|-----------|-------|
| **T1** | `PIPA-expert` solo | direct | 9 | 8 / 1 / 0 | ~60K | 582s | [`test-T1-20260410-121640/`](output/test-T1-20260410-121640/). Exposed a `library/grade-b/` KB gap, since resolved. |
| **Regression** | `game-legal-research` solo | direct | 32 | 25 / 0 / 7 | ~170K | 797s | [`test-regression-20260410-121640/`](output/test-regression-20260410-121640/). Specialist vs v1 generalist baseline: −3% comparable, 11/11 topic coverage. |
| **T2** | `[PIPA ∥ GDPR]` parallel | Pattern 1 | 26 | 26 / 0 / 0 | ~124K | 334s | [`test-T2-20260410-121640/`](output/test-T2-20260410-121640/). Both branches executed truly in parallel; 5-dimension cross-jurisdiction tagging intact. |

### Phase 2.1 Specialist Routing — [`skills/route-case.md`](skills/route-case.md) v2

- Grew from 153 to 637 lines: 8-agent roster, multi-domain 3-way matrix, shared injection block, events schema appendix, token budget table.
- Fully addressed all 13 issues + 4 critical FM gaps raised by `/plan-eng-review`.

### Phase 2.2 follow-up: PIPA-expert `library/grade-b/` expansion — complete

- **30 landmark items** across 6 topics (consent, third-party provision, safety measures/breach, cross-border transfer, pseudonymization, sensitive/unique identifiers).
- 20 legal interpretations (법제처 법령해석례) + 10 Supreme Court precedents (e.g., 2013두2945, 2015다24904, 2022두68923, 2024다210554).
- **Scope change from original plan:** the original plan was 20 PIPC decisions + 10 precedents, but `get_pipc_decision_text` MCP endpoint outage forced substitution with 20 legal interpretations. `pipc-decisions/` remains pending for endpoint recovery (`source-registry.json` documents the reason).
- All files `verification_status: VERIFIED` with verbatim MCP source text. See [kipeum86/PIPA-expert@6b8137c](https://github.com/kipeum86/PIPA-expert/commit/6b8137c).

### In progress / pending

- **Real debate logic in [`skills/manage-debate.md`](skills/manage-debate.md)** (Pattern 3) — currently a skeleton.
- **Multi-round debate E2E** (to prove the killer feature) — candidate scenario: the Korean game company with EU servers described under [Pattern 3 walkthrough](#pattern-3-walkthrough--a-concrete-scenario).
- **Case Replay MVP** (Next.js static viewer) — independent track; sample data ready (the Phase 1 E2E case + 3 mini E2E runs).
- **PIPC decision re-collection** — blocked on `get_pipc_decision_text` MCP endpoint recovery.

---

## Event Taxonomy

`events.jsonl` is an append-only JSONL stream. One event per line. Key types used today:

| Type | Emitted by | When | Key data |
|------|-----------|------|----------|
| `case_received` | orchestrator | On intake | `query`, `case_id` |
| `case_classified` | orchestrator | After routing decision | `jurisdiction`, `domain`, `task`, `complexity`, `pipeline` |
| `agent_assigned` | orchestrator | Before each dispatch | `agent_id`, `name`, `role` |
| `source_graded` | subagent | When a source is cited | `source`, `grade` (A/B/C/D), `citation` |
| `research_completed` | research agent | End of research stage | `output_file`, `sources_count`, `key_findings_count` |
| `writing_completed` | writing agent | End of drafting | `output_file`, `sources_count` |
| `review_completed` | review agent | End of review | `approval` (approved / approved_with_revisions / rejected), `comments_count` |
| `revision_requested` | orchestrator | When review returns `approved_with_revisions` | `cycle`, `max_cycles`, `critical`, `major`, `minor` |
| `error` | any agent | On failure | `error_type`, `message`, `attempt`, `max_attempts` |
| `verbatim_verified` | orchestrator | Meta-verification fallback | `verifier`, `reason`, `critical_pass`, `final_status` |
| `debate_round_start` / `debate_round_end` | orchestrator | Phase 2.3 — per debate round | `round`, `participants` |
| `docx_generated` | orchestrator | After final assembly | `output`, `size_bytes`, `tables`, `paragraphs`, `fonts` |
| `final_output` | orchestrator | Last event | `total_sources`, `grade_distribution`, `final_approval`, `agents_invoked` |

Sample line (actual line from the Phase 1 E2E case — the Nexon source grading):

```json
{"id":"evt_014","ts":"2026-04-09T16:53:26Z","agent":"general-legal-research","type":"source_graded","data":{"source":"공정거래위원회 2024.1.5. 전원회의 의결 ㈜넥슨코리아의 전자상거래소비자보호법 위반행위에 대한 건 (메이플스토리 큐브·블랙큐브·버블파이터 매직바늘 확률 조작·은폐 4건, 과징금 116억 4,200만원)","grade":"A","citation":"공정위 전원회의 의결 사건번호 2021전자1052, 2024.1.5. (결정문 ID 17235)"}}
```

Because it's append-only JSONL, you can `tail -f` a live case or diff two cases line by line. This stream is the input format for the Phase 3 Case Replay viewer.

---

## Quickstart

### 1. Prerequisites

- [Claude Code](https://docs.claude.com/claude-code) installed (Max subscription recommended — no per-call API costs)
- macOS / Linux (zsh or bash)
- Python 3.10+ (for DOCX conversion)
- [Korean Open Law API](https://open.law.go.kr/) account (`LAW_OC` key)

### 2. Clone and set environment

```bash
git clone https://github.com/kipeum86/legal-agent-orchestrator.git
cd legal-agent-orchestrator

# Open Law API key (required every shell session — Claude Code does NOT auto-load .env)
export LAW_OC=your_law_oc_key
```

### 3. Install agents

```bash
./setup.sh
```

Clones the 8 subordinate agents from GitHub, or creates symlinks from local copies during development.

### 4. Launch Claude Code

```bash
claude
```

Claude Code auto-loads `CLAUDE.md` (the orchestrator system prompt) and `.mcp.json` (korean-law + kordoc MCP servers). Ask a legal question, and the orchestrator will classify it and dispatch the appropriate pipeline.

### 5. Check results

```
output/{CASE_ID}/
├── events.jsonl            # full timeline (input for Case Replay)
├── {agent}-result.md       # per-agent detailed analysis
├── {agent}-meta.json       # summary + source grading
├── opinion.md              # final opinion (markdown)
└── opinion.docx            # final opinion (DOCX, per style guide §11)
```

---

## Project Structure

```
legal-agent-orchestrator/
├── CLAUDE.md                           # orchestrator system prompt
├── .mcp.json                           # MCP server config (korean-law + kordoc)
├── setup.sh                            # agent management (clone/link/status)
├── skills/
│   ├── route-case.md                   # classification + pipeline selection (v2, 637 lines)
│   ├── deliver-output.md               # final assembly
│   └── manage-debate.md                # Phase 2.3 debate logic (skeleton)
├── scripts/
│   └── md-to-docx.py                   # DOCX conversion (style guide §11)
├── agents/                             # 8 subordinate agents (symlinks or clones)
├── output/                             # case artifacts ({case-id}/)
│   ├── 20260410-012238-391f/           # Phase 1 E2E sample case
│   ├── test-T1-20260410-121640/        # Phase 2.2 T1 (PIPA solo)
│   ├── test-T2-20260410-121640/        # Phase 2.2 T2 (PIPA ∥ GDPR)
│   └── test-regression-20260410-121640/
└── docs/
    ├── design.md                       # design doc (office-hours APPROVED 9/10)
    ├── ko-legal-opinion-style-guide.md # canonical Korean opinion style guide
    ├── session-log-*.md                # dev session logs
    └── notes/
        └── architecture-defense.md     # source material for this README
```

---

## Tech Stack

- **Runtime**: Claude Code (Anthropic CLI)
- **Agent dispatch**: Claude Code `Agent` tool → independent 200K-context subagents
- **MCP servers**:
  - `korean-law` — Korean Ministry of Government Legislation (법제처) public API wrapper; Grade A primary sources (statutes, precedents, legal interpretations, constitutional court decisions)
  - `kordoc` — Korean court judgment retrieval
- **Skills system**: markdown procedure docs (`skills/*.md`) executed by the orchestrator as subroutines
- **Event logging**: JSONL (append-only, replayable)
- **Output format**: Markdown → DOCX (python-docx, dual-font: Times New Roman + 맑은 고딕)

---

## Roadmap

- [x] **Phase 0** — Tech spike (`Agent` tool / MCP / parallel execution — 6/8 PASS)
- [x] **Phase 1** — 3-agent baseline pipeline (research → writing → review) + E2E
- [x] **Phase 2.1** — Specialist routing (8-agent roster, multi-domain matrix, events schema)
- [x] **Phase 2.2** — Pattern 1 parallel dispatch (3 mini E2E runs validated)
- [x] **Phase 2.2 follow-up** — PIPA-expert `library/grade-b/` expansion (30 items)
- [ ] **Phase 2.3** — Pattern 3 multi-round debate (the killer feature)
- [ ] **Phase 3** — Case Replay (Next.js static viewer, dark-theme war-room UI)
- [ ] Public release of the 8 subordinate agents + license audit
- [ ] Classification regression test harness (route-case.md few-shot auto-validation)

---

## FAQ

**Is this production-ready?**
No. This is a portfolio / research project showing an unusual architecture that works end-to-end. The Phase 1 E2E case is real — the opinion draft is a real memorandum that a Korean lawyer could plausibly edit and deliver — but using it for actual client work would require (a) explicit disclaimer to the client that an AI system drafted it, (b) human review by an admitted attorney, (c) jurisdiction-specific disclaimers, and (d) handling of privileged information under your firm's own engagement policies.

**How does it handle client confidentiality?**
The orchestrator and subagents all run locally on your machine under your own Claude Code session. No data leaves Anthropic's API boundary — there's no intermediate SaaS. That said: Claude Code itself sends prompts to Anthropic for inference. Whether that's acceptable for a given matter depends on your firm's engagement policies. For sensitive matters, confirm with your IT / compliance team first. This repo intentionally gitignores `output/`, `agents/`, and `.env` so case files and API keys don't leak into commits.

**Why not just use Harvey / Casetext / commercial legal AI?**
Commercial tools are closed. You can't see which sources were cited, you can't replay how the answer was constructed, and you can't swap in a specialist agent you wrote yourself. This project sacrifices polish for transparency. If you need a battle-tested product today, use Harvey. If you want to understand, modify, or audit how multi-agent legal reasoning works, start here.

**Can it work for jurisdictions other than Korea / EU?**
Yes, but you would need to provide the agents. The orchestrator is jurisdiction-agnostic; what makes the current setup Korea/EU-focused is that the underlying specialist agents (`PIPA-expert`, `GDPR-expert`, `game-legal-research`, `korean-law` MCP) cover those jurisdictions. Adding a `US-privacy-expert` or `Japan-corporate-expert` would mean writing that agent as a standalone Claude Code project (with its own CLAUDE.md, skills, KB, MCP) and then adding one row to [`skills/route-case.md`](skills/route-case.md). The orchestrator contract is deliberately thin.

**What happens if an agent fails mid-pipeline?**
Depends on the failure. Rate-limit errors on research agents: retried once. Rate-limit on writing/review: the orchestrator attempts meta-verification directly via MCP (as happened in the Phase 1 E2E — see `evt_044` / `evt_045`). Unrecoverable errors: the case file is preserved, `events.jsonl` records the failure point, and the user gets a partial-output report. No silent drops.

**How much does one opinion cost?**
On Claude Code Max ($100/mo unlimited): nothing incremental. The Phase 1 E2E case consumed north of 200K tokens across all subagents but zero dollars of marginal cost. On metered API pricing: ballpark $3–10 per opinion depending on complexity and revision cycles. The real cost is wall-clock time — 5 to 15 minutes per pipeline with no parallelism, less with Pattern 1.

**Can I add my own specialist agent?**
Yes. Write it as a standalone Claude Code agent (any structure — CLAUDE.md, skills, KB, MCP of your choice), then either (a) drop it under `agents/` as a git submodule or (b) symlink it from its own location. Add one row to [`skills/route-case.md`](skills/route-case.md) so the router knows when to call it. No orchestrator changes needed. The design is intentionally plugin-shaped.

---

## References

| Document | Description |
|----------|-------------|
| [docs/design.md](docs/design.md) | Design doc (office-hours 6-round adversarial review, APPROVED 9/10) |
| [docs/notes/architecture-defense.md](docs/notes/architecture-defense.md) | Source material for this README — extended "why this architecture" defense |
| [docs/ko-legal-opinion-style-guide.md](docs/ko-legal-opinion-style-guide.md) | Canonical Korean legal opinion style guide (force-injected into every Korean agent call) |
| [skills/route-case.md](skills/route-case.md) | Classification + pipeline selection logic (v2, 637 lines) |
| [skills/deliver-output.md](skills/deliver-output.md) | Final assembly procedure |
| [skills/manage-debate.md](skills/manage-debate.md) | Phase 2.3 debate logic (skeleton) |
| [resume.md](resume.md) | Development status (cross-session handoff doc) |
| [output/20260410-012238-391f/](output/20260410-012238-391f/) | The sample case referenced throughout this README |

---

## License

Licensed under the **Apache License 2.0** — see [LICENSE](LICENSE).

Subordinate agents are hosted in separate repositories with their own licenses. Legal data comes from Korean Ministry of Government Legislation public APIs and court judgments (public-domain government works).
