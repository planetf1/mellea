# Phase 2: Validating Logic (System 2)
*Optimization: Injecting "Thinking Time" into critical nodes.*

This phase demonstrates how to add robustness (System 2) to a node using **Majority Voting**.
This strategy is excellent for filtering out "Random Noise" (arithmetic errors, hallucinations), but it has a limitation: it cannot fix "Systematic Errors" (logical fallacies).

## The Goal
Solve a logic puzzle: *A train leaves New York at 60 mph. Another leaves 2 hours later at 80 mph. How long until the second train catches the first?*
*   **Correct Answer**: 6 hours.
*   **Trap**: Many models confuse the relative distance and answer "1 hour" ($20mph / 20miles$) or "2 hours".

## The Comparison

### Option A: The Legacy Way (`2a_langchain_voting.py`)
In LangChain, "Parallelism" is architectural. You must explicitly construct a graph or chain branch.
*   **Complexity**: Requires `RunnableParallel`, manual aggregation, and "glue code" to count votes.

### Option B: The Mellea Way (`2b_mellea_voting.py`)
In Mellea, "Parallelism" is a **Sampling Strategy**.
*   **Simplicity**: One line of config: `strategy=MajorityVotingStrategyForMath(n=5)`.

## Side-by-Side Execution Results

### Option A: LangChain Output (`2a`)
```
--- Phase 2a: System 2 w/ LangChain (The Manual Way) ---
Running 5 parallel chains (Manual Architecture)...
Aggregating results...
Extracted Answers: [6, 8, 6, 2.25, 4]
Winner: 6 (Confidence: 2/5)
```
*Note: While it correctly identified '6' as a plurality, the 40% confidence shows the instability of forcing logic via manual graphs on small models. Configuration is high-overhead.*

### Option B: Mellea Output (`2b`)
```
--- System 2: Majority Voting (n=5) ---
...
Majority Vote Result: 1.0 (4/5 votes)
Winner: 1.0
```
*Note: In this specific run, Mellea's `MajorityVotingStrategy` converged on the common trap answer '1.0'.*

## Analysis of the "Failure"
Note that the models often converge on the trap answer **1.0**, which is **incorrect** (Systematic Error).
Because the model has a fundamental logical flaw in its reasoning path, simple voting often just amplifies the common mistake.
*   **What Voting Fixes**: Random slips (e.g., $2+2=5$).
*   **What Voting Misses**: Logical Flaws (e.g., trains problem).

**This failure is the motivation for Phase 3 (Reflection)**, where we use a critique loop to catch these logical flaws.
