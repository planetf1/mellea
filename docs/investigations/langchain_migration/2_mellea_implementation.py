import os
from typing import List
from pydantic import BaseModel, Field
from mellea import generative, start_session


# 1. Define the Schema (Standard Modern Pydantic)
class UserProfile(BaseModel):
    name: str
    age: int = Field(ge=18, description="User must be 18+")
    interests: List[str]


# 2. Define the Function (The Mellea Pattern)
@generative
def extract_profile(email_text: str) -> UserProfile:
    """Extract user information from the email."""
    ...


if __name__ == "__main__":
    # 3. Execution (The Runtime)
    m = start_session("ollama", model_id="ibm/granite4:micro")

    text = "Hi, I'm Alice. I'm 30 years old and I love tennis and coding."
    print(f"Input: {text}")
    print("Running Mellea (Granite4)...")

    # Call it like Python
    result = extract_profile(m, email_text=text)
    print(f"Result: {result}")
