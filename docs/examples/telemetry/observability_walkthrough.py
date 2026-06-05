# pytest: ollama, e2e, slow
"""Support-ticket triage and grounded-reply assistant.

A realistic customer-support pipeline that exercises Mellea's OpenTelemetry
instrumentation end-to-end, demonstrating why tracing, metrics, and logs are
useful in production GenAI applications.

Each stage is designed to answer one of four operational questions:

  "Did it fail, and where?"      → traces (ERROR span + exception event)
                                    + trace-correlated logs
  "Why is it slow?"              → metrics (operation.duration, ttfb)
                                    + trace waterfall
  "Debug this one request"       → logs correlated to a trace via trace_id
  "What am I spending (tokens)?" → metrics (tokens.input/output) per model

Pipeline stages
---------------
  0. Sessions       — open two sessions on different models to see routing in traces
  1. Triage         — classify ticket category and urgency (granite4.1:3b)
  2. Extract        — pull structured fields via constrained decoding (granite4.1:8b)
  3. Tool lookup    — order status via @tool (granite4.1:8b, tool_calls)
  4. Draft + gate   — draft reply with requirements + repair loop (granite4.1:8b)
  5. Stream         — stream final reply; captures TTFB metric (granite4.1:8b)
  6. Grounding      — verify draft against policy docs (granite-4.0-micro, HF)
                       opt-in via WALKTHROUGH_GROUNDING=1
  7. Outage         — simulate unreachable service → ERROR span + llm.errors metric

Running
-------
Use the companion script which sets OTLP env vars before importing mellea:

    ./run_with_otel.sh

Or configure the env yourself and run directly:

    export MELLEA_TRACES_ENABLED=true
    export MELLEA_TRACES_OTLP=true
    export MELLEA_METRICS_ENABLED=true
    export MELLEA_METRICS_OTLP=true
    export MELLEA_LOGS_OTLP=true
    export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317  # OTLP gRPC port
    uv run python docs/examples/telemetry/observability_walkthrough.py

Optional env vars:

    WALKTHROUGH_GROUNDING=1   enable the HF groundedness stage
    MELLEA_TRACES_CONTENT=true  enable prompt/response content capture (PII — opt-in)
"""

import asyncio
import logging
import os
from typing import Literal

from pydantic import BaseModel

from mellea import generative, start_session
from mellea.backends import ModelOption, tool
from mellea.stdlib.requirements import LLMaJRequirement, req
from mellea.stdlib.sampling import RejectionSamplingStrategy
from mellea.telemetry import is_metrics_enabled, is_tracing_enabled

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Domain models
# ---------------------------------------------------------------------------


class Triage(BaseModel):
    """Triage classification for an incoming support ticket."""

    category: Literal[
        "return_exchange", "shipping_delay", "billing", "product_defect", "other"
    ]
    urgency: Literal["high", "medium", "low"]
    summary: str


class TicketFields(BaseModel):
    """Structured fields extracted from a support ticket."""

    customer_name: str
    order_id: str
    product: str
    issue_type: str


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

_ORDER_DB: dict[str, dict] = {
    "SH-4821": {
        "status": "delivered",
        "delivery_date": "2025-05-10",
        "product": "Trail Runner Pro, size US8",
        "eligible_for_return": True,
        "return_window_days": 30,
    }
}


@tool
def lookup_order(order_id: str) -> dict:
    """Retrieve the delivery status and return eligibility for a customer order.

    Args:
        order_id: The order identifier, e.g. SH-4821.
    """
    record = _ORDER_DB.get(order_id.strip().lstrip("#").upper())
    if record is None:
        return {"found": False, "message": f"Order {order_id} not found."}
    return {"found": True, **record}


# ---------------------------------------------------------------------------
# @generative triage function (3b model)
# ---------------------------------------------------------------------------


@generative
def classify_ticket(ticket_text: str) -> Triage:  # type: ignore[return-value]
    """Classify this customer support ticket.

    Identify the category that best describes the customer's issue, the
    urgency level based on language and business impact, and write a
    one-sentence summary of the problem.
    """


# ---------------------------------------------------------------------------
# Policy docs for groundedness check
# ---------------------------------------------------------------------------

_POLICY: list[tuple[str, str]] = [
    (
        "Return Policy",
        "Customers may return unused items within 30 days of delivery for a full "
        "refund or free size exchange. Items must be in original condition with "
        "original packaging.",
    ),
    (
        "Exchange Policy",
        "Size exchanges are processed free of charge. The replacement item ships "
        "within 3-5 business days after the original item is received at our warehouse.",
    ),
    (
        "Shipping Policy",
        "Standard shipping takes 5-7 business days. Expedited 2-day shipping is "
        "available for an additional fee. We do not offer same-day or next-day delivery.",
    ),
]

# ---------------------------------------------------------------------------
# Sample support ticket
# ---------------------------------------------------------------------------

TICKET = """\
Hi team,

I ordered a pair of Trail Runner Pro shoes three weeks ago (Order #SH-4821) but they
arrived in the wrong size — I ordered US 10 but received US 8. I need to exchange them
for the right size. My name is Sarah Chen. I have an important trail race next weekend
and I'm worried I won't have my shoes in time.

Can you help me sort this out quickly?

— Sarah Chen
"""


# ---------------------------------------------------------------------------
# Telemetry helpers
# ---------------------------------------------------------------------------


def _flush_telemetry() -> None:
    """Force-flush all telemetry providers so batched data reaches the receiver."""
    try:
        from opentelemetry import (
            metrics as otel_metrics,  # type: ignore[import-untyped]
            trace,  # type: ignore[import-untyped]
        )

        tracer_provider = trace.get_tracer_provider()
        if hasattr(tracer_provider, "force_flush"):
            tracer_provider.force_flush(timeout_millis=10_000)

        meter_provider = otel_metrics.get_meter_provider()
        if hasattr(meter_provider, "force_flush"):
            meter_provider.force_flush(timeout_millis=10_000)
    except Exception:
        pass


def _section(n: int, title: str, signal_note: str) -> None:
    print(f"\n{'─' * 70}")
    print(f"  Stage {n}: {title}")
    print(f"  signals → {signal_note}")
    print(f"{'─' * 70}")


# ---------------------------------------------------------------------------
# Optional grounding stage (requires LocalHFBackend)
# ---------------------------------------------------------------------------


async def _run_grounding(reply: str) -> None:
    """Verify the drafted reply is grounded in our policy documents."""
    try:
        from mellea.backends.huggingface import LocalHFBackend
        from mellea.stdlib.components import Document, Message
        from mellea.stdlib.context import ChatContext
        from mellea.stdlib.requirements.rag import GroundednessRequirement

        logger.info("Loading HF backend for grounding check")
        hf_backend = LocalHFBackend(model_id="ibm-granite/granite-4.0-micro")

        docs = [
            Document(doc_id=f"p{i}", title=title, text=text)
            for i, (title, text) in enumerate(_POLICY)
        ]
        ctx = (
            ChatContext()
            .add(Message("user", "Is this reply grounded in our support policies?"))
            .add(Message("assistant", reply))
        )
        grounding_req = GroundednessRequirement(
            documents=docs, allow_partial_support=True
        )
        result = await grounding_req.validate(hf_backend, ctx)

        print(f"  Grounded : {result.as_bool()}")
        if result.reason:
            print(f"  Reason   : {result.reason[:200]}")
        logger.info("Groundedness check complete: passed=%s", result.as_bool())

    except Exception as exc:
        logger.warning("Grounding stage unavailable: %s", exc)
        print(f"  → Skipped: {exc}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def main() -> None:
    print("=" * 70)
    print("  Mellea Observability Walkthrough: Support Ticket Assistant")
    print("=" * 70)
    print(f"  Tracing enabled : {is_tracing_enabled()}")
    print(f"  Metrics enabled : {is_metrics_enabled()}")
    if not is_tracing_enabled() and not is_metrics_enabled():
        print("\n  Tip: run via run_with_otel.sh to enable OTLP export.")

    # -----------------------------------------------------------------------
    # Stage 0 — open sessions on two models
    # Signals: start_session + session_context application spans;
    #          gen_ai.conversation.id populated on backend spans within each session.
    # -----------------------------------------------------------------------
    _section(
        0,
        "Open sessions (two models)",
        "start_session + session_context spans; gen_ai.conversation.id",
    )
    logger.info(
        "Opening drafting session (granite4.1:8b) and triage session (granite4.1:3b)"
    )

    with start_session("ollama", "granite4.1:8b") as drafting:
        with start_session("ollama", "granite4.1:3b") as triage:
            print("  drafting → granite4.1:8b  |  triage → granite4.1:3b")

            # -------------------------------------------------------------------
            # Stage 1 — Triage via @generative (cheap 3b model)
            # Signals: backend chat span on granite4.1:3b; mellea.action_type;
            #          tokens.input/output; request.duration.
            # Answers: "What am I spending on cheap vs expensive model calls?"
            # -------------------------------------------------------------------
            _section(
                1,
                "Triage (granite4.1:3b)",
                "chat span; gen_ai.request.model=granite4.1:3b; token metrics",
            )
            triage_result: Triage = classify_ticket(triage, ticket_text=TICKET)
            logger.info(
                "Triage: category=%s urgency=%s",
                triage_result.category,
                triage_result.urgency,
            )
            print(f"  Category : {triage_result.category}")
            print(f"  Urgency  : {triage_result.urgency}")
            print(f"  Summary  : {triage_result.summary}")

            # -------------------------------------------------------------------
            # Stage 2 — Structured extraction (8b model, constrained decode)
            # Signals: backend chat span; mellea.has_format=True;
            #          mellea.format_type=TicketFields; tokens on 8b model.
            # Answers: "What am I spending on the stronger model?"
            # -------------------------------------------------------------------
            _section(
                2,
                "Structured extraction (granite4.1:8b)",
                "chat span; has_format=True; format_type=TicketFields; token metrics",
            )
            fields_result = drafting.instruct(
                "Extract the structured fields from this customer support ticket:\n\n{{ticket}}",
                user_variables={"ticket": TICKET},
                format=TicketFields,
            )
            fields = TicketFields.model_validate_json(str(fields_result))
            logger.info(
                "Extracted: customer=%s order=%s", fields.customer_name, fields.order_id
            )
            print(f"  Customer  : {fields.customer_name}")
            print(f"  Order ID  : {fields.order_id}")
            print(f"  Product   : {fields.product}")
            print(f"  Issue     : {fields.issue_type}")

            # -------------------------------------------------------------------
            # Stage 3 — Order lookup via @tool
            # Signals: backend chat span with mellea.tool_calls_enabled=True;
            #          mellea.tool.calls metric (tool=lookup_order, status=success).
            # Answers: "Did my tool call succeed?"
            # -------------------------------------------------------------------
            _section(
                3,
                "Order lookup via tool",
                "chat span; tool_calls_enabled=True; mellea.tool.calls metric",
            )
            tool_summary = ""
            try:
                tool_response = drafting.instruct(
                    "Look up order {{order_id}} and summarise the result in one sentence.",
                    user_variables={"order_id": fields.order_id},
                    tool_calls=True,
                    model_options={ModelOption.TOOLS: [lookup_order]},
                )
                tool_summary = str(tool_response).strip()
                logger.info("Tool response: %s", tool_summary[:120])
                if tool_summary:
                    print(f"  {tool_summary[:200]}")
                else:
                    print("  (model used tool; no further text generated)")
            except Exception as exc:
                logger.warning("Tool stage: %s", exc)
                order = _ORDER_DB.get(fields.order_id.upper(), {})
                tool_summary = (
                    f"Order {fields.order_id}: {order.get('product', 'unknown')} — "
                    f"eligible for return: {order.get('eligible_for_return', False)}"
                )
                print(
                    f"  Tool call failed ({exc.__class__.__name__}), using static data"
                )

            # -------------------------------------------------------------------
            # Stage 4 — Draft reply with requirements + repair loop
            # Signals: repeated backend chat spans (up to 3 attempts);
            #          LLM-as-judge backend spans per requirement;
            #          sampling.attempts / .successes / .failures metrics;
            #          requirement.checks / .failures metrics.
            # Answers: "Why did this request take longer than the others?"
            # -------------------------------------------------------------------
            _section(
                4,
                "Draft reply with quality gate",
                "repeated chat spans (repair loop); sampling + requirement metrics",
            )
            order_context = tool_summary or (
                f"Order {fields.order_id} is eligible for a free size exchange."
            )
            draft_result = drafting.instruct(
                "You are a customer support agent. Write a reply to {{customer}}'s "
                "ticket about order {{order_id}}. Use this order context: {{context}}. "
                "Address the urgency about the upcoming race.",
                user_variables={
                    "customer": fields.customer_name,
                    "order_id": fields.order_id,
                    "context": order_context,
                },
                requirements=[
                    req(f"The reply explicitly mentions order ID {fields.order_id}"),
                    LLMaJRequirement(
                        "The tone is empathetic and offers a clear resolution"
                    ),
                ],
                strategy=RejectionSamplingStrategy(loop_budget=3),
                return_sampling_results=True,
            )
            draft_reply = str(draft_result)
            logger.info("Draft ready (%d chars)", len(draft_reply))
            print(f"  {draft_reply[:350]}")

            # -------------------------------------------------------------------
            # Stage 5 — Stream the final reply
            # Signals: stream_with_chunking application span + span events
            #          (chunk / streaming_done / completed);
            #          mellea.llm.ttfb metric; request.duration with streaming=True.
            # Answers: "Why is it slow? (time to first token)"
            # -------------------------------------------------------------------
            _section(
                5,
                "Stream final reply",
                "stream_with_chunking span + events; llm.ttfb metric; streaming=True",
            )
            streamed = drafting.instruct(
                "Lightly polish this customer reply for clarity and conciseness. "
                "Keep the empathetic tone:\n\n{{draft}}",
                user_variables={"draft": draft_reply},
                model_options={ModelOption.STREAM: True},
            )
            final_reply = str(streamed)
            logger.info("Streamed reply (%d chars)", len(final_reply))
            print(f"  {final_reply[:350]}")
            if (
                streamed.generation.streaming
                and streamed.generation.ttfb_ms is not None
            ):
                print(
                    f"\n  → Time to first token: {streamed.generation.ttfb_ms:.0f} ms"
                )

            # -------------------------------------------------------------------
            # Stage 6 — Groundedness check against policy docs (opt-in, HF only)
            # Signals: HF backend chat spans on granite-4.0-micro;
            #          find_citations intrinsic → 4-step grounding pipeline;
            #          third distinct gen_ai.request.model label in traces.
            # Answers: "Does the reply actually match what our policies say?"
            # -------------------------------------------------------------------
            _section(
                6,
                "Policy grounding check",
                "HF chat spans (granite-4.0-micro); find_citations intrinsic; "
                "requirement.checks metric"
                if os.getenv("WALKTHROUGH_GROUNDING")
                else "skipped — set WALKTHROUGH_GROUNDING=1 to enable",
            )
            if os.getenv("WALKTHROUGH_GROUNDING"):
                await _run_grounding(final_reply)
            else:
                print(
                    "  Skipped. Set WALKTHROUGH_GROUNDING=1 to run the HF grounding stage."
                )

            # -------------------------------------------------------------------
            # Stage 7 — Simulated outage (error path)
            # Signals: ERROR-status backend chat span; error.type attribute;
            #          exception event on span; mellea.llm.errors metric
            #          (error_type=transport_error).
            # Answers: "Did it fail, and where? Can I correlate the error log to
            #           the failing span?"
            # -------------------------------------------------------------------
            _section(
                7,
                "Simulated enrichment service outage",
                "ERROR span; error.type; llm.errors counter (transport_error); "
                "correlated error log",
            )
            try:
                with start_session(
                    "ollama", "granite4.1:3b", base_url="http://localhost:19999"
                ) as err_session:
                    err_session.instruct(
                        "Run sentiment analysis on: {{text}}",
                        user_variables={"text": final_reply[:100]},
                    )
            except Exception as exc:
                logger.error(
                    "Enrichment service unreachable: %s",
                    type(exc).__name__,
                    exc_info=True,
                )
                print(f"  → Expected error: {type(exc).__name__}")
                print(
                    "  → An ERROR-status span with error.type is now in your trace backend."
                )
                print(
                    "  → The error log above carries trace_id/span_id for correlation."
                )

    # -----------------------------------------------------------------------
    # Done
    # -----------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("  Walkthrough complete.")
    print()
    print("  Check your OTLP receiver for:")
    print("    traces  — session_context → aact → chat span trees; ERROR in stage 7")
    print("    metrics — mellea.llm.tokens.*, mellea.llm.request.duration,")
    print("              mellea.llm.ttfb (stage 5), mellea.llm.errors (stage 7),")
    print("              mellea.sampling.*, mellea.requirement.*, mellea.tool.calls")
    print("    logs    — each log line carries trace_id + span_id for pivot-to-trace")
    print("=" * 70)

    _flush_telemetry()


if __name__ == "__main__":
    asyncio.run(main())
