import argparse
from warnings import filterwarnings

filterwarnings("ignore")

import numpy as np
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from math_verify import parse, verify

# Developer Value Note:
# To implement "Majority Voting" in LangChain, we must:
# 1. Manually construct parallel chains using RunnableParallel.
# 2. Manually collect results.
# 3. Manually implement the voting logic (MathVerify).
# In Mellea, this is: `m.instruct(..., strategy=MajorityVotingStrategy(n=5))`


def run_demo():
    print("--- Phase 2a: System 2 w/ LangChain (The Manual Way) ---")

    # 1. Setup Model
    llm = ChatOllama(model="llama3.2:1b", temperature=0.7)  # Temp > 0 for diversity

    # 2. Define the Chain
    prompt = ChatPromptTemplate.from_template(
        "Solve this math problem. Show your work. Return the final answer as a number.\n\nProblem: {question}"
    )

    chain = prompt | llm | StrOutputParser()

    # 3. Build Parallel Execution Architecture (Complexity spike!)
    # We explicitly parallelize the chain N times.
    N_SAMPLES = 5
    voting_chain = RunnableParallel(**{f"path_{i}": chain for i in range(N_SAMPLES)})

    question = "A train leaves New York at 60 mph. Another leaves 2 hours later at 80 mph. How long until the second train catches the first?"

    print(f"Question: {question}")
    print(f"Running {N_SAMPLES} parallel chains (Manual Architecture)...")

    # 4. Execute
    results_dict = voting_chain.invoke({"question": question})
    candidates = list(results_dict.values())

    # 5. Manual Aggregation Logic (The "Glue Code")
    print("Aggregating results...")
    parsed_candidates = []
    for c in candidates:
        try:
            # Attempt to extract number from unstructured text
            # This is fragile compared to Mellea's structured extraction
            nums = parse(c)
            if nums:
                parsed_candidates.append(nums[0])
            else:
                parsed_candidates.append(None)
        except:
            parsed_candidates.append(None)

    print(f"Extracted Answers: {parsed_candidates}")

    # Simple Majority Vote (String based for now since math_verify is complex)
    from collections import Counter

    valid_answers = [str(x) for x in parsed_candidates if x is not None]
    if not valid_answers:
        print("Failed to extract any valid answers.")
        return

    counter = Counter(valid_answers)
    winner, count = counter.most_common(1)[0]

    print(f"Winner: {winner} (Confidence: {count}/{N_SAMPLES})")


if __name__ == "__main__":
    run_demo()
