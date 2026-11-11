"""Tests for tool integration contracts, timing, and error handling."""

from triage_agent.tools.audit import MedallionAuditTool
from triage_agent.tools.crm import SalesforceCRMTool
from triage_agent.tools.erp import ERPInventoryTool


def test_erp_inventory_tool_stock_check() -> None:
    tool = ERPInventoryTool()
    res, rec = tool(items=[{"sku": "MNX-BIO-9021", "quantity": 10}])
    assert rec.status == "SUCCESS"
    assert rec.latency_ms >= 0.0
    assert res["all_in_stock"] is True
    assert res["has_hazardous_materials"] is False


def test_erp_inventory_hazardous_and_cryo() -> None:
    tool = ERPInventoryTool()
    res, rec = tool(items=[{"sku": "MNX-CRYO-1004", "quantity": 1}])
    assert rec.status == "SUCCESS"
    assert res["has_hazardous_materials"] is True
    assert res["requires_cryo_cold_chain"] is True


def test_salesforce_crm_tool_lookup() -> None:
    tool = SalesforceCRMTool()
    res, rec = tool(customer_id="CUST-ENT-001")
    assert rec.status == "SUCCESS"
    assert res["tier"] == "ENTERPRISE"
    assert res["credit_approved"] is True
    assert res["account_executive"] == "sarah.connor@multinex.ai"


def test_salesforce_crm_credit_hold() -> None:
    tool = SalesforceCRMTool()
    res, rec = tool(customer_id="CUST-STD-991")
    assert res["credit_hold"] is True
    assert res["credit_approved"] is False


def test_medallion_audit_commit() -> None:
    tool = MedallionAuditTool()
    res, rec = tool(order_id="ORD-AUDIT-99", estimated_cost_usd=0.003)
    assert rec.status == "SUCCESS"
    assert res["status"] == "COMMITTED"
    assert res["bronze_id"].startswith("brz-")
    assert res["silver_id"].startswith("slv-")
    assert res["gold_id"].startswith("gld-")
