# Draft mellea issue 1 (DOCS) — review before filing

Type: docs
Suggested title:
Document that temperature rescales (not randomises) likelihood-scored
intrinsic outputs on LocalHF

## What users expect

`core.requirement_check()`, `core.check_certainty()`, and the other
adapter functions accept `model_options`, documented as "model-generation
overrides forwarded to the backend". Passing `{"temperature": 0.7}` reads
as "sample with some randomness", so users expect (a) the score to vary
draw to draw and (b) the score's meaning to be stable across settings.

Neither holds, and the reason is not obvious from any docstring.

## What actually happens

The options DO reach generation: `huggingface.py:1251` copies the
temperature onto the rewritten request, the Granite base formatter turns
it into `do_sample`/`temperature`
(`mellea/formatters/granite/base/util.py:363-370`), and the remaining
options are applied at `huggingface.py:1302-1308`.

But `requirement_check`/`check_certainty` (and other adapters that use
it) score through the io.yaml **likelihood transform**
(`mellea/formatters/granite/intrinsics/output.py`, `YAML_NAME =
"likelihood"`): the returned float is computed from the probabilities at
the answer token, not from the sampled label. Consequences:

1. **No per-draw variance.** Every call with the same (input, setting)
   returns the same number, whatever label the model samples.
2. **Temperature changes the score without changing its meaning
   stably.** Measured, granite-4.1-3b, `requirement_check`, three calls
   per setting:

   | temperature | score (x3) |
   |---|---|
   | 0.0 | 0.04743 |
   | 0.3 | 4.54e-05 |
   | 1.0 | 0.04743 (greedy: unscaled logits) |
   | 2.0 | 0.18265 |

   A user who passes temperature 2.0 gets a flattened probability
   distribution — a systematically different confidence number — without
   any signal in the API that this is what happened.
3. **Per-draw verdict variance is unmeasurable from the API**, because
   the sampled label is not returned. Anyone building ensemble/retry
   logic on intrinsic scores needs it.

## Suggested change

- Document the semantics on the intrinsic functions (and in the
  adapters/intrinsics docs): for likelihood-scored outputs the returned
  value is a deterministic function of (input, temperature); temperature
  rescales the confidence distribution and introduces no randomness;
  `do_sample` is accepted but does not vary the score.
- Consider returning (or exposing via metadata) the sampled label and/or
  the full answer-token distribution, so callers can measure draw
  variance and build ensembles.

## Repro

```python
from mellea import start_backend
from mellea.stdlib.components import Message
from mellea.stdlib.components.intrinsic import core
from mellea.stdlib.context import ChatContext

ctx, backend = start_backend("hf", model_id="ibm-granite/granite-4.1-3b",
                             context_type="chat")
# high-level path: the requirement-check LoRA auto-resolves and downloads
c = ChatContext().add(Message("user", "Write a response.")).add(
    Message("assistant", "Cardiff is the capital city of Wales."))
for t in (0.0, 0.3, 1.0, 2.0):
    print(t, [round(core.requirement_check(c, backend,
             "The response uses bullet points.",
             model_options={"temperature": t}), 5) for _ in range(3)])
```

Expect identical triples within each row and different values across
rows — no randomness, but setting-dependent values.

Context: found while benchmarking aLoRA activation (issue #1679); the
first hypothesis ("model_options is dropped on the intrinsic path") was
checked against the code and is wrong — this is the corrected
understanding.
