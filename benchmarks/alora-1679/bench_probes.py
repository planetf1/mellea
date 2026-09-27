# Copyright IBM Corp. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Wave 3: labeled-probe accuracy eval.

Scores ~24 mechanical requirement probes (known ground truth: language,
bullets, word counts, negation traps, mixed/compound constraints) with each
judge type and reports verdict accuracy. This tests whether the adapters
make small models more accurate, and how base-model judgements compare.

Modes (the run script pairs each mode with the right code arm / model):
  base   -- explicit aLoRA loaded on PRE-FIX code: the adapter never
            activates, so the base model answers the io.yaml instruction.
            (This is what users were getting before #1685.)
  lora   -- no explicit adapter; intrinsic resolution selects the LoRA.
  alora  -- explicit aLoRA on FIXED code: the adapter is actually applied.
  switch -- granite-switch model, embedded adapter via chat template.

Usage:
    python bench_probes.py --mode alora --model ibm-granite/granite-4.1-3b \
        --out results/wave3/3b_alora.json
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
from mellea.stdlib.components.intrinsic import guardian
from mellea.stdlib.context import ChatContext

# Local
import bench_fixtures as fx

USER_PROMPT = "Write a response."


def build_backend(mode: str, model: str):
    if mode == "switch":
        return LocalHFBackend(model_id=model, load_embedded_adapters=True)
    backend = LocalHFBackend(model_id=model)
    if mode in ("base", "alora"):
        fx.add_alora_adapters(backend)
    return backend


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=["base", "lora", "alora", "switch"])
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--kind", default="requirement", choices=["requirement", "policy"])
    ap.add_argument("--probes", default=None)
    args = ap.parse_args()

    probes_file = args.probes or os.path.join(
        os.path.dirname(__file__),
        "policy_probes.json" if args.kind == "policy" else "probes.json",
    )
    with open(probes_file, encoding="utf-8") as f:
        spec = json.load(f)
    if "policies" in spec:
        # multi-policy format: list of {policy, probes}
        probe_blocks = [(b["policy"], b["probes"]) for b in spec["policies"]]
    elif args.kind == "policy":
        probe_blocks = [(spec.get("policy"), spec["probes"])]
    else:
        probe_blocks = [(None, spec["probes"])]

    backend = build_backend(args.mode, args.model)
    all_results = []
    correct = 0
    n_all = 0
    ambiguous = 0
    t0 = time.time()
    for policy_text, probes in probe_blocks:
        for p in probes:
            ctx = ChatContext().add(Message("user", USER_PROMPT)).add(
                Message("assistant", p["response"])
            )
            t1 = time.time()
            if args.kind == "policy":
                label = guardian.policy_guardrails(ctx, backend, policy_text)
                verdict = label == "Yes"
                if label == "Ambiguous":
                    ambiguous += 1
            else:
                score = core.requirement_check(ctx, backend, p["requirement"])
                verdict = score >= 0.5
                label = f"score={score:.4f}"
            dt = time.time() - t1
            expected = p["compliant"] if args.kind == "policy" else p["met"]
            ok = verdict == expected
            correct += int(ok)
            n_all += 1
            row = {
                "id": p["id"],
                "label": label,
                "verdict": verdict,
                "expected": expected,
                "correct": ok,
                "latency_s": round(dt, 3),
            }
            if policy_text is not None:
                row["policy"] = policy_text
            if p.get("soft"):
                row["soft"] = True
            all_results.append(row)
            print(f"{p['id']}: {label} expected={expected} {'OK' if ok else 'MISS'}", flush=True)

    strict_rows = [r for r in all_results if not r.get("soft")]
    payload = {
        "kind": args.kind,
        "mode": args.mode,
        "model": args.model,
        "host": fx.socket.gethostname(),
        "n_probes": n_all,
        "correct": correct,
        "accuracy": round(correct / n_all, 4) if n_all else None,
        "n_strict": len(strict_rows),
        "strict_correct": sum(1 for r in strict_rows if r["correct"]),
        "strict_accuracy": (
            round(sum(1 for r in strict_rows if r["correct"]) / len(strict_rows), 4)
            if strict_rows else None
        ),
        "ambiguous": ambiguous,
        "total_latency_s": round(time.time() - t0, 2),
        "probes": all_results,
    }
    fx.write_json(args.out, payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
