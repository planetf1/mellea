from mellea import start_session, generative
import mellea

# Question that failed in Phase C (Voting)
TRAIN_QUESTION = """
A train leaves New York at 60 mph. Another leaves 2 hours later at 80 mph. 
How long until the second train catches the first?
"""


@generative
def solve_math(question: str) -> str:
    """Solve the math problem. Show your work."""
    pass


@generative
def critique_answer(question: str, answer: str) -> str:
    """
    You are a strict Physics Professor checking a student's work.
    Review the answer to the question.

    CRITICAL CHECKLIST:
    1. Did the student use RELATIVE SPEED? (80mph - 60mph = 20mph)
    2. Did the student calculate the GAP DISTANCE? (60mph * 2hrs = 120 miles)
    3. Did they divide GAP / RELATIVE SPEED? (120 / 20 = 6 hours)

    If the answer is '1 hour', it is WRONG (classic mistake).
    If the answer is '2 hours', it is WRONG.

    If the answer is correct (6 hours), say 'CORRECT'.
    If wrong, say 'INCORRECT' and YOU MUST EXPLAIN THE RELATIVE SPEED CALCULATION.
    Example: "INCORRECT. You need to calculate the gap (120 miles) and divide by relative speed (20 mph) to get 6 hours."
    """
    pass


@generative
def refine_answer(question: str, previous_answer: str, critique: str) -> str:
    """
    Rewrite the answer based on the checking critique.
    Ensure the final answer is in hours.
    """
    pass


def main():
    # Use explicit model_id for the session
    # Set temperature=0 for parity with LangChain demo
    m = start_session(
        "ollama", model_id="llama3.2:1b", model_options={"temperature": 0.0}
    )

    print(f"--- System 1: Instinct (Llama 1B) ---")
    draft = solve_math(m, question=TRAIN_QUESTION)
    print(f"Draft Answer: {draft}\n")

    print(f"--- System 2: Reflection (Critique) ---")
    critique = critique_answer(m, question=TRAIN_QUESTION, answer=draft)
    print(f"Critique: {critique}\n")

    # Logic Fix: "correct" serves as a substring of "incorrect"
    is_correct = "CORRECT" in critique and "INCORRECT" not in critique

    if is_correct:
        final = draft
        print("Judge approved the draft.")
    else:
        print(f"--- System 2: Refinement (Correction) ---")
        final = refine_answer(
            m, question=TRAIN_QUESTION, previous_answer=draft, critique=critique
        )
        print(f"Refined Answer: {final}")


if __name__ == "__main__":
    main()
