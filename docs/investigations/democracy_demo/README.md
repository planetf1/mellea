# Investigation: The "Democracy" Demo (Majority Voting)

**Goal**: Demonstrate Mellea's "System 2" capabilities by boosting the confidence of a small local model (Llama 3.2 1B) using `MajorityVotingStrategy`.

## 1. The Scenario
We asked 3 reasoning questions (Ratio, Relative Velocity, PEMDAS).
*   **System 1**: Single Shot (`m.chat`).
*   **System 2**: Majority Voting (`m.instruct`, n=5).

## 2. Setup
```bash
# Uses standard mellea dev environment + math libraries
uv run --with math_verify --with rouge_score --with numpy python run_voting_demo.py
```
*Note: Script now defaults to `llama3.2:1b` (1.3GB) to test the lower limits of competence.*

## 3. Results (2026-01-16)

Model: `llama3.2:1b`.

| Question | System 1 Answer | System 2 Consensus | Result |
| :--- | :--- | :--- | :--- |
| **Money** (Ratio) | $\boxed{100}$ | $\boxed{100}$ | **Both Correct**. |
| **Trains** (Velocity) | $\boxed{1.5}$ | $\text{180 miles}$ | **Both Failed**. <br>Sys 1: Wrong Logic (Forgot Train A moves).<br>Sys 2: Wrong Unit (Calculated distance, not time). |
| **PEMDAS** (Arithmetic) | $\boxed{24}$ | $\boxed{24}$ | **Both Correct**. |

## 4. Conclusion
Even 1B models are surprisingly robust at arithmetic (Money/PEMDAS). but the **Trains** example highlights the "Edge of Capability":
1.  **System 1**: Hallucinated a simple division ($120/80=1.5$).
2.  **System 2**: Spent more time thinking, realized 180 miles was the gap, but failed to convert back to time effectively in the final "box".

## 5. Failure Analysis: Why Voting Didn't Fix It
Majority Voting assumes **independent errors** (noise). If the model has a **systematic bias** (e.g. fundamentally misunderstanding "catch up time" as "catch up distance"), all voters will agree on the wrong logic.
> "A consensus of errors is still an error."

### The "System 2" Fix: Sampling vs Reflection
To fix this, we need a different *Strategy*, not different prompts.

**Mellea Approach** (Strategy Pattern):
Swap `MajorityVotingStrategy` for a Reflective Strategy (like `MultiTurnStrategy` or `TreeOfThoughts` which are available in `m.stdlib.sampling`).
```python
# The Fix: Force the model to "Critique" its own answer 3 times before returning.
# Requires 0 changes to your business logic, just a config swap.
m.instruct(question, strategy=MultiTurnStrategy(loop_budget=3))
```

**LangChain Approach** (Graph Rewrite):
To implement this "Reflection Loop" in LangChain, you cannot just change a config. You must:
1.  Migrate from `Chain` to `LangGraph`.
2.  Define `node_generate`, `node_critique`, and `conditional_edges`.
3.  Rewrite your application logic to handle the graph state.
**Estimated Refactor Cost**: +50-100 lines of complex graph code.
**Mellea Cost**: 1 line.
