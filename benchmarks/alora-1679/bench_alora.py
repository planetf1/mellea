# Copyright IBM Corp. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""aLoRA benchmark driver (arms: before / middle / after).

Runs the fixed L0-L4 examples against one model size with the aLoRA
adapters loaded explicitly, and writes a JSON result file.

Usage:
    python bench_alora.py --arm before --model ibm-granite/granite-4.1-3b \
        --out results/3b_before.json [--levels L0,L1,L2,L3,L4]
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


def level_l0_lora_sanity(backend) -> dict:
    """High-level requirement_check with NO explicit adapter: auto-resolution
    selects the LoRA (aLoRA is never auto-selected pre-#1654). Scores must be
    identical across arms: the #1685 fix must not change LoRA behaviour."""
    return {
        "description": "LoRA auto-resolution sanity (arm-invariant expected)",
        "french": fx.call_stats(
            backend, None,
            lambda: core.requirement_check(
                fx.L2_CTX, backend, fx.L2_REQUIREMENT_FRENCH
            ), None,
        ),
        "bullets": fx.call_stats(
            backend, None,
            lambda: core.requirement_check(
                fx.L2_CTX, backend, fx.L2_REQUIREMENT_BULLETS
            ), None,
        ),
    }


def level_l1_certainty(backend) -> dict:
    """Single adapter, single call: certainty on a confident vs a hedged answer.
    Each probe runs 3x for latency distribution (scores are deterministic)."""
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
    """Two aLoRA adapters on one model, one response: requirement-check in
    both failure modes plus certainty on the same exchange. Each probe 3x."""
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
    """Multi-step RAG chain: answerability -> query_rewrite -> grounded
    generation -> requirement-check on the generated answer."""
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
    """Requirement-driven retry: the aLoRA score controls the flow. Loop
    until requirement_check passes or attempts are exhausted."""
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
    """Wave 2: a question the documents CANNOT answer. Working adapter:
    "unanswerable"; base model: tends to answer anyway."""
    ctx = fx.ChatContext().add(fx.Message("assistant", "Hello! How can I help?"))
    return fx.call_stats(
        backend, None,
        lambda: rag.check_answerability(fx.L3B_QUESTION, fx.L3_DOCUMENTS, ctx, backend),
        None,
    )


def level_l4b_false_pass(backend) -> dict:
    """Wave 2: single-requirement retry loop. The prompt asks for ONE
    SENTENCE, so the model never produces bullets; a working adapter scores
    it low and retries, while the broken path (base model) scores prose as
    bulleted (~0.99) and false-passes on attempt 1."""
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
    """Wave 2: guardian policy-guardrails aLoRA on a violating vs a
    compliant turn (Yes = compliant)."""
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
    "L0": level_l0_lora_sanity,
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
    ap.add_argument("--arm", required=True, choices=["before", "middle", "after"])
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--levels", default="L0,L1,L2,L3,L3b,L4,L4b,L5")
    args = ap.parse_args()

    backend = LocalHFBackend(model_id=args.model)

    results: dict = {"adapters_loaded": []}
    # L0 must run BEFORE the explicit aLoRA adapters are registered: it is the
    # LoRA auto-resolution sanity check (arm-invariant), and registering the
    # aLoRA first would let resolution pick it up and mask the LoRA path.
    if "L0" in args.levels:
        print(f"=== L0 start ({args.arm} / {args.model}) ===", flush=True)
        try:
            results["L0"] = fx.timed("L0", lambda: level_l0_lora_sanity(backend))
        except Exception as e:
            results["L0"] = {"error": f"{type(e).__name__}: {e}"}
        print(f"=== L0 done ===", flush=True)

    fx.add_alora_adapters(backend)
    results["adapters_loaded"] = sorted(backend._model.peft_config)

    for name in args.levels.split(","):
        name = name.strip()
        if name == "L0":
            continue
        fn = LEVELS[name]
        print(f"=== {name} start ({args.arm} / {args.model}) ===", flush=True)
        try:
            results[name] = fx.timed(name, lambda fn=fn: fn(backend))
        except Exception as e:  # a single malformed model output must not
            # kill the whole run; record and continue
            results[name] = {"error": f"{type(e).__name__}: {e}"}
        print(f"=== {name} done ===", flush=True)

    fx.write_json(args.out, fx.result_envelope(args.arm, args.model, results))
    return 0


if __name__ == "__main__":
    sys.exit(main())
