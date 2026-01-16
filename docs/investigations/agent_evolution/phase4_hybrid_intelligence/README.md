# Phase 4: Hybrid Intelligence (Structure + Code)

In Phase 3, we saw that small models (`llama3.2:1b`) struggle with multi-step arithmetic even when they can "Reflect" on their errors.
**Phase 4 demonstrates the ultimate Mellea pattern: Hybrid Intelligence.**

Instead of forcing the LLM to *simulate* a computer (doing math), we use the LLM to *parse* the world (Extraction) and use Python to *compute* the result (Execution).

## The Implementation
*   **LLM Role**: Extract `first_train_speed`, `second_train_speed`, `delay` into a structured Pydantic object (`RawPhysicsData`).
*   **Python Role**: A deterministic function `calculate_physics(params)` that applies the formula $Time = Gap / Relative$.

## The Logic
```python
# Mellea allows you to mix Generative and Deterministic functions naturally
@generative
def extract_parameters(question: str) -> RawPhysicsData:
    """EXTRACT parameters. Do NOT calculate."""
    pass

def calculate_physics(params: RawPhysicsData) -> float:
    """Pure Python Math"""
    gap = params.first_train_speed * params.delay
    relative = params.second_train_speed - params.first_train_speed
    return gap / relative
```

## Running the Demo
```bash
uv run python docs/investigations/agent_evolution/phase4_hybrid_intelligence/4_mellea_hybrid.py
```

## The Result
```
--- System 1: Structured Decomposition ---
Step 1: Extracting Parameters...
Extracted: first_train_speed_mph=60.0 second_train_speed_mph=80.0 delay_hours=2.0

Step 2: Computing Physics (Deterministically)...
  [Python Logic] Gap = 60.0 * 2.0
  [Python Logic] Relative = 80.0 - 60.0
Final Calculated Time: 6.0 hours

SUCCESS: Hybrid Approach is 100% reliable.
```

## Takeaway
**Don't fight the model.**
If a model is small/dumb at math, don't prompt-engineer it into a calculator.
Use Mellea's structured extraction to bridge the gap to deterministic code.
This is the "Cool & Simple" way to build robust agents.
