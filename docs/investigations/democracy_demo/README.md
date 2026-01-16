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
Even 1B models are surprisingly robust at arithmetic.
The **Trains** example highlights the "Edge of Capability":
1.  **System 1**: Hallucinated a simple division ($120/80=1.5$).
2.  **System 2**: Spent more time thinking, realized 180 miles was the gap, but failed to convert back to time effectively in the final "box".

**Demo Value**:
This proves Mellea's Voting Strategy runs successfully on local hardware, generating parallel chains and computing consensus. While it didn't magically fix the 1B model's physics reasoning, it faithfully executed the "System 2" process.
