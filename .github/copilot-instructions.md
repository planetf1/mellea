# Copilot Instructions for Mellea

This project is **mellea**, an open-source Python library for writing generative programs.

## Core pattern

Use the `@generative` decorator to turn typed Python functions into LLM-powered specifications. Do not write prompt templates, regex parsers, or manual JSON extraction.

```python
from mellea import generative, start_session
from pydantic import BaseModel

class UserProfile(BaseModel):
    name: str
    age: int
    interests: list[str]

@generative
def extract_profile(bio: str) -> UserProfile:
    """Extract a user profile from the given biography text."""
    ...

m = start_session()  # Ollama by default
profile = extract_profile(m, bio="Alice is 30 and loves hiking.")
```

## Key rules

- **Use `uv`** for all Python commands (`uv run pytest`, `uv sync`, not `pip` or bare `python`)
- **Function bodies use `...`** in `@generative` functions (the LLM fills them)
- **Docstrings are prompts** -- be specific, the LLM reads them
- **Type hints are schemas** -- Pydantic models define the output structure
- **Don't retry `@generative` calls** -- mellea handles retries internally via sampling strategies
- **Don't use `json.loads()`** -- use typed returns instead
- **Google-style docstrings** throughout the codebase
- **Angular commit format**: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`

## Sampling strategies

Add reliability with one parameter:

```python
from mellea.stdlib.sampling import (
    RejectionSamplingStrategy,      # retry on failure
    MajorityVotingSamplingStrategy,  # best-of-N voting
)

result = m.instruct("...", strategy=RejectionSamplingStrategy(loop_budget=3))
```

## Backends

```python
m = start_session()                                    # Ollama (default)
m = start_session("openai", model_id="gpt-4o")        # OpenAI
m = start_session("huggingface", model_id="...")       # HuggingFace local
```

## Testing

```bash
uv run pytest test/ -m "not qualitative"  # Fast tests (~2 min)
uv run pytest                              # Full suite
```

Markers: `@pytest.mark.ollama`, `@pytest.mark.openai`, `@pytest.mark.huggingface`, `@pytest.mark.qualitative`, `@pytest.mark.slow`

## For complete details

See `AGENTS.md` (contributing) and `docs/AGENTS_TEMPLATE.md` (using mellea).
