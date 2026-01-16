# Investigation: LangChain vs Mellea Migration

**Goal**: Create a side-by-side comparison of a common "Agentic" task implemented in LangChain (The "Before") and Mellea (The "After").

## The Scenario: "Structured Data Extraction & Validation"
We will extract a structured `UserProfile` from an unstructured email, with specific validation rules (e.g., age >= 18).

### 1. The "Before" (LangChain)
*   **Approach**: `PromptTemplate` + `LLMChain` + `PydanticOutputParser`
*   **Pain Points**: 
    *   Verbose setup.
    *   Fragile regex parsing.
    *   Handling "Retry" logic manually or opaquely.

### 2. The "After" (Mellea)
*   **Approach**: `@generative` function with Pydantic return type.
*   **Benefits**:
    *   Zero prompt engineering.
    *   Guaranteed type safety.
    *   Clean, Pythonic code.

## Setup
1.  Use a virtual environment with `langchain` installed.
2.  Run both scripts against the same backend (OpenAI or Local).
3.  Measure: Lines of Code (LOC), Readability, and Correctness.
