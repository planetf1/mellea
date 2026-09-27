# Copyright IBM Corp. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Wave 9b: growing-session check.

Five consecutive requirement-check calls on the SAME growing context
(user/assistant exchanges appended each round). Verifies aLoRA offset
computation stays correct as the conversation (and its KV) grows within
one session, and records per-round latency.

Usage:
    python bench_session.py --mode alora --model ibm-granite/granite-4.1-3b \
        --out out.json
"""

import argparse
import sys
import time

# First Party
from mellea.backends.huggingface import LocalHFBackend
from mellea.stdlib import functional as mfuncs
from mellea.stdlib.components import Message
from mellea.stdlib.components.intrinsic import core
from mellea.stdlib.context import ChatContext

# Local
import bench_fixtures as fx

EXCHANGES = [
    ("What is the weather like in Cardiff today?",
     "It is a mild and sunny day with light winds from the west."),
    ("How long is the riverside walk?",
     "The full loop takes about forty minutes at a relaxed pace."),
    ("Is there a cafe at the end of the walk?",
     "There is a small cafe near the bridge that opens at nine in the morning."),
    ("Do they take card payments?",
     "They accept cards and contactless payments, but cash is safer on quiet days."),
    ("What should I bring for the walk?",
     "A light jacket, some water, and comfortable shoes are all you need."),
]


def run_session(backend) -> dict:
    ctx = ChatContext()
    tok = backend._tokenizer
    rounds = []
    for i, (u, a) in enumerate(EXCHANGES):
        ctx = ctx.add(Message("user", u)).add(Message("assistant", a))
        ntok = sum(
            len(tok.encode(m.content, add_special_tokens=False))
            for m in ctx.messages
        ) if hasattr(ctx, "messages") else None
        # check 1: last exchange (fresh) — "in English" must be True
        t0 = time.time()
        s1 = core.requirement_check(ctx, backend, "The response is written in English.")
        dt1 = time.time() - t0
        # check 2: a requirement the response violates — must be low
        s2ctx = ChatContext().add(Message("user", u)).add(
            Message("assistant", a)
        )
        t0 = time.time()
        s2 = core.requirement_check(s2ctx, backend, "The response is written in French.")
        dt2 = time.time() - t0
        ok1 = s1 >= 0.5
        ok2 = s2 < 0.5
        rounds.append({
            "round": i + 1,
            "context_tokens_approx": ntok,
            "english_score": s1,
            "english_correct": ok1,
            "french_score": s2,
            "french_correct": ok2,
            "latency_s": [round(dt1, 3), round(dt2, 3)],
        })
        print(
            f"round {i + 1}: en={s1:.3f}({'ok' if ok1 else 'WRONG'}) "
            f"fr={s2:.3f}({'ok' if ok2 else 'WRONG'})",
            flush=True,
        )
    return {
        "description": "5-round growing session, 2 requirement-checks per round",
        "rounds": rounds,
        "all_correct": all(r["english_correct"] and r["french_correct"] for r in rounds),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=["base", "lora", "alora", "switch"])
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    if args.mode == "switch":
        backend = LocalHFBackend(model_id=args.model, load_embedded_adapters=True)
    else:
        backend = LocalHFBackend(model_id=args.model)
        if args.mode in ("base", "alora"):
            fx.add_alora_adapters(backend)

    result = run_session(backend)
    fx.write_json(args.out, fx.result_envelope(args.mode, args.model, result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
