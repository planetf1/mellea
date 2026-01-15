# Strategy & Demo Roadmap: "The Mellea Injection"
**Status**: Ready for Implementation
**Target Audience**: Future AI Agents & Mellea Contributors
**Context**: [Mellea GitHub Repo](https://github.com/planetf1/mellea)

## 1. The Mission: "Better Together"
Our goal is to drive adoption of Mellea not by effectively asking users to "switch frameworks", but by offering **surgical replacements** for the most painful parts of their existing stack.

We believe that **Structured Generation** (Mellea's core competency) is the missing link in the modern AI stack. Users struggle with brittle regex parsers (LangChain), over-engineered "Programs" (LlamaIndex), and flaky JSON from local models.

**The Strategy**: specific, clickable demos that show Mellea solving a well-known community pain point in <10 lines of code.

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
*   **Community**: RAG Evaluation / DL.AI Students
*   **The Hook**: "Stop your Judge from hallucinating formats. Get a raw `int` every time."
*   **The Solution to Hallucination**:
    *   *Type I (Format)*: Model answers "The score is 4" instead of "4". **Mellea Fix**: Token masks generally prevent any token except digits.
    *   *Type II (Range)*: Model answers "10" on a 1-5 scale. **Mellea Fix**: `Field(ge=1, le=5)` validation.

**The "After"**:
```python
class Grade(BaseModel):
    score: int = Field(ge=1, le=5)
    reasoning: str 

@generative
def grade_answer(q: str, a: str) -> Grade: ...
```

### Demo C: The "Local Llama 3" JSON Fix (Targeting HuggingFace)
*   **Community**: r/LocalLLaMA / Self-Hosters
*   **The Hook**: "Make 8B models behave like GPT-4 for structure."
*   **The Pain**: Llama 3 is notoriously chatty. `format="json"` is often ignored on small models.
*   **The Fix**: Mellea + `xgrammar` backend forces the logits.

### Demo D: The "Sub-Question" Logic (Targeting LlamaIndex)
*   **Community**: LlamaIndex / Advanced RAG
*   **The Hook**: "Replace 'PydanticProgram' complexity with standard Python functions."
*   **The Fix**:
```python
@generative
def decompose_query(query: str, tools: list[str]) -> list[SubQuestion]: ...
```

---

## 4. Implementation Plan
1.  Create `examples/langchain_extraction.py` (Demo A).
2.  Create `examples/rag_evaluation.py` (Demo B).
3.  Create `examples/local_llama_json.py` (Demo C).
4.  Write `docs/integrations/langchain.md` explaining the "Injection" pattern.

## 5. Architectural Patterns
*   **Reasoning Field (Anti-Hallucination)**: Add `reasoning: str` *before* the answer field. This forces the model to "show its work" (Chain of Thought), drastically reducing *logic* hallucinations compared to asking for a raw answer.
*   **Vector-less Router**: Use `Enum` return types for fast, zero-infra semantic routing.
*   **Schema-as-Code** (derived from *spotify-stop-ai*): Replace `.txt` prompt files containing JSON schemas (which drift) with Python Pydantic models (which don't).
*   **Validation-as-Types**: Replace post-hoc manual validation checks (e.g., `if confidence < 0.0`) with `Field` validators (e.g., `Field(ge=0.0)`).
*   **Test-Time Backend Switching**: Decouple logic from models by checking `os.environ` in test fixtures. This allows the same suite to run against Mocks (CI), Ollama (Local), or OpenAI (Staging) without changing code.

> **Technical Note**: These examples **work today** with the current Mellea release (Outputs/Return Types are fully supported). They do **not** depend on the hypothetical "Pydantic-as-Input" enhancements discussed previously.

## 5.1 The "Specialist Judge" Pattern (Mellea + Alora)
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


## 6. Future Frontier: IDE Agents via MCP
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
