# Agent Evolution: The "Better Together" Upgrade Path

This demo suite enables you to compare "Legacy" (Standard LangChain) patterns against "Modern" (Mellea) patterns side-by-side.
The goal is not to replace your entire stack, but to show how Mellea can optimize specific, high-value nodes in your architecture.

## Global Prerequisites
*   **Python**: 3.10+
*   **Package Manager**: `uv` (recommended)
*   **Ollama**: Running locally.
*   **Models**: `llama3.2:1b` (Standard for all demos).
    ```bash
    ollama pull llama3.2:1b
    ```

## The Phases

### [Phase 1: Extraction (Validating Data)](./phase1_data_extraction)
*Goal: Extract structured output (JSON) from unstructured text.*
*   **Comparison**: LangChain Parsers vs Mellea Pydantic Types.
*   **ROI**: Delete 20 lines of boilerplate; gain automatic retry-on-validation-error.

### [Phase 2: Robustness (Validating Logic)](./phase2_system2_voting)
*Goal: Solve logic puzzles using System 2 Majority Voting.*
*   **Comparison**: Manual `RunnableParallel` graph vs Injected `MajorityVotingStrategy`.
*   **ROI**: Add Robustness with **1 line of configuration** instead of rewriting your graph.

### [Phase 3: Reflection (Validating Thoughts)](./phase3_self_correction)
*Goal: Fix systematic logic errors using a self-correction loop.*
*   **Comparison**: LangGraph State Machine vs Python Functional Loop.
*   **ROI**: Flatten complex graphs into readable, debuggable Python control flow.

### [Phase 4: Hybrid Intelligence (Structure + Code)](./phase4_hybrid_intelligence)
*Goal: Solve complex logic with small models by mixing Agents and Python.*
*   **Concept**: Use LLM for Extraction (Parsing) and Python for Execution (Math).
*   **ROI**: 100% Reliability on logic tasks where purely generative models fail.


## Running the Comparisons

### Setup
```bash
uv sync
```

### Run Phase 1
```bash
uv run --with langchain --with langchain-community --with langchain-core --with langchain-ollama python docs/investigations/agent_evolution/phase1_data_extraction/1a_langchain_extraction.py
uv run python docs/investigations/agent_evolution/phase1_data_extraction/1b_mellea_extraction.py
```

### Run Phase 2
```bash
uv run --with langchain --with langchain-ollama --with math_verify --with numpy python docs/investigations/agent_evolution/phase2_system2_voting/2a_langchain_voting.py
uv run --with math_verify --with rouge_score --with numpy python docs/investigations/agent_evolution/phase2_system2_voting/2b_mellea_voting.py
```

### Run Phase 3
```bash
uv run --with langchain --with langchain-ollama --with langgraph python docs/investigations/agent_evolution/phase3_self_correction/3a_langchain_reflection.py
uv run python docs/investigations/agent_evolution/phase3_self_correction/3b_mellea_reflection.py
```

### Run Phase 4
```bash
uv run python docs/investigations/agent_evolution/phase4_hybrid_intelligence/4_mellea_hybrid.py
```

## Value Summary

| Metric | Legacy (LangChain) | Modern (Mellea) |
| :--- | :--- | :--- |
| **Boilerplate** | High (Parsers, Graphs) | Low (Types, Functions) |
| **Configurability** | Explicit Graph Wiring | Strategy Injection |
| **Developer Exp** | Learning the Library | Writing Python |
