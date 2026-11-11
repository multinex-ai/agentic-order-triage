"""Domain models and boundary schemas for the Enterprise Order-Triage Agent."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class OrderPriority(str, Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class CustomerTier(str, Enum):
    STANDARD = "STANDARD"
    STRATEGIC = "STRATEGIC"
    ENTERPRISE = "ENTERPRISE"


class RoutingDestination(str, Enum):
    AUTO_FULFILLMENT = "AUTO_FULFILLMENT"
    SPECIALTY_TRIAGE = "SPECIALTY_TRIAGE"
    SALESFORCE_HIGH_VALUE_HOLD = "SALESFORCE_HIGH_VALUE_HOLD"
    MANUAL_REVIEW = "MANUAL_REVIEW"


class OrderItem(BaseModel):
    sku: str = Field(..., description="Unique product identifier (e.g., MNX-BIO-9021)")
    description: str = Field(..., description="Item description or catalog name")
    quantity: int = Field(..., ge=1, description="Quantity requested")
    unit_price: float = Field(..., ge=0.0, description="Unit list price in USD")

    @property
    def line_total(self) -> float:
        return round(self.quantity * self.unit_price, 2)


class CustomerContext(BaseModel):
    customer_id: str = Field(..., description="Master customer record ID")
    company_name: str = Field(..., description="Legal company name")
    tier: CustomerTier = Field(default=CustomerTier.STANDARD)
    credit_approved: bool = Field(default=True)
    assigned_account_executive: Optional[str] = None


class OrderPayload(BaseModel):
    order_id: str = Field(..., description="Inbound PO or order reference")
    customer: CustomerContext
    items: List[OrderItem] = Field(default_factory=list)
    raw_email_body: str = Field(..., description="Raw text/email trigger from customer")
    special_handling: Optional[str] = None
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def total_value(self) -> float:
        return round(sum(item.line_total for item in self.items), 2)


class ToolCallRecord(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    result: Dict[str, Any]
    latency_ms: float
    status: str = "SUCCESS"


class MedallionAuditRecord(BaseModel):
    bronze_raw_ingest_id: str
    silver_curated_id: str
    gold_decision_id: str
    databricks_table: str = "enterprise_ai.order_triage_gold"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    estimated_cost_usd: float = Field(default=0.0024)


class TriageDecision(BaseModel):
    order_id: str
    destination: RoutingDestination
    priority: OrderPriority
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    requires_human_approval: bool
    approval_reason: Optional[str] = None
    applied_rules: List[str] = Field(default_factory=list)
    tool_calls: List[ToolCallRecord] = Field(default_factory=list)
    audit_record: Optional[MedallionAuditRecord] = None
    triage_latency_ms: float = 0.0
