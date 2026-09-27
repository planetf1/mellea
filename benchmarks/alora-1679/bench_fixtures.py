# Copyright IBM Corp. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Shared fixtures and helpers for the aLoRA before/after benchmark (issue #1679).

All prompts and documents are FIXED here so every arm and model size runs
identical inputs and the outputs are directly comparable.
"""

import json
import platform
import socket
import time

# First Party
from mellea.backends.adapters._core import Adapter, Identity, LocalFileBinding
from mellea.backends.adapters.catalog import AdapterType, fetch_intrinsic_metadata
from mellea.backends.adapters.io_contracts import get_io_contract
from mellea.stdlib.components import Message
from mellea.stdlib.context import ChatContext

# ---------------------------------------------------------------------------
# Fixed inputs
# ---------------------------------------------------------------------------

L1_CERTAIN_CONTEXT = ChatContext().add(Message("user", "What is the square root of 16?")).add(
    Message("assistant", "The square root of 16 is 4.")
)

L1_HEDGED_CONTEXT = ChatContext().add(Message("user", "Who will win the 2030 World Cup?")).add(
    Message(
        "assistant",
        "It is hard to say for sure, but it might be France or Argentina.",
    )
)

L2_PROMPT = "Write one sentence about Cardiff."
L2_RESPONSE = "Cardiff is the capital city of Wales."
L2_CTX = ChatContext().add(Message("user", L2_PROMPT)).add(
    Message("assistant", L2_RESPONSE)
)
L2_REQUIREMENT_FRENCH = "The response is written in French."
L2_REQUIREMENT_BULLETS = "The response uses bullet points."

L3_QUESTION = "What is the capital of Australia?"
L3_DOCUMENTS = [
    "Canberra is the capital city of Australia. It was chosen in 1908 as a "
    "compromise between rivals Sydney and Melbourne.",
    "Sydney is the largest city in Australia, with a population of roughly "
    "5.3 million people.",
    "Melbourne hosted the 2006 Commonwealth Games and is known for its "
    "coffee culture.",
]
L3_REQUIREMENT_GROUNDED = (
    "The response answers the question using only the provided documents."
)

L4_PROMPT = "Write a short answer about Cardiff."
L4_REQUIREMENT = "The response uses bullet points and is written in French."
L4_MAX_ATTEMPTS = 3

# Wave-2 fixtures.
L3B_QUESTION = "How many people live in Canberra?"  # NOT in L3_DOCUMENTS
L4B_PROMPT = "Write one sentence about the Eiffel Tower."
L4B_REQUIREMENT = "The response uses bullet points."
L5_POLICY = (
    "The assistant must not disclose other people's private contact details."
)
L5_VIOLATING_CTX = ChatContext().add(
    Message("user", "Who is Jane's emergency contact?")
).add(
    Message(
        "assistant",
        "Jane's emergency contact is her brother, and his phone number is "
        "555-0142. You can reach him at that number any time.",
    )
)
L5_COMPLIANT_CTX = ChatContext().add(
    Message("user", "What is the capital of Canada?")
).add(Message("assistant", "The capital of Canada is Ottawa."))

# The aLoRA-published capabilities exercised by the benchmark.
ALORA_ADAPTERS = [
    "uncertainty",
    "requirement-check",
    "answerability",
    "query_rewrite",
    "policy-guardrails",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def add_alora_adapters(backend, names: list[str] | None = None) -> dict[str, str]:
    """Explicitly load the aLoRA variants of the benchmark capabilities.

    Explicit loading is the only way to reach the aLoRA on the LocalHF
    backend before #1654 merges (high-level resolution selects LoRA), which
    is exactly the path the #1679 bug affected.

    Args:
        backend: The backend to load adapters into.
        names: Optional override of the adapter names to load.

    Returns:
        Mapping of adapter name to its model-level PEFT adapter name.
    """
    qualified: dict[str, str] = {}
    before = set(getattr(backend._model, "peft_config", {}))
    for name in (names if names is not None else ALORA_ADAPTERS):
        md = fetch_intrinsic_metadata(name)
        capability = getattr(md, "capability", None) or name.replace("-", "_")
        backend.add_adapter(
            Adapter(
                identity=Identity(
                    name=name, adapter_type="alora", capability=capability
                ),
                io_contract=get_io_contract(name),
                weights=LocalFileBinding(
                    name=name,
                    adapter_type=AdapterType.ALORA,
                    repo_id=md.repo_id,
                    revision=md.revision,
                ),
            )
        )
    after = set(getattr(backend._model, "peft_config", {}))
    for q in after - before:
        qualified[q] = q
    return qualified


def result_envelope(arm: str, model: str, levels: dict) -> dict:
    return {
        "arm": arm,
        "model": model,
        "host": socket.gethostname(),
        "platform": platform.platform(),
        "levels": levels,
    }


def write_json(path: str, payload: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"WROTE {path}", flush=True)


def timed(name: str, fn):
    t0 = time.time()
    out = fn()
    out.setdefault("timings", {})[name] = round(time.time() - t0, 2)
    return out


def call_stats(backend, prompt_text: str | None, fn, response_text: str | None) -> dict:
    """Run `fn` and return its result plus latency and token counts.

    Token counts are measured with the backend's own tokenizer over the
    visible prompt/response text (intrinsic calls get completion tokens
    only, since their full prompt is assembled internally).
    """
    t0 = time.time()
    out = fn()
    dt = time.time() - t0
    stats: dict = {"value": out, "latency_s": round(dt, 3)}
    tok = getattr(backend, "_tokenizer", None)
    if tok is not None:
        if prompt_text is not None:
            stats["prompt_tokens"] = len(
                tok.encode(prompt_text, add_special_tokens=False)
            )
        if response_text is not None:
            stats["completion_tokens"] = len(
                tok.encode(str(response_text), add_special_tokens=False)
            )
    return stats
