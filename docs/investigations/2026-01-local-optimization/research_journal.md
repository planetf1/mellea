# Research Journal: Local Optimization & Strategic Pivot
**Date**: 2026-01-14 / 2026-01-15
**Investigator**: Antigravity
**Context**: Initially investigating "Local HF Backend" performance on Apple Silicon.

## 1. The Starting Point: "Why doesn't it run?"
The initial goal was simple: Make `uv run pytest` pass on a MacBook M1/M2/M3.
*   **Blocker 1**: `RuntimeError: "addmm_impl_cpu_" not implemented for 'Half'`.
    *   *Fix*: Auto-detect `mps` device in `LocalHFBackend` and enforce `torch_dtype=torch.float16` if and only if on execution (not CPU fallback).
*   **Blocker 2**: Python 3.13 vs `outlines`.
    *   *Finding*: `outlines` (Rust dependency) failed to build on 3.13. We documented the recommendation to stick to 3.12 for local stability.

## 2. The Technical Pivot: "It runs, but is it good?"
Once the tests ran, we audited the `LocalHFBackend` quality with `Llama-3-8B-Instruct`.
*   **Discovery**: The model was "yapping" (conversational filler) instead of returning strict JSON, even with strict prompts.
*   **Solution**: We needed `xgrammar` (via `outlines`) to force the logits.
*   **Insight**: "Local LLMs are unusable for agents *unless* you have structural enforcement." -> This became a key selling point for Mellea.

## 3. The Strategic Pivot: "Selling the Solution"
We realized Mellea's strength wasn't just "running locally", but "fixing the pain" of modern agent engineering (Types vs Tokens).
*   **Market Analysis**:
    *   LangChain users struggle with `OutputParserException`.
    *   LlamaIndex users struggle with verbose `PydanticProgram`.
    *   Local LLM users struggle with structure.
*   **The "Mellea Injection" Strategy**: Don't replace the stack. Inject `@generative` functions to solve the hardest problems.

## 4. The Artifact Generation (Outputs)
We created a portable "Go-to-Market" kit to operationalize this strategy in any repo:

1.  **The Mission Brief**: [`strategy_and_demos.md`](./strategy_and_demos.md)
    *   A roadmap of 4 specific demos to prove the value (Extraction, Eval, Local, SubQuestion).
    *   Includes the "Agentic Migration Pattern" (Gamified demos).
2.  **The Governance**: [`AGENTS.md`](../../../AGENTS.md)
    *   Strict guidelines for contributors (Typed & Deterministic).
3.  **The Tool**: [`AGENTS_TEMPLATE.md`](../../AGENTS_TEMPLATE.md)
    *   A user-facing file to teach *their* agents (Cursor/Roo) how to use Mellea.

## 5. Conclusion
This investigation started as a bug fix hunt and evolved into a comprehensive Product Strategy refresh. We confirmed that Mellea's "Type-Safe Generation" value proposition is strongest when positioned as a surgical tool for existing broken workflows.
