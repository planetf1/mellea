#!/usr/bin/env bash
# Run the observability walkthrough with OTLP export enabled.
#
# Targets the standard OTLP gRPC endpoint (default: localhost:4317).
# Point OTEL_EXPORTER_OTLP_ENDPOINT at any OTLP-compatible receiver
# (OpenTelemetry Collector, Jaeger, or a local development receiver).
#
# Prerequisites:
#   1. An OTLP receiver listening on port 4317 (gRPC) or change the
#      endpoint/protocol below to target port 4318 (HTTP/protobuf).
#   2. Ollama running with granite4.1:8b and granite4.1:3b available.
#   3. (Optional) HuggingFace deps installed for the grounding stage:
#        uv sync --extra huggingface
#
# Usage:
#   chmod +x run_with_otel.sh
#   ./run_with_otel.sh
#
#   # Enable the HF grounding stage:
#   WALKTHROUGH_GROUNDING=1 ./run_with_otel.sh

# ---------------------------------------------------------------------------
# OTLP receiver endpoint
# Change this to target a remote collector or a different local port.
# ---------------------------------------------------------------------------
export OTEL_SERVICE_NAME="${OTEL_SERVICE_NAME:-mellea-support-assistant}"
# Mellea currently uses the OTLP gRPC exporter for all signals.
# Default: OTLP gRPC on port 4317 (insecure). An http:// scheme is treated as
# insecure by the OTel Python gRPC exporter — no separate insecure flag needed.
# For HTTP/protobuf (port 4318), mellea would need to be updated to respect
# OTEL_EXPORTER_OTLP_PROTOCOL — see the follow-up conformance issue.
export OTEL_EXPORTER_OTLP_ENDPOINT="${OTEL_EXPORTER_OTLP_ENDPOINT:-http://localhost:4317}"

# ---------------------------------------------------------------------------
# Mellea telemetry — enable all three signal families
# ---------------------------------------------------------------------------
export MELLEA_TRACES_ENABLED=true
export MELLEA_TRACES_OTLP=true

export MELLEA_METRICS_ENABLED=true
export MELLEA_METRICS_OTLP=true

export MELLEA_LOGS_OTLP=true

# Flush metrics quickly (default is 60 s; 5 s is better for a short-lived demo).
export OTEL_METRIC_EXPORT_INTERVAL="${OTEL_METRIC_EXPORT_INTERVAL:-5000}"

# ---------------------------------------------------------------------------
# Content capture (opt-in — may include PII such as prompt text and responses)
# Uncomment to enable once prompt/response capture is wired in the backend.
# ---------------------------------------------------------------------------
# export MELLEA_TRACES_CONTENT=true
# export OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true

# ---------------------------------------------------------------------------
# Run
# Env vars must be set before importing mellea (import-time config capture).
# ---------------------------------------------------------------------------
exec uv run python docs/examples/telemetry/observability_walkthrough.py
