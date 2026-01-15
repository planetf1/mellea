# Migration Manual: Refactoring `spotify-stop-ai` to Mellea

**Objective**: Replace fragile manual prompt engineering with Mellea's type-safe `Generative Programming` primitives.
**Target Audience**: An AI Agent (Cursor, Roo, or Human Developer) tasked with the refactor.

## 1. Detection: Is this code a candidate?

Use these heuristics to identify files ripe for Mellea migration.

| Pattern | Evidence in `spotify-stop-ai` | Why Mellea? |
| :--- | :--- | :--- |
| **Manual JSON Parsing** | `json.loads(response.strip().replace('```json', ''))` | Mellea handles parsing & validation automatically. |
| **Schema in System Prompt** | `Note: You must output JSON with keys: 'label', ...` | Mellea derives formatting instructions from Pydantic types. |
| **Manual Retry Logic** | `try: ... except json.DecodeError: ...` | `instruct-validate-repair` handles retries for you. |
| **Manual Validation** | `if not (0.0 <= confidence <= 1.0): return None` | Pydantic `Field(ge=0.0, le=1.0)` enforces ranges. |
| **Backend Coupling** | Hardcoded `/api/generate` endpoints | Mellea works with OpenAI, Anthropic, or Local execution. |

## 2. Preparation (The Setup)

Before refactoring code, establish the "Rules of the Road" for the agent.

### Step A: Create `AGENTS.md`
The repo currently lacks an `AGENTS.md`. Create one at the root using the **Mellea Standard Template**.
*   **Source**: Copy content from `mellea/docs/AGENTS_TEMPLATE.md`.
*   **Action**: Create `spotify-stop-ai/AGENTS.md`.
*   **Reason**: This teaches the coding agent *how* to use Mellea correctly (e.g., "Use `@generative`, not `OutputParser`").

### Step B: Install Mellea
Add `mellea` to the project dependencies.
```bash
# In pyproject.toml or requirements.txt
mellea>=0.1.0
```

## 3. Implementation Plan (`ollama_client.py`)

**Goal**: Delete `OllamaClient` complexity and replace with a Mellea Session.

### The "Before" Logic (Pseudocode)
```python
class OllamaClient:
    def classify(self, evidence):
        prompt = load_prompt("prompts/classify_artist.txt")
        raw_json = http_post(self.host, prompt)
        clean_json = regex_strip_markdown(raw_json)
        data = json.loads(clean_json)
        if validate(data): return data
```

### The "After" Logic (Mellea Pattern)
Define the schema once, and use `@generative`.

```python
# src/spotify_stop_ai/classification.py

from mellea import generative
from pydantic import BaseModel, Field
from typing import Literal

# 1. Define the Schema (Replaces 'prompts/classify_artist.txt')
class ClassificationResult(BaseModel):
    label: Literal["virtual_idol", "vocaloid", "vtuber", "fictional", "ai_generated", "human", "band", "unknown"]
    is_artificial: bool | None
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0-1")
    reason: str = Field(description="Brief explanation citing evidence")
    citations: list[str]
    ambiguity_notes: str | None

# 2. Define the Function (Replaces 'OllamaClient')
@generative
def classify_artist_evidence(evidence_summary: str) -> ClassificationResult:
    """
    Analyze the provided evidence to determine if the artist is artificial.
    Be conservative. If unsure, use 'unknown'.
    """

# 3. Usage
def run_classification(m, evidence):
    return classify_artist_evidence(m, evidence_summary=str(evidence))
```

## 4. Specific Refactoring Instructions

1.  **Delete** `prompts/classify_artist.txt`. (The Pydantic model is the new schema).
2.  **Modify** `src/spotify_stop_ai/ollama_client.py`:
    *   Remove `httpx` logic.
    *   Remove `json` parsing logic.
    *   Remove `_validate_output` method.
    *   Instantiate `mellea.start_session()` instead of `OllamaClient`.
    *   Call `classify_artist_evidence(m, ...)` directly.

## 5. Integrating the "Agent Fragment"

When instructing your AI to perform this work, use this prompt:

> "I need to refactor `ollama_client.py` to use Mellea.
> I have added `AGENTS.md` to the root of this repo.
> Please read `AGENTS.md` first to understand the `@generative` pattern.
> Then, look at `ClassificationResult` in my proposed plan.
> Refactor the code to use a typed `@generative` function instead of manual JSON parsing."
