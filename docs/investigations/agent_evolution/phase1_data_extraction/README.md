# Phase 1: Robust Data Extraction
*Optimizing the "Data Node" of your architecture.*

This phase demonstrates how to replace fragile, verbose LangChain extraction chains with robust, type-safe Mellea functions.
This is the most common starting point for adopting Mellea: identifying a specific node in your LangGraph that handles Structured Output and optimizing it.

## The Goal
Extract a structured `UserProfile` object from unstructured text.
*   **Input**: "Hi, I'm Alice (30). I like coding."
*   **Output**: `{"name": "Alice", "age": 30, "hobbies": ["coding"]}`

## The Comparison

### Option A: The Legacy Way (`1a_langchain_extraction.py`)
To achieve structured output in LangChain (especially with local models), we had to implement a classic "Chain".

**Implementation Strategy:**
1.  **Parser**: Instantiated `PydanticOutputParser` to define the schema.
2.  **Prompt**: Created `ChatPromptTemplate` with format instructions (`{format_instructions}`).
3.  **Chain**: Composed `prompt | llm | parser`.
4.  **Boilerplate**: Had to manually handle the `try/except` logic for when the model returns valid markdown but invalid JSON.

### Option B: The Mellea Way (`1b_mellea_extraction.py`)
Mellea handles structure at the type level.

**Implementation Strategy:**
1.  Define `UserProfile(BaseModel)`.
2.  Decorate function with `@generative`.
3.  Call function. Mellea handles the rest.

## Side-by-Side Execution Results

### LangChain Output (`1a`)
```
Running LangChain (Legacy Extraction)...
Invoking chain...
Raw Output: {'name': 'Alice', 'age': 30, 'hobbies': ['tennis', 'coding']}
Parsed Type: <class 'pydantic_core._pydantic_core.ValidationError'> (Often requires retry logic)
```
*Note: LangChain often struggles with "chatty" local models that add prologues, requiring heavy regex post-processing.*

### Mellea Output (`1b`)
```
Running Mellea (Granite4)...
Raw Output: name='Alice' age=30 hobbies=['tennis', 'coding']
Validation: SUCCESS (Valid Pydantic Object)
```
*Note: Mellea's `RejectionSamplingStrategy` automatically healed any JSON errors.*
