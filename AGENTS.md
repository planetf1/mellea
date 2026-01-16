# Agent Guidelines for Mellea Contributors (`AGENTS.md`)
> **For AI Agents:** Read this file before making any code changes **TO** the Mellea repository.
> (If you are looking for how to *use* Mellea in a project, see `docs/AGENTS_TEMPLATE.md`)

## 1. Quick Reference (The "Must Knows")
```bash
# Standard Dev Loop
uv sync                     # Install dependencies & fix lockfile
uv run pytest               # Run all tests
uv run pytest -m integration # Run tests requiring API keys (OpenAI/Anthropic)

# The "Self-Review" Check (Run BEFORE notifying user)
1. Did I break the build? (uv run pytest)
2. Did I export strict types? (Generative functions must return Pydantic/Types)
3. Did I over-engineer? (Prefer primitives over Classes)
````

## 2. Core Philosophy: "Typed & Deterministic"
Mellea is a library for **Generative Programming**, not "Chatbot Evaluation".
*   **Do**: Treat LLMs as "Fuzzy CPUs" that implement specific functions.
*   **Do**: Use standard Python control flow (`if`, `for`, `while`).
*   **Don't**: Create complex "Graph" abstractions or "Chains" unless necessary.
*   **Primary Primitive**: The `@generative` function.

## 2. Coding Standards
### 2.1 The `@generative` Decorator
When adding new capabilities, prefer **Generative Functions** over complex classes.
```python
# GOOD: Simple, typed, functional
@generative
def parse_receipt(text: str) -> Receipt:
    """Extract receipt details."""

# BAD: Over-engineered wrapper
class ReceiptParserAgent:
    def __init__(self, llm): ...
    def parse(self, text): ...
```
*   **Type Hints**: ALL arguments and return types must be fully typed. This is how Mellea ensures reliability.
*   **Docstrings**: The docstring is the prompt. Be specific.
*   **Hybrid Intelligence**: If a task involves arithmetic or exact logic, use the LLM to *Extract* parameters into a Pydantic model, then use a standard Python function to *Execute* the logic. Do not ask the LLM to do math.
*   **Small Model Support**: Mellea targets 1B-8B local models. Use "Teacher Forcing" (One-Shot examples in docstrings) for complex reasoning tasks.

### 2.2 Testing & Validation
*   **Run Tests Locally**: `uv run pytest`.
*   **No External Calls in Unit Tests**: Mellea's core tests should not depend on OpenAI/Anthropic/Ollama availability unless tagged `@pytest.mark.integration`.
*   **Fixing Tests**: If you break a test, fix the **code**, not the test (unless the test was hallucinated).

### 2.3 Dependency Management
*   **Tool**: We use `uv`.
*   **Adding Deps**: `uv add <package>`.
*   **Lockfile**: Always update `uv.lock`.

## 3. The "Agent Self-Review" Protocol
Before notifying the user, you **MUST** recursively verify your own work:

1.  **The Build Check**:
    *   Did I edit a file? -> Run `uv run pytest path/to/test.py`.
    *   Did I change dependencies? -> Run `uv sync`.
2.  **The Type Check**:
    *   Are all my new functions typed?
    *   Did I import from `typing`?
3.  **The "Simplicity" Check**:
    *   Did I write 50 lines of code where 5 lines of `@generative` logic would do?
    *   *Correction*: If yes, refactor to use Mellea's core primitives.

## 4. Strategic Context (Where are we going?)
*   **Primary Goal**: "Mellea Injection" (Surgical replacement of brittle logic in other frameworks).
*   **Current Frontier**: IDE Integration (MCP Servers).
*   **Reference**: See `docs/investigations/2026-01-local-optimization/strategy_and_demos.md` for the current strategic roadmap.

## 5. Directory Structure Map
*   `mellea/core`: The runtime engine (Prompt Engineering, Retry Loops).
*   `mellea/controllers`: The components that manage tool use and control flow.
*   `mellea/backends`: Integration with LLM providers (HF, OpenAI, Ollama).
*   `mellea/stdlib`: Standard patterns (e.g. `RejectionSamplingStrategy`).
