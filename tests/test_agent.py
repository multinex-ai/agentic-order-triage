"""Tests for agentic triage orchestration and invariant governance."""

from triage_agent.agent import OrderTriageAgent
from triage_agent.core.models import (
    CustomerContext,
    CustomerTier,
    OrderItem,
    OrderPayload,
    OrderPriority,
    RoutingDestination,
)


def test_agent_clean_auto_fulfillment() -> None:
    agent = OrderTriageAgent()
    order = OrderPayload(
        order_id="ORD-CLEAN-01",
        customer=CustomerContext(
            customer_id="CUST-STRAT-042",
            company_name="Metropolis Genomics Institute",
            tier=CustomerTier.STRATEGIC,
            credit_approved=True,
        ),
        items=[
            OrderItem(sku="MNX-BIO-9021", description="Taq Polymerase", quantity=2, unit_price=210.0),
        ],
        raw_email_body="Standard replenishment order.",
    )
    decision = agent.process_order(order)
    assert decision.destination == RoutingDestination.AUTO_FULFILLMENT
    assert decision.priority == OrderPriority.NORMAL
    assert decision.requires_human_approval is False
    assert decision.confidence_score >= 0.95
    assert decision.audit_record is not None
    assert len(decision.tool_calls) == 3


def test_agent_high_value_hitl_gate() -> None:
    agent = OrderTriageAgent()
    order = OrderPayload(
        order_id="ORD-HIGH-VAL",
        customer=CustomerContext(
            customer_id="CUST-ENT-001",
            company_name="Acro BioPharma Global",
            tier=CustomerTier.ENTERPRISE,
            credit_approved=True,
        ),
        items=[
            OrderItem(sku="MNX-GENE-4400", description="Reagent Kit", quantity=25, unit_price=1250.0),
        ],
        raw_email_body="Bulk requisition for Q4 clinical sequencing pipeline.",
    )
    decision = agent.process_order(order)
    assert decision.destination == RoutingDestination.SALESFORCE_HIGH_VALUE_HOLD
    assert decision.priority == OrderPriority.CRITICAL
    assert decision.requires_human_approval is True
    assert "exceeds high-value threshold" in (decision.approval_reason or "")


def test_agent_credit_hold_enforcement() -> None:
    agent = OrderTriageAgent()
    order = OrderPayload(
        order_id="ORD-HOLD-01",
        customer=CustomerContext(
            customer_id="CUST-STD-991",
            company_name="BioLabs Incubator",
            tier=CustomerTier.STANDARD,
            credit_approved=False,
        ),
        items=[
            OrderItem(sku="MNX-PLAST-0012", description="Falcon Tubes", quantity=1, unit_price=145.0),
        ],
        raw_email_body="Ship immediately.",
    )
    decision = agent.process_order(order)
    assert decision.destination == RoutingDestination.MANUAL_REVIEW
    assert decision.priority == OrderPriority.HIGH
    assert decision.requires_human_approval is True
    assert "credit hold flagged" in (decision.approval_reason or "")
