import os
from typing import List
from pydantic import BaseModel, Field, validator
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_community.chat_models import ChatOllama


# 1. Define the Schema (Standard Pydantic, but stuck in v1 for LangChain compat often)
class UserProfile(BaseModel):
    name: str = Field(description="The user's full name")
    age: int = Field(description="The user's age, must be >= 18")
    interests: List[str] = Field(description="List of user hobbies/interests")

    @validator("age")
    def validate_age(cls, v):
        if v < 18:
            raise ValueError("User must be 18+")
        return v


# 2. Setup the "Machinery" (The Boilerplate)
def extract_profile_langchain(email_text: str):
    # A. Parser
    parser = PydanticOutputParser(pydantic_object=UserProfile)

    # B. Prompt with "Injection"
    prompt = PromptTemplate(
        template="Extract user information from the following email.\n{format_instructions}\n\nEmail: {email}\n",
        input_variables=["email"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    # C. Model (Local Ollama)
    model = ChatOllama(model="ibm/granite4:micro", temperature=0)

    # D. The Chain
    chain = prompt | model | parser

    # E. Execution
    try:
        return chain.invoke({"email": email_text})
    except Exception as e:
        print(f"Error parsing output: {e}")
        return None


if __name__ == "__main__":
    text = "Hi, I'm Alice. I'm 30 years old and I love tennis and coding."
    print(f"Input: {text}")
    print("Running LangChain (Granite4)...")
    result = extract_profile_langchain(text)
    print(f"Result: {result}")
