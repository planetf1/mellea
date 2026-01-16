# Agent Guidelines for Mellea Contributors (`AGENTS.md`)
> [!IMPORTANT]
> **Role Distinction**:
> * **Building Mellea?** You are editing `mellea/core`, `backends`, or `stdlib`. Follow the "Internal Contributor" standards below.
> * **Using Mellea?** You are building a demo or a client app. Follow [`docs/AGENTS_TEMPLATE.md`](docs/AGENTS_TEMPLATE.md) for usage patterns.

## 1. Quick Reference (The "Must Knows")
```bash
# Standard Dev Loop
uv sync                     # Install dependencies & fix lockfile
uv run pytest               # Run all tests
uv run pytest -m integration # Run tests requiring API keys
```

## 2. Coding Standards (Internal Contributors)
*   **Type-Driven Development**: Mellea's strength is its types. ALL core functions must stay strictly typed.
*   **Minimalist Core**: Avoid adding complex "Chain" or "Graph" abstractions to the engine. We prefer standard Python control flow.
*   **Directory Map**:
    *   `mellea/core`: Low-level runtime (Context management, generation loops).
    *   `mellea/backends`: Provider implementations (HF, OpenAI, Ollama).
    *   `mellea/stdlib`: High-level generics (Genslots, Requirements, Sampling strategies).
    *   `mellea/templates` & `formatters`: Instruction string construction and output handling.

## 3. The "Feedback Loop" Rule
> [!TIP]
> If you encounter a recurring failure mode (e.g., "Small models keep missing JSON tags") or discover a new coding pattern, **UPDATE THIS FILE** or add a tip to the `docs/`. This ensures the next AI/Human collaborator benefits from your "pain".

### 3.1 Lessons from Demos (Gotchas & Tips)
*   **Small Model Reality**: Models like `llama3.2:1b` often fail at logic/math.
    *   *Tip*: Use **"Teacher Forcing"** (one-shot examples in the docstring) to guide reasoning.
    *   *Tip*: Use **"Hybrid Intelligence"** (LLM for extraction, Python for calculation). Avoid asking 1B models to solve math.
    *   *Tip*: Set **`temperature=0`** for logic puzzles to ensure deterministic reasoning paths.
*   **Boilerplate Avoidance**: Before writing a complex class, ask: "Can I do this with one `@generative` function and two `Requirement` objects?"

## 4. Strategic Position: "The Surgical Injection"
Mellea's primary goal is not to be a standalone "Agent Framework" but an **enhancement layer**.
*   When migrating from LangChain/LangGraph: Focus on replacing the most brittle nodes (Extraction, Validation) with Mellea types first.
*   Maintain compatibility: Ensure Mellea contexts and messages can be easily converted back to standard formats (see `examples/library_interop`).

## 5. Directory Structure Map
*   `mellea/core`: Low-level runtime (Context management, generation loops).
*   `mellea/backends`: Provider implementations (HF, OpenAI, Ollama, Watsonx).
*   `mellea/stdlib`: High-level generics (Genslots, Requirements, Sampling strategies).
*   `mellea/templates` & `formatters`: Instruction string construction and output handling.
*   `mellea/helpers`: Common utilities, logging, and model ID tables.

## 6. Agent Self-Review Protocol
1. **The Build**: Run `uv run pytest`.
2. **The Simplicity Check**: Did I write a 50-line state machine for a 5-line `@generative` task?
3. **The Documentation Check**: Are the docstrings (prompts) clear and concise?
