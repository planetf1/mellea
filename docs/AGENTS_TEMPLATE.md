# Usage Guidelines for Mellea (`AGENTS.md` Snippet)

> **User Instructions**: Copy the section below into your project's `AGENTS.md` or system prompt to teach your AI assistant (Cursor, Copilot, Roo) how to write correct Mellea code.

---

### Library: Mellea (Generative Programming)
**Context**: We use `mellea` for all LLM interactions. Do not use direct OpenAI/Anthropic SDK calls or LangChain `OutputParsers`.

**Prerequisites**:
*   Install: `pip install mellea`
*   Docs: [mellea.ai](https://mellea.ai)
*   Repo: [github.com/generative-computing/mellea](https://github.com/generative-computing/mellea)

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
m = start_session()
age = extract_age(m, text="Alice is 30") # Returns int(30) strictly
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

#### 4. Chain-of-Thought via "Reasoning Fields"
*   **Rule**: To improve accuracy on complex tasks, add a `reasoning` field to your Pydantic model.
*   **Why**: This forces the LLM to "think" (output tokens) before it commits to a final answer.
```python
class AnalysisResult(BaseModel):
    reasoning: str  # The LLM fills this first, "showing its work"
    conclusion: Literal["approve", "reject"]
    confidence: float = Field(ge=0.0, le=1.0)

@generative
def analyze_document(doc: str) -> AnalysisResult: ...
```

#### 5. Backend Portability
*   **Rule**: Mellea code is backend-agnostic. Write the function once, run it anywhere.
```python
# Option A: Local Development (Ollama/Granite)
m = start_session() 

# Option B: Production (OpenAI/Anthropic)
# m = MelleaSession(backend=OpenAIModelBackend(model_id="gpt-4o"))

# The logic remains identical:
result = analyze_document(m, text="...")
```

#### 6. Anti-Patterns (What NOT to do)
*   **Don't** wrap `@generative` calls in `try/except` loops. Mellea handles retries and validation internally.
*   **Don't** use `json.loads(response.content)`. Always use typed return signatures.
*   **Don't** create "Agent Classes" just to wrap a single function. Use a standalone function.

#### 7. Instruct-Validate-Repair (The "Killer Feature")
*   **Rule**: For complex generation with strict requirements, use `m.instruct()` instead of `@generative`.
*   **Why**: Mellea automatically retries (loops) until the `requirements` are met or budget is exhausted.
```python
from mellea.stdlib.requirement import req, simple_validate
from mellea.stdlib.sampling import RejectionSamplingStrategy

requirements = [
    req("Must be formal"), 
    req("Must use lower-case only", validation_fn=simple_validate(lambda x: x.islower()))
]

email = m.instruct(
    "Write an invite for {{name}}",
    requirements=requirements,
    strategy=RejectionSamplingStrategy(loop_budget=3),
    user_variables={"name": "Alice"}
)
#### 8. Hybrid Intelligence (The "Small Model" Fix)
*   **Rule**: Small models (1B-8B) are bad at math. Do NOT ask them to calculate.
*   **Pattern**: Use LLM to EXTRACT parameters + Python to EXECUTE logic.
*   **Example**:
```python
# 1. Define Extraction Model
class PhysicsParams(BaseModel):
    speed_a: float
    speed_b: float
    delay_hours: float

# 2. Define Extraction Function
@generative
def extract_params(text: str) -> PhysicsParams:
    """EXTRACT the raw numbers. Do not calculate."""
    pass

# 3. Define Python Logic
def calculate_gap(params: PhysicsParams) -> float:
    return params.speed_a * params.delay_hours
```

#### 9. Teacher Forcing (Prompting)
*   **Rule**: If a model struggles with a definition, provide a "One-Shot Example" in the docstring.
*   **Example**:
```python
@generative
def identify_fruit(text: str) -> str:
    """
    Extract the fruit.
    Ex: "I ate an apple" -> "apple"
    Ex: "The sky is blue" -> "None"
    """
```

#### 10. Logic & Precision Tips
*   **Deterministic Reasoning**: For math or logic-heavy tasks, always set **`temperature=0`** in your session or backend options.
*   **Boilerplate Avoidance**: Before reaching for `m.instruct()` with complex requirements, ask: "Can I do this with one simple `@generative` function and a clean Pydantic model?" Use `@generative` first; escalation to `instruct` is for multi-step "repair" loops.
