"""Evaluation harness executing benchmark tests, scoring accuracy, and calculating cost/latency."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List

from triage_agent.agent import OrderTriageAgent
from triage_agent.evals.datasets import EVAL_BENCHMARK_SUITE


@dataclass
class EvalSummary:
    total_cases: int
    passed_cases: int
    accuracy_pct: float
    human_gate_accuracy_pct: float
    mean_latency_ms: float
    total_cost_usd: float
    case_results: List[Dict[str, Any]]


class EvalBenchmarkRunner:
    """Benchmark runner for verifying agent routing precision, latency, and cost invariants."""

    def __init__(self, agent: OrderTriageAgent | None = None) -> None:
        self.agent = agent or OrderTriageAgent()

    def run_benchmark(self) -> EvalSummary:
        passed = 0
        gate_passed = 0
        total = len(EVAL_BENCHMARK_SUITE)
        latencies: List[float] = []
        case_results: List[Dict[str, Any]] = []

        for case in EVAL_BENCHMARK_SUITE:
            order = case["order"]
            decision = self.agent.process_order(order)
            latencies.append(decision.triage_latency_ms)

            dest_match = decision.destination == case["expected_destination"]
            prio_match = decision.priority == case["expected_priority"]
            gate_match = decision.requires_human_approval == case["expected_human_approval"]

            is_success = dest_match and prio_match and gate_match
            if is_success:
                passed += 1
            if gate_match:
                gate_passed += 1

            case_results.append(
                {
                    "case_name": case["case_name"],
                    "passed": is_success,
                    "destination": {
                        "actual": decision.destination.value,
                        "expected": case["expected_destination"].value,
                        "matched": dest_match,
                    },
                    "priority": {
                        "actual": decision.priority.value,
                        "expected": case["expected_priority"].value,
                        "matched": prio_match,
                    },
                    "human_gate": {
                        "actual": decision.requires_human_approval,
                        "expected": case["expected_human_approval"],
                        "matched": gate_match,
                    },
                    "confidence": decision.confidence_score,
                    "latency_ms": decision.triage_latency_ms,
                }
            )

        accuracy_pct = round((passed / total) * 100.0, 2)
        gate_accuracy_pct = round((gate_passed / total) * 100.0, 2)
        mean_latency = round(sum(latencies) / len(latencies), 2) if latencies else 0.0
        total_cost = round(total * 0.0024, 4)

        return EvalSummary(
            total_cases=total,
            passed_cases=passed,
            accuracy_pct=accuracy_pct,
            human_gate_accuracy_pct=gate_accuracy_pct,
            mean_latency_ms=mean_latency,
            total_cost_usd=total_cost,
            case_results=case_results,
        )


def main() -> None:
    runner = EvalBenchmarkRunner()
    summary = runner.run_benchmark()
    print("=" * 60)
    print("ENTERPRISE ORDER-TRIAGE AGENT: EVALUATION BENCHMARK RECEIPT")
    print("=" * 60)
    print(f"Total Test Cases:       {summary.total_cases}")
    print(f"Passed Cases:           {summary.passed_cases}")
    print(f"Routing Accuracy:       {summary.accuracy_pct}%")
    print(f"HITL Gate Accuracy:     {summary.human_gate_accuracy_pct}%")
    print(f"Mean Latency:           {summary.mean_latency_ms} ms")
    print(f"Total Estimated Cost:   ${summary.total_cost_usd:.4f} USD")
    print("=" * 60)
    print(json.dumps([r for r in summary.case_results], indent=2))


if __name__ == "__main__":
    main()
