# Jinju Law Firm Orchestrator · 법무법인 진주

**한국어:** [README.ko.md](README.ko.md)

> An AI law firm running on Claude Code. Eight specialist lawyer agents collaborate like a real firm to produce legal opinions.

**Status:** Phase 1 E2E passed (2026-04-10) · Phase 2.1/2.2 validated · Phase 2.3 (debate) + Case Replay in progress

---

## Overview

Most "legal AI" products are a single LLM you throw questions at. This project is different.

An **orchestrator plays the role of managing partner**, classifying each incoming question, routing it to the right specialist lawyer, and choosing the appropriate collaboration pattern (sequential handoff / parallel research / multi-round debate). The eight subordinate agents are real Claude Code agents — each with its own jurisdiction (Korea/EU), domain (privacy/gaming/contracts/translation), and task type (research/drafting/review). **This project reuses them 100% unmodified.**

Every step is logged to `events.jsonl`, producing a replayable artifact. Which lawyer was assigned, which sources (Grade A/B/C) were cited, what the fact-checker flagged — it's all visible.

---

## Why This Architecture

The standard playbook for multi-agent systems is to wrap a framework (LangGraph, CrewAI, AutoGen, Claude Agent SDK) in a web server. Using Claude Code itself as the orchestration runtime is non-standard — the first reaction from most developers is "why didn't you use Agent SDK?"

The answer starts with clearing up four misconceptions.

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
- What did the fact-checker flag? → visible (`verbatim_verified`, `revision_requested`)
- How did the inter-jurisdiction debate play out? → visible (`debate_round_*`)
- What did the reviewing partner comment on? → visible (`review_comment`)

Because we reuse real specialized agents with their own source grading and fact-checking, **the process itself becomes the product** — not the answer.

### 4. Case Replay — Not a 30-Second Demo

Most AI demos die after 30 seconds. This one doesn't.

Every processed case persists as `events.jsonl` (timeline) + per-agent `{agent}-result.md` and `{agent}-meta.json` + a final `opinion.md/.docx`. Phase 3 turns this data into a static JSON feed plus a static viewer (Case Replay): **no API key required, works offline, shareable and embeddable**. The legal process is the content; the visualization is just delivery.

### 5. Yes, It Burns a Lot of Tokens — On Purpose

A single case in this system can consume 60K–170K tokens per specialist, plus orchestrator handoff overhead. In Phase 2.2 validation, one parallel run (PIPA ∥ GDPR) crossed 124K tokens; the Korean gaming law regression hit 170K. That's not a bug — it's the design.

Every subagent gets its own full 200K context window because we want it to do its actual job:

- Load its complete `CLAUDE.md` (role, principles, tool policies)
- Load every skill it might need
- Browse its full knowledge base
- Run live MCP queries against primary sources
- Have room to think across multiple turns and revisions

Context-sharing, aggressive truncation, or prompt-level shortcuts could cut token usage sharply — and would degrade output quality by roughly the same amount. **Quality-per-case is the objective function; token spend is the price we pay for it.** On Claude Code Max, the marginal dollar cost per call is zero; the real cost is wall-clock time (minutes per pipeline, not milliseconds) — and that is the cost we're choosing to absorb.

If you want a cheap legal chatbot, this is the wrong project. If you want a legal opinion you can defend with a full audit trail, that burn rate is the price of admission.

---

## How It Works

### Workflow

```
1. Case intake
   └── Generate CASE_ID, create output/{CASE_ID}/, start events.jsonl

2. Classification (skills/route-case.md)
   └── Jurisdiction × domain × task type → agent combination + collaboration pattern

3. Agent dispatch (Agent tool)
   └── Each agent is an independent Claude instance
        ├── Loads its own CLAUDE.md + skills + knowledge base + MCP
        └── Saves results to {agent}-result.md + {agent}-meta.json

4. Handoff (if needed)
   └── Only summary + key_findings are passed to the next agent
        (Full result.md is referenced by path only → context-efficient)

5. Final assembly (skills/deliver-output.md)
   └── opinion.md + opinion.docx + events.jsonl + source list
```

### Three Collaboration Patterns

**Pattern 1 — Independent Research → Merge (Parallel)**
Specialists from different jurisdictions/domains each research, then writing merges. Validated in Phase 2.2.
```
Orchestrator → [PIPA-expert ∥ GDPR-expert] → legal-writing → second-review
```

**Pattern 2 — Sequential Handoff** (Phase 1 default)
```
Orchestrator → general-legal-research → legal-writing → second-review
```

**Pattern 3 — Multi-round Debate** (Phase 2.3, the killer feature)
For cross-jurisdiction questions where disagreement is likely. Two specialists exchange opinion → rebuttal → counter-rebuttal, then writing drafts a verdict.
```
Orchestrator → Agent A opinion → Agent B rebuttal → Agent A counter → writing verdict → review
```

Pattern 3 is where this architecture earns its keep — **it produces a depth no single LLM call can reproduce**.

---

## Agent Roster

| # | Agent ID | Lawyer | Role | Phase |
|---|----------|--------|------|-------|
| 1 | `general-legal-research` | 김재식 | Generalist legal research | Phase 1 ✓ |
| 2 | `legal-writing-agent` | 한석봉 | Legal drafting | Phase 1 ✓ |
| 3 | `second-review-agent` | 반성문 (Partner) | QA review & final sign-off | Phase 1 ✓ |
| 4 | `PIPA-expert` | 정보호 | Korean Personal Information Protection Act (개인정보보호법) | Phase 2 ✓ |
| 5 | `GDPR-expert` | 김덕배 | EU data protection law (GDPR) | Phase 2 ✓ |
| 6 | `game-legal-research` | 심진주 | International gaming law | Phase 2 ✓ |
| 7 | `contract-review-agent` | 고덕수 | Contract review | Phase 2 |
| 8 | `legal-translation-agent` | 변혁기 | Legal document translation | Phase 2 |

Each agent lives in its own GitHub repository. `setup.sh` auto-clones them, or creates local symlinks under `agents/` during development. **The orchestrator never modifies a subordinate agent's `CLAUDE.md`** — that's what "100% reuse" means in practice.

> Two briefing-style agents (`game-legal-briefing`, `game-policy-briefing`) exist as standalone Python apps outside this orchestrator's scope and are intentionally not listed above.

---

## Current Status

### Complete

**Phase 1 E2E test passed** — 2026-04-10
- Case: `20260410-012238-391f` (opinion on loot-box regulation)
- 47 events, 33 sources (29 Grade A, 4 Grade B), one revision cycle completed
- Discovered the meta-verification fallback pattern: when `legal-writing-agent` hit a rate limit mid-revision, the orchestrator called `korean-law` MCP directly to cross-check verbatim citations, rescuing the revision cycle (`evt_045` · `type=verbatim_verified` · `verifier=orchestrator_meta`)

**Phase 2.1 Specialist Routing** — [`skills/route-case.md`](skills/route-case.md) v2
- Grew from 153 to 637 lines: 8-agent roster, multi-domain 3-way matrix, shared injection block, events schema appendix, token budget table
- Fully addressed all 13 issues + 4 critical FM gaps from `/plan-eng-review`

**Phase 2.2 Pattern 1 Parallel Dispatch** — 3 mini E2E runs validated
- **T1** — PIPA-expert solo: 9 sources (8A + 1B), 60k tokens, 582s. Surfaced a KB gap in `library/grade-b/` — **since resolved** (see Phase 2.2 follow-up below)
- **Regression** — game-legal-research on Korean gaming law: 32 sources (25A + 7C), −3% comparable vs v1 baseline, 11/11 topic coverage. Library cache + domain framing proved their worth.
- **T2** — PIPA ∥ GDPR parallel: 13 sources each (all Grade A), both branches executed truly in parallel, 5-dimension tagging worked. 124k tokens, 334s.

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
│   ├── route-case.md                   # classification + pipeline selection
│   ├── deliver-output.md               # final assembly
│   └── manage-debate.md                # Phase 2.3 debate logic (skeleton)
├── scripts/
│   └── md-to-docx.py                   # DOCX conversion (style guide §11)
├── agents/                             # 8 subordinate agents (symlinks or clones)
├── output/                             # case artifacts ({case-id}/)
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
  - `korean-law` — Korean Ministry of Government Legislation (법제처) public API wrapper; Grade A primary sources (statutes, precedents, interpretations)
  - `kordoc` — Korean court judgment retrieval
- **Skills system**: markdown procedure docs (`skills/*.md`)
- **Event logging**: JSONL (append-only, replayable)
- **Output format**: Markdown → DOCX (python-docx, dual-font: Times New Roman + 맑은 고딕)

---

## Roadmap

- [x] **Phase 0** — Tech spike (`Agent` tool / MCP / parallel execution — 6/8 PASS)
- [x] **Phase 1** — 3-agent baseline pipeline (research → writing → review) + E2E
- [x] **Phase 2.1** — Specialist routing (8-agent roster, multi-domain matrix)
- [x] **Phase 2.2** — Pattern 1 parallel dispatch (3 mini E2E runs validated)
- [ ] **Phase 2.3** — Pattern 3 multi-round debate (the killer feature)
- [ ] **Phase 3** — Case Replay (Next.js static viewer, dark-theme war-room UI)
- [ ] Public release of the 8 subordinate agents + license audit
- [ ] Classification regression test harness (route-case.md few-shot auto-validation)

---

## References

| Document | Description |
|----------|-------------|
| [docs/design.md](docs/design.md) | Design doc (office-hours 6-round adversarial review, APPROVED 9/10) |
| [docs/notes/architecture-defense.md](docs/notes/architecture-defense.md) | Source material for this README — extended "why this architecture" defense |
| [docs/ko-legal-opinion-style-guide.md](docs/ko-legal-opinion-style-guide.md) | Canonical Korean legal opinion style guide (force-injected into every Korean agent call) |
| [skills/route-case.md](skills/route-case.md) | Classification + pipeline selection logic (v2, 637 lines) |
| [resume.md](resume.md) | Development status (cross-session handoff doc) |

---

## License

Licensed under the **Apache License 2.0** — see [LICENSE](LICENSE).

Subordinate agents are hosted in separate repositories with their own licenses. Legal data comes from Korean Ministry of Government Legislation public APIs and court judgments (public-domain government works).
