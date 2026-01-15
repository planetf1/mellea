# Research Report: Test Suite Categorization & Architecture
**Date**: 2026-01-14
**Topic**: Separating "Logic" from "Capability" in System Testing

## 1. The Problem: "Is the Library broken, or is the Model dumb?"
Running the full test suite (`test/`) against local models (Llama-3-8B) resulted in confusing failures.
*   **Logic Failures**: The library failed to construct a prompt correctly.
*   **Capability Failures**: The library worked, but the model gave the wrong answer ("2+2=5").

These were mixed together, making `uv run pytest` a noisy signal.

## 2. Categorization Findings
We audited the test suite and identified two distinct categories:

### A. Logic Tests (Deterministic)
Tests that verify the *machinery* of Mellea.
*   **Examples**: `test_router.py`, `test_mobject.py`, `test_tracing.py`.
*   **Expectation**: These should PASS even with a "Mock LLM" that returns hardcoded strings.
*   **Current State**: Many depend on live LLM calls, making them slow and flaky.

### B. Qualitative Tests (Probabilistic)
Tests that verify the *intelligence* of the system.
*   **Examples**: `test_math.py`, `test_extraction.py`.
*   **Expectation**: These require a smart model (GPT-4 class). They will likely fail on local 8B models without fine-tuning.

## 3. The "Marker" Strategy (Proposed)
We propose refactoring the `pytest` markers to explicitly separate these concerns.

```python
@pytest.mark.logic
def test_router_construction():
    # Should run on every commit. Use MockBackend.
    ...

@pytest.mark.capability
@pytest.mark.model("llama3-8b")
def test_math_reasoning():
    # Runs only during model evaluation or nightly builds.
    ...
```

## 4. Immediate Action Taken
We manually validated that the *core logic* of `LocalHFBackend` works (it runs, it streams, it constrained-decodes). failures in complex reasoning tasks (like "Write a polite email") were classified as "Model Capability Limitations", not "Backend Bugs".
