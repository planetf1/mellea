# Agent Guidelines for Mellea Contributors (`AGENTS.md`)
> [!IMPORTANT]
> **Role Distinction**:
> * **Building Mellea?** You are editing `mellea/core`, `backends`, or `stdlib`. Follow the "Internal Contributor" standards below.
> * **Using Mellea?** You are building a demo or a client app. Follow [`docs/AGENTS_TEMPLATE.md`](docs/AGENTS_TEMPLATE.md) for usage patterns.

## 1. Quick Reference (The "Must Knows")
```bash
# Setup
pre-commit install          # Install git hooks (REQUIRED for contributors)

# Standard Dev Loop
uv sync                     # Install dependencies & fix lockfile
uv run ruff check .         # Linting
uv run ruff format .        # Formatting
uv run pytest -m "not qualitative" # Fast loop (Unit tests only)
uv run pytest               # Full audit (Runs qualitative/slow tests)
uv run pytest -m integration # Run tests requiring API keys
```

## 2. Coding Standards (Internal Contributors)
*   **Type-Driven Development**: Mellea's strength is its types. ALL core functions must stay strictly typed.
*   **Minimalist Core**: Avoid adding complex "Chain" or "Graph" abstractions to the engine. We prefer standard Python control flow.
*   **Linting**: We use Ruff for linting and formatting. Ensure your code passes `ruff check` and is formatted with `ruff format` before submitting.

## 3. The "Feedback Loop" Rule
> [!TIP]
> * **Developing Mellea?** If you improve the core engine or find a bug, update **THIS FILE**.
> * **Building Agents?** If you discover a prompting trick or a new pattern (e.g., "Small models need X"), update [`docs/AGENTS_TEMPLATE.md`](docs/AGENTS_TEMPLATE.md).
>
> This ensures all future AI/Human collaborators benefit from your experience.

## 4. Strategic Position: "The Surgical Injection"
Mellea's primary goal is not to be a standalone "Agent Framework" but an **enhancement layer**.
*   **Migrating from LangChain**: Focus on replacing the most brittle nodes (Extraction, Validation) with Mellea types first.
*   **Interoperability**: Ensure Mellea contexts and messages can be easily converted back to standard formats (see [`docs/examples/library_interop`](docs/examples/library_interop)).

## 5. Directory Structure Map
*   `mellea/core`: Low-level runtime (Context management, generation loops).
*   `mellea/backends`: Provider implementations (HF, OpenAI, Ollama, Watsonx).
*   `mellea/stdlib`: High-level generics (Genslots, Requirements, Sampling strategies).
*   `mellea/templates` & `formatters`: Instruction string construction and output handling.
*   `mellea/helpers`: Common utilities, logging, and model ID tables.
*   `test/`: All test suites. Unit tests must not require API keys.

## 6. Development Conventions
*   **Branches**: Use descriptive names like `feat/topic` or `fix/issue-id`.
*   **Common Pitfalls**:
    *   Forgetting to update `uv.lock` after changing `pyproject.toml`.
    *   Adding `qualitative` markers to trivial unit tests (Keep the fast loop fast!).
    *   Not using `...` in `@generative` function bodies.

## 7. Agent Self-Review Protocol (Run BEFORE notifying user)
1. **The Build**: Does `uv run pytest -m "not qualitative"` pass?
2. **The Style**: Did I run `uv run ruff format .` and `uv run ruff check .`?
3. **The Coverage**: Did I add unit tests for new functionality?
4. **The Integrity**: Are all new functions typed and docstrings concise?
5. **The Simplicity**: Did I over-engineer? (Prefer primitives over Classes).
