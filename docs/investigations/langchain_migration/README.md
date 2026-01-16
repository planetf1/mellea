# Investigation: LangChain vs Mellea Migration

**Goal**: Create a side-by-side comparison of a common "Agentic" task implemented in LangChain (The "Before") and Mellea (The "After").

## The "Run Validation" (2026-01-16)
Both scripts were executed against a local backend (`ibm/granite4:micro` via Ollama).

| Metric | LangChain | Mellea |
| :--- | :--- | :--- |
| **Lines of Code** | 52 | 30 |
| **Dependencies** | 4 (`langchain`, `_core`, `_community`, `_openai`) | 1 (`mellea`) |
| **Setup Struggle** | **High**. Required 3 attempts to fix `ModuleNotFoundError` and `DeprecationWarning` due to `langchain-ollama` split. | **Low**. Worked immediately after config update. |
| **Result** | `name='Alice' age=30` | `name='Alice' age=30` |

> **Key Observation**: Even for this "Hello World" example, LangChain required importing from `langchain`, `langchain_core`, AND `langchain_community` separately. Mellea just required `mellea`.

## Setup: Clean Execution (IMPORTANT)
To avoid polluting the main `mellea` development environment with `langchain` dependencies, we use `uv` for ephemeral execution.

**Do NOT pip install langchain globally.**

### Running the "Before" (LangChain)
```bash
uv run --with langchain --with langchain-openai --with langchain-community --with langchain-core python 1_langchain_implementation.py
```

### Running the "After" (Mellea)
```bash
# Runs in the standard mellea dev environment
uv run python 2_mellea_implementation.py
```
