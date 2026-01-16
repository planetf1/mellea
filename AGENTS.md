# Agent Guidelines for Mellea Contributors (`AGENTS.md`)
> [!IMPORTANT]
> **Role Distinction**:
> * **Building Mellea?** You are editing `mellea/core`, `backends`, or `stdlib`. Follow the "Internal Contributor" standards below.
> * **Using Mellea?** You are building a demo or a client app. Follow [`docs/AGENTS_TEMPLATE.md`](docs/AGENTS_TEMPLATE.md) for usage patterns.

## 1. Quick Reference (The "Must Knows")
```bash
# Standard Dev Loop
uv sync                     # Install dependencies & fix lockfile
uv run pytest -m "not qualitative" # Fast loop (Unit tests only)
uv run pytest               # Full audit (Runs qualitative/slow tests)
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
> * **Developing Mellea?** If you improve the core engine or find a bug, update **THIS FILE**.
> * **Building Agents?** If you discover a prompting trick or a new pattern (e.g., "Small models need X"), update [`docs/AGENTS_TEMPLATE.md`](docs/AGENTS_TEMPLATE.md).
>
> This ensures all future AI/Human collaborators benefit from your experience.

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
