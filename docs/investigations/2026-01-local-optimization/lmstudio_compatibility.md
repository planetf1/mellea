# Research Report: LM Studio Compatibility & Ollama Parity
**Date**: 2026-01-14
**Topic**: Replacing `Ollama` with `LM Studio` for Local Inference

## 1. The Hypothesis
Since LM Studio offers an "Ollama-compatible Server", we hypothesized we could simply point `OllamaModelBackend` to `http://localhost:1234` and get free compatibility with all LM Studio features (GUI, model management).

## 2. The Experiment
We attempted to run `test_ollama.py` against a running LM Studio instance serving `Llama-3-8B`.

```python
backend = OllamaModelBackend(
    base_url="http://localhost:1234",
    model_id="local-model"
)
```

## 3. The Findings (Incompatibility)
The experiment failed due to API drift.
*   **Ollama API**: Mellea uses the `/api/generate` and `/api/chat` endpoints native to Ollama.
*   **LM Studio API**: LM Studio's "Ollama Compatibility" is incomplete. It primarily emulates the **OpenAI API** standards (`/v1/chat/completions`) and does *not* fully implement the proprietary Ollama control endpoints.

## 4. Conclusion & Recommendation
*   **Do Not Use `OllamaModelBackend` for LM Studio**.
*   **Use `OpenAIModelBackend` Instead**: Since LM Studio creates an OpenAI-compatible server, the correct integration path is to treat it as an OpenAI provider.

```python
# CORRECT WAY to use LM Studio
backend = OpenAIModelBackend(
    base_url="http://localhost:1234/v1",
    api_key="lm-studio"
)
```

## 5. Strategic Implication
We should stop trying to maintain "Backend-Specific" clients (Ollama, vLLM, DeepSeek) if they all eventually converge on the OpenAI specification. The `OpenAIModelBackend` should be the "Universal Backend" for 90% of use cases.
