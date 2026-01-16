# Investigation: LangChain vs Mellea Migration

**Goal**: Create a side-by-side comparison of a common "Agentic" task (Extraction) implemented in LangChain (The "Before") and Mellea (The "After").

## 1. The Scenario
The task is to extract a structured `UserProfile` (name, age, interests) from unstructured text, enforcing `age >= 18`.

*   **Local Backend**: adapted to use `ibm/granite4:micro` via Ollama for zero-cost reproduction.
*   **Relation to Tutorials**: This example mirrors standard "Structured Output" tutorials found in LangChain docs, but adapted for local execution without an OpenAI key.

## 2. Quick Start

**Do NOT pip install langchain globally.** We use `uv` to keep the environment clean.

### Option A: Run LangChain (The "Before")
```bash
uv run --with langchain --with langchain-community --with langchain-core python 1_langchain_implementation.py
```

### Option B: Run Mellea (The "After")
```bash
uv run python 2_mellea_implementation.py
```

## 3. Execution Results (Captured 2026-01-16)

We ran both scripts against the same local model (`granite4:micro`).

### LangChain Output
*> Note: Includes unavoidable deprecation warnings despite using modern code.*
```text
/libs/langchain/chat_models/ollama.py: Warning: The class `ChatOllama` was deprecated in LangChain 0.3.1.
Input: Hi, I'm Alice. I'm 30 years old and I love tennis and coding.
Running LangChain (Granite4)...
Result: name='Alice' age=30 interests=['tennis', 'coding']
```

### Mellea Output
```text
Input: Hi, I'm Alice. I'm 30 years old and I love tennis and coding.
Running Mellea (Granite4)...
Result: name='Alice' age=30 interests=['tennis', 'coding']
```

## 4. Summary

**The output is identical.** Both frameworks successfully coerced the Granite 4 model (a 2GB model!) to produce valid JSON adhering to the Pydantic schema.

**The Difference is the Developer Experience:**
1.  **Code Volume**: Mellea (30 lines) vs LangChain (54 lines).
2.  **Dependency Hell**: LangChain required importing from 3 different packages (`langchain_core`, `langchain_community`, `pydantic`) to get a basic chain working. Mellea required only `mellea`.
3.  **Modernity**: LangChain struggles with Pydantic V2 compatibility (warnings suppressed in final code but present during dev), whereas Mellea is built for Pydantic V2 native.
