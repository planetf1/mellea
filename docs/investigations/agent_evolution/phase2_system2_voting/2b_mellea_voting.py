from mellea import start_session
from mellea.stdlib.sampling.majority_voting import MajorityVotingStrategyForMath


def run_demo():
    # 1. Setup (Local Backend)
    # Using 'llama3.2:1b' (1.3GB) - even smaller than Granite 4 Micro
    m = start_session("ollama", model_id="llama3.2:1b")

    # Harder questions to force System 1 failure (Logic & Arithmetic)
    questions = [
        # Question 1: Ratio (Often confuses small models)
        "Janet has 50% more money than Bob. If Bob has $40, how much do they have together? Put your final answer in \\boxed{}.",
        # Question 2: Relative Velocity (Classic Physics Trap)
        "A train leaves New York at 60 mph. Another leaves 2 hours later at 80 mph. How long until the second train catches the first? Put your final answer in \\boxed{}.",
        # Question 3: PEMDAS/Arithmetic
        "Calculate 12 + 4 * (5 - 2). Put your final answer in \\boxed{}.",
    ]

    for i, question in enumerate(questions, 1):
        print(f"\nExample {i}: {question}")

        # 2. Baseline (System 1)
        print("--- System 1: Single Shot ---")
        response_1 = m.chat(question)
        print(f"System 1 Answer: {response_1}\n")

        # 3. Democracy (System 2)
        print("--- System 2: Majority Voting (n=5) ---")
        response_2 = m.instruct(
            question, strategy=MajorityVotingStrategyForMath(number_of_samples=5)
        )
        print(f"System 2 Consensus: {response_2}\n")
        print("-" * 50)


if __name__ == "__main__":
    run_demo()
