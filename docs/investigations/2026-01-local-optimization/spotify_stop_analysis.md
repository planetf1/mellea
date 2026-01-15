# Migration Proposal: Refactoring `spotify-stop-ai` to Mellea

**Objective**: Replace fragile manual prompt engineering with Mellea's type-safe `Generative Programming` primitives.
**Target Audience**: An AI Agent (Cursor, Roo, or Human Developer) tasked with the refactor.

> **Why Bother?** The current `ollama_client.py` is ~400 lines, with roughly half dedicated to manual JSON parsing, regex cleanup, and error handling. Mellea could reduce this to ~50 lines of type-safe code while improving reliability.

## 1. Context: What does the app do?
**spotify-stop-ai** monitors your currently playing Spotify track and attempts to classify the artist as "Human" or "Artificial" (e.g., Vocaloid, AI-generated, VTuber) to automatically skip AI music.

**The LLM's Role**: It acts as a **Fallback Judge**.
1.  The app first checks Wikidata, MusicBrainz, and Last.fm.
2.  If sources disagree or are inconclusive (missing data), the LLM analyzes web search results to make a final boolean decision: `is_artificial: true/false`.

## 2. Detection: Is this code a candidate?

Use these heuristics to identify files ripe for Mellea migration.

| Pattern | Evidence in `spotify-stop-ai` | Why Mellea? |
| :--- | :--- | :--- |
| **Manual JSON Parsing** | `json.loads(response.strip().replace('```json', ''))` | **Mellea Types**: Mellea guarantees valid objects, eliminating parsing code. |
| **Schema in System Prompt** | `Note: You must output JSON with keys: 'label', ...` | **Pydantic Models**: Your Python types *become* the schema, ensuring sync. |
| **Manual Retry Logic** | `try: ... except json.DecodeError: ...` | **Instruct-Validate-Repair**: Built-in loops handle validation failures automatically. |
| **Manual Validation** | `if not (0.0 <= confidence <= 1.0): return None` | **Field Validators**: `Field(ge=0.0, le=1.0)` runs validation before you see the data. |
| **Backend Coupling** | Hardcoded `/api/generate` endpoints | **Portability**: Write once, run on OpenAI/Anthropic/Local by passing a `Session`. |

## 3. Preparation (Mellea Context Only)

To enable the agent to use Mellea correctly, provide the *Mellea Pattern* definitions.

### Step A: Add Mellea Patterns
Create a file named `AGENTS.md` (or `docs/MELLEA_PATTERNS.md`) containing strictly Mellea usage examples.
*   **Source**: Copy content from `mellea/docs/AGENTS_TEMPLATE.md`.
*   **Action**: Create `spotify-stop-ai/AGENTS.md`.
*   **Why**: This file is a **technical reference** for the agent. It replaces "General Knowledge" with "Specific Mellea Syntax" (e.g. `@generative`).

### Step B: Install Mellea
Add `mellea` to the project dependencies.
```bash
# In pyproject.toml or requirements.txt
mellea>=0.1.0
```

## 4. Implementation Plan (`ollama_client.py`)

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

## 5. What Would Change

With Mellea handling structured output and validation, several pieces of the current implementation become unnecessary:

*   **Prompt Templates**: The file `prompts/classify_artist.txt` is replaced by the Pydantic model `ClassificationResult`, which defines the schema directly in code.
*   **Manual Parsing**: The custom logic to strip markdown code blocks and `json.loads` the response is handled automatically.
*   **Explicit Validation**: The `_validate_output()` method is redundant because `Field(ge=0.0, le=1.0)` enforces constraints before the function returns.
*   **Direct API Calls**: The `httpx` logic is abstracted by the Mellea Session.

*Note: The existing logic for `_web_search` and `_format_evidence` would remain, simply feeding into the new `@generative` function.*

> **Caveat**: This is an architectural sketch. The actual implementation will need to handle async execution (Mellea supports async via `await m.chat_async(...)`) and mapping the existing configuration values to the Mellea Session.

## 6. Integrating the "Agent Fragment"

When instructing your AI to perform this work, use this prompt:

> "I need to refactor `ollama_client.py` to use Mellea.
> I have added `AGENTS.md` to the root of this repo.
> Please read `AGENTS.md` first to understand the `@generative` pattern.
> Then, look at `ClassificationResult` in my proposed plan.
> Refactor the code to use a typed `@generative` function instead of manual JSON parsing."
