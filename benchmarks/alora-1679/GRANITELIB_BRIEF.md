# Adapter function quality: findings from the #1679 benchmark

Shared with the granitelib team. All measurements: granite-4.1 at 3b/8b/30b,
BlueVela H100, mellea LocalHFBackend, single-shot greedy inference
(deterministic; the intrinsic path does not sample — see note 5 below).
Every number below is reproducible from the probe files and scripts cited in
the appendix.

Scope: judgement quality of the published adapter functions (requirement-
check, uncertainty, answerability, query_rewrite, policy-guardrails,
factuality-detection, factuality-correction) as aLoRA (PEFT-loaded) and as
Granite Switch embedded adapters, versus LoRA where published and versus the
base model given the same io.yaml instruction.

## 1. The adapters are not interchangeable — and aLoRA ≠ LoRA in quality

Requirement-checking on 86 mechanical probes (language, bullets, word
counts, case, negation, compound constraints; labelled ground truth):

| Size | base | LoRA | aLoRA | switch |
|---|---|---|---|---|
| 3b | 0.605 | **0.791** | 0.698 | 0.686 |
| 8b | 0.744 | **0.814** | 0.802 | 0.791 |
| 30b | 0.849 | 0.849 | **0.861** | 0.849 |

- The 3b LoRA vs base gap is statistically significant (McNemar p = 0.007);
  no other pair is (86 probes is underpowered for ~8% effects — the
  "equivalences" below are "no detectable difference", not proof).
- **aLoRA is a weaker requirement-check judge than LoRA at every size on
  the mechanical set.** The gap is concentrated in counting and list
  structure: bullets exactly-N — LoRA 6/6 vs aLoRA/switch 2/6 at 3b;
  word-count boundaries missed by most arms (4-6/9); numbered-vs-bullet
  missed by all arms.
- aLoRA and switch agree almost perfectly (same embedded weights; identical
  miss lists at every size on both the 86- and 149-probe sets).

Re-run on a 149-item REALISTIC set, then expanded with 112 further
item-variance probes (paraphrases of the driving families + new content
for the count/length families) to a **combined 261-item set**:

| Size | base | LoRA | aLoRA | switch | significant vs base (McNemar) |
|---|---|---|---|---|---|
| 3b | 0.571 | 0.636 | **0.705** | **0.705** | **aLoRA p=0.0004, switch p=0.0004** (LoRA p=0.107) |
| 8b | 0.628 | **0.755** | 0.651 | 0.659 | **LoRA p=0.0001** only |
| 30b | 0.720 | 0.739 | 0.713 | 0.697 | none |

The item-variance expansion settles 3b: **aLoRA and switch beat base
significantly (p=0.0004)**; the 86-item mechanical set's "LoRA wins at
3b" was a counting-bullet artefact of that set and does not survive. At
8b, LoRA is the only significant judge (p=0.0001); aLoRA/switch there
also show threshold-straddling scores (0.41-0.62) on some content in
live sessions. **Durable result: 3b -> aLoRA/switch; 8b -> LoRA; 30b ->
nothing separates (base within noise).**

## 2. Per-adapter findings

**requirement-check (aLoRA)**
- Bullet/numbered/word-count discrimination is its weak spot (above).
- False-accepts a near-miss on a compound requirement at 8b: a French
  bullet response missing one of three constraints scored 0.80 in a
  rewrite loop and stopped the loop early (the PEFT-loaded same-weights
  arm got a different, fully-satisfied rewrite and scored it correctly —
  the error is in the judge, not the weights).
- Unfooled by adversarial inputs: self-referential responses, embedded
  fake score JSON, template-breaking characters in the requirement text,
  empty responses, 500-word responses, another adapter's invocation token
  in the prompt (all 12 arm/size combinations clean).
- The known io.yaml tokenization defect (issue #1679) is still the
  activation blocker for this adapter specifically.

**uncertainty (aLoRA)**
- Best certainty gate at 3b on 20 gated questions (10 facts + 10
  confabulation baits): switch 0.75, aLoRA 0.70, LoRA 0.60, base 0.50
  (base abstains on ALL 10 facts: flat ~0.07 certainty).
- At 30b all three adapter variants answer 8 of 10 baits (over-confident
  on confabulation prompts); LoRA-8b is the best 8b gate (0.75).
- Confident vs hedged discrimination is clean at every size once activated
  (0.89-0.94 confident, 0.36-0.45 hedged).

**answerability (aLoRA)**
- Correct on both positive and negative probes at every size/variant
  ("unanswerable" for a question the docs cannot answer — the base model
  says "answerable" at 3b/30b). No defects found.

**query_rewrite (aLoRA)**
- Produces sensible rewrites; no defects found in any workload.

**policy-guardrails (aLoRA) — the weakest published adapter in this data**
- 30-probe set across 3 policies (contact disclosure, medical diagnosis,
  refusing public info):
  | Size | base | LoRA | aLoRA | switch |
  |---|---|---|---|---|
  | 3b | 0.567 (20/30 Amb) | 0.667 (25/30 Amb) | **0.767** | 0.733 |
  | 8b | **0.900** | 0.533 | 0.667 | 0.800 |
  | 30b | **0.867** | 0.567 (17/30 Amb) | 0.733 | 0.700 |
- **At 8b it says "Yes" (compliant) on 3 of 4 blatant contact leaks**
  (phone number, personal email, third-party contact); the 30b variant is
  50% Ambiguous and also misses the blatant leaks.
- The 8b/30b base model given the same instruction beats every adapter
  variant on this task (0.87-0.90).
- Per policy: "must not refuse public info" is easy for all (8-10/10);
  contact disclosure is the hard one for adapters.

**factuality-detection (aLoRA)**
- Strictness is size-dominated, not variant-dominated: at 3b ALL variants
  (base included) flag a hedged confabulation ("on the winter solstice,
  beavers eat the stored branches..." where only the framing is
  unsourced); at 8b/30b ALL variants let the same answer through.
- One false positive: switch-3b flagged a clean refusal ("the document
  does not provide this") as factually incorrect; the PEFT variants did
  not.
- On a fully-unsourced numeric claim (heart rate), every model simply
  refused to invent the number, so the detector had nothing to catch —
  the RAG prompts we used elicit refusal rather than confabulation at
  8b/30b.

**factuality-correction (aLoRA, 3b)**
- When triggered, it did not remove the unsupported claim: the corrected
  answer kept the solstice framing. Correction strength at 3b is limited.

## 3. What base models do right (context for the above)

- 8b/30b base + io.yaml instruction is competitive on requirement-checking
  and better on policy; the adapters' accuracy case at 8b/30b is not
  supported by this data. Their case there is architectural (one
  checkpoint, many capabilities, shared KV, vLLM-served).
- Base-3b is the genuinely broken judge: confidently wrong on
  language/negation (0.99 that prose is French), evasive on policy
  (20/30 Ambiguous), flat on certainty (abstains on everything), parrots a
  fake `{"score": 0.99}` embedded in the response (returns 1.000), scores
  an empty response 1.000 as "uses bullet points", and crashes the
  certainty intrinsic with a malformed JSON output at 30b (mellea-side
  parsing note, separate from adapter quality).

## 4. Practical guidance that falls out of the data

- 3b deployments: use aLoRA/switch (significant over base, p=0.0004, on
  the combined 261-item requirement set; also the best certainty gates,
  0.70-0.75 vs LoRA 0.60). LoRA only for purely mechanical counting
  checks.
- 8b: LoRA is the significant judge on realistic requirement items
  (p=0.0001); expect threshold-straddling scores (0.41-0.62) from the
  aLoRA/switch variants on some content - treat near-0.5 verdicts with
  care.
- 8b/30b: pick the judge per capability (the table in §1-2); do not assume
  aLoRA ≡ LoRA — they are different adapters with different profiles.
  At 30b no judge beats base significantly - choose on serving mechanics.
- In multi-judge pipelines (AND gates), quality caps at the weakest judge:
  our 6-response AND-gate topped out at 4-5/6 in every arm configuration.
- aLoRA ≈ switch in judgement quality everywhere; choose between them on
  serving mechanics.

## 5. What the switch design buys (measured, per size)

PEFT base + 4 explicit aLoRA adapters vs the single switch checkpoint
(12 embedded), identical 10-call mixed workload:

| Size | PEFT: load / register 4 / mem | switch: load / register / mem | 10-call total (PEFT / switch) |
|---|---|---|---|
| 3b | 14.3s / 130.1s / 6.5 GiB | 13.5s / 0 / 7.8 GiB | 13.2s / 8.6s |
| 8b | 23.7s / 77.2s / 16.8 GiB | 24.1s / 0 / 17.9 GiB | 12.1s / 6.9s |
| 30b | 67.7s / 86.6s / 54.5 GiB | 68.1s / 0 / 60.1 GiB | 11.1s / 12.6s |

Steady-state per-call latency is at parity on HF transformers; each PEFT
aLoRA adds ~1.3-1.4 GiB (so beyond ~5 adapter functions switch is the
cheaper footprint); set_adapter switching is 10-14ms (negligible). Switch
value = zero registration cost + memory at multi-adapter scale + one
checkpoint + 2-4x lower latency when vLLM-served. Judgement quality is
identical (same weights).

## 6. Notes for interpreting

- Single-shot greedy scoring (the mellea intrinsic path drops
  `model_options` temperature on LocalHF — filed as a mellea follow-up),
  so no per-draw variance is visible; item-level variance across
  paraphrases is the remaining unknown (the 149-probe wave-8 set is
  running to address this).
- "Ambiguous" is counted as not-compliant in policy accuracy; the raw
  Ambiguous rate is reported alongside.
- Soft items (tone/audience) carry best-judgement labels; strict accuracy
  (mechanical items only) is reported separately in the raw JSON.

## 7. Appendix: reproduction

- Probe sets: `probes2.json` (86), `probes3_full.json` (149),
  `policy_probes.json` (10), `policy2.json` (30) in
  `scratchpad/alora-activation-1678/eval_1679/benchmark/` (mellea repo
  worktree for issue #1679).
- Scripts: `bench_probes.py` (labelled probes, `--kind requirement|policy`),
  `bench_scenarios.py` (S1 gating, S2/S2b rewrite loops, S3/S3b RAG gates),
  `bench_edges.py` (adversarial edges), `bench_pipeline.py` (S4 AND-gate,
  S5 iterative RAG), `bench_switchvalue.py` (load/memory/latency).
- Full raw data: `results/wave{1..7}{,a,c,d}/*.json` in the same folder;
  narrative: `REPORT.md` in the same folder.
