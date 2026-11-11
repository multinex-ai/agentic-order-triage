"""Core domain modules and configuration."""

from triage_agent.core.config import settings
from triage_agent.core.models import (
    CustomerContext,
    CustomerTier,
    MedallionAuditRecord,
    OrderItem,
    OrderPayload,
    OrderPriority,
    RoutingDestination,
    ToolCallRecord,
    TriageDecision,
)

__all__ = [
    "settings",
    "CustomerContext",
    "CustomerTier",
    "MedallionAuditRecord",
    "OrderItem",
    "OrderPayload",
    "OrderPriority",
    "RoutingDestination",
    "ToolCallRecord",
    "TriageDecision",
]
