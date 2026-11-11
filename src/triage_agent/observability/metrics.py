"""Prometheus metrics instrumentation for enterprise agent observability."""

from __future__ import annotations

from prometheus_client import Counter, Histogram, generate_latest

ORDERS_PROCESSED_TOTAL = Counter(
    "ai_orders_processed_total",
    "Total number of orders processed by the triage agent",
    ["destination", "priority", "status"],
)

ORDER_TRIAGE_LATENCY_SECONDS = Histogram(
    "ai_order_triage_latency_seconds",
    "End-to-end latency for agent triage execution in seconds",
    buckets=(0.05, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0),
)

TOKEN_COST_DOLLARS_TOTAL = Counter(
    "ai_token_cost_dollars_total",
    "Cumulative estimated token spend for LLM reasoning and tools",
    ["model", "destination"],
)

CONFIDENCE_SCORE_HISTOGRAM = Histogram(
    "ai_confidence_score",
    "Distribution of confidence scores emitted by the agent",
    buckets=(0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 1.0),
)

HUMAN_REVIEW_REQUIRED_TOTAL = Counter(
    "ai_human_review_required_total",
    "Count of orders gated for mandatory human approval (HITL)",
    ["trigger_reason"],
)

TOOL_EXECUTIONS_TOTAL = Counter(
    "ai_tool_executions_total",
    "Count of tool invocations across ERP, CRM, and Databricks audit",
    ["tool_name", "status"],
)


def record_triage_metrics(
    destination: str,
    priority: str,
    latency_sec: float,
    confidence: float,
    cost_usd: float,
    model_name: str = "gpt-4o",
    requires_human: bool = False,
    human_reason: str = "",
) -> None:
    """Record Prometheus metrics for a completed triage decision."""
    ORDERS_PROCESSED_TOTAL.labels(
        destination=destination,
        priority=priority,
        status="SUCCESS",
    ).inc()

    ORDER_TRIAGE_LATENCY_SECONDS.observe(latency_sec)
    CONFIDENCE_SCORE_HISTOGRAM.observe(confidence)

    TOKEN_COST_DOLLARS_TOTAL.labels(
        model=model_name,
        destination=destination,
    ).inc(cost_usd)

    if requires_human:
        HUMAN_REVIEW_REQUIRED_TOTAL.labels(
            trigger_reason=human_reason or "UNSPECIFIED",
        ).inc()


def get_prometheus_metrics_bytes() -> bytes:
    """Serialize the current metrics registry in Prometheus text format."""
    return generate_latest()
