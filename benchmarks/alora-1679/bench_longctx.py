# Copyright IBM Corp. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Wave 7a: long-context behaviour of aLoRA activation.

aLoRA applies from the invocation sequence to the end of the input. In the
intrinsic flow the invocation sequence sits at the END of the prompt (the
io.yaml instruction is appended), so most of a long context is processed by
the base weights and only the tail by the adapter. These runs check:

1. Does the adapter still activate and judge correctly when the probe
   exchange is buried after 2k / 8k / 32k tokens of filler conversation?
2. How does per-call latency scale with context length, per arm?
3. Edge: what happens when the literal invocation text ("<requirements>")
   appears in the FILLER (mid-context) as well as in the appended
   instruction? PEFT anchors offsets at the FIRST occurrence.

Usage:
    python bench_longctx.py --mode alora --model ibm-granite/granite-4.1-3b \
        --out out.json
"""

import argparse
import json
import os
import sys
import time

# First Party
from mellea.backends.huggingface import LocalHFBackend
from mellea.stdlib.components import Message
from mellea.stdlib.components.intrinsic import core
from mellea.stdlib.context import ChatContext

# Local
import bench_fixtures as fx

FILLER_SENTENCE = (
    "The quarterly review covered the migration of the billing pipeline to "
    "the new service mesh, the results of the spring hiring cycle across the "
    "platform team, and the upcoming calendar for the infrastructure budget "
    "discussion. Several action items were assigned to the reliability group "
    "before the next checkpoint meeting at the end of the month."
)


def build_context(backend, target_tokens: int, with_invocation_in_filler: bool) -> ChatContext:
    tok = backend._tokenizer
    ctx = ChatContext()
    current = 0
    i = 0
    while current < target_tokens:
        text = " ".join([FILLER_SENTENCE] * 4)
        if with_invocation_in_filler and i == 2:
            text += " Earlier we discussed the <requirements> format at length."
        role = "user" if i % 2 == 0 else "assistant"
        ctx = ctx.add(Message(role, text))
        current += len(tok.encode(text, add_special_tokens=False))
        i += 1
    return ctx, current


PROBES = [
    ("fr_not", "Write one sentence about Cardiff.",
     "Cardiff is the capital city of Wales.",
     "The response is written in French.", False),
    ("certain", "What is the square root of 16?",
     "The square root of 16 is 4.", None, True),
]


def run_probe(backend, ctx, probe):
    pid, prompt, response, requirement, _ = probe
    full = ctx.add(Message("user", prompt)).add(Message("assistant", response))
    t0 = time.time()
    if requirement is not None:
        score = core.requirement_check(full, backend, requirement)
    else:
        score = core.check_certainty(full, backend)
    dt = time.time() - t0
    verdict = score >= 0.5
    expected = True if (pid == "fr_not" and False) or (pid == "certain" and True) else False
    # fr_not: requirement NOT met -> expect False. certain: expect True.
    expected = (pid == "certain")
    return {
        "probe": pid,
        "score": score,
        "verdict": verdict,
        "expected": expected,
        "correct": verdict == expected,
        "latency_s": round(dt, 3),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=["base", "lora", "alora", "switch"])
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--lengths", default="2048,8192,32768")
    args = ap.parse_args()

    if args.mode == "switch":
        backend = LocalHFBackend(model_id=args.model, load_embedded_adapters=True)
    else:
        backend = LocalHFBackend(model_id=args.model)
        if args.mode in ("base", "alora"):
            fx.add_alora_adapters(backend)

    results = {"context_lengths": []}
    for length in args.lengths.split(","):
        length = int(length)
        for filler_invocation in (False, True):
            ctx, actual = build_context(
                backend, length, with_invocation_in_filler=filler_invocation
            )
            cell = {
                "target_tokens": length,
                "actual_filler_tokens": actual,
                "invocation_in_filler": filler_invocation,
                "probes": [],
            }
            for probe in PROBES:
                try:
                    cell["probes"].append(run_probe(backend, ctx, probe))
                except Exception as e:
                    cell["probes"].append({"probe": probe[0], "error": f"{type(e).__name__}: {e}"})
                print(
                    f"len={actual} invfill={filler_invocation} {probe[0]} done",
                    flush=True,
                )
            results["context_lengths"].append(cell)

    fx.write_json(args.out, fx.result_envelope(args.mode, args.model, results))
    return 0


if __name__ == "__main__":
    sys.exit(main())
