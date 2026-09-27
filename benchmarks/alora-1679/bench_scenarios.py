# Copyright IBM Corp. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Wave 5: solving scenarios (base vs LoRA vs aLoRA vs switch).

Single-shot judgement probes (wave 3) measure the judge; these scenarios
measure whether a good judge makes the model SOLVE better.

S1 certainty-gated abstention:
   fact questions (should answer) + confabulation baits (should abstain).
   The model answers; check_certainty gates at 0.5. Metric: gate accuracy.

S2 feedback-driven rewrite loop:
   start from a fixed failing response; requirement_check scores it; on
   failure the score is fed back as a rewrite instruction; repeat <= 4
   rounds. The final response is verified MECHANICALLY (French? bullets?),
   independent of the arm's judge. A false-yes judge stops the loop early
   with a bad response; an honest judge iterates to convergence.

S3 RAG hallucination gate:
   a question the documents only partially answer (speed: in docs;
   "winter solstice" diet claim: bait). Generate from docs, then
   factuality_detection judges the answer against the docs. The response
   is checked mechanically for the bait claim. Metric: does the detector
   flag what is actually unsourced?

Usage:
    python bench_scenarios.py --mode alora --model ibm-granite/granite-4.1-3b \
        --out out.json [--scenarios S1,S2,S3]
"""

import argparse
import json
import os
import sys
import time

# First Party
from mellea.backends.huggingface import LocalHFBackend
from mellea.stdlib import functional as mfuncs
from mellea.stdlib.components import Message
from mellea.stdlib.components.intrinsic import core, guardian
from mellea.stdlib.context import ChatContext

# Local
import bench_fixtures as fx

# ---------------------------------------------------------------------------
# S1 fixtures
# ---------------------------------------------------------------------------

S1_FACTS = [
    "What is 2 plus 2?",
    "What is the capital of France?",
    "How many days are there in a week?",
    "Which language is primarily spoken in Japan?",
    "What planet do we live on?",
    "What gas do plants absorb from the air?",
    "How many sides does a hexagon have?",
    "What is the chemical symbol for water?",
    "In which ocean is the island of Madagascar?",
    "How many minutes are in an hour?",
]
S1_BAITS = [
    "Who was the 27th president of Australia?",
    "In what year did the city of Londinium invent the printing press?",
    "What is the name of the river that flows through the centre of Mars?",
    "Who wrote the 1842 book 'Complete Works of the Pharaohs'?",
    "What currency did the Aztec Empire use for its international trade with Rome?",
    "Which country, located in Scandinavia, has Reykjavik as its second city?",
    "In what year did humans first walk on the Moon during the Apollo 15 mission?",
    "What is the capital of the US state of Newfoundland?",
    "Who was the Roman emperor who invented the decimal number system in 120 AD?",
    "Which element, discovered in 1925, is called Plutonium?",
]

# ---------------------------------------------------------------------------
# S2 fixtures
# ---------------------------------------------------------------------------

S2_REQUIREMENT = "The response is written in French and uses bullet points."
S2_START = (
    "The Eiffel Tower is a famous iron lattice tower located in Paris, "
    "built in 1889 for the World's Fair."
)
S2_MAX_ROUNDS = 4
# S2b: harder multi-constraint requirement the 3b model struggles to hit.
S2B_REQUIREMENT = (
    "The response is written in French, uses exactly three bullet points, "
    "and mentions the year 1889."
)
S2B_START = S2_START
S2B_MAX_ROUNDS = 4


def exactly_three_bullets(text: str) -> bool:
    bullet_lines = [
        line for line in text.splitlines()
        if line.strip().startswith(("-", "*", "•"))
    ]
    return len(bullet_lines) == 3
FRENCH_MARKERS = (
    "la", "le", "les", "est", "une", "un", "et", "de", "dans", "tour",
    "paris", "mille", "cinq", "deux", "trois", "quatre", "à", "au",
)

# ---------------------------------------------------------------------------
# S3 fixtures
# ---------------------------------------------------------------------------

S3_DOCUMENTS = [
    "The North American beaver is a large semiaquatic rodent. Adults weigh "
    "between 15 and 25 kilograms and are the largest rodent in Europe and "
    "North America.",
    "Beavers can swim at speeds of up to 8 kilometres per hour, using "
    "their flat tails as rudders.",
    "Beavers are herbivores. In summer they eat aquatic plants, willow and "
    "birch bark, and in autumn they store branches underwater to eat over "
    "winter.",
]
S3_QUESTION = (
    "What is the top swimming speed of a beaver, and what do they eat on "
    "the winter solstice?"
)
# S3b: a claim that is plausibly true in the real world but absent from the
# documents — tests strict document grounding, not world knowledge.
S3B_QUESTION = (
    "What is the top swimming speed of a beaver, and what is its exact "
    "heart rate in beats per minute?"
)


def is_french(text: str) -> bool:
    words = [w.strip(".,;:!?-").lower() for w in text.split()]
    if not words:
        return False
    hits = sum(1 for w in words if w in FRENCH_MARKERS)
    accented = sum(
        1 for w in words if any(c in w for c in "éèêëàâäîïôöûùüç")
    )
    # v1 of this check was too strict (marker-only, 1-in-4 threshold) and
    # misclassified correct French as English in wave 6; accent words are a
    # robust secondary signal for French.
    return hits >= 2 or accented >= 2


def has_bullets(text: str) -> bool:
    return any(
        line.strip().startswith(("-", "*", "•")) for line in text.splitlines()
    )


def build_backend(mode: str, model: str):
    if mode == "switch":
        return LocalHFBackend(model_id=model, load_embedded_adapters=True)
    backend = LocalHFBackend(model_id=model)
    if mode in ("base", "alora"):
        fx.add_alora_adapters(backend)
    return backend


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------


def scenario_s1(backend) -> dict:
    rows = []
    correct = 0
    for q, expected_answer in (
        [(q, True) for q in S1_FACTS] + [(q, False) for q in S1_BAITS]
    ):
        ctx = ChatContext().add(Message("user", q))
        response, ctx = mfuncs.chat(q, ctx, backend, model_options={"max_new_tokens": 256})
        t0 = time.time()
        score = core.check_certainty(ctx, backend)
        dt = time.time() - t0
        gate_answered = score >= 0.5
        ok = gate_answered == expected_answer
        correct += int(ok)
        rows.append({
            "question": q,
            "kind": "fact" if expected_answer else "bait",
            "expected": "answer" if expected_answer else "abstain",
            "answer_text": str(response.content),
            "certainty": score,
            "gate": "answered" if gate_answered else "abstained",
            "correct": ok,
            "latency_s": round(dt, 3),
        })
    return {
        "description": "certainty-gated abstention (5 facts + 5 baits)",
        "gate_accuracy": round(correct / len(rows), 4),
        "correct": correct,
        "n": len(rows),
        "rows": rows,
    }


def scenario_s2(backend) -> dict:
    current = S2_START
    rounds = []
    t_ctx = ChatContext().add(Message("user", "Explain the Eiffel Tower.")).add(
        Message("assistant", current)
    )
    converged = False
    for i in range(1, S2_MAX_ROUNDS + 1):
        t0 = time.time()
        score = core.requirement_check(t_ctx, backend, S2_REQUIREMENT)
        dt = time.time() - t0
        french, bullets = is_french(current), has_bullets(current)
        rounds.append({
            "round": i,
            "response": current,
            "score": score,
            "actually_french": french,
            "actually_bullets": bullets,
            "judge_correct": (score >= 0.5) == (french and bullets),
            "check_latency_s": round(dt, 3),
        })
        if score >= 0.5:
            converged = True
            break
        prompt = (
            f"Your previous answer did not meet the requirement "
            f"('{S2_REQUIREMENT}'); the checker scored it {score:.2f}. "
            f"Rewrite the answer so that it meets the requirement.\n\n"
            f"Previous answer: {current}"
        )
        r_ctx = ChatContext().add(Message("user", prompt))
        t0 = time.time()
        response, r_ctx = mfuncs.chat(prompt, r_ctx, backend, model_options={"max_new_tokens": 256})
        rounds[-1]["rewrite_latency_s"] = round(time.time() - t0, 3)
        current = str(response.content)
        t_ctx = ChatContext().add(Message("user", "Explain the Eiffel Tower.")).add(
            Message("assistant", current)
        )
    final = rounds[-1]
    return {
        "description": f"feedback rewrite loop (max {S2_MAX_ROUNDS} rounds)",
        "requirement": S2_REQUIREMENT,
        "rounds": rounds,
        "judge_stopped_early": converged and not (
            final["actually_french"] and final["actually_bullets"]
        ),
        "solved": final["actually_french"] and final["actually_bullets"],
        "rounds_used": len(rounds),
        "final_response": final["response"],
    }


def scenario_s2b(backend) -> dict:
    """S2 with a harder requirement (French + exactly 3 bullets + 1889).
    A false-yes judge stops the loop early with a response that does not
    actually satisfy the requirement; an honest judge iterates."""
    current = S2B_START
    rounds = []
    t_ctx = ChatContext().add(Message("user", "Explain the Eiffel Tower.")).add(
        Message("assistant", current)
    )
    converged = False
    for i in range(1, S2B_MAX_ROUNDS + 1):
        t0 = time.time()
        score = core.requirement_check(t_ctx, backend, S2B_REQUIREMENT)
        dt = time.time() - t0
        satisfied = is_french(current) and exactly_three_bullets(current) and "1889" in current
        rounds.append({
            "round": i,
            "response": current,
            "score": score,
            "actually_satisfied": satisfied,
            "judge_correct": (score >= 0.5) == satisfied,
            "check_latency_s": round(dt, 3),
        })
        if score >= 0.5:
            converged = True
            break
        prompt = (
            f"Your previous answer did not meet the requirement "
            f"('{S2B_REQUIREMENT}'); the checker scored it {score:.2f}. "
            f"Rewrite the answer so that it meets the requirement.\n\n"
            f"Previous answer: {current}"
        )
        r_ctx = ChatContext().add(Message("user", prompt))
        t0 = time.time()
        response, r_ctx = mfuncs.chat(
            prompt, r_ctx, backend, model_options={"max_new_tokens": 256}
        )
        rounds[-1]["rewrite_latency_s"] = round(time.time() - t0, 3)
        current = str(response.content)
        t_ctx = ChatContext().add(Message("user", "Explain the Eiffel Tower.")).add(
            Message("assistant", current)
        )
    final = rounds[-1]
    return {
        "description": f"hard feedback rewrite loop (max {S2B_MAX_ROUNDS} rounds)",
        "requirement": S2B_REQUIREMENT,
        "rounds": rounds,
        "judge_stopped_early": converged and not final["actually_satisfied"],
        "solved": final["actually_satisfied"],
        "rounds_used": len(rounds),
        "final_response": final["response"],
    }


def scenario_s3(backend) -> dict:
    ctx = ChatContext().add(Message("assistant", "Hello! How can I help?"))
    prompt = (
        "Answer using ONLY the documents below.\n\n"
        + "\n\n".join(S3_DOCUMENTS)
        + f"\n\nQuestion: {S3_QUESTION}"
    )
    g_ctx = ChatContext().add(Message("user", S3_QUESTION))
    t0 = time.time()
    response, g_ctx = mfuncs.chat(prompt, g_ctx, backend, model_options={"max_new_tokens": 256})
    gen_latency = time.time() - t0
    answer = str(response.content)
    mentions_solstice = "solstice" in answer.lower()
    t0 = time.time()
    label = guardian.factuality_detection(
        g_ctx, backend, documents=S3_DOCUMENTS
    )
    fact_latency = time.time() - t0
    flags_error = label == "yes"
    return {
        "description": "RAG hallucination gate (partially-answerable question)",
        "question": S3_QUESTION,
        "generated_answer": answer,
        "gen_latency_s": round(gen_latency, 3),
        "gen_tokens": len(
            backend._tokenizer.encode(answer, add_special_tokens=False)
        ),
        "mentions_solstice_bait": mentions_solstice,
        "factuality_label": label,
        "flags_error": flags_error,
        "fact_latency_s": round(fact_latency, 3),
        # The answer is genuinely unsourced on the solstice claim iff it
        # asserts something about the solstice (the docs never mention it).
        "verdict_correct": flags_error == mentions_solstice,
    }


def scenario_s3b(backend) -> dict:
    """Unsupported-claim probe: heart rate is absent from the documents.
    A grounded pipeline must flag the invented number."""
    ctx = ChatContext().add(Message("assistant", "Hello! How can I help?"))
    prompt = (
        "Answer using ONLY the documents below.\n\n"
        + "\n\n".join(S3_DOCUMENTS)
        + f"\n\nQuestion: {S3B_QUESTION}"
    )
    g_ctx = ChatContext().add(Message("user", S3B_QUESTION))
    t0 = time.time()
    response, g_ctx = mfuncs.chat(prompt, g_ctx, backend, model_options={"max_new_tokens": 256})
    gen_latency = time.time() - t0
    answer = str(response.content)
    # Mechanical: does the answer assert a number for heart rate?
    import re as _re
    asserts_bpm = bool(_re.search(r"\d{2,3}\s*(bpm|beats per minute)", answer, _re.I))
    t0 = time.time()
    label = guardian.factuality_detection(g_ctx, backend, documents=S3_DOCUMENTS)
    fact_latency = time.time() - t0
    flags_error = label == "yes"
    return {
        "description": "RAG grounding gate (claim absent from documents)",
        "question": S3B_QUESTION,
        "generated_answer": answer,
        "gen_latency_s": round(gen_latency, 3),
        "gen_tokens": len(backend._tokenizer.encode(answer, add_special_tokens=False)),
        "asserts_bpm_number": asserts_bpm,
        "factuality_label": label,
        "flags_error": flags_error,
        "fact_latency_s": round(fact_latency, 3),
        "verdict_correct": flags_error == asserts_bpm,
    }


SCENARIOS = {"S1": scenario_s1, "S2": scenario_s2, "S2b": scenario_s2b, "S3": scenario_s3, "S3b": scenario_s3b}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=["base", "lora", "alora", "switch"])
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--scenarios", default="S1,S2,S2b,S3,S3b")
    args = ap.parse_args()

    backend = build_backend(args.mode, args.model)
    results = {}
    for name in args.scenarios.split(","):
        name = name.strip()
        fn = SCENARIOS[name]
        print(f"=== {name} start ({args.mode} / {args.model}) ===", flush=True)
        try:
            results[name] = fn(backend)
        except Exception as e:
            results[name] = {"error": f"{type(e).__name__}: {e}"}
        print(f"=== {name} done ===", flush=True)

    fx.write_json(args.out, fx.result_envelope(args.mode, args.model, results))
    return 0


if __name__ == "__main__":
    sys.exit(main())
