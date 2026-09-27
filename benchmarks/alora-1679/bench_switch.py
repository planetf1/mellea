# Copyright IBM Corp. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Granite Switch benchmark driver (bonus comparison arm).

Runs the same L1-L4 examples against the pre-composed granite-switch
checkpoints, where the adapter functions are embedded in the model weights
and activated through the chat template (no PEFT loading, no aLoRA offset
mechanism). This is the "other way to get adapter functions" baseline:
it sidesteps both the Mellea activation bug and the io.yaml tokenization
mismatch by construction.

Usage:
    python bench_switch.py --model ibm-granite/granite-switch-4.1-3b-preview \
        --out results/switch_3b.json
"""

import argparse
import sys
import time

# First Party
from mellea.backends.huggingface import LocalHFBackend
from mellea.stdlib import functional as mfuncs
from mellea.stdlib.components.intrinsic import core, rag

# Local
import bench_fixtures as fx


def level_l1_certainty(backend) -> dict:
    p_certain = fx.call_stats(
        backend, None, lambda: core.check_certainty(fx.L1_CERTAIN_CONTEXT, backend), None
    )
    p_hedged = fx.call_stats(
        backend, None, lambda: core.check_certainty(fx.L1_HEDGED_CONTEXT, backend), None
    )
    certain_lats = [p_certain["latency_s"]]
    hedged_lats = [p_hedged["latency_s"]]
    for _ in range(2):
        t0 = time.time()
        core.check_certainty(fx.L1_CERTAIN_CONTEXT, backend)
        certain_lats.append(round(time.time() - t0, 3))
        t0 = time.time()
        core.check_certainty(fx.L1_HEDGED_CONTEXT, backend)
        hedged_lats.append(round(time.time() - t0, 3))
    return {
        "description": "check_certainty on confident vs hedged context (3x)",
        "certain": {**p_certain, "latencies_s": certain_lats},
        "hedged": {**p_hedged, "latencies_s": hedged_lats},
    }


def level_l2_dual(backend) -> dict:
    p_fr = fx.call_stats(
        backend, None,
        lambda: core.requirement_check(fx.L2_CTX, backend, fx.L2_REQUIREMENT_FRENCH), None,
    )
    p_bu = fx.call_stats(
        backend, None,
        lambda: core.requirement_check(fx.L2_CTX, backend, fx.L2_REQUIREMENT_BULLETS), None,
    )
    p_ce = fx.call_stats(
        backend, None, lambda: core.check_certainty(fx.L2_CTX, backend), None
    )
    fr_lats, bu_lats, ce_lats = [
        p_fr["latency_s"]
    ], [p_bu["latency_s"]], [p_ce["latency_s"]]
    for _ in range(2):
        t0 = time.time()
        core.requirement_check(fx.L2_CTX, backend, fx.L2_REQUIREMENT_FRENCH)
        fr_lats.append(round(time.time() - t0, 3))
        t0 = time.time()
        core.requirement_check(fx.L2_CTX, backend, fx.L2_REQUIREMENT_BULLETS)
        bu_lats.append(round(time.time() - t0, 3))
        t0 = time.time()
        core.check_certainty(fx.L2_CTX, backend)
        ce_lats.append(round(time.time() - t0, 3))
    return {
        "description": "requirement-check (french, bullets) + certainty (3x)",
        "french": {**p_fr, "latencies_s": fr_lats},
        "bullets": {**p_bu, "latencies_s": bu_lats},
        "certainty": {**p_ce, "latencies_s": ce_lats},
    }


def level_l3_rag_chain(backend) -> dict:
    ctx = fx.ChatContext().add(fx.Message("assistant", "Hello! How can I help?"))
    answerability = fx.call_stats(
        backend, None,
        lambda: rag.check_answerability(fx.L3_QUESTION, fx.L3_DOCUMENTS, ctx, backend), None,
    )
    rewritten = fx.call_stats(
        backend, fx.L3_QUESTION,
        lambda: rag.rewrite_question(fx.L3_QUESTION, ctx, backend), None,
    )
    gen_ctx = fx.ChatContext().add(fx.Message("user", fx.L3_QUESTION))
    prompt = (
        "Answer using ONLY the documents below.\n\n"
        + "\n\n".join(fx.L3_DOCUMENTS)
        + f"\n\nQuestion: {fx.L3_QUESTION}"
    )
    t0 = time.time()
    response, gen_ctx = mfuncs.chat(prompt, gen_ctx, backend)
    gen_latency = time.time() - t0
    answer_text = str(response.content)
    gen_stats = {
        "latency_s": round(gen_latency, 3),
        "prompt_tokens": len(
            backend._tokenizer.encode(prompt, add_special_tokens=False)
        ),
        "completion_tokens": len(
            backend._tokenizer.encode(answer_text, add_special_tokens=False)
        ),
    }
    check_ctx = fx.ChatContext().add(fx.Message("user", fx.L3_QUESTION)).add(
        fx.Message("assistant", answer_text)
    )
    grounded = fx.call_stats(
        backend, None,
        lambda: core.requirement_check(check_ctx, backend, fx.L3_REQUIREMENT_GROUNDED),
        answer_text,
    )
    return {
        "description": "answerability -> rewrite -> generate -> requirement-check",
        "answerability": answerability,
        "rewritten_query": rewritten,
        "generated": gen_stats,
        "generated_answer": answer_text,
        "grounded_check": grounded,
    }


def level_l4_retry_loop(backend) -> dict:
    attempts = []
    ctx = fx.ChatContext().add(fx.Message("user", fx.L4_PROMPT))
    passed = False
    for i in range(1, fx.L4_MAX_ATTEMPTS + 1):
        t0 = time.time()
        response, ctx = mfuncs.chat(fx.L4_PROMPT, ctx, backend)
        gen_latency = time.time() - t0
        text = str(response.content)
        check = fx.call_stats(
            backend, None,
            lambda: core.requirement_check(ctx, backend, fx.L4_REQUIREMENT), text,
        )
        score = check["value"]
        attempts.append({
            "attempt": i,
            "response": text,
            "score": score,
            "gen_latency_s": round(gen_latency, 3),
            "gen_tokens": len(
                backend._tokenizer.encode(text, add_special_tokens=False)
            ),
            "check_latency_s": check["latency_s"],
        })
        if score >= 0.5:
            passed = True
            break
    return {
        "description": f"retry until requirement met (max {fx.L4_MAX_ATTEMPTS})",
        "requirement": fx.L4_REQUIREMENT,
        "attempts": attempts,
        "passed": passed,
    }


def level_l3b_negative_answerability(backend) -> dict:
    ctx = fx.ChatContext().add(fx.Message("assistant", "Hello! How can I help?"))
    return fx.call_stats(
        backend, None,
        lambda: rag.check_answerability(fx.L3B_QUESTION, fx.L3_DOCUMENTS, ctx, backend),
        None,
    )


def level_l4b_false_pass(backend) -> dict:
    attempts = []
    ctx = fx.ChatContext().add(fx.Message("user", fx.L4B_PROMPT))
    passed = False
    for i in range(1, fx.L4_MAX_ATTEMPTS + 1):
        t0 = time.time()
        response, ctx = mfuncs.chat(fx.L4B_PROMPT, ctx, backend)
        gen_latency = time.time() - t0
        text = str(response.content)
        check = fx.call_stats(
            backend, None,
            lambda: core.requirement_check(ctx, backend, fx.L4B_REQUIREMENT), text,
        )
        score = check["value"]
        attempts.append({
            "attempt": i,
            "response": text,
            "score": score,
            "gen_latency_s": round(gen_latency, 3),
            "gen_tokens": len(
                backend._tokenizer.encode(text, add_special_tokens=False)
            ),
            "check_latency_s": check["latency_s"],
        })
        if score >= 0.5:
            passed = True
            break
    return {
        "description": "retry loop, single requirement (false-pass probe)",
        "requirement": fx.L4B_REQUIREMENT,
        "attempts": attempts,
        "passed": passed,
    }


def level_l5_guardian(backend) -> dict:
    from mellea.stdlib.components.intrinsic import guardian

    return {
        "description": "policy_guardrails on violating vs compliant turn",
        "violating": fx.call_stats(
            backend, None,
            lambda: guardian.policy_guardrails(
                fx.L5_VIOLATING_CTX, backend, fx.L5_POLICY
            ), None,
        ),
        "compliant": fx.call_stats(
            backend, None,
            lambda: guardian.policy_guardrails(
                fx.L5_COMPLIANT_CTX, backend, fx.L5_POLICY
            ), None,
        ),
    }


LEVELS = {
    "L1": level_l1_certainty,
    "L2": level_l2_dual,
    "L3": level_l3_rag_chain,
    "L3b": level_l3b_negative_answerability,
    "L4": level_l4_retry_loop,
    "L4b": level_l4b_false_pass,
    "L5": level_l5_guardian,
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--levels", default="L1,L2,L3,L3b,L4,L4b,L5")
    args = ap.parse_args()

    # load_embedded_adapters=True registers the switch model's built-in
    # adapter functions (embedded via chat-template control tokens).
    backend = LocalHFBackend(model_id=args.model, load_embedded_adapters=True)

    results: dict = {"switch": True}
    for name in args.levels.split(","):
        name = name.strip()
        fn = LEVELS[name]
        print(f"=== {name} start (switch / {args.model}) ===", flush=True)
        try:
            results[name] = fx.timed(name, lambda fn=fn: fn(backend))
        except Exception as e:  # see bench_alora.py
            results[name] = {"error": f"{type(e).__name__}: {e}"}
        print(f"=== {name} done ===", flush=True)

    fx.write_json(args.out, fx.result_envelope("switch", args.model, results))
    return 0


if __name__ == "__main__":
    sys.exit(main())
