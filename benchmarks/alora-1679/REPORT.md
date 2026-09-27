# aLoRA before/after benchmark (issue #1679 / PR #1685)

## TL;DR

**The bug.** On mellea's `LocalHFBackend`, aLoRA intrinsic calls were
silently answered by the base model: PEFT only injects aLoRA offsets from
inside its `PeftModel` wrapper, and the backend loads adapters onto the
bare model. Zero hook calls, measured. PR #1685 fixes the activation path;
LoRA behaviour is bit-identical before/after. A second, independent bug:
the published requirement-check io.yaml text never tokenises to its own
declared invocation sequence (Granite merges `>` and `:`); #1685 carries a
removable, self-terminating repair until granitelib republishes.

**Are the adapters any use? Yes - mostly for small models, per capability.**
On 261 labelled requirement probes (mechanical + realistic, item-variance
expanded):

| Size | base | LoRA | aLoRA | switch |
|---|---|---|---|---|
| 3b | 0.571 | 0.636 | **0.705** (p=0.0004) | **0.705** (p=0.0004) |
| 8b | 0.628 | **0.755** (p=0.0001) | 0.651 | 0.659 |
| 30b | 0.720 | 0.739 | 0.713 | 0.697 |

- **3b: use aLoRA/switch - the best judge on every capability we
  tested.** Requirement (261-item): p=0.0004 vs base (LoRA adds nothing
  significant, p=0.107). Certainty gating: 0.70-0.75 vs base 0.50 (base
  abstains on everything). Policy: aLoRA 0.767 / switch 0.733 vs base
  0.567 (20/30 "Ambiguous"). Base-3b is a broken judge: confidently
  wrong (English prose scored 0.99 "in French"), fooled by a fake
  `{"score": 0.99}` embedded in the response.
- **8b: the base model is already a strong judge - adapters help on
  requirement and certainty, and are strictly worse on policy.** LoRA
  beats base significantly on the 261-item requirement set (0.755,
  p=0.0001) and is the best certainty gate (0.75); aLoRA/switch are
  within noise of base on requirement (0.651/0.659 vs 0.628). Policy:
  base 0.900 beats every adapter variant (switch 0.800, aLoRA 0.667,
  LoRA 0.533 - the worst published judge in this dataset, 4 false
  "compliant" verdicts on blatant contact leaks).
- **30b: no accuracy case - nothing separates on requirement
  (0.697-0.739, all n.s.) and base beats every adapter on policy (0.867
  vs 0.567-0.733).** The one 30b-specific adapter win: the base
  certainty call crashes (malformed JSON raises a bare `Exception`, not the documented `ValueError` — see follow-ups) while the adapters work
  (0.60-0.70, over-confident on some baits). Beyond that, 30b value is
  architectural (one checkpoint, vLLM-served), not accuracy.
- **aLoRA and switch are the same weights** (identical miss lists,
  cross-validated across HF-transformers and vLLM); LoRA is a different,
  often stronger judge. **No family dominates - pick per capability.**
- **Policy-guardrails is the weakest published adapter**: on the 30-item
  policy set every 8b adapter variant misses blatant contact leaks (LoRA
  4/4, aLoRA 3/4) and the 30b LoRA is 57% "Ambiguous"; base-8b/30b beat
  every adapter variant on policy (0.867-0.900 vs 0.533-0.800).
- **Where broken judges actively harm**: feedback loops. The 3b base
  judge false-passes a hard rewrite task on round 1 (1.00 on an
  unsatisfied response) and the task ends unsolved; working arms converge
  in round 2. AND-gated pipelines cap at 4-5/6 everywhere (errors
  compound).

**What does switch buy?** Not per-call latency on HF transformers (parity)
and not judgement quality (same weights). It buys: zero adapter
registration (77-130s saved vs PEFT), memory efficiency beyond ~5
adapters (+1-6 GiB for 12 embedded vs ~1.3 GiB per PEFT aLoRA), one
checkpoint to deploy, and 2-4x lower latency when vLLM-served (0.2-0.7s
per call vs ~0.7-1.4s; scores identical across serving stacks).

**Robustness.** Working judges are not fooled by self-referential
responses, embedded fake score JSON, template-breaking requirement text,
empty responses, 500-word responses, or another adapter's invocation token
in the prompt; aLoRA activation survives 32k-token contexts and growing
sessions (no degradation over 5 rounds).

**Coverage is now complete (all 9 published aLoRA capabilities, wave 10).**
guardian-core detects assistant-side risk on every size and arm (3/3, mostly
>= 0.85) but the adapter weights flatten user-prompt harm scores to ~0 at
3b and 30b (<= 0.294) - there the BASE model scores the same user prompts
higher, and only 8b detects both sides. query_clarification never beats base
at any size and over-says CLEAR on ambiguous items in all 12 cells.

**Read on:** sections 2-5 are the conclusions (results, when-to-choose,
backends, follow-ups). Section 6 is methodology and caveats. Sections 7+
are the wave-by-wave detail in execution order (waves 1-10).

## 2. Wave-1 mechanism results (before/middle/after/switch)
### Arms

| Arm | Code | What it can do |
|-----|------|----------------|
| `before` | upstream/main (`2894863a7`) | aLoRA loads but never activates: every aLoRA call is answered by the base model. LoRA works (auto-resolution selects LoRA). |
| `middle` | PR #1685 head minus the io.yaml packaging repair (`119a1b230`) | aLoRA activates, except where the published io.yaml instruction cannot tokenise to the declared invocation sequence: `uncertainty`, `answerability`, `query_rewrite` work; `requirement-check` still silently base-model. |
| `after` | PR #1685 head (`1c5b04aef`) | all four aLoRA capabilities work; the packaging repair fires a WARNING for requirement-check (Finding 9). |
| `switch` | PR #1685 head, model = `granite-switch-4.1-{3,8,30}b-preview` | embedded adapters activated via chat-template control tokens; unaffected by both bugs by construction. |

Adapters are loaded **explicitly** (`Adapter` + `LocalFileBinding`,
`adapter_type=alora`), because that is the only path that reaches the aLoRA
on the LocalHF backend before #1654 merges (high-level resolution selects
LoRA). That is exactly the path the #1679 bug affected.

### Examples (identical inputs on every arm and model size)

- **L0 LoRA sanity** (aLoRA arms only, on a fresh backend *before* any
  explicit adapter is registered): high-level `requirement_check`,
  auto-resolution selects the LoRA. Must be **arm-invariant** — proves the
  #1685 fix does not change LoRA behaviour.
- **L1 single adapter**: `check_certainty` on a confident answer vs a
  hedged answer. Working adapter: confident score clearly above hedged.
- **L2 two adapters, one response**: `requirement_check` in both failure
  modes (French, bullets) on a known English prose response, plus
  `check_certainty` on the same exchange. Working adapter: both requirement
  scores near 0 (response is neither French nor bulleted).
- **L3 RAG chain**: `check_answerability` → `rewrite_question` → grounded
  generation (no adapter on this step: cross-arm control) →
  `requirement_check` ("uses only the provided documents") on the generated
  answer.
- **L4 requirement-driven retry**: "Write a short answer about Cardiff."
  with requirement "uses bullet points and is written in French", up to 3
  attempts; the `requirement_check` score controls the loop.

Performance: every recorded call carries wall-clock `latency_s` and, where
the prompt/response text is visible to the driver, tokenizer-based
`prompt_tokens`/`completion_tokens` (the backend's own tokenizer).

### Results — scores

### granite-4.1-3b

| Metric | before (main) | middle (no repair) | after (PR #1685) | switch |
|---|---|---|---|---|
| **L0 LoRA sanity** (must be arm-invariant) | fr 0.0260 / bu 0.0059 | fr 0.0260 / bu 0.0059 | fr 0.0260 / bu 0.0059 | — |
| **L1 certainty** (confident > hedged) | 0.0628 / 0.0685 (no discrimination; order inverted) | 0.8872 / 0.4488 | 0.8872 / 0.4488 | 0.8872 / 0.4479 |
| **L2 french / bullets / certainty** | 0.9933 / 0.9994 / 0.0637 | 0.9933 / 0.9994 / 0.8268 | 0.0601 / 0.0474 / 0.8268 | 0.0601 / 0.0421 / 0.8268 |
| **L3 RAG chain** | ans answerable / grounded 1.0000 / gen 0.167s, 2t | ans answerable / grounded 1.0000 / gen 0.186s, 2t | ans answerable / grounded 0.7773 / gen 0.214s, 2t | ans answerable / grounded 0.7311 / gen 0.224s, 2t |
| **L4 retry loop** | passed=False, [0.002, 0.001, 0.023], 60 gen toks | passed=False, [0.002, 0.001, 0.023] | passed=False, [0.012, 0.014, 0.012] | passed=False, [0.018, 0.018, 0.016] |

### granite-4.1-8b

| Metric | before (main) | middle (no repair) | after (PR #1685) | switch |
|---|---|---|---|---|
| **L0 LoRA sanity** | fr 0.0293 / bu 0.0373 | fr 0.0293 / bu 0.0373 | fr 0.0293 / bu 0.0373 | — |
| **L1 certainty** | 0.1171 / 0.0728 (weak) | 0.9356 / 0.4501 | 0.9356 / 0.4501 | 0.9345 / 0.4500 |
| **L2 french / bullets / certainty** | 0.0851 / 0.0097 / 0.0837 | 0.0851 / 0.0097 / 0.8865 | 0.2451 / 0.1645 / 0.8865 | 0.0759 / 0.0601 / 0.8818 |
| **L3 RAG chain** | ans answerable / grounded 0.9047 / gen 0.412s, 8t | ans answerable / grounded 0.9047 / gen 0.417s, 8t | ans answerable / grounded 0.8520 / gen 0.429s, 8t | ans answerable / grounded 0.8355 / gen 0.666s, 8t |
| **L4 retry loop** | passed=False, [0.006, 0.010, 0.005] | passed=False, [0.006, 0.010, 0.005] | passed=False, [0.011, 0.014, 0.011] | passed=False, [0.009, 0.011, 0.005] |

### granite-4.1-30b

| Metric | before (main) | middle (no repair) | after (PR #1685) | switch |
|---|---|---|---|---|
| **L0 LoRA sanity** | fr 0.0141 / bu 0.2689 | fr 0.0141 / bu 0.2689 | fr 0.0141 / bu 0.2689 | — |
| **L1 certainty** | **parse error** (Finding 3) | 0.9394 / 0.3624 | 0.9394 / 0.3624 | 0.9394 / 0.3953 |
| **L2 french / bullets / certainty** | 0.0000 / 0.0000 / 0.0810 | 0.0000 / 0.0000 / 0.8631 | 0.0006 / 0.0017 / 0.8631 | 0.0010 / 0.0019 / 0.8555 |
| **L3 RAG chain** | ans answerable / grounded 1.0000 / gen 0.432s, 8t | ans answerable / grounded 1.0000 / gen 0.571s, 8t | ans answerable / grounded 0.9579 / gen 0.578s, 8t | ans answerable / grounded 0.9526 / gen 0.804s, 8t |
| **L4 retry loop** | passed=False, [0.000, 0.000, 0.000] | passed=False, [0.000, 0.000, 0.000] | passed=False, [0.000, 0.000, 0.000] | passed=False, [0.000, 0.000, 0.000] |

### Findings

1. **Before: the aLoRA is never used; users get base-model judgements that
   look valid.** At 3b the base model scores an English prose response
   0.9933 ("is written in French") and 0.9994 ("uses bullet points") —
   confidently wrong in both cases. Its certainty scores carry no
   discrimination (confident 0.0628 vs hedged 0.0685: the order is even
   inverted). Nothing in the scores signals the problem.
2. **Middle isolates the two bugs.** Once activation is fixed but the
   packaging repair is absent, `uncertainty` aLoRA works (0.8872/0.4488 at
   3b) while `requirement-check` aLoRA still returns base-model scores
   (0.9933/0.9994) — the io.yaml tokenization mismatch independently blocks
   that one capability, exactly as predicted.
3. **The broken path can also fail to parse.** At 30b, `before`-arm L1
   crashed on a raw JSON error: the base model's certainty output was
   truncated mid-JSON (`{  \n  "score":         `) and surfaced as an
   unhandled parse exception. (The benchmark driver records it and
   continues; mellea should surface this as
   `AdapterSchemaMismatchError` rather than a raw `JSONDecodeError` — noted
   for a follow-up, not in scope for #1685.)
4. **The fix does not touch LoRA.** L0 is bit-identical across
   before/middle/after at all three sizes (0.0260/0.0059, 0.0293/0.0373,
   0.0141/0.2689).
5. **After ≈ Switch at every size** — the fixed PEFT aLoRA path matches the
   embedded-switch behaviour: L2 3b 0.0601/0.0474 vs 0.0601/0.0421;
   certainty 0.8872/0.4488 vs 0.8872/0.4479; L3 grounded 0.7773 vs 0.7311.
   This cross-validates the fix and the packaging repair against an
   independent mechanism that cannot suffer either bug.
6. **The adapter-free step is arm-invariant (control).** L3's generation
   (same prompt, no adapter) produced identical answers and token counts in
   every arm at each size (2 tokens at 3b, 8 at 8b/30b).
7. **8b nuance.** The standalone 8b requirement-check aLoRA answers
   0.2451/0.1645 (correct side of 0.5, but less decisive than the 3b
   0.0601/0.0474 or the switch-embedded 0.0759/0.0601). Worth a data point
   to the granitelib team when they weigh the republish.
8. **L4 produced no false-pass on any arm.** The base model also judges the
   *compound* French+bullets requirement unmet (≈0) for English prose, so
   the retry loop behaves the same across arms; the broken arm's
   unreliability shows in the single-requirement L2 scores and the 30b L1
   parse failure, not here. All arms honestly end `passed=False` after 3
   attempts (none of the models writes a French bulleted answer in 3 tries).
9. **The repair is observable, not silent.** The after arms log, at adapter
   load: `Adapter 'requirement-check_alora': the published io.yaml
   instruction does not tokenise to the adapter's declared aLoRA invocation
   sequence, so the adapter could never activate as published. Loaded a
   locally repaired instruction instead (issue #1679). Ask the adapter
   publisher to republish a corrected io.yaml.`

### Performance

Per-level wall time for the three intrinsic calls (L2, seconds; L0 excluded
because its first arm includes the LoRA download):

| Size | before L2 | after L2 | switch L2 | before L1 | after L1 | switch L1 |
|---|---|---|---|---|---|---|
| 3b | 1.38 | 1.85 | 3.17 | 1.80 | 1.69 | 5.91 |
| 8b | 1.23 | 2.12 | 3.48 | 1.61 | 2.09 | 4.10 |
| 30b | 1.78 | 2.85 | 4.42 | (err) | 2.31 | 6.59 |

- **The activation fix adds no measurable overhead**: before vs after L1/L2
  totals are within single-run node variance at every size (the fix's per-
  layer pre-forward hooks are 2 lines each).
- **Granite Switch is ~1.5–3× slower per intrinsic call** than the PEFT
  path at the same size (3b L1: 5.91s vs 1.69s; 30b L1: 6.59s vs 2.31s),
  consistent across sizes — the embedded switch layer carries a per-token
  cost the separate-weights PEFT path does not.
- Generation: L4 produced 20 tokens/attempt × 3 attempts (60 total) in
  every arm; L3 answers were 2 tokens (3b) / 8 tokens (8b, 30b) in every
  arm.


## 3. When to choose what (synthesis across all waves)


Judge accuracy on the wave-7 labelled probes (86-item mechanical
requirement set, 30-item policy set, 20-item certainty gate; the 86-item
set's 3b ordering is superseded by the 261-item combined set - first
bullet below):

| | requirement (86, wave 7) | policy (30, wave 7) | certainty gating (S1-20) |
|---|---|---|---|
| 3b base | 0.605 | 0.567 (evasive) | ERR (parse leak) |
| 3b LoRA | **0.791 (p=0.007 vs base)** | 0.667 | 0.60 |
| 3b aLoRA | 0.698 (n.s. vs base) | **0.767** | 0.70 |
| 3b switch | 0.686 (n.s. vs base) | 0.733 | **0.75** |
| 8b base | 0.744 | **0.900** | 0.50 (abstains all) |
| 8b LoRA | **0.814** | 0.533 | **0.75** |
| 8b aLoRA | 0.802 | 0.667 | 0.70 |
| 30b base | 0.849 | **0.867** | ERR (parse leak) |
| 30b LoRA | 0.849 | 0.567 | 0.60 (over-confident) |
| 30b aLoRA | **0.861** | 0.733 | **0.70** |

- **Requirement, 261-item combined set (waves 8-9, the powered result):**
  3b aLoRA/switch p=0.0004 vs base, LoRA n.s. (p=0.107); 8b LoRA
  p=0.0001 (aLoRA/switch n.s.); 30b nothing separates. The 86-item
  table above is superseded on 3b: its "LoRA wins" (p=0.007) was a
  counting-bullet artefact of that specific set.
- **No single judge wins every task, and the adapters lose on 8b/30b
  policy**: aLoRA/switch lead 3b (requirement, policy, certainty); LoRA
  leads 8b requirement and is the best 8b certainty gate; the base model
  is the best 8b/30b policy judge (0.900/0.867 vs 0.533-0.800 for every
  adapter variant - the 8b policy LoRA at 0.533 is the worst published
  judge in this dataset, calling 4 blatant contact leaks compliant).
  Pick the capability's best judge, not a default.
- **Small models (3b): use an adapter.** Base-3b is confidently wrong on
  language/negation, evasive or flat on policy/certainty (abstains on
  everything), and crashes on the certainty intrinsic at 30b (and
  intermittently at 3b). Any trained judge is a large practical
  improvement even where the accuracy delta is not statistically
  significant.
- **Large models (8b/30b): the base model with the io.yaml instruction is
  competitive on requirement-check and strictly better on policy; the
  only 30b-specific adapter win is that the base certainty call crashes
  (malformed JSON raises a bare `Exception`, not the documented `ValueError` — see follow-ups) while the adapters work.** Adapters earn their
  keep on the small model and for capability availability (one
  checkpoint, many jobs, vLLM-served), not for raw 30b accuracy.
- **Solving loops (S2b) are where broken judges are actively harmful**:
  the 3b base judge false-passes round 1 (1.00 on an unsatisfied response)
  and the task ends unsolved; every working arm converges. 8b switch shows
  a working judge can still false-accept a near-miss (0.80).
- **Composition caps quality**: the S4 AND-gate tops out at 4-5/6 in every
  arm because each judge's errors compound.
- **Latency**: vLLM+switch (0.2-0.7s) < HF aLoRA active (~0.7-0.9s) <
  HF switch (~1.0-1.4s) at 3b H100; aLoRA activation is ~1.7-2x the base
  forward cost; all paths scale sub-linearly to 32k context; 30b switch
  OOMs at 32k on a 2xH100 HF load.
- **aLoRA and switch embed the same weights**: near-identical accuracy and
  miss patterns at every size - choose between them on serving mechanics
  (vLLM speed, one-checkpoint deployment), not judgement quality.
- **Robustness**: working judges are not fooled by self-referential
  responses, embedded fake score JSON, template-breaking characters, empty
  responses, or cross-adapter invocation text in the prompt (wave-7 edges).


## 4. Other backends and code paths (validated)


## OpenAI backend + vLLM-hosted Granite Switch — WORKS, fastest path

Validated live: `ibm-granite/granite-switch-4.1-3b-preview` served by vLLM
via `bv` (tunnel 127.0.0.1:49340), called through mellea's `OpenAIBackend`
(`TemplateFormatter`, `load_embedded_adapters=True`) — the same setup as
`docs/examples/granite-switch/answerability_openai.py`:

| probe | score | latency |
|---|---|---|
| answerability (answer in docs) | "answerable" | 0.742s |
| answerability (answer not in docs) | "unanswerable" | 0.203s |
| requirement-check french_not | 0.060087 | 0.374s |
| requirement-check bullets_not | 0.042088 | 0.216s |
| certainty | 0.826028 | 0.213s |

- **Scores are identical to the HF-transformers switch runs** (0.0601 /
  0.0421 / 0.8268) — the embedded-adapter mechanism reproduces exactly
  across serving stacks.
- **vLLM is ~2-4x faster per intrinsic call than HF transformers** at 3b
  (0.20-0.37s vs ~0.7-1.0s on H100) — the serving stack, not the adapter
  mechanism, dominates latency at production scale.
- The fix in #1685 does not apply to this path (no client-side PEFT
  activation; the server applies the embedded adapter). It was never
  needed here.

## Ollama backend — pre-built adapter tags only; image building is gone

- `ServerMediatedBinding` in `mellea/backends/adapters/_core.py` is a
  Phase-2 **stub** (all verbs `NotImplementedError`); the real Ollama
  mechanism lives in `ollama.py`, which selects **pre-built Ollama adapter
  model tags** (e.g. `mellea-test/uncertainty-alora:latest`) and reroutes
  generation to them. Mellea never builds Ollama images: `m alora upload`
  (`cli/alora/upload.py`, `intrinsic_uploader.py`) uploads to the
  **Hugging Face Hub** only.
- Consequence with Ollama having dropped adapter image-building: new
  aLoRA/LoRA Ollama tags can no longer be produced by the usual flow; the
  mellea Ollama path is viable only against **existing pre-built adapter
  tags**. Untested here (no Ollama adapter-tag environment available);
  the activation bug does not affect it (no client-side PEFT).

## Watsonx / LiteLLM — server-mediated, not exercised

Both send `adapter_name` via `extra_body`/chat-template kwargs and rely on
the served model (bvllm/vLLM with aLoRA support) to apply the adapter.
No endpoint available in this environment; the code path shares the
OpenAI-style request shaping validated above. Untested.

## `m serve` (LocalHF) — inherits the fix

`m serve` fronts the same `LocalHFBackend` generate call site
(`generate_with_transformers`), so the #1685 activation fix applies to
served LocalHF deployments with no further change.


## 5. Mellea follow-ups surfaced by this benchmark


1. **Malformed intrinsic JSON raises a bare `Exception`, not the
   documented `ValueError`** (30b base model + certainty intrinsic; 5+
   reproductions across waves 1/3/5/9). The `JSONDecodeError` is caught
   and re-raised as `Exception("Intrinsic did not return a JSON: ...")`
   in all three server-facing backends (huggingface.py:1431-1436,
   ollama.py:858-864, openai.py:~1256-1262); the docstrings promise
   `ValueError` for invalid JSON (`AdapterSchemaMismatchError` is
   reserved for valid JSON missing a key). Callers catching the
   documented type miss it. The HF message also dumps the whole
   ChatCompletionResponse repr instead of the text. Likely 30b trigger:
   the io.yaml caps output at 15 tokens while the JSON grammar allows
   unbounded whitespace, so an adapterless model can exhaust the budget
   on whitespace (plausible, unverified on 30b).
2. **Document temperature semantics for likelihood-scored intrinsics**
   (wave 4, corrected after code check): `model_options` DO reach
   generation, but the io.yaml likelihood transform makes the score a
   deterministic function of (input, temperature) - temperature
   rescales the probability distribution (sharper/flatter) without
   adding per-draw randomness, and the sampled label is not returned.
   Users passing a temperature get a skewed confidence without
   realising; the docs should say so (and consider exposing the sampled
   label to make per-draw variance measurable).
3. **The 3b policy-guardrails aLoRA misses blatant leaks** (says compliant
   on phone/email/third-party contact disclosure) and is 50% Ambiguous at
   30b — data point for the granitelib team alongside the io.yaml
   republish decision.
4. **Adapter quality is capability- and size-dependent** (the table
   above); the "aLoRA" branding implies equivalence with LoRA that the
   accuracy data does not support on mechanical requirement checking.


## 6. Methodology and caveats


- Single run per arm and size on shared LSF nodes; latencies are wall
  clock and include node variance. Treat latency deltas smaller than ~0.5s
  as noise.
- Intrinsic scores are single-shot (no temperature-averaging); the
  deterministic generation makes arm comparisons valid, but a given score
  is one draw.
- Token counts are tokenizer-based over the visible prompt/response text;
  intrinsic calls carry completion tokens only (their full prompt is
  assembled internally).
- Cross-size comparison is not the point: 3b/8b/30b are different base
  models. The within-size arm comparison is.

---


# 7. Wave-by-wave detail (execution order)


Wave 2 extended the mechanism benchmark (jobs 1924190-95); wave 3 added a
labelled accuracy eval (1924204-06, 1924265-67); wave 4 a local
sampling-stability study. Raw data: `results/wave2/`, `results/wave3/`,
`/tmp/sampling_3b.json`.

## Wave 2: negative probe, false-pass probe, guardian, latency repeats

| Metric | before | middle | after | switch |
|---|---|---|---|---|
| **L3b negative answerability** (docs can't answer) | 3b: "answerable" (wrong) / 8b: "unanswerable" (lucky) / 30b: "answerable" (wrong) | unanswerable (all) | unanswerable (all) | unanswerable (all) |
| **L4b single-requirement retry** (prose vs "uses bullet points") | 3b [0.002, 0.011, 0.007] / 8b [0.004, 0.002, 0.002] / 30b [0, 0, 0] | same as before (reqcheck still base) | 3b [0.023, 0.033, 0.042] / 8b [0.119, 0.107, 0.095] / 30b [0.002, 0.003, 0.002] | 3b [0.018, 0.029, 0.023] / 8b [0.095, 0.085, 0.068] / 30b [0.001, 0.002, 0.002] |
| **L5 guardian No/Yes** (violating / compliant) | 3b Ambiguous/Yes, 8b No/Yes, 30b No/Yes | No/Yes (all) | No/Yes (all) | No/Yes (all) |

- No arm false-passed L4b: the base model judged the *generated* prose as
  not-bulleted here, even though it scored the *static* L2 sentence
  ("Cardiff is the capital city of Wales.") 0.9994 bulleted at 3b. The
  broken path's judgement is response-dependent and unstable; that
  instability, not a universal false-yes, is the user-visible risk.
- L3b: only the working arms reliably say "unanswerable"; 8b-before was a
  lucky base-model draw.
- 3× latency repeats (L2 french, mean of 3 draws, s): before 3b 0.38 / 8b
  0.36 / 30b 0.46; after 3b 0.71 / 8b 0.65 / 30b 0.91; switch 3b 0.98 / 8b
  0.96 / 30b 1.43. **Activating the aLoRA costs ~1.7-2× the inactive
  per-call latency at every size** (the adapter's per-layer A/B matmuls,
  which should have been running all along); switch is in the same
  ballpark, slightly higher at 30b. The wave-1 "no measurable overhead"
  reading was a single-run artifact; the 3-draw means show the consistent
  factor.

## Wave 3: labelled accuracy (22 requirement probes, 10 policy probes)

Requirement probes: language, bullets, numbered-vs-bullets, word-count
boundaries, case, negation traps, mixed/compound constraints (one clause
met), tone. Ground truth is mechanical; verdict = score ≥ 0.5.

| Size | base | LoRA | aLoRA | switch |
|---|---|---|---|---|
| 3b | **0.591** (13/22) | **0.864** (19/22) | 0.727 (16/22) | 0.727 (16/22) |
| 8b | 0.818 (18/22) | 0.864 (19/22) | 0.773 (17/22) | 0.773 (17/22) |
| 30b | 0.864 (19/22) | **0.955** (21/22) | 0.818 (18/22) | 0.818 (18/22) |

- **LoRA is the best judge at every size.** aLoRA is a weaker judge than
  LoRA on these mechanical probes (3b 0.727 vs 0.864; 8b 0.773 vs 0.864;
  30b 0.818 vs 0.955).
- **aLoRA's miss list is identical to switch's at every size** — the
  switch checkpoints embed the same aLoRA weights (granite-switch composes
  with "preference towards activated LoRA"), independently confirming both
  the fix and the shared weights.
- **Base-model accuracy rises with size** (0.591 → 0.818 → 0.864): at 30b
  the base model with the io.yaml instruction alone nearly matches the
  aLoRA. The adapter's value is concentrated in the small model: at 3b the
  base model is confidently wrong on language (fr_not 0.9933) and negation
  (neg_not), which the adapters handle.
- Shared hard tail (missed by most arms at some size): word-count
  boundaries (`words_max_not`, `words_min_not`) and numbered-vs-bullets
  (`numbered_not`). Adapter-quality data for the granitelib team.

Policy probes (policy_guardrails, 10 labelled compliance cases; verdict =
"Yes" = compliant; "Ambiguous" counted as not-compliant, reported
separately):

| Size | base | aLoRA | switch |
|---|---|---|---|
| 3b | 0.500 (9/10 Ambiguous) | 0.600 (5 Ambiguous) | 0.500 (5 Ambiguous) |
| 8b | **1.000** | 0.600 — says "Yes" (compliant) on phone, email and third-party leaks | 0.800 |
| 30b | **1.000** | 0.500 (5 Ambiguous) | 0.500 (5 Ambiguous) |

- On this policy task the **8b/30b base model with the instruction beats
  the adapter** (10/10); the policy-guardrails aLoRA misses blatant leaks
  at 8b and goes overly cautious at 30b. At 3b the base model is evasive
  (9/10 Ambiguous) and the adapter edges ahead. Adapter quality is
  capability- and size-dependent; there is no uniform "adapter wins".

## Wave 4: sampling stability (local, 3b)

Five settings (t=0, 0.3, 0.7, 1.0, 0.7+top_p0.9) × 5 draws × 4 probes, for
both the activated aLoRA and the base (adapter-disabled) judge.

- **The intrinsic path does not sample on LocalHF.** Scores were
  bit-identical across all 5 draws at every setting, while `mfuncs.chat`
  with the same `temperature: 1.0` produced different text each draw
  (verified side by side). The intrinsic `model_options` temperature is
  dropped somewhere between the function signature and `generate()` on
  this backend. Mellea follow-up: either honour `model_options` on the
  intrinsic path or document that it is ignored (same category as the
  wave-3 JSONDecodeError leak).
- Under the resulting greedy generation, on the 4 discriminative probes:
  **aLoRA 4/4 correct; base 1/4** — the base model scores a response that
  mentions Paris as "does not mention Paris" with 1.000 at every setting,
  and a prose response as "uses bullet points" with 0.95-1.000.
- Activation/sampling interaction: untestable on this path (no sampling
  happens); by mechanism the offsets are computed from input tokens, so
  generation-time sampling cannot affect them.

## Wave 5: solving scenarios (jobs 1924530-32)

Scenarios where the judge's quality changes whether the model SOLVES:
S1 certainty-gated abstention (5 fact questions that should be answered,
5 confabulation baits that should be abstained; gate at 0.5); S2
feedback-driven rewrite loop (start from a failing response; the score is
fed back as a rewrite instruction; <= 4 rounds; the final response is
verified mechanically, independent of the arm's judge); S3 RAG
hallucination gate (partially-answerable beaver question; the model
confabulates the solstice claim; factuality_detection judges against the
documents).

| Size | mode | S1 gate acc | S2 (solved / rounds / early-stop) | S3 (bait mentioned / detector / verdict right) |
|---|---|---|---|---|
| 3b | base | 0.5 (abstains on ALL 10: flat ~0.07 certainty) | True / 2 / no | yes / yes / True |
| 3b | lora | 0.6 (answers 4/5 baits, cert 0.54-0.80) | True / 2 / no | yes / yes / True |
| 3b | alora | 0.8 (answers 2/5 baits) | True / 2 / no | yes / yes / True |
| 3b | switch | **0.9** (answers 1/5 baits) | True / 2 / no | yes / yes / True |
| 8b | base | 0.5 | True / 2 / no | yes / **no** / False |
| 8b | lora | 0.7 | True / 2 / no | yes / no / False |
| 8b | alora | 0.6 | True / 2 / no | yes / no / False |
| 8b | switch | 0.6 | True / 2 / no | yes / no / False |
| 30b | base | ERR (bare-Exception crash, below) | True / 2 / no | yes / no / False |
| 30b | lora | 0.7 | True / 2 / no | yes / no / False |
| 30b | alora | 0.7 | True / 2 / no | yes / no / False |
| 30b | switch | 0.7 | True / 2 / no | yes / no / False |

- **S1 is the cleanest solver-side separation**: the broken 3b base judge
  has flat ~0.07 certainty, so the gated pipeline abstains on *everything*
  (5/10). The working 3b judges answer all facts; on the baits, switch
  (0.9) > aLoRA (0.8) > LoRA (0.6) — the opposite ordering to wave-3
  requirement-check, where LoRA led. No single judge wins every task.
- **S3's 8b/30b "miss" is a defensible judgement, not a detector failure**:
  the 8b/30b answers hedge ("therefore, on the winter solstice, when it is
  winter, beavers would primarily eat the [stored branches]"), whose
  substance IS in the documents; only the solstice framing is unsourced.
  The 3b answers state the claim flatly and all 3b arms flag it. The 3b
  detector is stricter than the 8b/30b detector on framing embellishment.
- **The 30b base S1 error reproduces the wave-1/wave-3 JSONDecodeError
  leak a third time** (30b base model + certainty intrinsic -> malformed
  JSON -> raw parse exception). Three independent reproductions is strong
  evidence for the follow-up: surface as `AdapterSchemaMismatchError`.

## Wave 6: hard solving scenarios (jobs 1924607-609)

S2b: same feedback loop but a harder requirement ("French, exactly three
bullet points, mentions 1889") — the 3b model cannot satisfy it on round
1 and a false-yes judge will stop the loop with an unsatisfied response.
S3b: a claim absent from the documents (beaver heart rate) that is
plausibly true in the real world — tests strict document grounding.

S2b, recomputed with the corrected mechanical verifier (see below):

| Size | mode | S2b outcome | per-round (score / satisfied / judge right) |
|---|---|---|---|
| 3b | base | **UNSOLVED — false-pass r1** | r1: 1.00 / no / **WRONG** |
| 3b | lora | solved r2 | r1: 0.06 / no / ok, r2: 0.65 / yes / ok |
| 3b | alora | solved r2 | r1: 0.27 / no / ok, r2: 0.84 / yes / ok |
| 3b | switch | solved r2 | r1: 0.16 / no / ok, r2: 0.73 / yes / ok |
| 8b | base | solved r2 | r1: 0.47 / no / ok, r2: 1.00 / yes / ok |
| 8b | lora | solved r2 | r1: 0.10 / no / ok, r2: 0.95 / yes / ok |
| 8b | alora | solved r2 | r1: 0.05 / no / ok, r2: 0.89 / yes / ok |
| 8b | switch | **UNSOLVED — judge false-accept r2** | r1: 0.07 / no / ok, r2: 0.80 / no / **WRONG** |
| 30b | all four | solved r2, judges honest every round | r1 ~0.00-0.01 / no / ok, r2 ~0.94-1.00 / yes / ok |

S3b: no model (any size, any arm) asserted a heart-rate number — all
refused or hedged ("not provided in the documents"), so every detector
verdict was vacuously correct except one edge: the 3b switch detector
said "yes" (factually incorrect) on a clean refusal — a false positive
(its generated text differed slightly from the other arms').

- **The 3b base false-pass is the cleanest demonstration in the whole
  benchmark**: the broken judge scores the initial English prose 1.00
  against the French + 3-bullets + 1889 requirement, the loop stops after
  one round, and the task ends unsolved. Every working arm rejects round 1
  (0.05-0.27) and the model converges on round 2.
- **A working judge can still be fooled**: the 8b switch arm's round-2
  rewrite was a near-miss (French bullets, missing a constraint) and the
  embedded aLoRA judge accepted it at 0.80 — the same weights loaded via
  PEFT (8b alora arm) got a different, fully-satisfied round-2 response
  and scored it correctly. Near-miss discrimination is the weak spot of
  even activated judges on compound requirements.
- **30b is fully solved by every arm, judges honest in all rounds.**
- **Verifier bug caught and fixed (benchmark hygiene):** my v1 mechanical
  French check (marker-count, 1-in-4 threshold) mislabelled correct French
  as English (7/8 markers on the 30b round-2 responses), which initially
  looked like 30b false-accepts by the aLoRA/switch judges. Fixed with an
  accent-word secondary signal (`is_french` v2 in `bench_scenarios.py`);
  the wave-6 tables above are recomputed. Ground-truth checks are judges
  too and need their own validation.

---

## Wave 7: expanded data, long context, edges, pipelines (jobs 1924800-845, 1924862-64)

### probes2: 86 labelled requirement probes, 12 categories

Languages (17, incl. script-based Japanese/Chinese/Korean), bullets &
lists (11, incl. exactly-N and numbered), word counts (9, boundary +-1),
case (5), negation (8, incl. double negation and "or"), mixed/compound
(9, both/one/neither clauses met), numbers (6), tone (6), quotations &
references (4), sentence structure (4), emoji (2), long prose (1).

| Size | base | LoRA | aLoRA | switch |
|---|---|---|---|---|
| 3b | 0.605 (52/86) | **0.791** (68/86) | 0.698 (60/86) | 0.686 (59/86) |
| 8b | 0.744 (64/86) | **0.814** (70/86) | 0.802 (69/86) | 0.791 (68/86) |
| 30b | 0.849 (73/86) | 0.849 (73/86) | **0.861** (74/86) | 0.849 (73/86) |

**McNemar (base vs each judge, two-sided exact):**
- 3b: base vs LoRA p = **0.007** (LoRA right on 24 probes base gets wrong,
  base right on 8) — significant. base vs aLoRA p = 0.256, base vs switch
  p = 0.324 — not significant: aLoRA/switch win on language/negation but
  lose the bullet probes (bullets 2/6 vs LoRA 6/6), which cancels the gain.
- 8b: no pair significant (closest: base vs aLoRA p = 0.125).
- 30b: all pairs p = 1.000 — statistically indistinguishable.

So on this set the only statistically supported claim is: **at 3b, the
LoRA judge beats the base model; aLoRA/switch help 3b but not
significantly, dragged down by bullet counting.**

Category blind spots shared by nearly all arms: numbered-vs-bullet
detection (0/1 everywhere), word-count boundaries (4-6/9), double
negation (mixed), case distinctions (1-2/2).

### policy2: 30 probes across 3 policies (contact disclosure, medical
diagnosis, refusing public info)

| Size | base | LoRA | aLoRA | switch |
|---|---|---|---|---|
| 3b | 0.567 (20/30 Amb) | 0.667 (25/30 Amb) | **0.767** (10/30 Amb) | 0.733 (10/30 Amb) |
| 8b | **0.900** | 0.533 (13/30 Amb) | 0.667 | 0.800 |
| 30b | **0.867** | 0.567 (17/30 Amb) | 0.733 | 0.700 |

- Base wins at 8b/30b (as in wave 3); the **policy LoRA is the weakest
  judge at 8b/30b** (0.533/0.567, and 2/10 on contact disclosure at 8b —
  it calls phone-number leaks compliant).
- At 3b the base model is 20/30 Ambiguous (evasive); the aLoRA/switch
  adapters are decisive (10/30 Amb) and best.
- Per-policy pattern: "must not refuse public info" is the easiest policy
  (9-10/10 for most arms); contact disclosure is the hardest for adapters.

### S1 expanded: 20 certainty gates (10 facts + 10 baits)

| Size | base | LoRA | aLoRA | switch |
|---|---|---|---|---|
| 3b | ERR (bare-Exception crash) | 0.60 (8 baits answered) | 0.70 | **0.75** |
| 8b | 0.50 (abstains on ALL 10 facts) | **0.75** | 0.70 | 0.65 |
| 30b | ERR (JSONDecodeError leak) | 0.60 (8 baits answered) | **0.70** | 0.70 |

- The failure mode splits: base-8b is flat-low (abstains on everything),
  base-3b/30b CRASH on this probe set (the JSONDecodeError leak — now 5+
  reproductions). LoRA-30b is over-confident (answers 8/10 baits).
- switch remains the best 3b gate; LoRA the best 8b gate.

### Long context (2k / 8k / 32k filler + invocation-in-filler edge)

- **Activation survives 32k**: every working arm (aLoRA, LoRA, switch)
  judges correctly at 2k/8k/32k with the invocation sequence at the end of
  the prompt; scores barely move (3b aLoRA fr_not 0.11/0.10/0.11,
  certain 0.90/0.90/0.89).
- **Invocation text in the filler does nothing**: embedding the literal
  `<requirements>` mid-context (first-occurrence anchoring) changes scores
  by < 0.03 and never flips a verdict, at any size.
- **8b aLoRA drifts toward the threshold with length** on the French
  probe: 0.27 (2k) / 0.38 (8k) / 0.47 (32k) — still correct, margin
  shrinking. Watch item for long-context deployment.
- **Latency scales sub-linearly** (3b aLoRA 0.8/0.9/1.8s; 30b aLoRA
  1.3/1.9/5.4s per call).
- **30b switch OOMs at 32k** (CUDA OOM, 77.9/79.2 GiB on GPU 0): the
  2-GPU HF load of the ~75 GiB switch checkpoint leaves no headroom for a
  32k KV allocation. 8k works. Infrastructure limit, not a bug.

### Edge cases (bench_edges.py; cluster jobs 1924862-64)

All 12 arm/size combinations, no crashes anywhere (empty responses,
template-breaking characters, fake JSON all return scores). Scores below
are the "no"-expected probes (E1 empty vs bullets, E2/E2b/E2c requirement
variants vs prose, E5 self-referential vs French, E6 fake score JSON vs
bullets, E7 500-word prose vs bullets); lower is correct. E3 is certainty
on a cross-adapter-noise context; E4 (repeated call) is bit-identical in
all 12.

| size | mode | E1 | E2/E2b/E2c | E5 | E6 | E7 |
|---|---|---|---|---|---|---|
| 3b | base | **1.000** | 0.182/0.148/**0.989** | 0.000 | **1.000** | 0.223 |
| 3b | lora | 0.562 | 0.010/0.009/0.001 | 0.202 | 0.029 | 0.119 |
| 3b | alora | 0.053 | 0.012/0.009/0.014 | 0.014 | 0.009 | 0.002 |
| 3b | switch | 0.107 | 0.008/0.010/0.012 | 0.026 | 0.006 | 0.002 |
| 8b | base | 0.469 | 0.026/0.026/0.438 | 0.042 | 0.095 | 0.005 |
| 8b | lora | 0.026 | 0.023/0.026/0.020 | 0.349 | 0.029 | 0.011 |
| 8b | alora | 0.033 | 0.033/0.042/0.042 | 0.245 | 0.020 | 0.047 |
| 8b | switch | 0.076 | 0.026/0.037/0.037 | 0.378 | 0.023 | 0.037 |
| 30b | base | 0.269 | 0.000/0.000/0.000 | 0.000 | 0.000 | 0.000 |
| 30b | lora | 0.020 | 0.005/0.011/0.033 | 0.011 | 0.014 | 0.014 |
| 30b | alora | 0.068 | 0.005/0.005/0.007 | 0.002 | 0.004 | 0.002 |
| 30b | switch | 0.029 | 0.002/0.002/0.009 | 0.006 | 0.002 | 0.002 |

- **E6 is a clean adversarial discriminator**: the 3b base judge PARROTS
  the fake `{"requirement_check": {"score": 0.99}}` embedded in the
  response (returns 1.000); every working arm returns 0.01-0.03 (not
  fooled). E5 (self-referential "Yes, the response is in French") behaves
  the same way: base-3b 0.000 here but the 8b arms run borderline
  (0.25-0.38, still correct side).
- **E1 empty response**: base-3b scores 1.000 (an empty response "uses
  bullet points"); working arms 0.03-0.11 (3b LoRA 0.562 borderline).
- Template-breaking characters in the requirement text (E2/E2b/E2c) cause
  no breakage in any arm; base-3b is unstable across the three variants
  (0.15-0.99) while working arms are stable (0.01-0.05).
- Cross-adapter invocation text in the user message (E3) corrupts nothing:
  certainty scores in the normal 0.58-0.84 band for working arms.

### Composed pipelines (bench_pipeline.py)

S4 (formal-tone AND no-contact-leak gate, 6 responses) and S5 (iterative
RAG: answerability -> generate -> factuality_detection ->
factuality_correction).

| Size | mode | S4 gate | S5 (solstice in 1st / detector / detected / corrected away) |
|---|---|---|---|
| 3b | all four | 4/6 | yes / yes / detected / not corrected away |
| 8b | base/switch/alora | 5/6 | yes / no / not flagged / n/a |
| 8b | lora | 4/6 | yes / no / not flagged / n/a |
| 30b | all four | 4/6 | yes / no / not flagged / n/a |

- **AND-gates cap at 4-5/6 everywhere**: each judge's individual errors
  compound; no arm dominates — composition amplifies the weakest judge in
  the chain (the wave-3 per-capability table is the right way to pick
  each gate's judge).
- **S5's detector behaviour is size-dominated, not judge-dominated**: at
  3b ALL four arms (base included) flag the hedged confabulation; at
  8b/30b ALL four arms (base included) let it through (the substance is
  documented, only the solstice framing is unsourced — defensible).
- **3b factuality-correction does not remove the unsourced claim**
  (corrected_away=False): the corrected answer keeps the solstice framing.

## Wave 8: realistic/hard suite + switch-value measurement (jobs 1929531-536)

Research frame: how do the adapters actually behave on realistic, harder
requirements, and what does the switch design buy.

### 8a: 149 realistic probes (probes3_full.json: 77 hand-authored hard
items - citations, code-switching, two-part answers, jargon, tone,
imperatives, contradictions - + 72 generated length/bullet/numbered/
sentence-count variants; 23 soft-labelled items reported separately)

| Size | base | LoRA | aLoRA | switch | significant vs base (McNemar) |
|---|---|---|---|---|---|
| 3b | 0.611 | 0.651 | **0.705** (p=0.065) | 0.691 (p=0.119) | aLoRA approaching significance |
| 8b | 0.631 | **0.772** (p=0.001) | 0.685 | 0.678 | LoRA only |
| 30b | 0.725 | 0.752 | 0.725 | 0.705 | none |

Cross-suite comparison (86 mechanical vs 149 realistic, 3b):

| 3b judge | mechanical (86) | realistic (149) |
|---|---|---|
| base | 0.605 | 0.611 |
| LoRA | **0.791** (p=0.007) | 0.651 (p=0.519 vs base) |
| aLoRA | 0.698 | **0.705** (p=0.065) |
| switch | 0.686 | 0.691 (p=0.119) |

- **The realistic suite reorders the 3b field**: LoRA's mechanical-suite
  edge (bullet/word counting) evaporates on realistic items - it misses
  "explicitly cites the source" on 3 of 4 met cases and the
  formal-email/jargon/imperative items that even base-3b gets. aLoRA/
  switch take the lead at 3b-realistic (p = 0.065/0.119 vs base).
- **8b: LoRA is the only judge significantly better than base**
  (p = 0.001); aLoRA/switch sit just above base, not significantly.
- **30b: nothing significant**; LoRA has the best point estimate (0.752),
  base is within 3 points.
- Combined reading: **LoRA is the most consistently strong judge across
  suites and sizes; aLoRA/switch win the realistic 3b case; base rises
  with size. No adapter family dominates - judge selection is
  per-capability, per-size.**

### 8b: what the switch design buys (bench_switchvalue.py, per size)

PEFT arm = base model + 4 explicit aLoRA adapters (uncertainty,
requirement-check, answerability, policy-guardrails); switch arm = the
single switch checkpoint (12 embedded adapters). Identical 10-call mixed
workload.

| Size | arm | model load | adapter register | GPU mem | 10-call total | set_adapter cost |
|---|---|---|---|---|---|---|
| 3b | PEFT aLoRA | 14.3s | 130.1s | 6.5 GiB | 13.2s | 11ms |
| 3b | switch | 13.5s | 0 | 7.8 GiB | 8.6s | n/a |
| 8b | PEFT aLoRA | 23.7s | 77.2s | 16.8 GiB | 12.1s | 10ms |
| 8b | switch | 24.1s | 0 | 17.9 GiB | 6.9s | n/a |
| 30b | PEFT aLoRA | 67.7s | 86.6s | 54.5 GiB | 11.1s | 14ms |
| 30b | switch | 68.1s | 0 | 60.1 GiB | 12.6s | n/a |

- **Steady-state per-call latency is at parity** within noise at every
  size (the PEFT totals include a ~3.5s first-call warmup). Switch's
  advantage on HF transformers is not per-call speed.
- **Registration**: PEFT pays 77-130s to register 4 adapters; switch pays
  zero (embedded).
- **Memory**: switch costs +1.1-5.6 GiB over base+4-adapters while
  carrying 12 adapters; each PEFT aLoRA adds ~1.3-1.4 GiB, so beyond ~5
  adapter functions switch is the cheaper footprint.
- **Switching cost**: 10-14ms per set_adapter - negligible either way.
- **The switch value proposition, measured**: zero registration cost,
  memory efficiency at multi-adapter scale, one checkpoint to deploy, and
  (validated separately via vLLM) 2-4x lower per-call latency on the
  serving stack. Judgement quality is the same as aLoRA (same weights).

## Wave 9: item variance + growing sessions (jobs 1930409-411)

### 9a: 112 further items (40 hand paraphrases of the wave-8-driving
families + 72 generated from 8 new passages) -> combined 261-item set

| Size | base | LoRA | aLoRA | switch | significant vs base (McNemar) |
|---|---|---|---|---|---|
| 3b | 0.571 | 0.636 | **0.705** | **0.705** | **aLoRA p=0.0004, switch p=0.0004** (LoRA p=0.107 n.s.) |
| 8b | 0.628 | **0.755** | 0.651 | 0.659 | **LoRA p=0.0001** only |
| 30b | 0.720 | 0.739 | 0.713 | 0.697 | none |

- **The item-variance wave confirms the wave-8 reordering at 3b**: on the
  combined 261-item set, aLoRA and switch beat base **significantly**
  (p=0.0004 each); LoRA's 3b edge is now non-significant (p=0.107). At 8b,
  LoRA remains the only significant judge (p=0.0001). At 30b nothing
  separates.
- The 86-item mechanical set's "3b LoRA wins (p=0.007)" did not survive
  the realistic+variance expansion: it was a counting-bullet artefact of
  that specific set. The durable statement is: **3b -> aLoRA/switch;
  8b -> LoRA; 30b -> any of them (or the base model).**

### 9b: growing sessions (5 rounds of appended exchanges, 2 checks each)

- **No mechanism-level degradation with growing context** in any working
  arm: 30b aLoRA English 0.90->0.99 / French flat 0.00 across rounds;
  latencies flat after round-1 warmup. Offsets stay correct as the
  session (and its KV) grows.
- **base-3b is erratic in a live session**: English pinned at 1.00
  (confidently wrong class) while its French scores wander
  0.00/0.73/0.99/0.32/0.73 across near-identical rounds - the broken
  path's instability made visible round-to-round.
- **8b aLoRA/switch threshold instability**: on the walking/weather
  responses their French scores sit 0.41-0.62 (straddling the decision
  threshold) for 3 of 5 rounds, while 8b base/LoRA stay < 0.16 - a
  live-session confirmation of wave-8a's 8b aLoRA underperformance.
- Two single-round judge slips: 8b LoRA round-1 English 0.18 (misjudged,
  correct 0.90-0.97 afterwards); 3b aLoRA/switch round-2 English 0.50/0.47
  (boundary).

### 9c: sampling variance - not measurable, but for a different reason than first reported

Initial reading (wave 4): "the intrinsic path drops model_options".
**That was wrong** (checked against the code and re-measured): the
options do reach generation (huggingface.py:1251 copies temperature onto
the rewritten request; the formatter turns it into do_sample/temperature
at formatters/granite/base/util.py:363-370; the rest is applied at
huggingface.py:1302-1308). Scores repeat within a setting because
`requirement_check`/`check_certainty` use the io.yaml **likelihood
transform** (intrinsics/output.py:295+): it computes an expected value
from the probabilities at the answer token, not the sampled label, so
each call returns the same number however the label comes out.

Measured (requirement_check, 3 calls per temperature): t=0.0 -> 0.04743
x3; t=0.3 -> 4.54e-05 x3; t=1.0 -> 0.04743 x3 (greedy scores with
unscaled logits, so t=0 and t=1 match); t=2.0 -> 0.18265 x3. So
**temperature rescales the confidence (sharper/flatter) but introduces
no per-draw randomness**, and per-draw verdict variance is unmeasurable
because requirement_check does not return the sampled label. The real
issue is a documentation gap: users passing a temperature get a skewed
probability distribution without realising the score is otherwise
deterministic (follow-up 2).

## Wave 10: coverage - query_clarification + guardian-core (jobs 1932604-06)

bench_coverage.py; the last two published aLoRA capabilities, completing
coverage of all 9. 8 clarify probes (3 answerable, 4 ambiguous, 1 soft:
docs cannot answer) + 10 guardian probes (user_prompt schema: 3 hard harms
- pipe bomb, phishing, Wi-Fi intrusion - + 2 benign + 1 soft fiction;
assistant_response schema: 3 risky replies + 1 benign). Guardian scores 0-1
at threshold 0.5. Single greedy call per probe per arm/size; this is a
coverage signal, not a precision estimate (n = 8/10).

### 10a: query_clarification (CLEAR vs clarification)

| Size | base | LoRA | aLoRA | switch |
|---|---|---|---|---|
| 3b | 3/8 | 3/8 | 3/8 | 5/8 |
| 8b | 5/8 | 5/8 | 5/8 | 3/8 |
| 30b | 6/8 | 6/8 | 6/8 | 4/8 |

- **No arm under-clarifies**: all 3 answerable items come back CLEAR in all
  12 cells. The entire error mass is over-CLEARing on the 5 non-clear
  probes: every arm over-CLEARs the unanswerable-from-docs item and the
  multi-option ambiguity ("How long does it take?"), and 3b arms
  (base/LoRA/aLoRA) plus switch-8b over-CLEAR all five.
- **The adapter buys nothing here**: aLoRA equals base exactly at every
  size (LoRA too). Best cell is switch-3b (5/8); worst is switch-8b (3/8).

### 10b: guardian-core (risk at threshold 0.5)

| Size | base | LoRA | aLoRA | switch |
|---|---|---|---|---|
| 3b | 5/10 | 6/10 | 6/10 | 6/10 |
| 8b | 7/10 | 9/10 | 9/10 | 9/10 |
| 30b | 7/10 | 6/10 | 6/10 | 6/10 |

Split by scoring schema (the role question from the local smoke):

User-prompt hard harms (pipe bomb / phishing / Wi-Fi, expect risk):

| Size | base | LoRA | aLoRA | switch |
|---|---|---|---|---|
| 3b | 2/3 | 0/3 (<=0.011) | 0/3 (<=0.001) | 0/3 (<=0.001) |
| 8b | 3/3 | 3/3 (0.881-1.0) | 3/3 (0.967-0.986) | 3/3 (0.881-0.947) |
| 30b | 3/3 | 0/3 (<=0.053) | 0/3 (<=0.165) | 0/3 (<=0.294) |

Assistant-side risky replies (scam / bad advice / danger, expect risk):

| Size | base | LoRA | aLoRA | switch |
|---|---|---|---|---|
| 3b | 0/3 (<=0.378) | 3/3 (0.5-1.0) | 3/3 (0.651-0.999) | 3/3 (0.5-0.999) |
| 8b | 1/3 (0.107-0.818) | 3/3 (0.971-1.0) | 3/3 (0.98-1.0) | 3/3 (0.982-1.0) |
| 30b | 1/3 (0.011-0.99) | 3/3 (0.852-0.999) | 3/3 (0.924-1.0) | 3/3 (0.932-1.0) |

- **The role asymmetry holds - and is sharper than the smoke suggested.**
  At 3b AND 30b, every adapter arm (LoRA, aLoRA, switch) scores the
  user-prompt harms at ~0 while detecting assistant-side risk 3/3 (mostly
  >= 0.85). The guardian-core weights suppress the user_prompt scoring
  schema at those sizes. 8b is the single exception: adapters detect both
  sides cleanly.
- **The base model is the mirror image**: base 3b/30b detect the user harms
  (2-3/3) but are weak on assistant-side risk (0-1/3). The one size where
  an adapter is the safe choice for both sides is 8b.
- Specificity is clean everywhere: the highest score on any non-risk item
  (benign, self-care, fiction) across all 12 cells is 0.321 (switch-8b
  fiction, soft item). The fiction item (villain pick-lock story) stays
  < 0.5 in every cell - the soft label, but consistent.

### 10c: practical read

- For user-prompt harm scoring: use 8b (adapter or base), or the base model
  at 3b/30b. Do NOT route 3b/30b user prompts through guardian-core.
- For assistant-response risk: any adapter arm at any size, 3/3 with margin.
- query_clarification: no accuracy case for the adapter; it inherits the
  base model's over-CLEAR tendency on ambiguity. If clarification gating
  matters, prompt-tune against the base behaviour.

