"""Tests for benchmark evals runner and API endpoints."""

from fastapi.testclient import TestClient

from triage_agent.api import app
from triage_agent.evals.benchmark import EvalBenchmarkRunner


def test_eval_benchmark_runner() -> None:
    runner = EvalBenchmarkRunner()
    summary = runner.run_benchmark()
    assert summary.total_cases == 4
    assert summary.passed_cases == 4
    assert summary.accuracy_pct == 100.0
    assert summary.human_gate_accuracy_pct == 100.0
    assert summary.mean_latency_ms > 0.0
    assert summary.total_cost_usd > 0.0


def test_api_healthz() -> None:
    client = TestClient(app)
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "HEALTHY"


def test_api_metrics_endpoint() -> None:
    client = TestClient(app)
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert b"ai_orders_processed_total" in resp.content


def test_api_evals_benchmark_endpoint() -> None:
    client = TestClient(app)
    resp = client.get("/api/v1/evals/benchmark")
    assert resp.status_code == 200
    data = resp.json()
    assert data["accuracy_pct"] == 100.0
    assert data["total_cases"] == 4
