# Copyright IBM Corp. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Wave 4: sampling-stability study (local; 3b).

Questions:
1. Under non-deterministic sampling (temperature/top_p), do intrinsic
   verdicts flip draw-to-draw, and is that worse with the base model
   (broken path) than with the activated aLoRA?
2. Does sampling interact with aLoRA activation at all (offsets are
   computed from input tokens; generation-time sampling should not affect
   them, but verify empirically)?

Judges: alora (explicit aLoRA on fixed code) vs base (same model, adapters
disabled at the generate level via set_adapter([]) around the call).

Usage:
    python bench_sampling.py --model ibm-granite/granite-4.1-3b \
        --out /tmp/sampling_3b.json [--n 5]
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

USER_PROMPT = "Write a response."

PROBES = [
    ("fr_not", "Cardiff is the capital city of Wales.",
     "The response is written in French.", False),
    ("bullets_not", "The sky is blue and the sea is salt.",
     "The response uses bullet points.", False),
    ("neg_not", "Paris is famous for the Eiffel Tower.",
     "The response must not mention Paris.", False),
    ("mixed_half_bullets", "- Cardiff is the capital city of Wales.",
     "The response uses bullet points and is written in French.", False),
]

SETTINGS = [
    {"temperature": 0.0},
    {"temperature": 0.3},
    {"temperature": 0.7},
    {"temperature": 1.0},
    {"temperature": 0.7, "top_p": 0.9},
]


def check(backend, ctx, requirement, model_options, qualified):
    if qualified is None:
        return core.requirement_check(ctx, backend, requirement,
                                      model_options=model_options)
    orig = backend._model.generate

    def off_gen(*a, **kw):
        backend._model.set_adapter([])
        try:
            return orig(*a, **kw)
        finally:
            backend._model.set_adapter(qualified)

    backend._model.generate = off_gen
    try:
        return core.requirement_check(ctx, backend, requirement,
                                      model_options=model_options)
    finally:
        backend._model.generate = orig


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--n", type=int, default=5)
    args = ap.parse_args()

    backend = LocalHFBackend(model_id=args.model)
    fx.add_alora_adapters(backend)
    qualified = next(
        k for k in backend._model.peft_config if k.startswith("requirement-check")
    )

    ctxs = {
        pid: ChatContext().add(Message("user", USER_PROMPT)).add(
            Message("assistant", resp)
        )
        for pid, resp, _req, _met in PROBES
    }

    results = {}
    t0 = time.time()
    for judge, qual in (("alora", None), ("base", qualified)):
        for setting in SETTINGS:
            key = f"{judge}_t{setting.get('temperature')}p{setting.get('top_p', 1.0)}"
            cell = {}
            for pid, _resp, req, met in PROBES:
                scores = [
                    check(backend, ctxs[pid], req, setting, qual)
                    for _ in range(args.n)
                ]
                verdicts = [s >= 0.5 for s in scores]
                flips = sum(1 for v in verdicts[1:] if v != verdicts[0])
                cell[pid] = {
                    "scores": [round(s, 4) for s in scores],
                    "met": met,
                    "verdicts": verdicts,
                    "flips": flips,
                    "all_correct": all(v == met for v in verdicts),
                }
            results[key] = cell
            print(f"{key}: done", flush=True)

    payload = {
        "model": args.model,
        "n": args.n,
        "host": fx.socket.gethostname(),
        "total_s": round(time.time() - t0, 1),
        "results": results,
    }
    fx.write_json(args.out, payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
