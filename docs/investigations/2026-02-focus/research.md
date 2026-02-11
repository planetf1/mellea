# Mellea Focus Research: DevRel, Adoption, and the Path to Users

**Date**: February 2026
**Status**: Draft -- open for collaboration
**Repository**: [github.com/generative-computing/mellea](https://github.com/generative-computing/mellea) (v0.3.0)
**Branch**: `dev/focus`
**Audience**: Leadership (strategic direction), DevRel/adoption team (execution plan), core contributors (context for how research connects to users)
**Scope**: This document focuses on developer relations and adoption. It is not a roadmap for research features. Core research and innovation will continue in parallel -- this document is about making sure that innovation reaches people.

### What is mellea?

[Mellea](https://github.com/generative-computing/mellea) is an open-source Python library for writing **generative programs** -- structured, maintainable, robust AI workflows expressed as ordinary Python. Published on [PyPI](https://pypi.org/project/mellea/), it provides a `@generative` decorator that turns typed Python functions into LLM-powered specifications, a pluggable sampling strategy system (rejection sampling, majority voting, budget forcing, process reward models), and a uniform backend API spanning Ollama, OpenAI, HuggingFace, vLLM, LiteLLM, and AWS Bedrock. It works as a standalone tool for structured generation and equally well as a drop-in execution layer inside existing pipelines.

---

## 1. Executive Summary

### The situation

The team has built something genuinely differentiated. Mellea v0.3.0 has capabilities that no competing library matches:

- **`@generative` decorator**: write a typed Python function, get structured LLM output. No parsers, no chains, no graphs. Docstrings are prompts; type hints are schemas.
- **Pluggable sampling strategies**: rejection sampling, majority voting, budget forcing, process reward models -- swap reliability strategies with one parameter. This is a first-class abstraction unique to mellea.
- **Constrained decoding for local models**: guaranteed valid JSON at the token level via Outlines/xgrammar. Instructor and PydanticAI rely on post-hoc retry for local models -- they cannot offer this guarantee.
- **Instruct-validate-repair as a primitive**: not a pattern users build themselves, but a built-in loop with composable Requirements.
- **7 backends, uniform API**: Ollama, OpenAI, HuggingFace, vLLM, LiteLLM, Bedrock, Watsonx (legacy; being phased out).

These are real innovations, built by researchers and engineers who understand the space deeply. The sampling strategy architecture in particular is something the wider community is only now catching up to through inference-time scaling research.

**The challenge is bridging the gap between this work and the developers who need it.**

The project has initial momentum to build on: a [TheNewStack feature article](https://thenewstack.io/ibms-mellea-tackles-open-source-ais-hidden-weakness/), [IBM Research blog posts](https://research.ibm.com/blog/generative-computing-mellea), a [PyData Boston 2025 talk](https://www.youtube.com/watch?v=WFm0nao9hlY), community articles on dev.to, and ~13K PyPI downloads/month. But there are specific barriers between that initial awareness and active adoption:

- **The coverage is "announcement" press, not developer content.** Existing articles explain what mellea is. What's missing is the tutorials, comparisons, and how-tos that address a specific pain point a developer is already searching for (e.g., "LangChain OutputParser alternative", "Ollama structured JSON").
- **The install is too heavy for experimentation.** `pip install mellea` pulls ~500MB+ of dependencies (including Docker sandboxing, ML validation libraries, and a web framework) because the core package bundles everything. Compare: `pip install instructor` is ~10MB. This is a structural barrier -- someone wanting to try `@generative` with OpenAI shouldn't need to wait for Docker sandbox libraries to download.
- **The first-run experience has gaps.** The Colab quickstart has issues (#335). The tutorial needs work (#429). `@generative` documentation needs to be expanded (#1). Some core paths have bugs (#426 validation, #432 error handling). The good news: the public API is clean (`from mellea import generative, start_session`) and error messages for missing optional dependencies are excellent.
- **The issue tracker needs attention.** 137 open issues, some from very early in the project, with inconsistent labelling. To an outside evaluator, this can read as lack of momentum -- which is the opposite of reality.

None of this reflects badly on the engineering work. It reflects the natural state of a project that has (correctly) prioritised building the right thing over marketing it. The question now is: **how do we lower the barriers so more developers actually try it?**

### The opportunity

The landscape is favourable. Developers are in "post-framework fatigue" -- deleting LangChain boilerplate and replacing it with raw Python (the Octomind case study, high LangChain production drop-off rates across multiple industry reports). But raw Python has no validation, no retry, no structured output. There is a clear gap between "heavyweight framework" and "no framework at all."

Mellea fits that gap perfectly -- both as a standalone tool and as a drop-in execution layer inside existing frameworks.

The target audiences, based on landscape analysis and search/community signals:
1. **Frustrated LangChain users** -- OutputParser pain, graph complexity ("OutputParserException" has 10K+ hits)
2. **Local LLM builders** -- r/LocalLLaMA (600K+ members), the "yapping" JSON problem
3. **FastAPI/Pydantic developers** -- want LLM output as Pydantic models without glue code
4. **Developers evaluating structured output libraries** -- comparing Instructor vs PydanticAI vs alternatives

### What we recommend

Three phases, sequenced to build on each other. Research and innovation continue throughout -- these phases are specifically about the adoption and DevRel work stream.

**Phase 1: Fix the front door** (prerequisite for any outreach)
- **Slim down core dependencies** so `pip install mellea` is fast and lightweight (~50MB, not ~500MB). Move Docker sandboxing, ML validation libraries, web framework, and Granite-specific packages to optional extras. (See Section 3.1 for details.)
- Fix the high-impact bugs a new user would hit: validation logic (#426), backend error messages (#432), broken examples (#335, #383, #404)
- Write a real quickstart: `pip install mellea`, copy one file, run, see structured output in <2 minutes
- Improve `@generative` documentation (#1) and address tutorial quality (#429)
- Triage the issue tracker: close stale issues, label consistently, project health signals
- **Exit criteria**: a new developer installs in under 30 seconds and succeeds on first attempt, consistently

**Phase 2: Give them a reason to come** (content that brings people to the door)
- Ship 5 "gateway" tutorials, each targeting a specific pain point someone is already searching for:
  1. "Fix Your OutputParser in 5 Lines" (LangChain users)
  2. "Structured Output from Local Llama -- No Yapping" (r/LocalLLaMA)
  3. "Make Your LLM More Reliable in 1 Line" (anyone with flaky outputs)
  4. "LLM Can't Do Math? Don't Make It." (hybrid intelligence pattern)
  5. "Mellea vs Instructor: Where Each Shines" (comparison shoppers)
- Provide Colab notebooks that work with just an OpenAI API key (no Ollama required)
- Rewrite the README opening with a before/after code hook
- Publish honest "vs" comparison pages for SEO
- **Exit criteria**: mellea content appears in search results for key pain-point queries

**Phase 3: Make them stay** (turn tryers into users into advocates)
- Build framework integration adapters (#446, #449, #450) so users can inject mellea into existing LangChain/DSPy/CrewAI pipelines without learning a new API
- Ship a "Mellea + LangGraph" reference example demonstrating the Leaf Node Thesis
- Create migration recipes (LangChain extraction chain, manual retry loop, CrewAI task node)
- Add MCP tool calling (#409), starter templates (#438), and pre-built requirements (#440)
- **Exit criteria**: at least one external "I migrated from X to mellea" story

### How this relates to ongoing research work

This document does not propose stopping or deprioritizing core research. Capabilities like new sampling strategies (#157), self-repairing requirements (#454), SoFAI enhancements, and LoRA-backed validation are the engine that keeps mellea ahead of the competition. They should continue.

What this document argues is that **adoption work should not wait for more research to be complete.** The current feature set -- `@generative`, sampling strategies, constrained decoding, validate-repair -- is already compelling enough to attract users. What's missing is the bridge: documentation, demos, content, and bug fixes that let people discover and succeed with what already exists.

The ideal state is research and adoption running in parallel: researchers continuing to push the frontier, while the DevRel/adoption team packages existing capabilities for the outside world. The two reinforce each other -- more users means more feedback, more feedback means better-directed research.

### The bottom line

Mellea has a genuine technical moat. The team should be proud of what's been built -- sampling strategies as a first-class abstraction, constrained decoding for local models, functions-as-specifications. These are innovations the wider ecosystem hasn't caught up to.

The adoption work stream focus should be: **fix, document, demonstrate, distribute.** In that order. Not because the research is done, but because what's already built deserves to be used.

---

This document provides the detailed evidence behind these recommendations. The rest covers: landscape analysis (Section 2), adoption funnel assessment (Section 3), target audiences and entry point scenarios (Section 4), feature-to-pain mapping (Section 5), competitive differentiation (Section 6), tutorial proposals (Section 7), content strategy (Section 8), issue tracker analysis (Section 9), phased priorities (Section 10), key insights (Section 11), taglines (Section 12), open questions (Section 13), ecosystem overview (Section 14), and proposed new issues (Section 15).

---

## 2. The Landscape (February 2026)

### 2.1 What developers reach for today

| Framework | Sweet spot | Weakness mellea exploits |
|:---|:---|:---|
| **LangChain / LangGraph** | Orchestration, integrations, state machines | OutputParser fragility, graph complexity, debugging opacity |
| **LlamaIndex** | RAG, document workflows, indexing | Heavy for non-retrieval tasks; `SubQuestionQueryEngine` is hard to debug |
| **OpenAI Agents SDK** | OpenAI-native tool use | Provider lock-in; no local-model story |
| **CrewAI** | Multi-agent "crews" with roles | Simulated tool use; agents fabricate observations |
| **AutoGen** | Multi-agent research prototyping | Production hardening; observability gaps |
| **smolagents** | Minimalism, HuggingFace ecosystem | No validation, no structured output, no sampling strategies |
| **PydanticAI** | Type-safe tool contracts | No sampling/voting, no repair loops, no local constrained decoding |
| **Instructor** | Structured output from API models (8.6M+ monthly downloads) | Rely on JSON Mode (flaky); no logit-level constraint for local models |
| **Outlines / guidance** | Constrained decoding at token level | Low-level libraries, not application frameworks |
| **DSPy** | Prompt optimization via compilation | Steep learning curve; opaque compiled programs; common user complaint that compiled prompts are hard to inspect |
| **OpenAI AgentKit** (Oct 2025) | Visual agent builder + ChatKit UI | Deep vendor lock-in to OpenAI ecosystem |
| **Claude Agent SDK** (Sep 2025) | MCP-native, secure, composable agents | More setup required; Anthropic-centric |
| **Strands Agents** (AWS) | Model-agnostic with native OpenTelemetry | Newer; ecosystem still forming |
| **Agno** | High-performance multi-agent runtime | Smaller ecosystem than LangChain |
| **Agent Lightning** (Microsoft, mid-2025) | RL-based agent training (GRPO/PPO for tool-use agents) | Training-time optimization; complements mellea's inference-time strategies |

### 2.2 The industry pain we see

Four macro-trends create opportunity for mellea:

1. **"Post-framework fatigue"**: Engineers are deleting LangChain boilerplate and replacing it with 20-line Python loops. The Octomind case study (2024) is canonical: "All LangChain has achieved is increased the complexity of the code with no perceivable benefits." Industry analyses consistently report high drop-off: one widely-cited estimate puts the LangChain-to-production conversion at ~45% (source: aggregated developer survey data, 2025). Multiple case studies document significant token overhead from LangChain's internal processing compared to equivalent direct implementations. But raw Python has no validation, no retry, no structured output. *There is a gap between "framework" and "raw code."* The LangWatch 2026 framework comparison now includes "No Framework" as a recommended option -- which validates the gap but not the solution. Mellea is that solution.

2. **Local-first is mainstream**: Ollama passed 1M+ GitHub stars and tens of millions of downloads. Models run on consumer hardware. But local models "yap" -- they wrap JSON in markdown, add conversational filler, fail `json.loads()`. API-oriented solutions (Instructor, PydanticAI) rely on JSON Mode or retry-based parsing, which doesn't solve the fundamental problem for local models. *Logit-level constrained decoding for local models is under-served.* Mellea does it via Outlines/xgrammar integration in the HuggingFace and vLLM backends.

3. **Inference-time compute is the new frontier**: Snell et al. ([arXiv:2408.03314](https://arxiv.org/abs/2408.03314), Aug 2024) showed that optimal test-time compute scaling can outperform a 14x larger model. OpenAI's o1 (Sep 2024) commercialised this. DeepSeek R1 (Jan 2025) demonstrated open-source inference-time scaling. Microsoft's Agent Lightning (mid-2025, [arXiv:2508.03680](https://arxiv.org/abs/2508.03680)) applies RL (GRPO/PPO) to agent training. These are converging on a principle: *model quality is not fixed at training time.* Mellea's sampling strategies (best-of-N voting, budget forcing, process reward models) implement the inference-time side of this principle as library features. No mainstream framework offers this as a pluggable abstraction. (Note: mellea has an open issue for RL-based tuning too -- #405 -- complementing the inference-time strategies with training-time optimization.)

4. **MCP as ecosystem plumbing**: Anthropic's Model Context Protocol was donated to the Linux Foundation's Agentic AI Foundation in late 2025, co-founded by Anthropic, OpenAI, Block, with Google, Microsoft, AWS, and Cloudflare support. MCP itself is not a differentiator -- every framework is adding MCP support. What matters for mellea is *what we expose via MCP*. The repo already has a working MCP server example (`docs/examples/mcp/mcp_example.py`) that wraps a `MelleaSession` with `RejectionSamplingStrategy` as an MCP tool via FastMCP. The June 2025 MCP spec update added `outputSchema` for structured tool output -- which maps directly to mellea's `@generative` + Pydantic approach. The opportunity: **"quality-guaranteed MCP tools"** -- when an IDE or agent calls a mellea-backed MCP tool, it gets validated, requirement-checked, inference-time-optimised output. No other MCP server does this.

### 2.3 Where mellea fits

Mellea is **not** another orchestration framework. It does not compete with LangGraph on state machines, LlamaIndex on indexing, or CrewAI on multi-agent roles.

Mellea competes on the **execution node**: the moment when you need an LLM to produce a correct, structured, validated result.

**Two adoption modes:**
1. **Standalone**: Write a `@generative` function, call it from plain Python. No framework needed. This is the entry point for most new users and the focus of our tutorials.
2. **Injection**: Use mellea as the **leaf node** inside an existing LangGraph/DSPy/CrewAI pipeline. Replace one flaky node with a validated, strategy-backed mellea function. This is the enterprise adoption path and the focus of the framework adapter epic (#434).

Both modes share the same API. The positioning adjusts by audience:
- For greenfield developers: *"Structured LLM output in 8 lines of Python."*
- For framework users: *"Keep your orchestrator. Use mellea where it matters -- at the point of generation."*

---

## 3. The Adoption Funnel (the core framework for everything below)

Every decision in this document should be evaluated against this funnel. Where are we losing people?

```
DISCOVER  -->  LAND  -->  FIRST SUCCESS  -->  REAL USE  -->  ADVOCATE
   |             |             |                  |              |
Can they     Does the      Can they run       Does it       Would they
find us?     README/docs   a working example  solve their   recommend it
             convince them in <5 minutes?     actual         to others?
             to try?                          problem?
```

### 3.0 Current state of the funnel

| Stage | Current state | Status | Key issues |
|:---|:---|:---|:---|
| **DISCOVER** | Some initial coverage exists (see below), but not reaching the right developer communities. Not on framework comparison sites. No "vs" content, no SEO for pain-point queries. | Has a foundation | Needs developer-targeted content |
| **LAND** | README is functional but doesn't show the "before/after" contrast that hooks evaluators. Install is heavy (~500MB+ core deps -- see Section 3.1). | Decent, but install barrier | Could lead with stronger demo |
| **FIRST SUCCESS** | Colab has issues (#335). Tutorial needs rework (#429). `@generative` docs are thin (#1). Public API is clean (`from mellea import generative, start_session`). Error messages for missing deps are good. | Mixed -- API is clean, docs need work | #335, #429, #1, #76 |
| **REAL USE** | Some core paths have bugs (#426 validation, #432 error handling, #404 tool calling). | Needs fixes | #426, #432, #404 |
| **ADVOCATE** | Early but not zero: PyData Boston 2025 talk, TheNewStack article, IBM Research blog posts, dev.to article. ~13K PyPI downloads/month. | Starting | Needs organic/community reach |

**Existing coverage we should build on** (not starting from zero):
- [TheNewStack](https://thenewstack.io/ibms-mellea-tackles-open-source-ais-hidden-weakness/): "IBM's Mellea Tackles Open Source AI's Hidden Weakness" (syndicated to startupnews.fyi, LinkedIn)
- [IBM Research blog](https://research.ibm.com/blog/generative-computing-mellea): "Towards a generative future for computing" + [interview with lead engineers](https://research.ibm.com/blog/interview-with-mellea-lead-engineers)
- [PyData Boston 2025](https://pretalx.com/pydata-boston-2025/talk/HBBZYB/): "Generative Programming with Mellea" (Nathan Fulton, Jake Lorocco) -- [YouTube recording](https://www.youtube.com/watch?v=WFm0nao9hlY)
- [dev.to](https://dev.to/aairom/meeting-mellea--4ge2): "Meeting mellea!!!"
- [aitech365](https://aitech365.com/news/ibm-research-introduces-mellea-a-structured-programmable-library-for-generative-computing/): "IBM Introduces Mellea"
- [mellea.ai](https://mellea.ai/) project website
- [IBM BeeAI Workshop](https://ibm.github.io/beeai-workshop/opentech/mellea/overview/) with mellea content

**Branded search works.** Searching "mellea python" or "mellea llm" returns a clean page of mellea-related results (PyPI, GitHub, mellea.ai, docs.mellea.ai, IBM Research blogs). The name is distinctive and has no meaningful competition.

**Category/problem search: invisible.** When someone searches for the *problem* mellea solves, mellea doesn't appear:
- "structured output python llm" -- top 10 results mention Instructor, Outlines, Pydantic, magentic, BAML, Marvin, LangChain, PydanticAI. No mellea.
- "langchain outputparser alternative" -- all results are LangChain's own docs. No mellea.
- "ollama structured output python" -- Ollama docs, Instructor's Ollama page, blog posts. No mellea despite Ollama being a core backend.
- Paul Simmering's widely-read [comparison of 10 structured output libraries](https://simmering.dev) does not include mellea.
- "Instructor vs" comparisons discuss BAML, PydanticAI, Outlines, raw JSON mode. No mellea.

**Community signals: near zero.**
- Zero Reddit threads about mellea (the library)
- Zero Hacker News submissions
- Zero StackOverflow questions
- Zero appearances in any framework comparison/listicle/benchmark post
- The dev.to articles appear to be from IBM-adjacent authors, not independent developers

This is the core of the discoverability problem: people who already know mellea can find it, but people searching for solutions to the exact problems mellea solves will never encounter it.

**Scale context** (monthly PyPI downloads, GitHub stars):
| Package | Downloads/month | GitHub stars | Context |
|:---|:---|:---|:---|
| LangChain | ~200M | 100K+ | Ecosystem incumbent |
| PydanticAI | ~9.7M | N/A | Rising fast; Pydantic team backing |
| Instructor | ~8.6M | ~11K | Dominant structured output library |
| Outlines | ~1.4M | ~10K | Constrained decoding library |
| **Mellea** | **~13K** | **313** | Early stage; ~650x gap to Instructor |

The natural sequencing: fix FIRST SUCCESS (people who do find us should succeed), then invest in DISCOVER (bring more people to the door with developer-targeted content), then build for REAL USE and ADVOCATE. This is the structure behind the phased plan in Section 10.

### 3.1 The hidden adoption barrier: install weight

**This may be the single most impactful structural issue for adoption.**

`pip install mellea` currently pulls ~500MB+ of dependencies because the core package includes everything:

| Core dependency | Why it's there | Who actually needs it |
|:---|:---|:---|
| `openai`, `ollama` | Backend SDKs | Most users (good) |
| `pydantic`, `jinja2` | Core abstractions | All users (good) |
| `llm-sandbox[docker]` | Code interpreter tool | Only users running sandboxed code |
| `math_verify`, `rouge_score` | MajorityVotingSamplingStrategy | Only users doing majority voting |
| `granite-common` | Granite intrinsics & adapters | Only Granite model users |
| `huggingface-hub` | Model registry access | Only HF/upload users |
| `fastapi`, `uvicorn` | `m serve` CLI | Only users serving APIs |
| `pillow` | Image processing | Only vision model users |
| `typer`, `click` | CLI framework | Only CLI users |
| `mistletoe` | Markdown parsing | Only MarkdownRequirement users |

**Compare to competitors:**
- `pip install instructor`: ~10MB (openai + pydantic + tenacity). Done in seconds.
- `pip install pydantic-ai`: ~15MB. Equally fast.
- `pip install mellea`: ~500MB+. Minutes to install. Docker dependency.

A developer who just wants to try `@generative` with OpenAI should not need to install Docker sandboxing, ML validation libraries, and a web framework. **This is a structural barrier that no amount of tutorials can overcome** -- if the install is slow and heavy, people abandon before they even run code.

**Recommendation**: Restructure dependencies so that `pip install mellea` gives you the minimal core (`@generative`, `start_session`, basic sampling, Ollama + OpenAI backends) in under 30 seconds and under 50MB. Move everything else to optional extras:
- `mellea[serve]` for FastAPI/uvicorn
- `mellea[voting]` for math_verify/rouge_score
- `mellea[granite]` for granite-common, intrinsics
- `mellea[sandbox]` for llm-sandbox
- `mellea[vision]` for Pillow
- Keep existing `mellea[hf]`, `mellea[vllm]`, `mellea[litellm]`, etc.

This is a code change, not a content change, but it directly serves adoption. It should be a Phase 1 item.

---

## 4. Who We Target

### 4.1 Primary audiences

| Audience | Size signal | Their pain | How they find us |
|:---|:---|:---|:---|
| **Frustrated LangChain users** | "OutputParserException" has 10K+ Stack Overflow/GitHub hits | Brittle parsers, retry hell, graph complexity | Search: "LangChain OutputParserException fix", "LangChain alternative" |
| **Local LLM builders** (r/LocalLLaMA) | 600K+ subreddit members | Models that "yap", can't force JSON, no structured output | Search: "Llama force JSON output", "Ollama structured output" |
| **FastAPI / Pydantic developers** | Millions of Pydantic users | Want LLM output as Pydantic models without glue code | Search: "Pydantic LLM", "structured LLM output Python" |
| **AI course students** (DeepLearning.AI, fast.ai) | Hundreds of thousands | Course code uses brittle patterns; regex parsing, manual retry | GitHub repos of course projects; tutorial comment sections |

### 4.2 Secondary audiences

| Audience | Their pain | Mellea angle |
|:---|:---|:---|
| **Kaggle / math reasoning researchers** | Need System 2 voting, best-of-N without boilerplate | `MajorityVotingSamplingStrategy(n=8)` -- one line |
| **IDE agent developers** (Cursor extensions, MCP tools) | Need structured reasoning over code | `@generative` functions as MCP tool endpoints via `m serve` |
| **Enterprise teams with existing stacks** | Can't rip-and-replace; need surgical improvements | "Inject mellea into one node" -- the Leaf Node Thesis |
| **Robotics / safety-critical developers** | Type safety isn't optional -- wrong types cause physical harm | Pydantic validation + sampling strategies = verified outputs |

### 4.3 Adoption model

Two paths, same library:

**Path A -- Standalone (greenfield):**
```
1. DISCOVER: Hit a pain point (parser fails, output is wrong, retry loop is ugly)
2. TRY:     pip install mellea, copy a @generative example, run it
3. EXPAND:  Add requirements, sampling strategies, more generative functions
4. BUILD:   Realise you don't need a framework -- plain Python + mellea is enough
```

**Path B -- Injection (brownfield/enterprise):**
```
1. DISCOVER: Existing LangChain/DSPy pipeline has a flaky node
2. INJECT:   pip install mellea, wrap that ONE node with @generative + validation
3. EXPAND:   Replace more nodes, add sampling strategies
4. SIMPLIFY: The orchestrator becomes thinner as mellea handles more
```

Both paths converge: tutorials must show **before/after at the single-function level**, not "here's how to build an app with mellea from scratch."

### 4.4 Entry point scenarios: "Why would I try this?"

This is the most important subsection in the document. Each scenario describes a **real developer with a real problem**, what they're currently doing, why it hurts, and the exact moment where mellea earns their attention. If we can't articulate these crisply, nothing else matters.

**Scenario A: "My OutputParser keeps crashing"**
- *Who*: A developer using LangChain with a local model (Ollama/Llama). They followed a tutorial, built a `prompt | llm | PydanticOutputParser` chain. It worked in the demo. In production it fails 30% of the time because the model wraps JSON in markdown or adds "Here is your JSON:" preamble.
- *What they've tried*: `OutputFixingParser`, `RetryOutputParser`, regex stripping, "respond ONLY in JSON" prompt hacks. Each fix breaks something else.
- *The mellea moment*: Show them the same extraction in 8 lines with `@generative`. It works on the first try because mellea uses constrained decoding (not post-hoc parsing). No parser, no retry, no regex.
- *What we need to make this work*: A runnable side-by-side (LangChain vs mellea) that they can copy-paste. Needs Ollama OR OpenAI variants. Must work in <2 minutes.
- *Current blocker*: Quickstart is broken (#335), @generative docs are missing (#1). No runnable side-by-side extraction comparison exists anywhere in the repo or docs.

**Scenario B: "I need JSON from my local model and it keeps yapping"**
- *Who*: An r/LocalLLaMA user running Llama 3 or Granite via Ollama. They want structured output (JSON) but the model adds conversational filler, markdown code fences, or refuses to output bare JSON.
- *What they've tried*: "You MUST respond with ONLY JSON", `json.loads()` with try/except and string stripping, regex extraction of JSON from markdown blocks. Fragile and model-version-dependent.
- *The mellea moment*: `@generative` with a Pydantic return type. Show the model "yapping" with raw Ollama, then show mellea producing clean JSON guaranteed at the token level. Zero retry needed.
- *What we need*: A single Python file they can run against their local Ollama. Show the raw Ollama output (with yapping) vs the mellea output (clean). Make it dramatic.
- *Current blocker*: No such example exists as a standalone file. The concept is proven in the codebase but not packaged for consumption.

**Scenario C: "My LLM gives the wrong answer 20% of the time"**
- *Who*: Any developer whose LLM pipeline "mostly works" but has an unacceptable failure rate. Could be extraction errors, classification mistakes, or reasoning failures.
- *What they've tried*: Better prompts, few-shot examples, temperature tuning. Maybe manual retry loops. The 80% success rate is frustrating because the failures are unpredictable.
- *The mellea moment*: Add `strategy=MajorityVotingSamplingStrategy(n=5)` to their existing call. Same code, same model, dramatically better accuracy. One line of configuration replaces an entire retry/voting architecture.
- *What we need*: A demo that shows accuracy jumping from ~60-70% to ~90%+ with a simple strategy swap. Include a benchmark (even a small one) so the claim is credible.
- *Current blocker*: No standalone "before/after reliability" demo exists. The `MajorityVotingSamplingStrategy` is implemented in `mellea/stdlib/sampling/majority_voting.py` but there's no self-contained demo showing the accuracy improvement.

**Scenario D: "I want to use mellea from inside my existing LangChain/DSPy pipeline"**
- *Who*: An enterprise developer or team with an existing LangGraph workflow. They can't rip it out, but they want to improve one flaky node.
- *What they've tried*: Various LangChain OutputParsers, or manual validation code inside their graph node.
- *The mellea moment*: `pip install mellea`, import the LangChain adapter, swap their `BaseChatModel` for one backed by mellea. Their graph stays the same. The node now has validation, repair, and constrained output.
- *What we need*: Framework integration adapters (#446, #449, #450). A "Mellea + LangGraph" reference example showing a real graph with one mellea-backed node.
- *Current blocker*: The adapters don't exist yet (#434 epic). This is the highest-effort item but potentially the highest-leverage for enterprise adoption.

**Scenario E: "I'm evaluating structured output libraries (Instructor vs PydanticAI vs ???)"**
- *Who*: A developer doing due diligence before committing to a library. They've seen Instructor (8.6M+ downloads), PydanticAI, and want to understand the options.
- *What they want*: Honest comparison. Code side-by-side. What does each do better?
- *The mellea moment*: Show that Instructor does great with API models but falls back to retry-based parsing for local models. PydanticAI has no sampling strategies. Mellea does constrained decoding locally AND has voting/repair/validation. It's the only one that works reliably across local and cloud models with pluggable reliability strategies.
- *What we need*: A comparison page/blog post. Not marketing fluff -- actual code showing the same task in each library with notes on what each handles well and poorly. Honest about where Instructor is better (simpler API for pure-API use cases).
- *Current blocker*: No comparison content exists. Instructor is not mentioned in any mellea documentation.

---

## 5. What We Solve: Pain Points and Features

### 5.1 Pain-to-feature mapping

| Pain point | Feature | Unique? | Code |
|:---|:---|:---|:---|
| **OutputParser breaks on local models** | `@generative` with Pydantic return types + constrained decoding | Yes (for local models) | `@generative` `def extract(text: str) -> UserProfile: ...` |
| **Manual retry/repair loops** | `RejectionSamplingStrategy(loop_budget=3)` | Easier than alternatives | Built into `instruct()` and `@generative` |
| **No way to vote across samples** | `MajorityVotingSamplingStrategy(n=8)` | Unique as pluggable strategy | One-line strategy swap |
| **LLM does math badly** | Hybrid Intelligence pattern: LLM extracts, Python computes | Design pattern (not code) | `@generative` for extraction + Python function for logic |
| **Prompt engineering is disconnected from code** | Docstrings ARE prompts; type hints ARE schemas | Unique DX | Function signature = full specification |
| **Switching backends is painful** | 7 backends, uniform API, `start_session("ollama")` | Comparable to LiteLLM | `start_session("openai", model_id="gpt-4o")` |
| **Can't validate LLM output beyond parsing** | Requirements system (Python, LLM-as-Judge, Markdown, Safety) | Richer than most | `Requirement` protocol with `ValidationResult` |
| **Process reward models are research-only** | SoFAI sampling strategy (implemented) | Unique in a library | `SoFAIStrategy(reward_model=...)` |
| **RAG answers can't be verified** | `check_answerability()`, answer relevance intrinsics | Comparable (Granite-specific) | RAG intrinsics module |
| **Safety checking is an afterthought** | Guardian module (PII, harm, jailbreak detection) | Comparable (Granite-specific) | `guardian.check(...)` |

### 5.2 The four selling layers

**Layer 1 -- "Just works" (Zero friction, immediate ROI)**
- `@generative` decorator: typed function -> structured LLM output
- Universal backend: Ollama, OpenAI, HuggingFace, vLLM, LiteLLM, Bedrock
- Constrained decoding on local models (no retry needed for JSON)
- *This is the entry point. Every tutorial starts here.*

**Layer 2 -- "Make it robust" (Low friction, high ROI)**
- Instruct-Validate-Repair: automatic retry with repair prompts
- Majority Voting: best-of-N with frequency analysis
- Requirements: composable validation (Python checks, LLM-as-Judge, format checks)
- *This is the "aha moment" -- add one line of config, get dramatically better results.*

**Layer 3 -- "Make it production" (Medium friction, specialized)**
- SoFAI: process reward models for inference-time scaling
- Budget Forcing: token budget enforcement
- Tool calling: LangChain/smolagents tool interop
- Code Interpreter: sandboxed Python execution
- OpenTelemetry: distributed tracing
- `m serve`: wrap generative programs as OpenAI-compatible API endpoints
- *This is for teams going to production.*

**Layer 4 -- "Make it smart" (Granite-specific, specialist)**
- RAG intrinsics: answerability, relevance, citation checking
- Guardian: harm/jailbreak/bias detection
- Activated LoRA: hot-swappable validation adapters
- `m decompose`: break complex prompts into structured subtasks
- *This is for IBM Granite users and enterprise teams.*

---

## 6. Competitive Differentiation: Honest Assessment

### 6.1 Where we are genuinely unique

1. **Pluggable sampling strategies as a first-class abstraction**: No other framework lets you swap between rejection sampling, majority voting, budget forcing, and process reward models with a single parameter change. This is mellea's deepest moat.

2. **Constrained decoding for local models via Outlines/xgrammar**: Instructor and PydanticAI rely on API-level JSON Mode. Mellea enforces structure at the logit level for local HuggingFace/vLLM models. This matters enormously for the local-LLM community.

3. **Functions-as-specifications**: The `@generative` decorator turns a Python function signature (name, docstring, type hints, Pydantic return type) into a complete LLM specification. No prompt templates, no chain definitions, no graph nodes. Just Python.

4. **The Validate-Repair loop as a primitive**: Not a pattern you implement yourself -- it's built into the sampling strategy layer. Requirements are composable, and repair is automatic.

5. **Mify -- brownfield LLM integration**: The `@mify` decorator lets you add LLM capabilities (query, transform) to existing Python classes. No other framework offers a "brownfield integration" pattern this clean for injecting AI into legacy codebases.

### 6.2 Where we are comparable (not unique, but well-executed)

- Multi-backend support (LiteLLM also does this)
- Tool calling interop (PydanticAI, smolagents also do this)
- LLM-as-Judge validation (LangChain, DSPy also do this)
- Structured output from API models (Instructor, PydanticAI also do this)

### 6.3 Where we would lose (be honest)

- **RAG-heavy use cases**: LlamaIndex is far more mature for indexing, chunking, and retrieval.
- **Multi-agent orchestration**: CrewAI, AutoGen, LangGraph are all ahead.
- **"I just want to ship a chatbot fast"**: OpenAI AgentKit, Claude Agent SDK, or even raw API + Instructor are faster paths.
- **Ecosystem integrations**: LangChain's connector catalog is unmatched.
- **Developer community size**: Smaller community means fewer StackOverflow answers, blog posts, and examples. This is our biggest non-technical gap.

### 6.4 Where we have feature gaps

| Gap | Impact | Priority | Notes |
|:---|:---|:---|:---|
| **No Instructor comparison** | Missing the closest direct competitor from messaging | **P0** | Instructor is the #1 search result for "structured LLM output Python". We need head-to-head demos. |
| **RAG intrinsics are Granite-only** | Limits value for OpenAI/Llama users | **P1** | Backend-agnostic refactoring needed |
| **Guardian is Granite-only** | Same issue | **P1** | Need generic safety checking path |
| **No streaming in @generative** | Users expect streaming for chat UX | **P1** | Session supports streaming but generative slots don't surface it |
| **No agent orchestration** | Users looking for "agents" won't find us | **P2** | By design -- we are the execution layer, not the orchestrator. But we should have a clear "mellea + LangGraph" story. |
| **No memory / persistence** | Long-running conversations need state | **P2** | ChatContext is in-memory only |
| **No explicit async @generative** | Async is expected in modern Python | **P1** | `aact()` exists but `@generative` async story is incomplete |
| **Limited docs / SEO** | People can't find us | **P0** | README is good but no blog posts, no comparison pages, no "vs" content |
| **No "copy-paste-and-run" experience** | Demos require Ollama setup | **P1** | Need Colab notebooks that work with OpenAI API key only |

---

## 7. Proposed Tutorials and Examples

### 7.1 The "Gateway Drug" series (P0 -- do these first)

These are single-file, < 50 line, copy-paste-and-run examples that demonstrate immediate value. Each shows a **before** (the pain) and **after** (the mellea way).

#### Tutorial 1: "Fix Your OutputParser in 5 Lines"
- **Target**: LangChain users hitting `OutputParserException`
- **Before**: LangChain `PydanticOutputParser` + `OutputFixingParser` + retry logic (~50 lines)
- **After**: `@generative` function with Pydantic return type (~8 lines)
- **Backend**: Ollama (local) and OpenAI (cloud) variants
- **Key message**: Delete your parser. Keep your types.

#### Tutorial 2: "Structured Output from Local Llama -- No Yapping"
- **Target**: r/LocalLLaMA users struggling with JSON output
- **Before**: Prompt hacks, regex stripping, "respond ONLY in JSON" instructions
- **After**: `@generative` with constrained decoding -- guaranteed valid JSON at the token level
- **Backend**: Ollama
- **Key message**: Stop asking nicely. Enforce it.

#### Tutorial 3: "Make Your LLM More Reliable in 1 Line"
- **Target**: Anyone with flaky LLM outputs
- **Before**: Single-shot generation that sometimes fails
- **After**: Add `strategy=MajorityVotingSamplingStrategy(n=5)` -- same code, dramatically better accuracy
- **Backend**: Any
- **Key message**: You don't need a better model. You need a better strategy.

#### Tutorial 4: "LLM Can't Do Math? Don't Make It."
- **Target**: Developers trying to get LLMs to calculate/reason
- **Before**: Elaborate chain-of-thought prompts that still fail on arithmetic
- **After**: Hybrid Intelligence -- `@generative` extracts parameters into Pydantic model, Python does the math
- **Backend**: Any (works great even with tiny models)
- **Key message**: Use the LLM for what it's good at. Use Python for the rest.

#### Tutorial 5: "Mellea vs Instructor: Where Each Shines"
- **Target**: Developers evaluating structured output libraries
- **Before**: Instructor `client.chat.completions.create(response_model=...)` -- API models only, retry-based
- **After**: `@generative` -- works on local AND API models, constrained decoding, pluggable strategies
- **Backend**: Both Ollama and OpenAI side-by-side
- **Key message**: Instructor is excellent for pure API use cases. Mellea covers the local model and agentic gap -- constrained decoding at the logit level, pluggable sampling strategies, and multi-step validation. Be honest about where Instructor is simpler (pure API, fewer dependencies).

### 7.2 The "Level Up" series (P1 -- do after gateway)

These show intermediate patterns for users who've adopted the basics.

#### Tutorial 6: "Add Validation Without Rewriting Your Code"
- Show the Requirements system: Python requirements, LLM-as-Judge, chained validation
- Before: manual `if` checks after generation
- After: `instruct(..., requirements=[MyRequirement()])` with automatic repair

#### Tutorial 7: "Compose Generative Functions Like Regular Python"
- Show how `@generative` functions compose: output of one is input to another
- Pre/postconditions with contract-oriented programming
- The "generative pipeline as a Python call stack" pattern

#### Tutorial 8: "Plug Mellea Into Your LangGraph"
- The "Leaf Node Thesis" in practice
- Build a LangGraph workflow but use `@generative` for the execution nodes
- Show how mellea handles validation/retry so the graph stays simple

#### Tutorial 9: "Serve Your Generative Program as an API"
- `m serve` to wrap a `@generative` function as an OpenAI-compatible endpoint
- Show FastAPI integration for production deployment

#### Tutorial 10: "Process Reward Models: Inference-Time Scaling"
- SoFAI sampling strategy
- Best-of-N with reward model selection
- The research-to-practice bridge

### 7.3 The "Migration Recipes" (P1 -- concrete refactoring guides)

These show how to incrementally adopt mellea into existing codebases.

#### Recipe A: "Migrate a LangChain Extraction Chain"
- Take a real LangChain `prompt | llm | parser` chain
- Replace with `@generative` -- same result, 80% less code
- Keep the rest of the LangChain stack unchanged

#### Recipe B: "Migrate a Manual Retry Loop"
- Take a common pattern: `for attempt in range(3): try: result = llm(...); validate(result); except: ...`
- Replace with `instruct(..., strategy=RejectionSamplingStrategy(loop_budget=3))`

#### Recipe C: "Migrate a CrewAI Task Node"
- Replace a CrewAI task's execution with a mellea `@generative` function
- Keep the crew structure, improve the execution reliability

### 7.4 Notebooks for Colab (P0 -- lower barrier to entry)

**Colab viability**: Google Colab free tier provides ~12GB RAM, up to 12 hours runtime, and CPU/GPU access. For mellea tutorials using the OpenAI backend, free Colab is ideal -- no local setup, just an API key. For local model tutorials (Ollama), Colab is not suitable (Ollama doesn't install cleanly on Colab VMs -- this is exactly what #335 documents). The existing `generative-computing/mellea-tutorials` repo already has Colab notebook infrastructure.

**Strategy**: All Colab notebooks should use the **OpenAI backend** (or Watsonx for IBM-internal). Local model tutorials belong in the repo `docs/examples/` as standalone `.py` files, not Colab.

Update existing notebooks in `mellea-tutorials` and create new ones:

- Hello World (OpenAI variant)
- Structured Extraction (the "Fix Your OutputParser" tutorial as notebook)
- Majority Voting demo
- Hybrid Intelligence demo

---

## 8. Content and Distribution Strategy

### 8.1 "Vs" pages (SEO / discoverability)

Create short, honest comparison pages:
- **Mellea vs Instructor**: constrained decoding, local models, sampling strategies
- **Mellea vs LangChain OutputParser**: code comparison, reliability numbers
- **Mellea vs PydanticAI**: similar philosophy but mellea has sampling/validation layer
- **Mellea vs raw Python**: mellea IS Python, but with validation and repair built in

### 8.2 Where to publish

| Channel | Content | Audience |
|:---|:---|:---|
| r/LocalLLaMA | "Structured output from Llama without regex" | Local LLM builders |
| r/MachineLearning | "Pluggable sampling strategies for inference-time compute" | Researchers |
| Hacker News | "We deleted our LangChain OutputParser" migration story | Engineers |
| dev.to / Medium | Tutorial series (gateway drugs) | Intermediate developers |
| Latent Space Discord | Technical deep-dives | AI engineers |
| DeepLearning.AI forums | "Fix the brittle patterns in your course project" | Students |
| PyPI / GitHub README | Clear "5-minute quickstart" | Anyone evaluating |

### 8.3 The "Agentic Migration" experiment

An idea worth exploring: have an AI coding agent (Cursor, Claude Code) refactor brittle LangChain code into mellea code, using a mellea-specific instruction template. This would be both a demo and a distribution mechanism -- developers watch their own AI agent choose mellea over manual parsing. The repo already has a `docs/AGENTS_TEMPLATE.md` that teaches AI agents mellea patterns, which could serve as the basis for this. The concept is unproven but the viral potential is high.

---

## 9. What the Issue Tracker Tells Us (137 Open Issues)

The [GitHub issue tracker](https://github.com/generative-computing/mellea/issues) provides ground-truth signal about where the project needs attention and where external demand lies. All issue numbers below link to the tracker. Here are the key themes:

### 9.1 Reliability blockers (fix before promoting)

These issues would embarrass us if a new user hit them:

| Issue | Problem | Impact |
|:---|:---|:---|
| **#426** | Validation logic is wrong and needs rewriting | Core value prop is broken |
| **#427** | `is_computed`/`value` invariant violation, hard to debug | Users see confusing crashes |
| **#432** | Backends don't handle exceptions properly | Raw tracebacks instead of actionable errors |
| **#404** | Tool calling broken with Pydantic model parameters | Tool use demos fail |
| **#378** | HuggingFace backend memory blowup on repeated instruct() | OOM on basic usage |
| **#335** | Colab Hello World broken (Ollama install fails) | First impression is broken |
| **#383** | Tool examples broken after MelleaTool refactor | Examples don't run |

**Verdict**: We cannot promote mellea to new users until at least #426, #432, #335, and #383 are fixed. These are the "front door" -- if the quickstart or core validation doesn't work, nothing else matters.

### 9.2 Framework integration adapters (highest-leverage growth work)

A brand-new epic (#434, #446, #449, #450) aims to make mellea a **drop-in backend for LangChain, DSPy, and CrewAI**:

| Issue | Integration |
|:---|:---|
| **#446** | LangChain `BaseChatModel` wrapper backed by mellea |
| **#449** | DSPy LM driver for mellea backends |
| **#450** | CrewAI LLM adapter for mellea backends |
| **#447** | Core adapter interface definition |
| **#451** | Integration testing infrastructure |
| **#452** | Package structure for integrations |

This is the **Leaf Node Thesis made real**: users keep their orchestrator but get mellea's reliability at the execution layer. This aligns perfectly with our positioning and is arguably the single highest-leverage work for adoption.

### 9.3 Documentation is the biggest non-code gap

17 open documentation issues. Key themes:

- **No working quickstart** (#437, #441, #335) -- the Colab doesn't work, tutorial.md is called "bad docs worse than no docs" (#429)
- **Core concepts unexplained** (#76) -- no diagram showing Components vs CBlocks vs Backends vs Contexts vs Sessions
- **Prompt internals opaque** (#81) -- users don't understand how Python objects become prompts
- **@generative is underdocumented** (#1) -- this is issue NUMBER ONE and still open
- **Examples lack READMEs** (#350, closed) and **broken code samples** (#199, #182)

### 9.4 Feature requests that align with our strategy

| Issue | Feature | Strategy alignment |
|:---|:---|:---|
| **#409** | MCP tool calling | MCP is becoming universal standard |
| **#403** | Streaming for sampling results | Production UX requirement |
| **#401** | Iterative search / deep research pattern | High-value starter template |
| **#400** | Mellea programs as tools | Composability story |
| **#389** | Configuration file support | DX improvement |
| **#454** | Self-repairing requirements | Extends the validate-repair moat |
| **#438** | Starter templates: ReACT, multi-agent, HITL | Tutorials people are asking for |
| **#440** | Pre-built requirements catalog | Lower barrier for validation |
| **#33** | `m serve` OpenAI API compliance | Enables drop-in deployment |

### 9.5 Test infrastructure assessment

The test suite is decent for a project at this stage but has structural issues that matter for adoption:

| Metric | Value | Assessment |
|:---|:---|:---|
| Total test functions | ~378 across 50 files | Good volume |
| Pure unit tests (no LLM needed) | ~150-160 | **Good** -- these run fast in CI |
| LLM-requiring tests | ~220-230 | Need Ollama/OpenAI/GPU to run |
| CI matrix | Python 3.10, 3.11, 3.12 | Missing 3.13 (outlines issue) |
| CI timeout | 90 minutes | **High** -- suggests heavy test runs |
| Coverage tracking | Configured (pytest-cov) but not reported externally | **No coverage badge or trend** |
| Flaky tests | #398 (model safety refusal), #384 (strict assertion) | Needs attention |
| Marker gaps | #419 (some tests run without required backend) | Needs attention |

**Key observation**: Most tests require a running Ollama instance with Granite models, meaning contributors cannot run the full suite without significant local setup. The pure unit tests (~160) should be clearly documented as the "contributor-friendly" test path.

**Recommendations for Phase 1**:
- Fix test marker gaps (#419) so `pytest -m "not ollama"` is reliable
- Add a coverage badge to the README (signals project health)
- Document the "contributor test path" (unit tests only, no LLM required)
- Address flaky tests (#398, #384) to make CI green consistently

### 9.6 Observability is becoming table-stakes

Three new epics (#442, #443, #444) formalize structured logging, metrics, and distributed tracing. The existing logging is acknowledged as problematic (#149, #277). PydanticAI and Strands Agents ship OpenTelemetry by default -- we need to catch up.

### 9.7 Issue tracker health

- 137 open issues is a lot for a project at this stage. Many are old (some from issue #1).
- Labels are inconsistent -- some issues have labels, many don't.
- The recent burst of well-structured epics (#434-#454) by @psschwei on Feb 10, 2026 represents a coordinated adoption/DevRel planning effort. This is a positive signal -- the team is already aligning on this direction.
- **Recommendation**: Adopt a consistent labelling scheme (see Section 9.8) and use a GitHub Project board for the adoption work stream.

### 9.8 Recommended labels and project structure

**Labels** (apply consistently across all issues):

| Label | Color | Purpose |
|:---|:---|:---|
| `adoption` | green | Directly serves adoption funnel |
| `documentation` | blue | Docs, tutorials, examples |
| `bug` | red | Something broken |
| `dx` | purple | Developer experience improvements |
| `research` | orange | Research features / innovation track |
| `integration` | teal | Framework adapters, MCP, tool interop |
| `P0-blocker` | red | Must fix before any outreach |
| `P1-important` | yellow | Important for adoption phases |
| `good-first-issue` | light green | Suitable for new contributors |
| `help-wanted` | green | Community contributions welcome |
| `stale` | grey | Needs triage -- close or revive |

**GitHub Project board**: Create "Mellea Adoption" project with columns:
- **Backlog** | **Phase 1: Front Door** | **Phase 2: Content** | **Phase 3: Retention** | **Done**

This gives leadership a single view of adoption progress and helps the team prioritize.

---

## 10. Priorities (Adoption-First)

The organizing principle: **every item is justified by where it unblocks the adoption funnel** (Section 3). Research features and internal architecture continue on their own track (see "Research-track items" below) -- the items here are specifically about getting more people to discover, try, and succeed with mellea.

### Phase 1: "Fix the front door" (FIRST SUCCESS)

Nothing else matters if people can't install mellea and run a working example in 5 minutes. This is the minimum bar before any outreach.

| Item | Issues | Funnel stage | Effort |
|:---|:---|:---|:---|
| **Slim down core dependencies** (see Section 3.1) | #453 | FIRST SUCCESS | Medium |
| **Fix validation logic** | #426 | FIRST SUCCESS / REAL USE | Medium |
| **Fix backend error handling** (actionable messages, not tracebacks) | #432, #427 | FIRST SUCCESS | Medium |
| **Fix all broken examples** (tools, Colab, notebooks) | #335, #383, #404 | FIRST SUCCESS | Small |
| **Write a real quickstart** (install, run, see output in <2 min) | #437, #441 | FIRST SUCCESS | Small |
| **Document @generative properly** (this is issue #1, literally) | #1, #76 | FIRST SUCCESS | Medium |
| **Delete or rewrite tutorial.md** | #429 | FIRST SUCCESS | Small |
| **Triage issue tracker** (close stale, label consistently, show project health) | -- | LAND | Small |
| **Fix test marker gaps and add coverage badge** | #419 | LAND / contributor health | Small |

**Exit criteria for Phase 1**: A developer with Python and either Ollama or an OpenAI API key can `pip install mellea` in under 30 seconds, copy one example, run it, and get a correct structured output in under 5 minutes. **Time to Hello World (TTHW) under 5 minutes.** No crashes, no confusing errors, no "see issue #X."

### Phase 2: "Give them a reason to come" (DISCOVER + LAND)

Once the front door works, create content that brings people to it. Each piece of content targets a **specific pain point** someone is already googling.

| Item | Target audience | Funnel stage | Effort |
|:---|:---|:---|:---|
| **Tutorial: "Fix Your OutputParser in 5 Lines"** | LangChain users | DISCOVER | Small |
| **Tutorial: "Structured Output from Local Llama"** | r/LocalLLaMA | DISCOVER | Small |
| **Tutorial: "Make Your LLM More Reliable in 1 Line"** | Anyone with flaky outputs | DISCOVER | Small |
| **Tutorial: "LLM Can't Do Math? Don't Make It."** | Chain-of-thought prompt engineers | DISCOVER | Small |
| **Tutorial: "Mellea vs Instructor: Where Each Shines"** | Structured output evaluators | DISCOVER | Small |
| **Colab notebooks** (OpenAI-only variants, no Ollama required) | Everyone | LAND | Small |
| **README rewrite** with before/after code hook in first 10 lines | Everyone | LAND | Small |
| **"vs" comparison pages** (vs Instructor, vs LangChain parsers, vs PydanticAI) | SEO / evaluators | DISCOVER | Medium |

**Exit criteria for Phase 2**: Searching "structured LLM output Python", "LangChain OutputParser alternative", or "Ollama JSON output" surfaces mellea content within the first 2 pages. At least 3 tutorials are runnable and linked from the README.

### Phase 3: "Make them stay" (REAL USE + ADVOCATE)

For users who got past the quickstart and want to solve real problems. This is where code changes and deeper features earn their keep -- but only the ones that directly serve retention and word-of-mouth.

| Item | Issues | Why (adoption reason) | Effort |
|:---|:---|:---|:---|
| **Framework adapters** (LangChain, DSPy, CrewAI) | #434, #446, #449, #450 | Lets users inject mellea without learning a new API -- biggest adoption multiplier | Large |
| **"Mellea + LangGraph" reference example** | #446 | Proves the Leaf Node Thesis with runnable code | Medium |
| **Migration recipes** (LangChain chain, manual retry loop, CrewAI task) | -- | Reduces switching cost from "I should try this" to "I just did" | Medium |
| **MCP tool calling** | #409 | Aligns with ecosystem direction; makes mellea usable from IDE agents | Medium |
| **Starter templates** (ReACT, deep research, HITL) | #438, #401 | People are explicitly asking for these (#438 exists as an issue) | Medium |
| **Pre-built requirements catalog** | #440 | Users shouldn't write validators from scratch; ship common ones | Medium |
| **Streaming for sampling results** | #403 | Production chat UX demands this | Medium |
| **Observability** (structured logging, tracing) | #442, #443, #444 | Table-stakes for production teams evaluating us | Medium |

**Exit criteria for Phase 3**: At least one "I migrated X from LangChain to mellea" blog post or testimonial exists. The framework adapters allow someone to `pip install mellea` and use it as a LangChain `BaseChatModel` without changing their graph.

### Research-track items (continuing in parallel, not blocked on adoption)

These are valuable innovation areas that the research team should continue pursuing. They are not deprioritized -- they run on a parallel track. The key constraint: **changes to core mellea should not break the stable install base.** The `mellea-contribs` repo (generative-computing/mellea-contribs, 11 forks, active) is the right home for experimental features until they stabilise.

| Item | Issues | Track | Notes |
|:---|:---|:---|:---|
| Self-repairing requirements | #454 | Research | Exciting extension of the validate-repair moat |
| RL tuning for agents | #405 | Research | Complements inference-time strategies; `trl` already a dependency (currently SFT-only via `m alora`). Microsoft Agent Lightning (mid-2025, GRPO/PPO for tool-use) validates this direction. |
| New sampling strategies (MCMC, importance sampling) | #157 | Research | Extends mellea's deepest differentiator |
| SoFAI enhancements | -- | Research | Process reward models are the cutting edge |
| Backend-agnostic RAG intrinsics | -- | Research | Large effort; Granite users already have it; generalise when demand appears |
| Backend-agnostic Guardian | -- | Research | Same pattern |
| Memory / persistence | -- | Infrastructure | Important for production but users can't get through the door yet |
| vLLM v1 migration | #334 | Infrastructure | Doesn't bring new users but keeps the stack current |
| Docker container | #139 | Infrastructure | Deployment convenience |
| Configuration file support | #389 | DX polish | Not an adoption blocker |

**Guardrail for research contributions**: Research items that touch core `mellea/` should include tests (use the marker system) and should not add new core dependencies. If a feature needs a heavy dependency, it goes in an optional extra or in `mellea-contribs`.

### Granite small models: a unique leverage point

IBM Granite models go down to very small sizes (Granite 4 Micro at 3B parameters) and are fully open source. This creates a unique pitch: **mellea + Granite Micro = structured AI on a laptop, no API key, no cost, no data leaving your machine.** This resonates strongly with the privacy-conscious local-LLM community and the education market.

However, this should be a *secondary* message, not the lead:
- **Lead with model-agnostic features** (`@generative`, sampling strategies, validation) -- these work with GPT-4o, Claude, Llama, Granite, anything.
- **Highlight Granite Micro as a bonus**: "Works with any model. Ships with optimised support for Granite -- including 3B models that run on a laptop."
- **Don't lock positioning to Granite**: Developers who only want OpenAI should feel equally welcome. The recent Granite 4 migration (#357) shows the codebase already handles this well -- Granite is a first-class backend, not the only one.

---

## 11. Key Insights (with evidence)

These are the most important strategic observations, each justified by what we can see in the code, the issue tracker, or the landscape today.

### 11.1 The strongest demos we could build (and why)

Looking at the codebase, four patterns stand out as mellea's most demonstrable advantages -- each maps to a real pain point and can be shown in a side-by-side comparison:

1. **Extraction: `@generative` vs OutputParser.** The code in `mellea/stdlib/components/genslot.py` shows that `@generative` turns a typed function signature into a complete LLM specification. Compare this to LangChain's `PydanticOutputParser`, which requires a parser object, a prompt template with `{format_instructions}`, a chain composition, and `try/except` retry logic. The mellea version is ~8 lines vs ~50. More importantly, mellea uses constrained decoding on local models (via `mellea/backends/huggingface.py` Outlines integration) -- guaranteed valid JSON at the token level, not post-hoc parsing that fails on "yapping" models. *Evidence: the genslot code exists and works; LangChain OutputParser pain is extensively documented on Stack Overflow, Reddit, and the Octomind case study.*

2. **Majority Voting: one-line strategy swap.** `mellea/stdlib/sampling/majority_voting.py` implements Minimum Bayes Risk Decoding as a `SamplingStrategy`. A user adds `strategy=MajorityVotingSamplingStrategy(n=5)` to their existing call -- no graph changes, no parallel runner, no aggregation code. In LangChain, the equivalent requires `RunnableParallel`, manual vote counting, and explicit graph wiring. Important caveat: voting amplifies the most common answer, which helps with random errors but not systematic reasoning failures. *Evidence: the code exists in stdlib; no competing framework offers pluggable sampling strategies as a first-class abstraction.*

3. **Hybrid Intelligence: LLM extracts, Python computes.** This is a design pattern, not a library feature, but mellea makes it natural: use `@generative` with a Pydantic return type to extract structured parameters, then pass the Pydantic object to a deterministic Python function. Works reliably even with tiny models (1B-3B) because the LLM only does extraction, not reasoning. *Evidence: the `@generative` + Pydantic pattern is the core of genslot.py; the tutorial examples in `docs/examples/tutorial/` show this composition. Small models are known to fail at multi-step arithmetic but succeed at extraction tasks -- this is well-documented in the ML literature and confirmed by models like Granite 4 Micro being positioned for extraction.*

4. **Instruct-Validate-Repair loop.** `mellea/stdlib/sampling/base.py` implements automatic retry with repair when requirements fail. `mellea/core/requirement.py` defines `ValidationResult` with result, reason, and score. The loop is built into the sampling strategy, not something users implement manually. *Evidence: the code exists; `RejectionSamplingStrategy` with `loop_budget` is the default strategy in `session.py`. Issue #426 indicates the validation logic needs a rewrite -- fixing this is prerequisite to promoting this feature.*

### 11.2 Positioning: the execution layer, not the orchestrator

Mellea should not try to compete with LangGraph, CrewAI, or AutoGen on orchestration. The framework landscape (Section 2) shows that orchestration is crowded, opinionated, and complaint-heavy. Instead, mellea competes at the **point of generation** -- the moment when you need an LLM to produce a correct, structured, validated result.

This means mellea is the **leaf node** in someone else's graph, the **reliable function** in someone else's pipeline. The framework integration epic (#434, #446, #449, #450) is the right strategic move -- it makes this positioning concrete by letting LangChain/DSPy/CrewAI users inject mellea without changing their orchestration.

*Evidence: the genta.dev 2026 framework guide recommends "Treat LangChain as the integration/runtime utilities, and let LangGraph manage state & control." This implicitly creates a market for better execution nodes inside these graphs. Mellea fills that role.*

### 11.3 Schema-as-code is an underrated DX advantage

Mellea's `@generative` turns Python constructs into LLM specifications: function name = task name, docstring = prompt, type hints = schema, Pydantic `Field(description=...)` = field-level instructions. This means prompt engineering becomes code -- version-controlled, refactorable, testable with standard Python tools.

Compare this to the typical approach: prompt templates in separate `.txt` files or string constants, format instructions injected at runtime, parsing logic separate from the schema. In mellea, the specification and the schema are the same object.

*Evidence: inspect `mellea/stdlib/components/genslot.py` lines 40-60: `create_response_format()` introspects the function's type hints to build a Pydantic response model dynamically. The docstring is read at decoration time and becomes the instruction. This is not a marketing claim -- it's how the code works.*

### 11.4 What already works well for DX

Not everything needs fixing. An audit of the actual first-run experience found:

- **Public API is clean and discoverable.** `mellea/__init__.py` exports exactly four things: `generative`, `start_session`, `MelleaSession`, `model_ids`. A new user can write `from mellea import generative, start_session` and be productive immediately.
- **Error messages for missing optional deps are excellent.** Each backend in `session.py` (lines 55-96) catches `ImportError` and gives a specific, actionable message (e.g., "Please install them with: pip install 'mellea[hf]'"). The tool integration in `backends/tools.py` does the same for LangChain and smolagents tools. This is better than most libraries.
- **Tutorial examples are self-contained and progressive.** `docs/examples/tutorial/sentiment_classifier.py` is 15 lines and demonstrates `@generative` end-to-end. `simple_email.py` progresses from basic to validation to sampling in 54 lines. These are good starting points.
- **Both Ollama and OpenAI work without optional deps.** The Ollama and OpenAI backends are core dependencies, so the most common paths don't require extras.

### 11.5 Technical adoption blockers in the current code

Things that will cause a new user to fail, based on the issue tracker and code inspection:

- **Validation is broken** (#426): The core value proposition (instruct-validate-repair) has fundamental logic errors. A user who follows the tutorial pattern will hit incorrect validation behaviour.
- **Backends crash opaquely** (#432, #427): `is_computed`/`value` invariant violations and unhandled exceptions during generation produce raw Python tracebacks instead of actionable error messages.
- **HuggingFace backend leaks memory** (#378): Repeated `instruct()` calls cause OOM. A user running the tutorial examples in a loop will hit this.
- **Tool calling is broken for Pydantic models** (#404): The `MelleaTool` wrapper doesn't handle Pydantic parameters correctly, so tool-use demos fail.
- **Colab quickstart doesn't work** (#335): The hello-world notebook fails because the Ollama install step is broken in the Colab environment.
- **Core install is ~500MB+** (see Section 3.1): `pip install mellea` pulls Docker sandboxing, ML validation libraries, a web framework, and Granite-specific packages. This is the biggest structural barrier -- `pip install instructor` takes seconds; `pip install mellea` takes minutes.
- **Python 3.13 compatibility**: `outlines` (used for constrained decoding in the HuggingFace backend) has Rust compilation issues on Python 3.13. Users should be guided to Python 3.12.

*Evidence: all from the GitHub issue tracker, confirmed open.*

---

## 12. Proposed Taglines (for discussion)

- **"Generative programs, not generative spaghetti."**
- **"Your functions. Your types. Your LLM."**
- **"Stop asking your LLM nicely. Enforce it."**
- **"Keep your orchestrator. Fix your execution."**
- **"The last parser you'll ever write is no parser at all."**

---

## 13. Open Questions for the Team

All framed through the adoption lens:

1. **What's the single most impactful first tutorial?** Scenario A (OutputParser fix) targets the biggest pain with the smallest effort. Scenario B (local JSON) targets the most passionate community. Scenario C (reliability boost) has the most universal appeal. We should pick one, make it perfect, and ship it before starting the others.

2. **Framework adapters vs gateway tutorials -- sequencing?** Adapters (#434-#452) let existing LangChain/DSPy/CrewAI users inject mellea without learning a new API -- the biggest adoption multiplier for enterprise. Tutorials attract greenfield users. Both are high-leverage but compete for engineering time. **Recommendation**: Tutorials first (smaller effort, prove the story), adapters second (larger effort, scale the story).

3. **How much should we lean into "local-first"?** The constrained decoding story is genuinely unique for local models and the r/LocalLLaMA community is passionate and evangelical. But OpenAI API users are a larger market. **Recommendation**: Lead with local (it's our unique angle), but every tutorial should have an OpenAI variant too.

4. **Should we triage the 137 open issues before promoting?** Issue #1 (`Better @generative documentation`) being open since inception sends a signal. A developer evaluating mellea will look at the issue tracker. 137 open issues with inconsistent labels looks unmaintained. **Recommendation**: Yes -- a triage pass (close stale, label, milestone the P0s) should be part of Phase 1.

5. **Do we need an "easy try" experience beyond Colab?** Colab notebooks (OpenAI-only, no Ollama) are the minimum. A hosted playground (like Vercel's AI SDK playground) would be ideal but is high-effort. **Recommendation**: Fix Colab first (#335). Consider a playground only after Phase 2 proves demand.

6. **How honest should comparison content be?** The best DevRel content acknowledges where competitors are better. Instructor is simpler for pure-API use cases. LangGraph is better for complex state machines. Saying so builds trust and makes our strengths more credible. **Recommendation**: Very honest. "Use Instructor if you only need OpenAI. Use mellea if you need local models, sampling strategies, or validation."

7. **Granite-specific features: promote or de-emphasize?** RAG intrinsics and Guardian are Granite-only. Promoting them limits the perceived audience. **Recommendation**: De-emphasize in adoption content. Position them as "if you use Granite, you get bonus capabilities" rather than leading with them. The gateway should be model-agnostic features (@generative, sampling, requirements).

---

## 14. The Ecosystem: Repositories and Roles

The `generative-computing` GitHub org contains 5 repositories. Understanding their roles clarifies where adoption work should land:

| Repository | Role | Stars | Activity |
|:---|:---|:---|:---|
| **mellea** | Core library. Stable API surface. | 313 | Very active (Feb 2026) |
| **mellea-contribs** | Incubation for community/experimental contributions | 3 | Active (5 open PRs, Jan 2026) |
| **mellea-tutorials** | Colab-friendly notebooks | 3 | Last updated Jan 2026 |
| **docs** | Documentation site (MDX, docs.mellea.ai) | 1 | Stale (Nov 2025) |
| **blog** | Generative Computing blog | 1 | Stale (Oct 2025) |

**Key implications for adoption work**:
- Gateway tutorials (Section 7.1) go in **mellea** `docs/examples/` and **mellea-tutorials** (Colab variants)
- Framework adapters (#434 epic) should start in **mellea-contribs** and graduate to **mellea** when stable
- The **docs** site needs updating as part of Phase 1 -- it's 3 months stale
- The **blog** should be revived for comparison content and migration stories (Phase 2)

---

## 15. Proposed New Issues

These issues would track the adoption work described in this document. Each is scoped to be a single allocatable work item or discussion.

### Code / Infrastructure
| Proposed issue | Type | Phase | Notes |
|:---|:---|:---|:---|
| Slim core dependencies: move llm-sandbox, math_verify, rouge_score, granite-common, fastapi to optional extras | Engineering | Phase 1 | Highest-impact structural change for adoption (Section 3.1) |
| Add coverage badge to README and CI coverage upload | Engineering | Phase 1 | Project health signal |
| Fix test marker gaps (#419) and document contributor test path | Engineering | Phase 1 | Lower barrier for contributors |
| Create OpenAI-only Colab quickstart notebook | Engineering | Phase 1 | Replace broken Ollama-based Colab (#335) |
| `@generative` as MCP tool endpoint (extend `m serve`) | Engineering | Phase 3 | Makes mellea's unique features available via MCP |

### Content / DevRel
| Proposed issue | Type | Phase | Notes |
|:---|:---|:---|:---|
| Write "Fix Your OutputParser in 5 Lines" tutorial with runnable code | Content | Phase 2 | Gateway tutorial #1 |
| Write "Structured Output from Local Llama -- No Yapping" tutorial | Content | Phase 2 | Gateway tutorial #2 |
| Write "Mellea vs Instructor: Where Each Shines" comparison page | Content | Phase 2 | SEO + honest positioning |
| Rewrite README opening with before/after code hook | Content | Phase 2 | First 10 lines must sell |
| Publish r/LocalLLaMA post: "Guaranteed JSON from Ollama" | Outreach | Phase 2 | Highest-passion community |
| Submit to Paul Simmering's structured output comparison | Outreach | Phase 2 | Fill the gap (Section 3.0) |

### Project Management
| Proposed issue | Type | Phase | Notes |
|:---|:---|:---|:---|
| Issue triage pass: close stale issues, apply consistent labels | Ops | Phase 1 | See Section 9.8 for label scheme |
| Create "Mellea Adoption" GitHub Project board | Ops | Phase 1 | Track all adoption work |
| Update docs site (docs.mellea.ai) to match v0.3.0 | Ops | Phase 1 | Site is 3 months stale |

---

## Appendix A: Feature Inventory (v0.3.0)

### Backends
Ollama, OpenAI, HuggingFace (local), vLLM, LiteLLM, Bedrock, Watsonx (deprecated)

### Sampling Strategies
RejectionSampling, MajorityVoting, BudgetForcing, SoFAI

### Components
Instruction, Message, Chat, GenerativeSlot (@generative), MObject, SimpleComponent, RichDocument

### Requirements
LLMaJRequirement, ALoraRequirement, PythonRequirement, MarkdownRequirement, ToolRequirement, SafetyGuardian

### CLI Tools
`m serve`, `m decompose`, `m alora`, `m eval`

### Integrations
LangChain tools, smolagents tools, Docling documents, OpenTelemetry, MCP (via m serve)

### Context Types
SimpleContext (stateless), ChatContext (conversational with window)

---

## Appendix B: Evidence Sources

| Source | URL / Location | What it tells us |
|:---|:---|:---|
| **Mellea codebase** (v0.3.0) | [github.com/generative-computing/mellea](https://github.com/generative-computing/mellea) | Feature inventory, architecture, capabilities and gaps |
| **GitHub issue tracker** | [github.com/generative-computing/mellea/issues](https://github.com/generative-computing/mellea/issues) | 137 open issues: bugs, feature demand, documentation gaps |
| **PyPI** | [pypi.org/project/mellea](https://pypi.org/project/mellea/) | Package distribution, version history |
| **genta.dev 2026 framework guide** | [genta.dev/resources/best-ai-agent-frameworks-2026](https://genta.dev/resources/best-ai-agent-frameworks-2026) | Competitive landscape, framework recommendations |
| **Instructor** | [pypi.org/project/instructor](https://pypi.org/project/instructor/) | ~8.6M monthly downloads; closest competitor for structured output |
| **PydanticAI** | [pypi.org/project/pydantic-ai](https://pypi.org/project/pydantic-ai/) | ~9.7M monthly downloads; rising fast with Pydantic team backing |
| **PyPI stats for mellea** | [pypistats.org/packages/mellea](https://pypistats.org/packages/mellea) | ~13K monthly downloads (Feb 2026) |
| **PyData Boston 2025 talk** | [youtube.com/watch?v=WFm0nao9hlY](https://www.youtube.com/watch?v=WFm0nao9hlY) | "Generative Programming with Mellea" -- Nathan Fulton, Jake Lorocco |
| **TheNewStack article** | [thenewstack.io](https://thenewstack.io/ibms-mellea-tackles-open-source-ais-hidden-weakness/) | "IBM's Mellea Tackles Open Source AI's Hidden Weakness" |
| **IBM Research blogs** | [research.ibm.com](https://research.ibm.com/blog/generative-computing-mellea) | Launch blog + lead engineer interview |
| **r/LocalLLaMA** | [reddit.com/r/LocalLLaMA](https://reddit.com/r/LocalLLaMA) | 600K+ members; recurring "force JSON output" and "yapping" threads |
| **MCP / Linux Foundation** | [modelcontextprotocol.io](https://modelcontextprotocol.io) | MCP becoming universal standard; co-founded by Anthropic, OpenAI, Google, Microsoft, AWS |
| **Outlines** | [github.com/dottxt-ai/outlines](https://github.com/dottxt-ai/outlines) | Constrained decoding library mellea integrates for local model structured output |
| **mellea.ai** | [mellea.ai](https://mellea.ai/) | Project website |
| **docs.mellea.ai** | [docs.mellea.ai](https://docs.mellea.ai/) | Documentation site |
| **GitHub repo stats** | [github.com/generative-computing/mellea](https://github.com/generative-computing/mellea) | 313 stars, 77 forks (Feb 2026) |
| **`docs/AGENTS_TEMPLATE.md`** | In mellea repo | Existing template for AI coding agents to learn mellea patterns |
| **Simmering structured output comparison** | [simmering.dev](https://simmering.dev) | Lists 10 libraries; mellea absent -- a concrete SEO target |
| **mellea-contribs** | [github.com/generative-computing/mellea-contribs](https://github.com/generative-computing/mellea-contribs) | Incubation repo for community contributions (11 forks, 5 open PRs) |
| **mellea-tutorials** | [github.com/generative-computing/mellea-tutorials](https://github.com/generative-computing/mellea-tutorials) | Colab-friendly notebooks for tutorials |
| **Mellea test suite** | `test/` directory, `conftest.py`, `.github/workflows/quality.yml` | 378 tests, 50 files; CI on Python 3.10-3.12; coverage configured |
| **OpenAI o1** (Sep 2024) | [openai.com/index/learning-to-reason-with-llms](https://openai.com/index/learning-to-reason-with-llms/) | Inference-time compute as a scaling paradigm |
| **DeepSeek R1** (Jan 2025) | [deepseek.com](https://deepseek.com/) | Open-source inference-time scaling |
| **Microsoft Agent Lightning** (mid-2025) | [arxiv.org/abs/2508.03680](https://arxiv.org/abs/2508.03680), [github.com/microsoft/agent-lightning](https://github.com/microsoft/agent-lightning) | RL-based agent training (GRPO/PPO); validates mellea's RL tuning direction (#405) |
| **Snell et al. test-time compute** (Aug 2024) | [arxiv.org/abs/2408.03314](https://arxiv.org/abs/2408.03314) | Foundational paper: optimal test-time scaling outperforms 14x larger models |
| **Octomind case study** (2024) | [octomind.dev/blog](https://octomind.dev/blog/why-we-no-longer-use-langchain-for-building-our-ai-agents/) | "We used LangChain in production for 12 months, then removed it" |
| **Google Colab FAQ** | [research.google.com/colaboratory/faq.html](https://research.google.com/colaboratory/faq.html) | Free tier: 12-hour max runtime, T4 GPU, ~12.7GB RAM |
| **MCP structured output spec** (Jun 2025) | [modelcontextprotocol.io](https://modelcontextprotocol.io/specification/2025-06-18/changelog) | `outputSchema` for tools -- aligns with mellea's Pydantic output |
| **Mellea MCP example** | `docs/examples/mcp/mcp_example.py` in repo | Working MCP server wrapping MelleaSession with sampling strategy |
| **Vibe-Data local LLM report** (Nov 2025) | [vibe-data.com](https://vibe-data.com/intelligence/posts/local-llm-ecosystem-nov-2025) | 695 local LLM models, Ollama at 154K stars, privacy as #1 driver |
| **LangChain criticism / post-framework fatigue** | [analyticsindiamag.com](https://analyticsindiamag.com/ai-features/why-developers-are-quitting-langchain/), [designveloper.com](https://www.designveloper.com/blog/is-langchain-bad/) | Multiple industry analyses of LangChain drop-off |
| **Sebastian Raschka inference scaling survey** (2025) | [sebastianraschka.com](https://sebastianraschka.com/blog/2025/state-of-llm-reasoning-and-inference-scaling.html) | Comprehensive taxonomy of inference-time compute methods |
| **Microsoft inference-time scaling survey** (Mar 2025) | [microsoft.com/research](https://www.microsoft.com/en-us/research/wp-content/uploads/2025/03/Inference-Time-Scaling-for-Complex-Tasks-Where-We-Stand-and-What-Lies-Ahead.pdf) | "Where We Stand and What Lies Ahead" |
