# Jinju Law Firm Orchestrator · 법무법인 진주

**한국어:** [README.ko.md](README.ko.md)

> An AI law firm running on Claude Code. Eight specialist lawyer agents collaborate like a real firm to produce legal opinions with full audit trails.

![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)
![Runtime: Claude Code](https://img.shields.io/badge/Runtime-Claude_Code-orange)
![MCP: korean-law](https://img.shields.io/badge/MCP-korean--law-green)

---

## Overview

Most "legal AI" products are a single LLM you throw questions at. This one is different.

An **orchestrator plays the role of managing partner**. It classifies each incoming question, routes it to the right specialist lawyer, and picks the collaboration pattern (sequential handoff / parallel research / multi-round debate). The eight subordinate agents are real Claude Code agents — each with its own jurisdiction, knowledge base, and MCP tools — and this project reuses them **100% unmodified**.

Every step is logged to `events.jsonl`, and the final delivery step folds the whole case folder into a single `case-report.md`. Which lawyer was assigned, which sources (Grade A/B/C) were cited, what the fact-checker flagged, and how revisions resolved — it's all visible in one narrative artifact.

---

## Meet the Team — 법무법인 진주 소속 에이전트

This orchestrator is the **main office** of a fictional Korean law firm, 법무법인 진주 (Jinju Law Firm). Each of the eight attorneys below lives in its own independent GitHub repository as a standalone Claude Code agent. When you run `./setup.sh` they are all cloned into `agents/` and ready to be dispatched.

| Attorney | Agent repository | What they actually do | Phase |
|----------|------------------|-----------------------|-------|
| **김재식 (Kim Jaesik)** | [general-legal-research](https://github.com/kipeum86/general-legal-research) | Evidence-based international legal research across **17+ jurisdictions**. The generalist research associate — any legal question, any jurisdiction, grade-A source-first workflow. | Phase 1 ✓ |
| **한석봉 (Han Seokbong)** | [legal-writing-agent](https://github.com/kipeum86/legal-writing-agent) | Bilingual (KR/EN) drafter for **non-contract** legal documents. Drafts via a D1–D6 pipeline, revises via an R1–R7 tracked-change pipeline. Korean drafts follow 쟁점→결론→분석 conventions; English drafts follow IRAC/CRAC with Bluebook/OSCOLA. | Phase 1 ✓ |
| **반성문 (Ban Seong-mun)** · *Partner* | [second-review-agent](https://github.com/kipeum86/second-review-agent) | Final quality gate for AI-generated legal documents. Verifies citations against primary legal databases (law.go.kr, congress.gov, eur-lex, and more), checks legal logic, and ships redlined DOCX with tracked changes. Independent release gate (Pass / Pass with Warnings / Manual Review Required / Not Recommended). Zero tolerance for hallucinated citations. | Phase 1 ✓ |
| **정보호 (Jeong Bo-ho)** | [PIPA-expert](https://github.com/kipeum86/PIPA-expert) | Korean data privacy law specialist built on structured RAG: **929 statute files, 46 PIPC official guidelines, 30 landmark cases and interpretations, 2,369 cross-reference edges**. Produces law firm-grade DOCX opinions. | Phase 2 ✓ |
| **김덕배 (Kim De Bruyne)** | [GDPR-expert](https://github.com/kipeum86/GDPR-expert) | EU data protection law specialist built on structured RAG: **5 EU laws (321 articles + 535 recitals), 120 EDPB documents, 51 CJEU judgments, 33 enforcement decisions** — 1,060+ indexed items. | Phase 2 ✓ |
| **심진주 (Sim Jinju)** | [game-legal-research](https://github.com/kipeum86/game-legal-research) | International game-industry legal research — cross-jurisdiction regulatory comparison for game clients. Evidence-based, primary-source-first, with real local output pipeline for deliverable-grade work product. | Phase 2 ✓ |
| **고덕수 (Ko Duksoo)** | [contract-review-agent](https://github.com/kipeum86/contract-review-agent) | Contract review pipeline — drop a contract in, get back a **DOCX with tracked-change redlines, margin comments (internal strategy + external-facing), a full analysis report, and negotiation recommendations**. Node.js + Python stack. Final legal judgment stays with the human. | Phase 2 |
| **변혁기 (Byeon Hyeok-gi)** | [legal-translation-agent](https://github.com/kipeum86/legal-translation-agent) | Legal document translation across **5 languages** with zero-omission guarantee and dual-pass translation merged via comparative synthesis. Jurisdiction-aware terminology (BGB, UCC, PRC, Taiwan, APPI) and a persistent firm-wide translation memory that grows with every job. | Phase 2 |

**The orchestrator never modifies a subordinate agent's `CLAUDE.md`, skills, or knowledge base.** That's what "100% reuse" means in practice. If an attorney ships a bug fix to their own repo, it flows through here on the next `./setup.sh update`.

> Two briefing-style agents (`game-legal-briefing`, `game-policy-briefing`) exist in the same author's GitHub org but are standalone Python apps outside this orchestrator's scope and are not cloned by `setup.sh`.

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

    F --> OUT([opinion.md + opinion.docx<br/>case-report.md + events.jsonl + sources.json])
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

We inverted the tradeoff: **Claude Code as the runtime, agents preserved 100% intact, and final delivery collapsed into a single `case-report.md` artifact instead of a web UI.** Real legal work, not a demo.

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

## Getting Started

### Prerequisites

- **[Claude Code](https://docs.claude.com/claude-code)** installed and logged in. Max subscription strongly recommended — a single case can burn 200K+ tokens across subagents, and on metered API pricing that adds up. On Max, marginal cost is zero.
- **macOS or Linux** with `git`, `bash` or `zsh`, and `python3` (3.10+).
- **[법제처 Open API](https://open.law.go.kr/) account.** Free, sign up with an email. You'll get an `LAW_OC` key which the `korean-law` MCP server uses to query Korean statutes, precedents, and administrative interpretations in real time.

### 1. Clone the orchestrator

```bash
git clone https://github.com/kipeum86/legal-agent-orchestrator.git
cd legal-agent-orchestrator
```

What you have now: the orchestrator itself — `CLAUDE.md` (the managing partner's system prompt), `.mcp.json` (MCP server config), `skills/` (routing and assembly logic), `setup.sh`, and `samples/` with four real cases you can inspect immediately. The eight subordinate agents are **not yet installed**.

### 2. Install the eight subordinate agents

```bash
./setup.sh
```

This script clones all eight attorneys' GitHub repositories into `agents/` under their Agent ID names:

```
agents/
├── general-legal-research/     ← 김재식
├── legal-writing-agent/        ← 한석봉
├── second-review-agent/        ← 반성문 (Partner)
├── PIPA-expert/                ← 정보호
├── GDPR-expert/                ← 김덕배
├── game-legal-research/        ← 심진주
├── contract-review-agent/      ← 고덕수
└── legal-translation-agent/    ← 변혁기
```

Each folder is an independent Claude Code agent with its own `CLAUDE.md`, `skills/`, knowledge base, and MCP configuration. When the orchestrator dispatches a case, it calls into these agents via Claude Code's `Agent` tool with `cwd: agents/{agent-id}/`, so each subagent runs in its own working directory with its own context.

Other `setup.sh` commands:
- `./setup.sh update` — pull the latest commit for every already-cloned agent
- `./setup.sh status` — show branch + latest commit for each agent
- `./setup.sh link` — **development mode**: if you already have the agent repositories checked out under `~/코딩 프로젝트/`, create symlinks instead of fresh clones so your local edits flow through immediately

### 3. Set your Korean Open Law API key

```bash
export LAW_OC=your_law_oc_key
```

⚠️ This is required **every shell session**. Claude Code does not auto-load `.env`, and without `LAW_OC` the `korean-law` MCP server will fail to answer the first statute lookup. The simplest solution is to put `export LAW_OC=...` in your `~/.zshrc` or `~/.bashrc`.

### 4. Launch Claude Code from the orchestrator directory

```bash
claude
```

When Claude Code starts, it auto-loads:
- **[CLAUDE.md](CLAUDE.md)** — the orchestrator system prompt that tells the main Claude session "you are the managing partner of Jinju Law Firm, here is your workflow, here are your eight attorneys, here are the skills you can invoke"
- **[.mcp.json](.mcp.json)** — the MCP servers available (`korean-law` and `kordoc`); each subagent inherits these on dispatch
- **`skills/*.md`** — markdown procedure documents the orchestrator executes as subroutines

You're now talking to the managing partner. Ask a legal question in Korean or English.

### 5. Your first case

Try one of these:

```
확률형 아이템 공급 확률 정보공개 의무 — 해외 관계회사가 한국 이용자 대상
게임을 운영할 때 국내대리인 지정 요건과 위반 시 리스크는?
```

```
Our SaaS product is based in Seoul but has ~12% EU users. Do we need a
GDPR Art.27 representative, and what happens if we don't appoint one?
```

What happens next:
1. The orchestrator classifies the question (jurisdiction × domain × task), picks a pipeline, creates `output/{CASE_ID}/`, and starts appending to `events.jsonl`.
2. It dispatches the first subagent via `Agent` tool. You'll see the subagent run in a nested context — calling MCP, reading its KB, writing results.
3. Control returns to the orchestrator, which reads the subagent's `{agent}-meta.json` summary and dispatches the next agent in the pipeline.
4. When all agents finish, `skills/deliver-output.md` assembles `opinion.md`, converts it to `opinion.docx`, and generates `case-report.md`.

Expect 5–15 minutes of wall-clock time per case. The orchestrator is not trying to minimize latency — it's trying to minimize the number of things you have to manually double-check afterwards.

### 6. Find your results

```
output/{CASE_ID}/
├── events.jsonl            ← full timeline, one event per line
├── {agent}-result.md       ← each subagent's detailed analysis
├── {agent}-meta.json       ← each subagent's 2000-token summary + graded sources
├── opinion.md              ← final opinion in markdown
├── case-report.md          ← single-file narrative case archive
└── opinion.docx            ← final opinion as DOCX (client-ready)
```

The sample cases under [`samples/`](samples/) show exactly what a completed case file looks like. If you want to see what "a real case that this system successfully processed" looks like without running anything, start with [`samples/20260410-012238-391f/case-report.md`](samples/20260410-012238-391f/case-report.md) — the single-file archive for the Korean loot-box regulation opinion.

### 7. Generate `case-report.md`

The orchestrator does not ship a web viewer anymore. Instead, every completed case can be collapsed into a single Markdown archive that renders directly on GitHub.

Generate it manually for an existing case:

```bash
python3 scripts/generate-case-report.py samples/20260410-012238-391f
```

Or for a freshly completed live case:

```bash
python3 "$PROJECT_ROOT/scripts/generate-case-report.py" "$PROJECT_ROOT/output/$CASE_ID"
```

`skills/deliver-output.md` now calls this automatically at the final delivery step, so completed cases should end with:

- `opinion.md`
- `opinion.docx`
- `sources.json`
- `events.jsonl`
- `case-report.md`

The generated report is designed to be the one file you open first. It includes:
- case metadata and status
- human-readable timeline derived from `events.jsonl`
- participating lawyers and their contributions
- partner review findings grouped by severity
- source table with grade breakdown
- the final opinion inlined under one document
- relative links to the original raw artifacts

---

## FAQ

**How does it handle client confidentiality?**
Everything runs locally on your machine under your own Claude Code session. No intermediate SaaS. Claude Code itself sends prompts to Anthropic for inference — whether that's acceptable for a given matter depends on your firm. `output/`, `agents/`, and `.env` are gitignored so case files and API keys don't leak into commits.

**What does `./setup.sh` actually do to my machine?**
It creates an `agents/` folder inside this repository and clones eight public GitHub repositories into it, one per attorney. Nothing outside this directory is touched. No global package installs, no environment mutations beyond whatever `git clone` does. Each agent folder is roughly 10–80 MB depending on its knowledge base size.

**Can I add my own specialist agent?**
Yes. Write it as a standalone Claude Code agent (its own `CLAUDE.md`, `skills/`, optional `library/`, optional `.mcp.json`), drop it under `agents/` (or symlink it), add one line to the `REPOS` array in `setup.sh`, and add one row to [`skills/route-case.md`](skills/route-case.md) so the router knows when to call it. No orchestrator code changes needed. The design is plugin-shaped.

**How much does it cost per opinion?**
On Claude Code Max: zero marginal dollars. On metered API pricing: roughly $3–10 per opinion depending on complexity. The real cost is wall-clock time (5–15 minutes per pipeline).

---

## Project Structure

```
legal-agent-orchestrator/
├── CLAUDE.md                           # orchestrator system prompt
├── .mcp.json                           # MCP server config (korean-law + kordoc)
├── setup.sh                            # clones the 8 subordinate agents
├── skills/
│   ├── route-case.md                   # classification + pipeline selection
│   ├── deliver-output.md               # final assembly + case-report generation handoff
│   ├── generate-case-report.md         # single-file case archive generation
│   └── manage-debate.md                # Phase 2.3 debate (skeleton)
├── scripts/
│   ├── md-to-docx.py                   # DOCX conversion (dual-font Korean style guide §11)
│   └── generate-case-report.py         # narrative case-report.md generator
├── agents/                             # 8 subordinate agents (gitignored, populated by setup.sh)
├── output/                             # live case artifacts (gitignored)
├── samples/                            # frozen portfolio-evidence case snapshots
│   ├── README.md                       # agent-by-agent breakdown of all 4 samples
│   ├── 20260410-012238-391f/case-report.md
│   └── ...
└── docs/
    └── ko-legal-opinion-style-guide.md # canonical Korean legal opinion style guide
```

---

## License

**Apache License 2.0** — see [LICENSE](LICENSE).

Subordinate agents are hosted in separate repositories with their own licenses. Legal data comes from Korean Ministry of Government Legislation public APIs and court judgments (public-domain government works).
