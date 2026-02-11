# Mellea Adoption: Action Plan

| | |
|:---|:---|
| **Date** | February 2026 |
| **Context** | [research.md](research.md) (full analysis, including industry trends in Section 16 and AI agent discoverability in Section 17) |
| **Tracking** | Create "Mellea Adoption" GitHub Project board with columns: Backlog / Phase 1 / Phase 2 / Phase 3 / Done |

---

## Blockers (fix before ANY outreach)

These must be resolved before tutorials, blog posts, or community engagement. If any of these are broken, a new user's first experience fails.

| # | Item | Issue | Owner | Status |
|:--|:-----|:------|:------|:-------|
| B1 | Fix validation logic (core value prop is broken) | #426 | | |
| B2 | Fix backend error handling (tracebacks instead of messages) | #432, #427 | | |
| B3 | Fix broken examples (tools, Colab, notebooks) | #335, #383, #404 | | |
| B4 | Slim core dependencies to <50MB (currently ~500MB) | #453 | | |

**Exit gate**: `pip install mellea` completes in <30 seconds. A new user copies one example, runs it, gets correct output. No crashes.

---

## Phase 1: Fix the front door

Goal: Time to Hello World (TTHW) under 5 minutes. Gated on blockers above.

| # | Item | Issue | Owner | Status |
|:--|:-----|:------|:------|:-------|
| 1.1 | Write a real quickstart (install, run, output in <2 min) | #437, #441 | | |
| 1.2 | Document `@generative` properly | #1, #76 | | |
| 1.3 | Delete or rewrite tutorial.md | #429 | | |
| 1.4 | Triage issue tracker (close stale, apply labels from scheme below) | -- | | |
| 1.5 | Fix test marker gaps, document contributor test path | #419 | | |
| 1.6 | Add coverage badge to README | -- | | |
| 1.7 | Update docs.mellea.ai to match v0.3.0 | -- | | |
| 1.8 | Create "Mellea Adoption" GitHub Project board | -- | | |
| 1.9 | Add `llms.txt` to repo root and mellea.ai | -- | | |
| 1.10 | Add `.github/copilot-instructions.md` and `.cursorrules` | -- | | |
| 1.11 | Review PyPI long description (clear examples, keywords) | -- | | |

**Exit gate**: New developer installs and succeeds on first attempt, consistently. Issue tracker looks healthy (labelled, triaged, project board visible). AI coding agents can discover mellea via `llms.txt`.

---

## Phase 2: Give them a reason to come

Goal: Mellea appears in search results for pain-point queries. Gated on Phase 1.

| # | Item | Target audience | Owner | Status |
|:--|:-----|:----------------|:------|:-------|
| 2.1 | Tutorial: "Fix Your OutputParser in 5 Lines" | LangChain users | | |
| 2.2 | Tutorial: "Structured Output from Local Llama -- No Yapping" | r/LocalLLaMA | | |
| 2.3 | Tutorial: "Make Your LLM More Reliable in 1 Line" | Anyone with flaky outputs | | |
| 2.4 | Tutorial: "LLM Can't Do Math? Don't Make It." | Prompt engineers | | |
| 2.5 | Tutorial: "Mellea vs Instructor: Where Each Shines" | Library evaluators | | |
| 2.6 | OpenAI-only Colab notebooks (no Ollama required) | Everyone | | |
| 2.7 | Rewrite README opening with before/after code hook | Everyone | | |
| 2.8 | "vs" comparison pages (Instructor, LangChain parsers, PydanticAI) | SEO | | |
| 2.9 | Publish to r/LocalLLaMA | Local LLM community | | |
| 2.10 | Submit to Simmering's structured output comparison | SEO | | |
| 2.11 | Revive the blog for comparison content | -- | | |
| 2.12 | Create `llms-full.txt` with complete API reference | AI agents | | |
| 2.13 | Answer StackOverflow "structured output" questions with mellea | Training data / SEO | | |

**Exit gate**: Searching "structured LLM output Python", "LangChain OutputParser alternative", or "Ollama JSON output" surfaces mellea content within first 2 pages. At least 3 tutorials runnable and linked from README.

---

## Phase 3: Make them stay

Goal: Turn tryers into users into advocates. Gated on Phase 2.

| # | Item | Issue | Owner | Status |
|:--|:-----|:------|:------|:-------|
| 3.1 | Framework adapters (LangChain, DSPy, CrewAI) | #434, #446, #449, #450 | | |
| 3.2 | "Mellea + LangGraph" reference example | #446 | | |
| 3.3 | Migration recipes (LangChain chain, retry loop, CrewAI task) | -- | | |
| 3.4 | MCP tool calling | #409 | | |
| 3.5 | Starter templates (ReACT, deep research, HITL) | #438, #401 | | |
| 3.6 | Pre-built requirements catalog | #440 | | |
| 3.7 | Streaming for sampling results | #403 | | |
| 3.8 | Observability (structured logging, tracing) | #442, #443, #444 | | |
| 3.9 | Package MCP server for `@generative` functions | #409 | | |

**Exit gate**: At least one external "I migrated from X to mellea" story. Framework adapters allow `pip install mellea` and use as LangChain `BaseChatModel`.

---

## Key decisions (from research)

These are settled. Don't re-litigate unless new evidence appears.

1. **Lead with model-agnostic features.** `@generative`, sampling strategies, validation work with any model. Granite is a bonus, not the lead.
2. **Leaf Node positioning.** We are the execution layer inside other frameworks' graphs, not a competing orchestrator. Don't build orchestration features.
3. **Honest comparisons.** Acknowledge where Instructor is simpler (pure API) and LangGraph is better (complex state machines). Our credibility depends on it.
4. **Research continues in parallel.** Adoption work does not slow research. New sampling strategies, SoFAI, RL tuning (#405), self-repairing requirements (#454) continue on their own track. Key constraint: research features must not add core dependencies.
5. **Tutorials before adapters.** Tutorials are smaller effort and prove the story. Framework adapters are larger effort and scale the story. Sequence accordingly.
6. **"Agentic engineering" framing.** Position mellea as the engineering discipline that makes agents reliable, not as another agent framework. Lead with reliability and auditability in all content. (Section 16.1)
7. **"Providers solved simple JSON. We solve the hard parts."** Don't lead with basic structured output -- lead with multi-step validation, cross-provider portability, and auditable pipelines. (Section 16.4)

---

## Trends to act on (Section 16)

Time-sensitive items from the industry trends analysis:

| Trend | Action | Timing |
|:------|:-------|:-------|
| **Agentic engineering backlash** | Frame all content around reliability/auditability, not features. Reference Klarna/Replit failures as context. | Now (influences all Phase 2 content) |
| **EU AI Act (Aug 2, 2026)** | Consider a compliance-focused tutorial or whitepaper. Prioritise observability epics (#442-#444). | Urgent -- 6 months to enforcement |
| **Reasoning model think-then-extract** | Add a tutorial showing reasoning model + mellea for structured extraction from chain-of-thought | Phase 2 (new tutorial candidate) |
| **AI agent discoverability** | `llms.txt`, copilot-instructions, cursorrules, StackOverflow presence | Phase 1 (llms.txt) + Phase 2 (ongoing) |

---

## Label scheme

Apply to all issues for consistent tracking:

| Label | Purpose |
|:------|:--------|
| `adoption` | Directly serves adoption funnel |
| `documentation` | Docs, tutorials, examples |
| `bug` | Something broken |
| `dx` | Developer experience |
| `research` | Research / innovation track |
| `integration` | Framework adapters, MCP, tool interop |
| `P0-blocker` | Must fix before any outreach |
| `P1-important` | Important for adoption phases |
| `good-first-issue` | Suitable for new contributors |
| `help-wanted` | Community contributions welcome |
| `stale` | Needs triage -- close or revive |
