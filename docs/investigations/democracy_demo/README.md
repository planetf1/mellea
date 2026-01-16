# Investigation: The "Democracy" Demo (Majority Voting)

**Goal**: Demonstrate Mellea's "System 2" capabilities by boosting the accuracy of a small local model (Granite 4) using `MajorityVotingStrategy`.

## The Hypothesis
A small model like `granite4:micro` might be inconsistent at complex logic/math. By generating $N$ answers and voting, we should filter out the noise (hallucinations) and converge on the truth.

> "Quality through Quantity."

## The Scenario
**Question**: "If I have 3 apples and you take away 2, how many apples do you have?" (A classic riddle where models often say "1" instead of "2" because they confuse ownership).
*Or a similar logic puzzle.*

## Plan
1.  **Baseline Script**: Ask the question once (standard `@generative`). Record failure/inconsistency.
2.  **Mellea Script**: Use `m.instruct(..., strategy=MajorityVotingStrategyForMath(n=5))`.
3.  **Validate**: Show the consensus winner.

## Setup
```bash
# Uses standard mellea dev environment
uv run python run_voting_demo.py
```
