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

### The "Agentic Migration" Pattern (How to Demo)
Instead of just showing the "After" code, we can gamify the demo using our **Agent Template**:
1.  Provide a folder with `legacy_langchain.py` (a brittle script).
2.  Provide `AGENTS_TEMPLATE.md`.
3.  **The Challenge**: "Drop the Template into this folder and ask Cursor to 'Refactor legacy_langchain.py to use Mellea'."
4.  **The Win**: The user watches *their own AI* fix the code using Mellea's simple primitives. This proves Mellea is "Agent-Native".


### Demo B: The "Reliable RAG Grader" (Targeting DeepLearning.AI)
*   **Community**: RAG Evaluation / DL.AI Students
*   **The Hook**: "Get integer scores (1-5), not string hallucinations ('4/5')."
*   **Unique Value**: Token-level constraint (ge=1, le=5).

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
*   **Reasoning Field**: Improve accuracy effectively by adding `reasoning: str` to Pydantic models (Chain of Thought).
*   **Vector-less Router**: Use `Enum` return types for fast, zero-infra semantic routing.

## 6. Future Frontier: IDE Code Generation
Users are moving beyond "Chatboxes" to "Agents in the Editor". Mellea is uniquely positioned to handle the **Structure** required for robust code automation.

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

## 7. Strategic Artifacts (Created)
We have established the "Rules of the Road" for both contributors and users.
*   **For Contributors**: [`AGENTS.md`](../../../AGENTS.md) - The strict internal development standard.
*   **For Users**: [`docs/AGENTS_TEMPLATE.md`](../../AGENTS_TEMPLATE.md) - A "Copy-Paste" guide for users to teach their own agents (Cursor/Roo) how to write Mellea code.
    *   *Usage*: "Add this file to your repo to make Copilot stop writing LangChain code."
