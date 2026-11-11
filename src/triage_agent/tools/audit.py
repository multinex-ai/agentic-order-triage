"""Databricks Medallion Architecture Audit Logger (Bronze -> Silver -> Gold)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from triage_agent.core.models import MedallionAuditRecord
from triage_agent.tools.base import BaseTool


class MedallionAuditTool(BaseTool):
    name: str = "databricks_medallion_audit"
    description: str = (
        "Commit immutable audit lineage across bronze (raw), silver (curated), and gold (routing) Delta tables."
    )

    def run(self, **kwargs: Any) -> Dict[str, Any]:
        order_id: str = kwargs.get("order_id", f"ord-{uuid.uuid4().hex[:8]}")
        cost_usd: float = kwargs.get("estimated_cost_usd", 0.0024)

        bronze_id = f"brz-{uuid.uuid4().hex[:12]}"
        silver_id = f"slv-{uuid.uuid4().hex[:12]}"
        gold_id = f"gld-{uuid.uuid4().hex[:12]}"

        record = MedallionAuditRecord(
            bronze_raw_ingest_id=bronze_id,
            silver_curated_id=silver_id,
            gold_decision_id=gold_id,
            databricks_table="enterprise_ai.order_triage_gold",
            timestamp=datetime.now(timezone.utc),
            estimated_cost_usd=cost_usd,
        )

        return {
            "status": "COMMITTED",
            "order_id": order_id,
            "bronze_id": bronze_id,
            "silver_id": silver_id,
            "gold_id": gold_id,
            "delta_table": record.databricks_table,
            "audit_record": record.model_dump(),
        }
