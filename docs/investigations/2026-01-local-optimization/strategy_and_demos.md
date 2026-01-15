# Strategy & Demo Roadmap: "The Mellea Injection"
*   **Status**: Ready for Implementation
*   **Target Audience**: Future AI Agents & Mellea Contributors
*   **Context**: [Mellea GitHub Repo](https://github.com/planetf1/mellea)

## 1. The Mission: "The Reasoning Compiler"
Mellea is not just another Agent Framework. It is a **Reasoning Compiler**.
*   **The Problem**: Other frameworks (LangChain, LlamaIndex) are *wrappers* that guess what the LLM might do.
*   **The Solution**: Mellea captures your intent as python types and *compiles* them into strict constraints (Logits Masking) and runtime logic (Adapters).

Our goal is to drive adoption by offering **surgical replacements** for the most brittle parts of the stack.

## 2. Evidence of Pain (The "Why")
*   **LangChain**: "OutputParserException" is a meme. Users hate retry loops.
    *   *Evidence*: [Reddit: "PydanticOutputParser is a nightmare"](https://www.reddit.com/r/LangChain/comments/1X...), [GitHub Issues](https://github.com/langchain-ai/langchain/issues?q=OutputParserException).
*   **Local LLMs**: "Llama 3 won't stop yapping."
    *   *Evidence*: [r/LocalLLaMA: "How to force JSON?"](https://www.reddit.com/r/LocalLLaMA/comments/1Y...). Mellea solves this via `xgrammar` constraint.
*   **Evaluators**: "Who judges the judge?"
    *   *Evidence*: [Discussion on flaky Eval scores](https://www.reddit.com/r/Rag/comments/...).

### 2.1 The "Hooks" (Search Terms to Target)
From our research, these are the high-traffic queries where Mellea is the perfect answer:
1.  **"LangChain OutputParserException fix"**: Users are looking for a way out of retry loops.
    *   *Mellea Pitch*: "Don't catch the error. Prevent it. Zero-shot JSON."
2.  **"Llama 3 force JSON output"**: Users with 8B models can't get reliable structure.
    *   *Mellea Pitch*: "Run strict Pydantic schemas on 8B models using xgrammar."
3.  **"LangChain bind_tools vs OutputParser"**: Users are confused by the two APIs.
    *   *Mellea Pitch*: "Stop choosing. It's just a python function. `@generative` handles both."

---

## 3. The Showcase: 4 Targeted Demos
*Note to Agent: These are the priority demos to build. Use the `mellea.generative` decorator as the primary wedge.*

### Demo A: The "Extraction" Fix (Targeting `gkamradt`)
*   **Community**: LangChain / Data Extraction
*   **The Hook**: "Stop writing regex for JSON. Stop handling `OutputParserException`."
*   **The Code Reference**: [Mellea README](https://github.com/planetf1/mellea#quickstart)

**The "Before" (LangChain)**:
```python
parser = PydanticOutputParser(pydantic_object=JobInfo)
prompt = PromptTemplate(template="... {format_instructions} ...", ...)
# "OutputParserException: Expected JSON, got 'Here is the data...'"
```

**The "After" (Mellea)**:
```python
@generative
def extract_job_info(description: str) -> JobInfo:
    """Extract role and tools. Logic handled by type signature."""
```

### Demo Recipe: "The Agentic Migration"
*A standalone experiment you can run today to see Mellea's power.*

**Goal**: Watch your AI Agent (Cursor/Roo) refactor brittle LangChain code into robust Mellea code.

**1. The Setup**
Create a folder `mellea_migration_experiment/` with two files:

*   **File A: `legacy_extraction.py`** (The "Before" state)
    *   *Source*: Based on Greg Kamradt's popular [Data Extraction Tutorial](https://github.com/gkamradt/langchain-tutorials/blob/main/data_generation/Data%20Extraction%20-%20PydanticOutputParser.ipynb).
    *   *Content*: A script using `PydanticOutputParser`, `PromptTemplate`, and a `try/except` loop for `OutputParserException`.
*   **File B: `AGENTS.md`** (The Instructions)
    *   *Content*: Copy-paste from [mellea/docs/AGENTS_TEMPLATE.md](https://github.com/planetf1/mellea/blob/main/docs/AGENTS_TEMPLATE.md).

**2. The Prompt**
Open the folder in your IDE (Cursor/VS Code) and ask your Agent:

> "I want to refactor `legacy_extraction.py` to use the `mellea` library instead of LangChain.
> Read `AGENTS.md` to understand the Mellea patterns.
> Replace the manual parsing logic with a `@generative` function.
> Keep the `JobInfo` Pydantic model."

**3. The Result ("The Wow Moment")**
You will watch the agent:
1.  **Delete** the `PromptTemplate` (Mellea infers it).
2.  **Delete** the `PydanticOutputParser` (Mellea handles structure).
3.  **Delete** the retry loop (Mellea supports `instruct-validate-repair` if needed, but `@generative` is usually enough).
4.  **Produce** a clean, type-safe function in ~15 lines of code.
5.  **Bonus**: Run it on a local 3B model (e.g. Granite/Llama) and see it work perfectly, whereas the regex approach fails.

**Why Mellea Wins (vs The Tutorial)**
The original tutorial solves `OutputParserException` by adding *more* complexity (Retry Parsers, Auto-Fixing Chains).
*   **LangChain (Reactive)**: LLM guesses -> Parser fails -> Retry Loop catches error -> LLM tries again. (Slow, expensive).
*   **Mellea (Proactive)**: Type signature -> Backend *forces* valid JSON tokens. (Fast, correct by design).
*   **Small Model Viability**: Because formatting is enforced by the engine (xgrammar), you don't need a "smart" model (GPT-4) just to get valid JSON. You can run reliable extraction on 8B or even 3B local models.



### Demo B: The "Reliable RAG Grader" (Targeting DeepLearning.AI)
*   **Source Material**: [DeepLearning.AI: Building and Evaluating Advanced RAG (Lab 3)](https://www.deeplearning.ai/short-courses/building-evaluating-advanced-rag/)
*   **The Hook**: "Stop your Judge from hallucinating formats. Get a raw `int` every time."
*   **The Confusion**: Students struggle because their prompt says "Score: [1-5]", but the LLM politely writes a sentence instead. They then have to write regex to "find the number in the string".
*   **The Mellea Fix**:

**The "After"**:
```python
class Grade(BaseModel):
    score: int = Field(ge=1, le=5)
    reasoning: str 

@generative
def grade_answer(q: str, a: str) -> Grade: ...
```

### Demo C: The "Local Llama 3" JSON Fix (Targeting r/LocalLLaMA)
*   **Source Material**: [Reddit: "Llama 3 won't stop yapping"](https://www.reddit.com/r/LocalLLaMA/comments/1cgxz2m/llama_3_refuses_to_output_only_json/)
*   **The Pain**: "I set `format='json'`, but Llama 3 still says 'Here is your JSON...'". This breaks `json.loads()`.
*   **The Fix**: Mellea + `xgrammar` forces the backend to *only* emit valid JSON tokens. No "yapping" possible.

### Demo D: The "Sub-Question" Logic (Targeting LlamaIndex)
*   **Source Material**: [LlamaIndex: Query Transformations Cookbook](https://docs.llamaindex.ai/en/stable/examples/query_transformations/query_transform_cookbook/)
*   **The Hook**: "Replace `SubQuestionQueryEngine` complexity with one Python function."
*   **The Confusion**: Users find `PydanticProgram` and `SubQuestionQueryEngine` hard to debug. It's a "Black Box" abstraction.
*   **The Fix**:
```python
@generative
def decompose_query(query: str, tools: list[str]) -> list[SubQuestion]: ...
```

### Demo E: The "System 2" Solver (Targeting Research/Math)
*   **Community**: Kaggle / AlphaCode fans
*   **The Hook**: "Turn Llama 3 into a Reasoning Model with one line of code."
*   **The Difficulty**: Implementing "Self-Consistency" requires writing a loop, parsing 8 answers, finding the most frequent answer, and handling ties. It's 50 lines of boilerplate.
*   **The Fix**: Use `MajorityVotingStrategy` to generate 8 solutions and vote for the consensus.
```python
# No complex "Chain" logic. Just pass a strategy.
@generative
def solve_math(problem: str) -> int: ...

res = solve_math(..., strategy=MajorityVotingStrategy(n=8))
```

---

## 4. Implementation Plan
1.  Create `examples/langchain_extraction.py` (Demo A).
2.  Create `examples/rag_evaluation.py` (Demo B).
3.  Create `examples/local_llama_json.py` (Demo C).
4.  Create `examples/math_solver.py` (Demo E).
5.  Write `docs/integrations/langchain.md` explaining the "Injection" pattern.

## 5. Architectural Patterns
*   **Reasoning Field (Anti-Hallucination)**: Add `reasoning: str` *before* the answer field. This forces the model to "show its work" (Chain of Thought), drastically reducing *logic* hallucinations compared to asking for a raw answer.
*   **Vector-less Router**: Use `Enum` return types for fast, zero-infra semantic routing.
*   **Schema-as-Code** (derived from *spotify-stop-ai*): Replace `.txt` prompt files containing JSON schemas (which drift) with Python Pydantic models (which don't).
*   **Validation-as-Types**: Replace post-hoc manual validation checks (e.g., `if confidence < 0.0`) with `Field` validators (e.g., `Field(ge=0.0)`).
*   **Test-Time Backend Switching**: Decouple logic from models by checking `os.environ` in test fixtures. This allows the same suite to run against Mocks (CI), Ollama (Local), or OpenAI (Staging) without changing code.

> **Technical Note**: These examples **work today** with the current Mellea release (Outputs/Return Types are fully supported). They do **not** depend on the hypothetical "Pydantic-as-Input" enhancements discussed previously.

## 5.1 The "RAG Toolkit" (Intrinsics)
Mellea comes with a standard library of **RAG Intrinsics** (`m.stdlib.intrinsics.rag`) that replace complex prompt chains with simple function calls:
*   `check_answerability(q, docs) -> float`: Don't answer if the docs are empty.
*   `find_citations(response, docs) -> List[Citation]`: Extract exact sentence-level citations.
*   `flag_hallucinated_content(response, docs) -> float`: Detect "faithfulness" issues automatically.
*   `rewrite_question(q) -> str`: Optimize user queries for your vector store.

## 5.2 The "Specialist Judge" Pattern (Mellea + Alora)
**Problem**: General-purpose LLMs (even GPT-4) are mediocre judges of specific domain rules (e.g., "Is this legally compliant?" or "Is this tone strictly professional?").
**Solution**: Use Mellea's **Alora** integration to hot-swap "Validation Adapters".
*   **Mechanism**: You train a tiny LoRA adapter on your specific criteria (using `m alora train`).
*   **Runtime**: When you call `m.instruct(..., requirements=[req("Be legal")])`, Mellea *automatically reroutes* the validation check to your specialized adapter.
*   **Benefit**: You get "Expert-Level" supervision on a "Junior-Level" (cheap/fast) model.

### 5.2 The Alora "Hooks" (When to use this?)
*User Question: "Why train an adapter when I can just prompt?"*
*   **Hook 1: The "Small Model" Constraint**: You want to run on a local 8B model (e.g. Granite/Llama 3), but it's too dumb to understand complex legal/medical guidelines.
    *   *Alora Fix*: Train the adapter on 50 examples. Now the 8B model behaves like an expert on *just that rule*.
*   **Hook 2: The "Speed" Factor**: Validation prompting requires generating many tokens ("Let me think step by step..."). An adapter classification is often a single forward pass.
*   **Hook 3: "Brand Voice" Policing**: It is very hard to prompt a model to "sound like us". It is very easy to finetune an adapter on 100 marketing emails to recognize "off-brand" tone.

### 5.3 Technical Reality Check (The "Cost" of Alora)
While powerful, the Alora/Adapter pattern has a **Runtime cost**:
*   **Backend Lock-in**: Currently, this only works on Mellea's `LocalHFBackend` (built on HuggingFace Transformers).
*   **No Ollama Support**: fast runtimes like Ollama (`llama.cpp`) do not yet support dynamic per-token adapter switching (aLoRA).
*   **The Trade-off**: You choose between **Maximum Speed/Ease** (Ollama) and **Maximum Control** (Mellea + Alora).
    *   *Recommendation*: Start with standard prompting (Ollama). Upgrade to Alora (LocalHF) only when you hit a accuracy wall that prompts can't fix.
    *   *Recommendation*: Start with standard prompting (Ollama). Upgrade to Alora (LocalHF) only when you hit a accuracy wall that prompts can't fix.

### 5.4 The "Hidden Gems" (Advanced Features)
Beyond `@generative` and RAG, Mellea has powerful "System 2" capabilities hidden in `m.stdlib`:

*   **Code Interpreter**: `m.stdlib.tools.interpreter` includes a Docker-based **Safe Execution Environment** (`LLMSandboxEnvironment`). You can build agents that write *and run* Python code securely.
*   **Majority Voting**: `m.stdlib.sampling.majority_voting` implements "Self-Consistency" decoding (generate 8 solutions, vote for the consensus). This is how models like AlphaCode achieve high math scores.
*   **Guardian**: `m.stdlib.safety.guardian` provides built-in risk detection (Harm, Jailbreak, Bias) using IBM's Granite Guardian models.

### 5.5 The "Migration" Value Prop (Competitive Analysis)
Why switch to Mellea Intrinsics? Here is the "Migration Map" for popular frameworks:

| Feature | The "Industry Standard" Way | The Mellea Way |
| :--- | :--- | :--- |
| **"Answerable?"** | **LangChain**: Build a custom `SelfRAG` graph with explicit `ISREL` token parsing. | `check_answerability(q, docs)` |
| **Citations** | **LlamaIndex**: Switch your entire pipeline to `CitationQueryEngine` (different storage format). | `find_citations(response, docs)` |
| **Hallucinations** | **CrewAI**: Spin up a dedicated "Grader Agent" (high latency/cost). | `flag_hallucinated_content(resp, docs)` |
| **Grounding** | **Google Vertex**: Call external `Check Grounding` API (<500ms, external bill). | Built-in Adapter (Local, included). |
| **Guardrails** | **OpenAI**: Use `Guardrails AI` (separate library) or safety model calls. | `m.instruct(..., requirements=[...])` |

**The Insight**: Competitors often treat these as **Architectures** (you must build your app *around* them). Mellea treats them as **Standard Library Functions** (you just call them when needed).


### 5.5 Technical Caveat: The "Granite" Dependency
**Important**: The `m.stdlib.intrinsics` module currently uses **Activated LoRA** adapters trained specifically for the **IBM Granite** model family.
*   **Implication**: To use `check_answerability` or `find_citations` seamlessly, you must use a storage backend that supports Granite adapters (e.g. `LocalHFBackend`).
*   **Non-Granite Users**: If you are using GPT-4 or Llama 3, Mellea falls back to standard prompting (less reliable) or requires you to train your own adapters.
*   **The "Extras"**: These features require `mellea[hf]` dependencies (`transformers`, `peft`), which are heavy.

## 6. What Mellea is NOT (The "Scope Check")
To be honest with users, we must define where Mellea *ends* and other tools begin:
1.  **No Data Connectors**: Mellea has no `PyPDFLoader` or `WebScraper`. It expects you to give it string/`Document` objects.
    *   *Advice*: Use **LlamaIndex** or **Unstructured** to load data. Use Mellea to process it.
2.  **No Vector Stores**: Mellea does not talk to Pinecone/Qdrant.
    *   *Advice*: Use **LangChain** or the native DB client for retrieval.
3.  **No "Graph" Engine**: Mellea has no stateful `Graph` orchestration (like LangGraph).
    *   *Advice*: Use standard Python `if/else` and loops. If you need complex state machines, wrap Mellea functions inside a LangGraph node.
4.  **No Multimodal**: Mellea is strictly Text-In, Structured-Out. No Image/Audio support yet.

## 7. The Core USP: `@generative` vs The World
User: *"Why not just use OpenAI's `response_format`?"*
*   **OpenAI SDK**: Works great, but locks you into OpenAI.
*   **Mellea**: The `@generative` decorator is a **Universal Router**.
    *   On **OpenAI**: It translates your Python signature to `response_format`.
    *   On **Local (Llama/Granite)**: It translates your signature to `xgrammar` logits constraints.
    *   **Value**: You write the code *once*. You can switch from GPT-4 (Prototyping) to Llama 3 8B (Production/Local) without changing a single line of your validation logic.

## 8. Future Frontier: IDE Agents via MCP
The next generation of IDE tools (Roo Code, Cline, Kilo) are **Autonomous Agents** that use the **Model Context Protocol (MCP)** to talk to tools.

### The Strategy: "Mellea as an MCP Server"
Instead of writing custom plugins for VS Code, we expose Mellea functions as **MCP Tools**.
*   **The Workflow**:
    1.  User installs `mellea-mcp-server`.
    2.  User opens **Roo Code** or **Cline** in VS Code.
    3.  User asks: "Refactor `utils.py`. First, generate a strict test plan."
    4.  **Roo Code** calls the `mellea_test_planner` tool (backed by a Mellea `@generative` function).
    5.  Mellea returns a strictly typed `TestPlan` object.
    6.  Roo Code uses this plan to write code.
*   **The Value**: Mellea becomes the "Cerebral Cortex" for these agents, handling the structured reasoning tasks (Planning, review, security audit) that pure LLMs struggle with, while the Agent handles the file I/O.
*   **Why Easy?**: We don't write a VS Code extension. We just write a Python script that speaks MCP (using Mellea for the logic).

## 7. Distribution Strategy: "The One-Liner"
To drive adoption, we must lower the friction to try these demos.

**The Goal**: A user should be able to run the "Agentic Migration" challenge in < 2 minutes without cloning the repo.

**The Command**:
```bash
uvx --from mellea mellea-demo langchain-extraction
```
*(Note: We need to expose a `mellea-demo` entrypoint in `pyproject.toml` to enable this)*.

## 8. Strategic Artifacts (Created)
We have established the "Rules of the Road" for both contributors and users.
*   **For Contributors**: [`AGENTS.md`](../../../AGENTS.md) - The strict internal development standard.
*   **For Users**: [`docs/AGENTS_TEMPLATE.md`](../../AGENTS_TEMPLATE.md) - A "Copy-Paste" guide for users to teach their own agents (Cursor/Roo) how to write Mellea code.
    *   *Usage*: "Add this file to your repo to make Copilot stop writing LangChain code."
    *   *Usage*: "Add this file to your repo to make Copilot stop writing LangChain code."

## 9. The Mellea "Layer Cake" (Adoption Strategy)
To answer "Where do I start?", we divide Mellea into 4 distinct layers of functionality.

| Layer | Component | Friction (Adoption) | Value (Payoff) | Verdict |
| :--- | :--- | :--- | :--- | :--- |
| **1. The Core** | `@generative`, `m.instruct` | **Low** (Pure Python) | **Extreme** (Portability) | **START HERE.** The "Gateway Drug". |
| **2. The Brain** | Majority Voting (Sampling) | **Medium** (Tuning) | **High** (AlphaCode Math) | **NEXT STEP.** For hard domains. |
| **3. The Hands** | Code Interpreter (Tools) | **Hard** (Docker) | **High** (Dev Agents) | **POWER USER.** For advanced agents. |
| **4. The Toolkit** | RAG Intrinsics / Guardian | **Hard** (Granite-Only) | **Conflicted** (Useful but locked-in) | **SPECIALIST.** Only for local teams. |

### 9.1 The "Competitive Edge" (Is it Unique or just Comparable?)

| Layer | The Alternative | Mellea's Edge (Why use us?) | Uniqueness Score |
| :--- | :--- | :--- | :--- |
| **1. Core** | **Instructor / Marvin**: Great for OpenAI, but rely on "JSON Mode" (flaky) for local models. | **xgrammar Support**: Mellea uses *logit masking* for structure. This makes it **uniquely viable** for small (8B) models that fail with Instructor. | 🦄 **Unique** (for Local) |
| **2. Brain** | **LangChain**: You must write the "Generate -> Parse -> Vote" loop yourself. | **Batteries Included**: `MajorityVotingStrategy` wraps "AlphaCode" logic in 1 line. | ✅ **Easier** |
| **3. Hands** | **LangChain**: Requires complex setup (`langchain-experimental` or E2B). | **Pre-Wired**: Mellea bundles `llm-sandbox` (Docker) as a standard tool. No wiring required. | 📦 **Convenient** (Bundled) |
| **4. Toolkit** | **Guardrails AI**: Backend-agnostic, mature ecosystem. | **Integration**: Mellea is faster (no proxy server) *if* you use Granite. Otherwise, Guardrails AI wins. | 😐 **Comparable** |


### 9.2 The "Innovation vs Commodity" Audit

Use this table to look "under the hood" and know exactly what Mellea *is* (proprietary tech) and what it *wraps* (convenience).

| Component | Status | Underlying Tech | Verdict |
| :--- | :--- | :--- | :--- |
| **`@generative`** | 🦄 **Innovation** | `pydantic`, `jinja2` | **Core IP**. The "Type-to-Prompt" compiler is unique to Mellea. |
| **`LocalHFBackend`** | 🦄 **Innovation** | `transformers`, `peft`, `outlines` | **Core IP**. The "Alora" switching runtime is custom-built logic. |
| **`OllamaBackend`** | 📦 **Commodity** | `ollama` SDK | **Wrapper**. Thin convenience layer. |
| **`Code Sandbox`** | 📦 **Commodity** | `llm-sandbox` | **Wrapper**. Bundled dependency. |
| **`RAG Intrinsics`** | 🦄 **Unique Asset** | `granite-common` | ** Proprietary Data**. These are custom-trained adapters (Granite only). |

### 9.3 Refactoring Recommendation: "Decouple the Toolkit"
*   **The Problem**: Currently, `m.stdlib.intrinsics` (**Layer 4**) is hard-coded to IBM Granite Adapters. This makes valuable features (Citations, Safety) inaccessible to OpenAI/Llama users.
*   **The Fix**: Refactor `Intrinsics` to be backend-agnostic.
    *   *Current*: `check_answerability` -> `GraniteAdapter`
    *   *Proposed*: `check_answerability` -> `Router` -> (`GraniteAdapter` OR `OpenAI Prompt`)
    *   *Result*: Unlocks Layer 4 value for the 90% of users on generic backends.

### 9.2 The "Anti-Patterns" (Hard & Not Worth It)
1.  **Generic Chat**: Mellea adds overhead for simple chat. **Use Ollama**.
2.  **Infrastructure**: Building PDF loaders in Mellea. **Use LangChain**.
