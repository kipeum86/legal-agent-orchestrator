# Jinju Law Firm Orchestrator · 법무법인 진주

**한국어:** [README.ko.md](README.ko.md)

> An AI law firm running on Claude Code. Eight specialist lawyer agents collaborate like a real firm to produce legal opinions with full audit trails.

![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)
![Runtime: Claude Code](https://img.shields.io/badge/Runtime-Claude_Code-orange)
![MCP: korean-law](https://img.shields.io/badge/MCP-korean--law-green)
![Status: Phase 2.2 validated](https://img.shields.io/badge/Status-Phase_2.2_validated-brightgreen)

**Status:** Phase 1 E2E passed · Phase 2.1/2.2 validated with 3 mini runs · Phase 2.3 (multi-round debate) in progress.

---

## Overview

Most "legal AI" products are a single LLM you throw questions at. This one is different.

An **orchestrator plays the role of managing partner**. It classifies each incoming question, routes it to the right specialist lawyer, and picks the collaboration pattern (sequential handoff / parallel research / multi-round debate). The eight subordinate agents are real Claude Code agents — each with its own jurisdiction, knowledge base, and MCP tools — and this project reuses them **100% unmodified**.

Every step is logged to `events.jsonl`, producing a replayable artifact. Which lawyer was assigned, which sources (Grade A/B/C) were cited, what the fact-checker flagged — it's all visible.

---

## How It Works

Send a legal question. The orchestrator routes it, the specialists do the work, and you get an opinion. Here is what happened on one real query — full files at [`samples/20260410-012238-391f/`](samples/20260410-012238-391f/):

> **Query:** "한국 게임산업법의 확률형 아이템(가챠) 규제에 대한 법률 의견서를 작성해줘"

| Stage | Agent | What it did | Output |
|-------|-------|-------------|--------|
| **1. Research** | 김재식 · `general-legal-research` | Pulled 14 primary sources from `korean-law` MCP — statute text, the KFTC ₩11.6B Nexon decision, enforcement path | [`research-result.md`](samples/20260410-012238-391f/research-result.md) |
| **2. Drafting** | 한석봉 · `legal-writing-agent` | Wrote a Korean law-firm memorandum (summary → disclaimer → 7 issue analyses → risk matrix → 8 recommendations) | [`opinion-v1.md`](samples/20260410-012238-391f/opinion-v1.md) |
| **3. Review** | 반성문 · `second-review-agent` | Ran verbatim MCP checks on every block quote, returned **9 comments (2 Critical + 3 Major + 4 Minor)** — including a real statute-text mismatch | [`review-result.md`](samples/20260410-012238-391f/review-result.md) |
| **4. Revision rescue** | `legal-writing-agent` + orchestrator | Writer hit a rate limit mid-revision; orchestrator took over and cross-checked the fixed citations directly against `korean-law` MCP | [`verbatim-verification.md`](samples/20260410-012238-391f/verbatim-verification.md) |
| **5. Delivery** | orchestrator | Assembled final DOCX (Times New Roman + 맑은 고딕 per the Korean legal style guide) | [`opinion.docx`](samples/20260410-012238-391f/opinion.docx) |

**Result:** 33 sources (29 Grade A + 4 Grade B) · 47 events · 1 revision cycle · approved.

Full event timeline → [`events.jsonl`](samples/20260410-012238-391f/events.jsonl) · Agent-by-agent deep dive for all 4 sample cases → [`samples/README.md`](samples/README.md).

### System diagram

```mermaid
flowchart TB
    Q([Incoming legal question])
    Q --> I

    subgraph OrcTop["Orchestrator · Claude Code main session (~25-40K ctx)"]
        direction TB
        I["1 · Intake<br/>generate CASE_ID<br/>init events.jsonl"]
        C["2 · Classify<br/><i>skills/route-case.md</i><br/>jurisdiction × domain × task"]
        D["3 · Dispatch<br/>Claude Code Agent tool"]
        I --> C --> D
    end

    D --> SA
    D --> SB
    D --> SC

    subgraph Subs["Subagents · independent Claude instances, each with fresh 200K ctx"]
        direction LR
        SA["Subagent A<br/>own CLAUDE.md + skills + KB + MCP"]
        SB["Subagent B<br/>own CLAUDE.md + skills + KB + MCP"]
        SC["Subagent C<br/>own CLAUDE.md + skills + KB + MCP"]
    end

    SA -.->|"A-result.md<br/>A-meta.json"| H
    SB -.->|"B-result.md<br/>B-meta.json"| H
    SC -.->|"C-result.md<br/>C-meta.json"| H

    subgraph OrcBot["Orchestrator · assembly"]
        direction TB
        H["4 · Handoff<br/>summary + key_findings only<br/>result.md referenced by path"]
        F["5 · Final assembly<br/><i>skills/deliver-output.md</i>"]
        H --> F
    end

    F --> OUT([opinion.md + opinion.docx<br/>events.jsonl + sources.json])
```

### Three collaboration patterns

| Pattern | Shape | When | Status |
|---------|-------|------|--------|
| **1 · Parallel research → merge** | `[A ∥ B] → writing → review` | Cross-domain or cross-jurisdiction that doesn't need debate (e.g. PIPA + GDPR combined compliance) | ✅ validated Phase 2.2 |
| **2 · Sequential handoff** | `A → writing → review` | Single-jurisdiction or focused domain work (Phase 1 default) | ✅ validated Phase 1 E2E |
| **3 · Multi-round debate** | `A → B rebuts → A counters → writing verdict → review` | Cross-jurisdiction questions where specialists are likely to disagree | 🚧 Phase 2.3 (skeleton) |

Pattern 3 is the killer feature — two specialists from different jurisdictions, each with their own knowledge base, actually argue. No single LLM can genuinely produce that kind of depth because "role-playing a PIPA expert" and "role-playing a GDPR expert" come from the same priors. Two real agents genuinely don't share context.

---

## Why This Architecture

The standard playbook for multi-agent systems is to wrap a framework (LangGraph, CrewAI, AutoGen, Claude Agent SDK) in a web server. Using Claude Code itself as the orchestration runtime is non-standard. Four misconceptions usually come up first:

### 1. "Doesn't stuffing 8 agents into one orchestrator kill performance?"

No — that's a misconception about how Claude Code's `Agent` tool works.

Each subagent is a **completely independent new Claude instance** with its own fresh 200K context window. The orchestrator doesn't carry their weight — it just coordinates.

```mermaid
flowchart LR
    O["Orchestrator<br/>200K ctx<br/><i>actual ~25-40K</i>"]
    A["Subagent A<br/><i>fresh 200K</i>"]
    B["Subagent B<br/><i>fresh 200K</i>"]
    C["Subagent C<br/><i>fresh 200K</i>"]
    O -->|Agent tool call| A
    O -->|Agent tool call| B
    O -->|Agent tool call| C
    A -.->|result file| O
    B -.->|result file| O
    C -.->|result file| O
```

The orchestrator spends tokens only on classification, dispatch prompts, and reading result summaries (~25–40K total). Each specialist runs at full capacity with its own CLAUDE.md, skills, knowledge base, and MCP tools. **This is the opposite of "stuffing" — it's the most context-efficient multi-agent architecture possible.**

### 2. "Why not LangGraph or Agent SDK?"

Wrapping existing Claude Code agents in a web framework loses 40–50% of their capability: MCP breaks, the skills system needs reimplementation, knowledge-base browsing changes. You end up with a pretty demo producing legal opinions at half quality.

We inverted the tradeoff: **Claude Code as the runtime, agents preserved 100% intact, visualization decoupled into static Case Replay.** Real legal work, not a demo.

### 3. The Process Is the Product

Harvey AI is a black box. You get an answer; you don't know how.

Jinju Law Firm is the opposite. Which lawyer was assigned, which sources were consulted, what the fact-checker flagged, how revision cycles resolved — all visible in `events.jsonl`, one line per event.

Failure modes are in the permanent record too. In the [Phase 1 E2E case](samples/20260410-012238-391f/events.jsonl), a mid-revision rate-limit error (`evt_044`) triggered an orchestrator-level meta-verification rescue (`evt_045`). In a single-LLM system, that failure would have been a dead chat tab. Here it's a typed event in an append-only log. **That's what "the process is the product" means in practice.**

### 4. Yes, it burns a lot of tokens — on purpose

A single case can consume 60K–170K tokens per specialist. Phase 1 E2E burned north of 200K across all subagents. That's not a bug.

Every subagent gets its own full 200K context window so it can load its CLAUDE.md, every skill it needs, its knowledge base, and run live MCP queries against primary sources. Context-sharing and aggressive truncation could cut token usage sharply — and would degrade quality by roughly the same amount. **Quality-per-case is the objective function; token spend is the price we pay for it.** On Claude Code Max, the marginal dollar cost is zero. The real cost is wall-clock time.

If you want a cheap legal chatbot, this is the wrong project. If you want a defensible legal opinion with a full audit trail, that burn rate is the price of admission.

### Comparison

| Aspect | Single LLM | LangGraph / Agent SDK | **Jinju Law Firm** |
|--------|-----------|----------------------|---------------------|
| Multi-specialist reasoning | Prompt personas | Agents reimplemented in the framework | **Real Claude Code agents, 100% reused** |
| Knowledge bases | Stuffed into context | Rebuilt for the framework | Each agent's native KB, untouched |
| MCP / primary sources | Inherits caller's tools | Rewired server-side | Each agent keeps its own MCP config |
| Fact-checker | None, or bolted on | Custom implementation | Real `second-review-agent` with its own CLAUDE.md |
| Audit trail | Chat log | Custom logging layer | Native `events.jsonl` per case |
| Cross-jurisdiction debate | One model playing both sides | Sequential state machine | Parallel dispatch + meta-verification fallback |
| Demo persistence | Dies with the tab | Requires a running server | Static files you can `cat` |

---

## Agent Roster

| # | Agent ID | Lawyer | Jurisdiction | Role |
|---|----------|--------|--------------|------|
| 1 | `general-legal-research` | 김재식 | KR | Generalist legal research |
| 2 | `legal-writing-agent` | 한석봉 | KR | Drafts opinions in Korean law-firm memorandum format |
| 3 | `second-review-agent` | 반성문 (Partner) | KR | QA partner — verbatim MCP checks, issues Critical/Major/Minor comments |
| 4 | `PIPA-expert` | 정보호 | KR | Korean Personal Information Protection Act specialist |
| 5 | `GDPR-expert` | 김덕배 | EU | EU data protection law specialist |
| 6 | `game-legal-research` | 심진주 | KR + international | Gaming law specialist (loot boxes, live services, content regulation) |
| 7 | `contract-review-agent` | 고덕수 | KR | Commercial contract review |
| 8 | `legal-translation-agent` | 변혁기 | KR / EN | Legal document translation, tone preserved |

Each agent lives in its own GitHub repository. `setup.sh` auto-clones them. **The orchestrator never modifies a subordinate agent's `CLAUDE.md`** — that's what "100% reuse" means in practice.

---

## Quickstart

```bash
# 1. Prerequisites: Claude Code (Max subscription recommended), Python 3.10+,
#    Korean Open Law API account (LAW_OC key)

git clone https://github.com/kipeum86/legal-agent-orchestrator.git
cd legal-agent-orchestrator

# 2. Set API key (every shell session — Claude Code does NOT auto-load .env)
export LAW_OC=your_law_oc_key

# 3. Install the 8 subordinate agents
./setup.sh

# 4. Launch Claude Code; CLAUDE.md and .mcp.json auto-load
claude
```

Then ask a legal question. Results land under `output/{CASE_ID}/` with `events.jsonl`, per-agent `result.md`/`meta.json`, and final `opinion.md` + `opinion.docx`.

---

## Status & Roadmap

- [x] **Phase 0** — Tech spike (Agent tool, MCP, parallel execution)
- [x] **Phase 1** — 3-agent baseline pipeline + E2E (see [sample case](samples/20260410-012238-391f/))
- [x] **Phase 2.1** — Specialist routing ([`skills/route-case.md`](skills/route-case.md) v2, 637 lines)
- [x] **Phase 2.2** — Pattern 1 parallel dispatch (3 mini runs validated — see [`samples/README.md`](samples/README.md))
- [x] **Phase 2.2 follow-up** — PIPA-expert `library/grade-b/` expansion (30 landmark items: 20 legal interpretations + 10 Supreme Court precedents, [kipeum86/PIPA-expert@6b8137c](https://github.com/kipeum86/PIPA-expert/commit/6b8137c))
- [ ] **Phase 2.3** — Pattern 3 multi-round debate (the killer feature)
- [ ] **Phase 3** — Case Replay (Next.js static viewer)
- [ ] Public release of the 8 subordinate agents

---

## FAQ

**Is this production-ready?**
No. This is a portfolio/research project. The Phase 1 E2E opinion draft is a real memorandum that a Korean lawyer could edit and deliver, but using it for actual client work requires human review by an admitted attorney, jurisdiction disclaimers, and your firm's engagement policies.

**How does it handle client confidentiality?**
Everything runs locally on your machine under your own Claude Code session. No intermediate SaaS. Claude Code itself sends prompts to Anthropic for inference — whether that's acceptable for a given matter depends on your firm. `output/`, `agents/`, and `.env` are gitignored so case files and API keys don't leak into commits.

**Can I add my own specialist agent?**
Yes. Write it as a standalone Claude Code agent, drop it under `agents/` (or symlink it), and add one row to [`skills/route-case.md`](skills/route-case.md). No orchestrator changes needed. The design is plugin-shaped.

**How much does it cost per opinion?**
On Claude Code Max: zero marginal dollars. On metered API pricing: roughly $3–10 per opinion depending on complexity. The real cost is wall-clock time (5–15 minutes per pipeline).

---

## Project Structure

```
legal-agent-orchestrator/
├── CLAUDE.md                           # orchestrator system prompt
├── .mcp.json                           # MCP server config (korean-law + kordoc)
├── setup.sh                            # agent clone/link management
├── skills/
│   ├── route-case.md                   # classification + pipeline selection
│   ├── deliver-output.md               # final assembly
│   └── manage-debate.md                # Phase 2.3 debate (skeleton)
├── scripts/
│   └── md-to-docx.py                   # DOCX conversion (dual-font Korean style guide §11)
├── agents/                             # 8 subordinate agents (gitignored)
├── output/                             # live case artifacts (gitignored)
├── samples/                            # frozen portfolio-evidence case snapshots
│   ├── README.md                       # agent-by-agent breakdown of all 4 samples
│   └── ...
└── docs/
    └── ko-legal-opinion-style-guide.md # canonical Korean legal opinion style guide
```

---

## License

**Apache License 2.0** — see [LICENSE](LICENSE).

Subordinate agents are hosted in separate repositories with their own licenses. Legal data comes from Korean Ministry of Government Legislation public APIs and court judgments (public-domain government works).
