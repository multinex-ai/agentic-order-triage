"""Curated evaluation dataset representing enterprise edge cases and invariant stress tests."""

from __future__ import annotations

from typing import Any, Dict, List

from triage_agent.core.models import (
    CustomerContext,
    CustomerTier,
    OrderItem,
    OrderPayload,
    OrderPriority,
    RoutingDestination,
)

EVAL_BENCHMARK_SUITE: List[Dict[str, Any]] = [
    {
        "case_name": "clean_standard_auto_fulfillment",
        "description": "Routine lab supplies within stock and standard credit limits",
        "order": OrderPayload(
            order_id="ORD-EVAL-001",
            customer=CustomerContext(
                customer_id="CUST-STRAT-042",
                company_name="Metropolis Genomics Institute",
                tier=CustomerTier.STRATEGIC,
                credit_approved=True,
            ),
            items=[
                OrderItem(
                    sku="MNX-PLAST-0012",
                    description="Falcon Tubes 50mL Case",
                    quantity=10,
                    unit_price=145.0,
                ),
                OrderItem(
                    sku="MNX-BIO-9021",
                    description="Taq Polymerase 500U",
                    quantity=4,
                    unit_price=210.0,
                ),
            ],
            raw_email_body="Please ship 10 cases of falcon tubes and 4 vials of Taq polymerase to Metropolis Lab B.",
        ),
        "expected_destination": RoutingDestination.AUTO_FULFILLMENT,
        "expected_priority": OrderPriority.NORMAL,
        "expected_human_approval": False,
    },
    {
        "case_name": "high_value_hitl_enterprise_gate",
        "description": "Enterprise sequencing order over $25,000 requiring human governance",
        "order": OrderPayload(
            order_id="ORD-EVAL-002",
            customer=CustomerContext(
                customer_id="CUST-ENT-001",
                company_name="Acro BioPharma Global",
                tier=CustomerTier.ENTERPRISE,
                credit_approved=True,
            ),
            items=[
                OrderItem(
                    sku="MNX-GENE-4400",
                    description="NextGen Sequencing Reagent Kit 96-well",
                    quantity=25,
                    unit_price=1250.0,
                ),
            ],
            raw_email_body="Urgent production replenishment: 25 kits of NextGen 96-well sequencing reagents.",
        ),
        "expected_destination": RoutingDestination.SALESFORCE_HIGH_VALUE_HOLD,
        "expected_priority": OrderPriority.CRITICAL,
        "expected_human_approval": True,
    },
    {
        "case_name": "hazardous_cryogenic_specialty_triage",
        "description": "Liquid nitrogen vapor shipper requiring hazardous handling and cryo protocol",
        "order": OrderPayload(
            order_id="ORD-EVAL-003",
            customer=CustomerContext(
                customer_id="CUST-STRAT-042",
                company_name="Metropolis Genomics Institute",
                tier=CustomerTier.STRATEGIC,
                credit_approved=True,
            ),
            items=[
                OrderItem(
                    sku="MNX-CRYO-1004",
                    description="Liquid Nitrogen Vapor Shipper 25L",
                    quantity=2,
                    unit_price=4850.0,
                ),
            ],
            raw_email_body="Need 2 LN2 vapor shippers for biological specimen transfer to storage.",
        ),
        "expected_destination": RoutingDestination.SPECIALTY_TRIAGE,
        "expected_priority": OrderPriority.HIGH,
        "expected_human_approval": False,
    },
    {
        "case_name": "credit_hold_billing_gate",
        "description": "Account with active credit hold must be held for financial review",
        "order": OrderPayload(
            order_id="ORD-EVAL-004",
            customer=CustomerContext(
                customer_id="CUST-STD-991",
                company_name="BioLabs San Diego Incubator",
                tier=CustomerTier.STANDARD,
                credit_approved=False,
            ),
            items=[
                OrderItem(
                    sku="MNX-PLAST-0012",
                    description="Falcon Tubes 50mL Case",
                    quantity=5,
                    unit_price=145.0,
                ),
            ],
            raw_email_body="BioLabs ordering 5 cases falcon tubes on account.",
        ),
        "expected_destination": RoutingDestination.MANUAL_REVIEW,
        "expected_priority": OrderPriority.HIGH,
        "expected_human_approval": True,
    },
]
