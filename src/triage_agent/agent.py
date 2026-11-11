"""Core Enterprise Order-Triage Agent implementation."""

from __future__ import annotations

import time
from typing import List, Optional

from triage_agent.core.config import settings
from triage_agent.core.models import (
    CustomerTier,
    MedallionAuditRecord,
    OrderPayload,
    OrderPriority,
    RoutingDestination,
    ToolCallRecord,
    TriageDecision,
)
from triage_agent.observability.metrics import (
    TOOL_EXECUTIONS_TOTAL,
    record_triage_metrics,
)
from triage_agent.observability.tracer import tracer
from triage_agent.tools.audit import MedallionAuditTool
from triage_agent.tools.crm import SalesforceCRMTool
from triage_agent.tools.erp import ERPInventoryTool


class OrderTriageAgent:
    """Production Agent orchestrating ERP, CRM, and Databricks audit under strict guardrails."""

    def __init__(
        self,
        erp_tool: Optional[ERPInventoryTool] = None,
        crm_tool: Optional[SalesforceCRMTool] = None,
        audit_tool: Optional[MedallionAuditTool] = None,
    ) -> None:
        self.erp = erp_tool or ERPInventoryTool()
        self.crm = crm_tool or SalesforceCRMTool()
        self.audit = audit_tool or MedallionAuditTool()

    def process_order(self, order: OrderPayload) -> TriageDecision:
        """Execute full agentic triage cycle with tool integrations and metrics instrumentation."""
        start_time = time.perf_counter()
        tool_records: List[ToolCallRecord] = []
        applied_rules: List[str] = []

        # 1. Start distributed observability trace
        trace = tracer.start_trace(
            name="order_triage_decision_flow",
            user_id=order.customer.customer_id,
            metadata={"order_id": order.order_id, "total_value": order.total_value},
        )

        # 2. Tool Invocation: CRM Account & Credit Check
        crm_raw, crm_rec = self.crm(customer_id=order.customer.customer_id)
        tool_records.append(crm_rec)
        TOOL_EXECUTIONS_TOTAL.labels(tool_name="salesforce_crm_lookup", status=crm_rec.status).inc()

        # 3. Tool Invocation: ERP Inventory & Material Handling
        item_dicts = [item.model_dump() for item in order.items]
        erp_raw, erp_rec = self.erp(items=item_dicts)
        tool_records.append(erp_rec)
        TOOL_EXECUTIONS_TOTAL.labels(tool_name="erp_inventory_check", status=erp_rec.status).inc()

        # 4. Agentic Policy Evaluation & Guardrail Execution
        destination = RoutingDestination.AUTO_FULFILLMENT
        priority = OrderPriority.NORMAL
        requires_human = False
        approval_reason: Optional[str] = None
        confidence = 0.96

        total_value = order.total_value
        credit_approved = crm_raw.get("credit_approved", True)
        all_in_stock = erp_raw.get("all_in_stock", True)
        requires_cryo = erp_raw.get("requires_cryo_cold_chain", False)
        has_hazardous = erp_raw.get("has_hazardous_materials", False)
        customer_tier = crm_raw.get("tier", CustomerTier.STANDARD.value)

        # Invariant 1: Credit Hold Enforcement
        if not credit_approved:
            destination = RoutingDestination.MANUAL_REVIEW
            priority = OrderPriority.HIGH
            requires_human = True
            approval_reason = "Customer credit hold flagged in Salesforce CRM"
            applied_rules.append("RULE_CREDIT_HOLD_ENFORCED")
            confidence = 0.99

        # Invariant 2: High-Value Threshold Gate (HITL)
        elif total_value >= settings.high_value_threshold_usd:
            destination = RoutingDestination.SALESFORCE_HIGH_VALUE_HOLD
            priority = OrderPriority.HIGH if customer_tier != CustomerTier.ENTERPRISE.value else OrderPriority.CRITICAL
            requires_human = True
            limit_usd = settings.high_value_threshold_usd
            approval_reason = f"Order total ${total_value:,.2f} exceeds high-value threshold (${limit_usd:,.2f})"
            applied_rules.append("RULE_HIGH_VALUE_HITL_TRIGGER")
            confidence = 0.98

        # Invariant 3: Hazardous & Cryogenic Cold Chain Material Handling
        elif has_hazardous or requires_cryo:
            destination = RoutingDestination.SPECIALTY_TRIAGE
            priority = OrderPriority.HIGH
            requires_human = False
            specialty_reasons = []
            if has_hazardous:
                specialty_reasons.append("Hazardous materials handling required")
            if requires_cryo:
                specialty_reasons.append("Cold-chain cryogenic shipping protocol (-80C/-196C)")
            applied_rules.append("RULE_SPECIALTY_LOGISTICS_ROUTED: " + "; ".join(specialty_reasons))
            confidence = 0.95

        # Invariant 4: Stockout / Inventory Shortage
        elif not all_in_stock:
            destination = RoutingDestination.MANUAL_REVIEW
            priority = OrderPriority.NORMAL
            requires_human = True
            approval_reason = "ERP inventory backorder; split shipment or partial allocation required"
            applied_rules.append("RULE_INVENTORY_BACKORDER_DETECTED")
            confidence = 0.92

        # Invariant 5: Clean Automated Execution
        else:
            destination = RoutingDestination.AUTO_FULFILLMENT
            priority = OrderPriority.NORMAL
            applied_rules.append("RULE_CLEAN_AUTO_FULFILLMENT_QUALIFIED")
            confidence = 0.97

        # 5. Tool Invocation: Databricks Medallion Audit Commit
        audit_raw, audit_rec = self.audit(
            order_id=order.order_id,
            estimated_cost_usd=0.0024,
        )
        tool_records.append(audit_rec)
        TOOL_EXECUTIONS_TOTAL.labels(tool_name="databricks_medallion_audit", status=audit_rec.status).inc()

        audit_model: Optional[MedallionAuditRecord] = None
        if "audit_record" in audit_raw:
            audit_model = MedallionAuditRecord(**audit_raw["audit_record"])

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        elapsed_sec = elapsed_ms / 1000.0

        # 6. Record Prometheus Metrics & Langfuse Scores
        record_triage_metrics(
            destination=destination.value,
            priority=priority.value,
            latency_sec=elapsed_sec,
            confidence=confidence,
            cost_usd=0.0024,
            model_name=settings.model_name,
            requires_human=requires_human,
            human_reason=approval_reason or "",
        )

        tracer.log_score(
            trace_id=trace["trace_id"],
            name="confidence",
            value=confidence,
            comment=f"Routing destination: {destination.value}",
        )

        return TriageDecision(
            order_id=order.order_id,
            destination=destination,
            priority=priority,
            confidence_score=confidence,
            requires_human_approval=requires_human,
            approval_reason=approval_reason,
            applied_rules=applied_rules,
            tool_calls=tool_records,
            audit_record=audit_model,
            triage_latency_ms=elapsed_ms,
        )
