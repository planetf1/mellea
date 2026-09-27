# Copyright IBM Corp. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Wave 8b: what does the switch design actually buy?

Compares, per size, a PEFT setup (base model + 4 explicit aLoRA adapters)
against the single switch checkpoint (12 embedded adapters):
  - model load time
  - GPU memory after load
  - adapter registration time (PEFT) vs none (switch)
  - per-call latency on an identical 10-call mixed workload
    (2x uncertainty, 2x requirement-check, 2x answerability,
     2x policy-guardrails, 2x plain generation)
  - explicit set_adapter switching cost (PEFT only)

Usage:
    python bench_switchvalue.py --model ibm-granite/granite-4.1-3b \
        --switch-model ibm-granite/granite-switch-4.1-3b-preview --out out.json
"""

import argparse
import gc
import json
import sys
import time

# Standard
import torch

# First Party
from mellea.backends.huggingface import LocalHFBackend
from mellea.stdlib import functional as mfuncs
from mellea.stdlib.components import Message
from mellea.stdlib.components.intrinsic import core, guardian, rag
from mellea.stdlib.context import ChatContext

# Local
import bench_fixtures as fx

ADAPTERS = ["uncertainty", "requirement-check", "answerability", "policy-guardrails"]

CTX = ChatContext().add(Message("user", "Write one sentence about Cardiff.")).add(
    Message("assistant", "Cardiff is the capital city of Wales.")
)
QCTX = ChatContext().add(Message("assistant", "Hello! How can I help?"))
Q = "What is the square root of 4?"
DOCS_OK = ["The square root of 4 is 2."]
POLICY = "The assistant must not disclose other people's private contact details."
VIO_CTX = ChatContext().add(Message("user", "Who is Jane's contact?")).add(
    Message("assistant", "Jane's brother can be reached at 555-0142.")
)


def mixed_calls(backend):
    """10 identical calls: 2 per capability + 2 plain generations."""
    calls = []

    def rec(name, fn):
        t0 = time.time()
        out = fn()
        calls.append({"call": name, "latency_s": round(time.time() - t0, 3)})

    for i in range(2):
        rec(f"uncertainty{i}", lambda: core.check_certainty(CTX, backend))
        rec(
            f"requirement{i}",
            lambda: core.requirement_check(
                CTX, backend, "The response is written in French."
            ),
        )
        rec(
            f"answerability{i}",
            lambda: rag.check_answerability(Q, DOCS_OK, QCTX, backend),
        )
        rec(f"policy{i}", lambda: guardian.policy_guardrails(VIO_CTX, backend, POLICY))
        rec(
            f"gen{i}",
            lambda: mfuncs.chat(
                "Write one short sentence about the sea.",
                ChatContext().add(Message("user", "hi")),
                backend,
            )[0].content,
        )
    return calls


def measure_peft(model: str) -> dict:
    t0 = time.time()
    torch.cuda.reset_peak_memory_stats()
    backend = LocalHFBackend(model_id=model)
    load_model_s = time.time() - t0

    t0 = time.time()
    fx.add_alora_adapters(backend, names=ADAPTERS)
    register_s = time.time() - t0
    mem_gib = torch.cuda.max_memory_allocated() / 1024**3

    # explicit switching cost: 20 set_adapter round trips
    names = sorted(backend._model.peft_config)
    t0 = time.time()
    for i in range(20):
        backend._model.set_adapter(names[i % len(names)])
    switch_s = (time.time() - t0) / 20

    calls = mixed_calls(backend)
    out = {
        "kind": "peft_alora",
        "load_model_s": round(load_model_s, 2),
        "register_adapters_s": round(register_s, 2),
        "gpu_mem_gib": round(mem_gib, 2),
        "set_adapter_s": round(switch_s, 5),
        "calls": calls,
        "n_adapters_loaded": len(names),
    }
    del backend
    gc.collect()
    torch.cuda.empty_cache()
    return out


def measure_switch(model: str) -> dict:
    t0 = time.time()
    torch.cuda.reset_peak_memory_stats()
    backend = LocalHFBackend(model_id=model, load_embedded_adapters=True)
    load_model_s = time.time() - t0
    mem_gib = torch.cuda.max_memory_allocated() / 1024**3

    calls = mixed_calls(backend)
    out = {
        "kind": "switch_embedded",
        "load_model_s": round(load_model_s, 2),
        "register_adapters_s": 0.0,
        "gpu_mem_gib": round(mem_gib, 2),
        "set_adapter_s": None,
        "calls": calls,
        "n_adapters_loaded": None,  # all embedded
    }
    del backend
    gc.collect()
    torch.cuda.empty_cache()
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--switch-model", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    results = {"host": fx.socket.gethostname()}
    print("=== PEFT arm start ===", flush=True)
    try:
        results["peft"] = measure_peft(args.model)
    except Exception as e:
        results["peft"] = {"error": f"{type(e).__name__}: {str(e)[:200]}"}
    print("=== PEFT arm done ===", flush=True)
    print("=== switch arm start ===", flush=True)
    try:
        results["switch"] = measure_switch(args.switch_model)
    except Exception as e:
        results["switch"] = {"error": f"{type(e).__name__}: {str(e)[:200]}"}
    print("=== switch arm done ===", flush=True)

    fx.write_json(args.out, results)
    return 0


if __name__ == "__main__":
    sys.exit(main())
