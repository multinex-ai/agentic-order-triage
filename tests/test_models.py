"""Tests for core domain models and validation."""

from triage_agent.core.models import (
    CustomerContext,
    CustomerTier,
    OrderItem,
    OrderPayload,
)


def test_order_item_line_total() -> None:
    item = OrderItem(
        sku="MNX-BIO-9021",
        description="Taq Polymerase",
        quantity=5,
        unit_price=210.0,
    )
    assert item.line_total == 1050.0


def test_order_payload_total_value() -> None:
    order = OrderPayload(
        order_id="ORD-TEST-100",
        customer=CustomerContext(
            customer_id="CUST-ENT-001",
            company_name="Acro BioPharma",
            tier=CustomerTier.ENTERPRISE,
        ),
        items=[
            OrderItem(sku="SKU-1", description="Item 1", quantity=2, unit_price=100.0),
            OrderItem(sku="SKU-2", description="Item 2", quantity=3, unit_price=50.0),
        ],
        raw_email_body="Test order body",
    )
    assert order.total_value == 350.0
