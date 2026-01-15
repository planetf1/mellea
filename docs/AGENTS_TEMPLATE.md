# Usage Guidelines for Mellea (`AGENTS.md` Snippet)

> **User Instructions**: Copy the section below into your project's `AGENTS.md` or system prompt to teach your AI assistant (Cursor, Copilot, Roo) how to write correct Mellea code.

---

### Library: Mellea (Generative Programming)
**Context**: We use `mellea` for all LLM interactions. Do not use direct OpenAI/Anthropic SDK calls or LangChain `OutputParsers`.

#### 1. The `@generative` Pattern
*   **Rule**: To create a function backed by an LLM, use the `@generative` decorator.
*   **Do Not**: Write prompt templates, `chain.invoke()`, or regex parsers to extract JSON.
*   **Do**: Define a typed function signature and let Mellea handle the rest.

**BAD (LangChain/Raw Style):**
```python
# Don't do this!
prompt = "Extract the user age from: {text}"
response = openai.chat.completions.create(prompt)
age = int(re.search(r"\d+", response).group())
```

**GOOD (Mellea Style):**
```python
from mellea import generative

@generative
def extract_age(text: str) -> int:
    """Extract the age of the user mentioned in the text."""

# Usage
age = extract_age("Alice is 30") # Returns int(30) strictly
```

#### 2. Type Safety
*   **Rule**: Mellea relies on Pydantic and native types.
*   **Complex Outputs**: If you need multiple fields, define a `Pydantic` model and set it as the return type.
```python
class UserProfile(BaseModel):
    name: str
    age: int
    interests: list[str]

@generative
def parse_profile(bio: str) -> UserProfile: ...
```

#### 3. Control Flow
*   **Rule**: Use Python `if/for/while` for agentic logic. Do not use "Graph" frameworks.
*   **Reasoning**: Mellea treats LLM functions as standard Python functions.
*   **Example**:
```python
if analyze_sentiment(email) == "negative":
    draft = draft_apology(email)
else:
    draft = draft_response(email)
```
