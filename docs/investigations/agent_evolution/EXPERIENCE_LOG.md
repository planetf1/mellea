# Agent Evolution Demo: Engineering Experience Log

This document captures the internal learnings, failures, and "Aha!" moments from building the Agent Evolution Suite (Mellea vs LangChain).

## 1. The "Small Model" Reality Check
We standardized on `llama3.2:1b` to ensure the demo is accessible to everyone locally. This constraint revealed significant insights:
*   **The "Cheat" Trap**: When we provided a specific example in the prompt to guide reasoning (CoT), the 1B model often just **copied the example numbers** instead of applying the logic to the new problem. It didn't "reason by analogy"; it "pattern-matched the output".
*   **The "Honest" Failure**: When we removed the specific example, the model failed the arithmetic. This is an important, honest result: Architecture (Reflection/Loops) cannot cure a model that can't do math, but it *can* help you catch it (the Critic worked!).

## 2. The Mellea "Iteration Loop" Advantage
The strongest argument for Mellea wasn't "Better Logic" (since the model limited us), but **Faster Iteration**.
*   **LangChain**: To fix the prompt, we had to traverse the Graph definition, find the node function, and edit the string buried in the code.
*   **Mellea**: We iterated on the prompt 5 times in 2 minutes because it was just the **Function Docstring**.
*   *Key Takeaway*: Mellea turns "Prompt Engineering" into "Code Documentation", which reduces friction for developers.

## 3. Parity is Possible (But Hard)
We achieved parity (LangChain and Mellea both solving the hard puzzle), but it required:
1.  **Fairness**: Explicitly aligning `temperature=0` and prompts.
2.  **Teaching**: Heavily guiding the 1B model with "Teacher Forcing" prompts.

## 4. The "Structure" Pivot (Phase 3c)
We attempted a "Structured Output" demo (`3c`) to show how Pydantic models can force reasoning.
*   **Result**: The 1B model struggled even with structure initially (copying example values).
*   **Fix**: We had to switch from "Reasoning Examples" to "Extraction Instructions" (Extract Speed A, Speed B, then Calculate).
*   *Verdict*: Structure helps, but for very small models, you effectively have to write the program *in English* in the docstring.
