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

## 2. Core Philosophy: "Building the Typed AI Runtime"
We are building the **runtime** that enables Generative Programming.
*   **Goal**: Enable users to treat LLMs as "Fuzzy CPUs".
*   **Values**:
    *   **Robustness**: The engine must never crash on bad inputs; it must handle retries/backoff transparently.
    *   **Invisibility**: Mellea's complexity should be hidden. Users see `@generative`, we see `AsyncGenerativeSlot`.

## 2. Coding Standards
### 2.1 The `@generative` Decorator (When to use it)
*   **Infrastructure Code** (`mellea/backends`, `mellea/core`): **DO NOT** use `@generative`. You are building the engine. Use standard, robust Python (httpx, asyncio, Pydantic).
*   **Standard Library / Examples** (`mellea/stdlib`, `examples/`): **DO** use `@generative`. We "eat our own dogfood" to build higher-level primitives.

#### Example: Adding a new capability
If you are adding a refined "Receipt Parser" to the standard library:
```python
# GOOD (Stdlib/Example): Uses Mellea's own primitives
@generative
def parse_receipt(text: str) -> Receipt: ...
```

If you are adding a new LLM Provider (e.g. Groq):
```python
# GOOD (Infrastructure): Uses raw Python/HTTP
class GroqBackend(BaseBackend):
    async def chat(self, ...):
        async with httpx.AsyncClient() as client: ...
```
*   **Type Hints**: ALL arguments and return types must be fully typed. This is how Mellea ensures reliability.
*   **Docstrings**: The docstring is the prompt. Be specific.

### 2.2 Testing & Validation
*   **Run Tests Locally**: `uv run pytest`.
*   **No External Calls in Unit Tests**: Mellea's core tests should not depend on OpenAI/Anthropic/Ollama availability unless tagged `@pytest.mark.integration`.
*   **Fixing Tests**: If you break a test, fix the **code**, not the test (unless the test was hallucinated).

### 2.3 Dependency Management

### 2.3 Dependency Management (Contributors Only)
*   **Tool**: We use `uv` for development. (Users will install via `pip`).
*   **Adding Deps**: `uv add <package>`. Keep dependencies minimal to ensure fast installs for users.
*   **Lockfile**: Always update `uv.lock`.

## 3. The "Agent Self-Review" Protocol
Before notifying the user, you **MUST** recursively verify your own work:

1.  **The Build Check**:
    *   Did I edit a file? -> Run `uv run pytest path/to/test.py`.
    *   Did I change dependencies? -> Run `uv sync`.
2.  **The Type Check**:
    *   Are all my new functions typed?
    *   Did I import from `typing`?
3.  **The "API Design" Check**:
    *   Did I leak implementation details (e.g. `http_client`) to the user?
    *   Did I maintain the "Zero Setup" promise? (Users shouldn't need to configure 10 objects to make a call).

## 4. Strategic Context (Where are we going?)
*   **Primary Goal**: "Mellea Injection" (Surgical replacement of brittle logic in other frameworks).
*   **Current Frontier**: IDE Integration (MCP Servers).
*   **Reference**: See `docs/investigations/2026-01-local-optimization/strategy_and_demos.md` for the current strategic roadmap.

## 5. Directory Structure Map
*   `mellea/core`: The runtime engine (Prompt Engineering, Retry Loops).
*   `mellea/controllers`: The components that manage tool use and control flow.
*   `mellea/backends`: Integration with LLM providers (HF, OpenAI, Ollama).
*   `mellea/stdlib`: Standard patterns (e.g. `RejectionSamplingStrategy`).
