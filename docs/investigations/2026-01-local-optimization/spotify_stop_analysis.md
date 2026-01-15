# Analysis: `spotify-stop-ai` Migration Opportunity

**Target Repo**: `../spotify-stop-ai`
**Current Implementation**: `OllamaClient` in `src/spotify_stop_ai/ollama_client.py`

## 1. Summary of Inefficiencies
The current implementation works, but is "High Friction" code. It re-invents several wheels that Mellea provides out of the box.

*   **Manual JSON Parsing**: The client has ~40 lines of code just to strip markdown backticks and `json.loads` the response.
*   **Prompt-Based Schema**: The prompt (`classify_artist.txt`) wastes ~20 lines explaining JSON syntax to the LLM.
*   **Manual Validation**: `_validate_output` manually checks types and ranges (e.g., `0.0 <= confidence <= 1.0`).
*   **Backend Lock-in**: Hardcoded to Ollama endpoints (`/api/generate`).

## 2. The "Before" (Current Code)
```python
# src/spotify_stop_ai/ollama_client.py (Simplified)

# 1. Complex Prompting
prompt = """
Response format (strict JSON):
{
  "label": "virtual_idol|vocaloid...",
  "confidence": 0.0-1.0
}
"""

# 2. Manual Parsing
raw = response["response"]
if raw.startswith("```json"): raw = raw[7:-3]
data = json.loads(raw)

# 3. Manual Validation
if not (0.0 <= data["confidence"] <= 1.0):
    return None
```

## 3. The "After" (Mellea Code)
Mellea replaces the parsing, prompting, and validation with a Type Signature.

```python
from mellea import generative
from pydantic import BaseModel, Field
from typing import Literal

# 1. Schema DEFINES the Prompt and Validation
class ArtistClassification(BaseModel):
    label: Literal["virtual_idol", "vocaloid", "human", "band", "unknown"]
    is_artificial: bool | None
    confidence: float = Field(ge=0.0, le=1.0) # Validators included!
    reason: str
    citations: list[str]

@generative
def classify_artist(evidence: str) -> ArtistClassification:
    """
    Analyze the evidence to classify the artist.
    Be conservative. If unsure, use 'unknown'.
    """

# Usage
# No parsing, no validation code needed. Mellea guarantees it matches the schema.
result = classify_artist(formatted_evidence)
```

## 4. Key Improvements
1.  **Robustness**: Mellea uses `xgrammar` (if local) or native function calling to *force* valid JSON. The `try/except json.JSONDecodeError` block disappears.
2.  **Portability**: The Mellea version works with OpenAI (GPT-4), Anthropic (Claude), or Local (Granite) by just changing the Session backend. The current `OllamaClient` only works with Ollama.
3.  **Simplicity**: Reduces `ollama_client.py` from 400 lines to ~50 lines.

## 5. Recommendation
This is a perfect candidate for the **Agentic Migration** pilot.
1.  Copy `docs/AGENTS_TEMPLATE.md` into `spotify-stop-ai`.
2.  Ask Cursor: "Refactor `ollama_client.py` to use Mellea primitives defined in AGENTS_TEMPLATE.md".
