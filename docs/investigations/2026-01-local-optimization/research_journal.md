# Research Journal: Local Optimization & Strategic Pivot
**Date**: 2026-01-14 / 2026-01-15
**Investigator**: Antigravity
**Context**: Initially investigating "Local HF Backend" performance on Apple Silicon.

## 1. Technical Investigations (Detailed Reports)
We have separated our technical findings into specific deep-dives:

*   **[Local Backend Optimization](./local_backend_optimization.md)**: Details the switch to `float16` on Apple Silicon and the `xgrammar` dependency.
*   **[Test Suite Categorization](./test_suite_categorization.md)**: Analyzing the split between "Logic" (deterministic) and "Qualitative" (probabilistic) tests.
*   **[LM Studio Compatibility](./lmstudio_compatibility.md)**: Findings on why `OllamaModelBackend` fails with LM Studio and the recommendation to use `OpenAIModelBackend`.

## 2. The Strategic Pivot
Once the technical baseline was established, we realized Mellea's strength wasn't just "running locally", but...

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
