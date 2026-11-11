"""Production FastAPI service exposing triage agent, Prometheus metrics, and evals."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Response

from triage_agent.agent import OrderTriageAgent
from triage_agent.core.config import settings
from triage_agent.core.models import OrderPayload, TriageDecision
from triage_agent.evals.benchmark import EvalBenchmarkRunner
from triage_agent.observability.metrics import get_prometheus_metrics_bytes

app = FastAPI(
    title="Enterprise Order-Triage Agent API",
    description="Forward Deployed Agentic AI Service for ERP, CRM, and Databricks Medallion Order Routing.",
    version="1.0.0",
)

agent = OrderTriageAgent()
eval_runner = EvalBenchmarkRunner(agent=agent)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """Readiness and liveness probe for Kubernetes / container runtime."""
    return {
        "status": "HEALTHY",
        "service": settings.app_name,
        "environment": settings.environment,
    }


@app.get("/metrics")
def metrics() -> Response:
    """Prometheus metrics endpoint."""
    return Response(
        content=get_prometheus_metrics_bytes(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


@app.post("/api/v1/triage", response_model=TriageDecision)
def triage_order(order: OrderPayload) -> TriageDecision:
    """Execute end-to-end agentic triage on an inbound enterprise order."""
    try:
        return agent.process_order(order)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Agent triage failure: {str(exc)}") from exc


@app.get("/api/v1/evals/benchmark")
def get_eval_benchmark() -> dict[str, object]:
    """Execute and return benchmark evaluation scores and invariants."""
    summary = eval_runner.run_benchmark()
    return {
        "total_cases": summary.total_cases,
        "passed_cases": summary.passed_cases,
        "accuracy_pct": summary.accuracy_pct,
        "human_gate_accuracy_pct": summary.human_gate_accuracy_pct,
        "mean_latency_ms": summary.mean_latency_ms,
        "total_cost_usd": summary.total_cost_usd,
        "case_results": summary.case_results,
    }
