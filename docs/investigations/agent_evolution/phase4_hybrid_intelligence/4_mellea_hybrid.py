from mellea import start_session, generative
from pydantic import BaseModel, Field

# Question: Relative Velocity Trap
TRAIN_QUESTION = "A train leaves New York at 60 mph. Another leaves 2 hours later at 80 mph. How long until the second train catches the first?"


class RawPhysicsData(BaseModel):
    """Raw numbers extracted from the text."""

    first_train_speed_mph: float = Field(..., description="Speed of the first train")
    second_train_speed_mph: float = Field(..., description="Speed of the second train")
    delay_hours: float = Field(
        ..., description="Time delay before the second train starts"
    )


@generative
def extract_parameters(question: str) -> RawPhysicsData:
    """
    EXTRACT the numbers from the text.
    Do NOT do any math. Just extract the raw values.
    """
    pass


def calculate_physics_deterministic(params: RawPhysicsData) -> float:
    """
    Perform the physics calculation using PRECISE PYTHON LOGIC.
    This demonstrates Mellea's power: mixing LLM Extraction with Python Execution.
    """
    print(
        f"  [Python Logic] Gap = {params.first_train_speed_mph} * {params.delay_hours}"
    )
    gap = params.first_train_speed_mph * params.delay_hours

    print(
        f"  [Python Logic] Relative = {params.second_train_speed_mph} - {params.first_train_speed_mph}"
    )
    relative = params.second_train_speed_mph - params.first_train_speed_mph

    if relative <= 0:
        return -1.0

    return gap / relative


def main():
    # Set temperature=0 for consistent "logic"
    m = start_session(
        "ollama", model_id="llama3.2:1b", model_options={"temperature": 0.0}
    )

    print(f"--- System 1: Structured Decomposition (System 2 Thinking) ---")
    print(f"Question: {TRAIN_QUESTION}\n")

    # Step 1: Extract (Focus only on finding numbers)
    print("Step 1: Extracting Parameters...")
    params = extract_parameters(m, question=TRAIN_QUESTION)
    print(f"Extracted: {params}\n")

    # Step 2: Compute (Focus only on math)
    print("Step 2: Computing Physics (Deterministically)...")
    # Note: We pass the *Object* to the Python function.
    # This is "Hybrid Intelligence": LLM Parses, Python Calculates.
    result = calculate_physics_deterministic(params=params)
    print(f"Final Calculated Time: {result} hours")

    if abs(result - 6.0) < 0.1:
        print(
            "\nSUCCESS: Hybrid Approach (LLM Parsing + Python Math) is 100% reliable."
        )
    else:
        print("\nFAIL: Logic error.")


if __name__ == "__main__":
    main()
