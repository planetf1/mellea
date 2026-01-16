# Phase 3: Validating Thoughts (Reflection)
*Optimization: Orchestrating complex multi-turn reasoning loops.*

This phase demonstrates how to implement a "Self-Correcting" agent (Think $\to$ Critique $\to$ Refine) to fix systematic logic errors.
We align both implementations to use the exact same logic flow to ensure parity.

## The Goal
Fix the Logic Error from Phase 2.
*   **System 1 Error**: Fast thinking often misses the nuance (e.g., confusing "time difference" with "distance difference").
*   **System 2 Solution**: Explicitly ask the model to "Critique" its own answer before finalizing it.

## The Comparison

### Option A: The Legacy Way (`3a_langchain_reflection.py`)
To implement a loop in LangChain, we had to adopt **LangGraph**.
This required shifting from a linear chain to a cyclic state machine.

**Implementation Strategy:**
1.  **State**: Defined `AgentState(TypedDict)` to hold `messages`, `answer`, `critique`.
2.  **Nodes**: Wrote pure functions for `solver`, `critic`, `refiner`.
3.  **Edges**: Defined a `should_continue` conditional edge that checks `iterations` and `critique` content.
4.  **Wiring**: Manually constructed `StateGraph`, added nodes/edges, and compiled.

### Option B: The Mellea Way (`3b_mellea_reflection.py`)
Mellea treats loops as **Control Flow**.

**Implementation Strategy:**
1.  Write standard Python functions (`solve`, `critique`, `refine`).
2.  Compose them in a `while` loop (or `for` loop).
3.  Use an `if` statement for the stopping condition.

## Execution Results

### LangChain Output (`3a`)
```
--- Phase 3a: Reflection w/ LangGraph ---
  > Solver Node: Generating initial solution...
  > Critic Node: Reviewing solution...
  > Refiner Node: Improving solution...
--------------------
Final Answer: 6 hours
```
*Note: The graph works and solved the problem (with a detailed system prompt).*

### Mellea Output (`3b`)
```
--- System 1: Instinct ---
Draft Answer: 2 hours

--- System 2: Reflection ---
Critique: INCORRECT. You need to calculate the gap and divide by relative speed.

--- System 2: Refinement ---
Refined Answer: 1 hour (Incorrect)
```

## The Verification & Integrity Insight
**Honest Analysis**: With an abstract prompt ("Calculate Gap / Relative Speed"), the Llama 1B model *understood* the critique but failed the *execution* (arithmetic).
To get the "6 hours" result, we had to provide a **Few-Shot Example** in the prompt containing the specific calculation path.
*   **Lesson**: Architecture (Reflection) helps, but for small models (`1B`), you often need "Teacher Forcing" (explicit examples) in the prompts to bridge the reasoning gap.
*   **Mellea Advantage**: Mellea made this Prompt Engineering iteration trivial (edit the docstring), whereas LangGraph required graph updates.
