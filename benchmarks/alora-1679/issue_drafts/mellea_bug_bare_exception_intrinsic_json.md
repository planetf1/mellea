# Draft mellea issue 2 (BUG) — review before filing

Type: bug
Suggested title:
Malformed intrinsic output raises bare `Exception`, not the documented
`ValueError` (HF, Ollama, OpenAI backends)

## Contract

The intrinsic functions' docstrings promise `ValueError` when the model
output is not valid JSON or not a JSON object (e.g.
`mellea/stdlib/components/intrinsic/core.py:37-41`,
`mellea/stdlib/components/intrinsic/_util.py:207-213`, and
`_DictContract.parse`). `AdapterSchemaMismatchError` is a *different*
contract: valid JSON that is missing a required key (or has both
`label` and `score`) — its constructor takes observed/expected keys,
which unparseable text does not have.

## Actual behaviour

When the generated text is not valid JSON, the backends catch
`json.JSONDecodeError` and re-raise it as a **bare `builtins.Exception`**:

- `mellea/backends/huggingface.py:1431-1436`
  `raise Exception(f"Intrinsic did not return a JSON: {chunk}") from e`
  — where `chunk` is the whole streaming chunk, so the message dumps the
  entire `ChatCompletionResponse` repr instead of the model's text.
- `mellea/backends/ollama.py:858-864` — same pattern.
- `mellea/backends/openai.py:~1256-1262` — same pattern.

The `JSONDecodeError` only appears as `__cause__`, so tracebacks look
like a raw parser crash even though a (wrong) wrapper exists.

## Impact

- Callers catching the documented `ValueError` do not catch this — they
  need a bare `except Exception`, which defeats the point of the
  documented contract.
- Any pipeline using intrinsics for control flow (gates, retry loops)
  takes down the whole task on one malformed model output instead of
  handling the documented error.

## Reproduction (two ways)

1. **Forced truncation** (deterministic, verified 2026-09-27 on
   granite-4.1-3b): run any intrinsic with the output cap below the JSON
   length:

   ```python
   from mellea import start_backend
   from mellea.backends import ModelOption
   from mellea.stdlib.components import Message
   from mellea.stdlib.components.intrinsic import core
   from mellea.stdlib.context import ChatContext

   ctx, backend = start_backend("hf", model_id="ibm-granite/granite-4.1-3b",
                                context_type="chat")
   c = ChatContext().add(Message("user", "What is the square root of 16?")).add(
       Message("assistant", "The square root of 16 is 4."))
   try:
       core.check_certainty(c, backend,
                            model_options={ModelOption.MAX_NEW_TOKENS: 3})
   except BaseException as e:
       print(type(e), isinstance(e, ValueError))
   # <class 'Exception'> False
   ```

   Note: plain-string option keys (e.g. `{"max_new_tokens": 3}`) are
   silently ignored - the sentinel keys from `mellea.backends.ModelOption`
   are the working form.
2. **Observed in the wild (5+ reproductions)**: granite-4.1-30b *base
   model* (no active adapter) + `core.check_certainty` on a normal
   context emits truncated JSON such as `'{\n  "score":         '` and
   the call raises `Exception("Intrinsic did not return a JSON: ...")`.
   Plausible trigger (unverified on 30b): the io.yaml caps output at
   `max_completion_tokens: 15` while the JSON grammar allows unlimited
   whitespace, so an adapterless model can spend its token budget on
   whitespace and never close the object. This is exactly the failure
   mode users hit whenever an adapter does not activate (mispackaged
   io.yaml, wrong backend path) — the broken path should at least fail
   with the documented error type.

## Suggested fix

In all three backends, raise `ValueError` (or a small `ValueError`
subclass) carrying the raw output text:

```python
except json.JSONDecodeError as e:
    raise ValueError(
        f"Intrinsic output was not valid JSON: {text!r}"
    ) from e
```

- For HF: use the extracted message text in the message, not the chunk
  repr.
- Add a test per backend asserting the exception type (and that
  `AdapterSchemaMismatchError` is NOT raised for unparseable text).

## Not in scope

- Whether the 30b-base truncation itself can be made more robust
  (adapter packaging / activation is tracked in #1679).
- Retrying on malformed output (a strategy-level feature).
