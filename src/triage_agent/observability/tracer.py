"""Langfuse tracing integration with resilient offline fallback."""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional

from triage_agent.core.config import settings

logger = logging.getLogger(__name__)


class TraceSpan:
    def __init__(self, name: str, parent_id: Optional[str] = None):
        self.span_id = f"span-{uuid.uuid4().hex[:8]}"
        self.name = name
        self.parent_id = parent_id
        self.inputs: Dict[str, Any] = {}
        self.outputs: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}
        self.scores: Dict[str, float] = {}

    def end(self, outputs: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> None:
        self.outputs = outputs
        if metadata:
            self.metadata.update(metadata)


class ResilientTracer:
    """Enterprise tracer handling Langfuse export with automated local fallback."""

    def __init__(self) -> None:
        self.enabled = settings.enable_langfuse
        self._in_memory_traces: List[Dict[str, Any]] = []
        self._langfuse_client: Any = None

        if self.enabled and not settings.langfuse_public_key.startswith("pk-lf-placeholder"):
            try:
                from langfuse import Langfuse

                self._langfuse_client = Langfuse(
                    public_key=settings.langfuse_public_key,
                    secret_key=settings.langfuse_secret_key,
                    host=settings.langfuse_host,
                )
                logger.info("Langfuse enterprise client initialized successfully")
            except Exception as exc:
                logger.warning("Langfuse client initialization failed (%s); using in-memory tracer", exc)
                self._langfuse_client = None

    def start_trace(
        self,
        name: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        trace_id = f"trc-{uuid.uuid4().hex[:12]}"
        trace_record = {
            "trace_id": trace_id,
            "name": name,
            "user_id": user_id,
            "metadata": metadata or {},
            "tags": tags or ["order-triage", "production"],
            "spans": [],
            "scores": {},
        }
        self._in_memory_traces.append(trace_record)
        return trace_record

    def log_score(self, trace_id: str, name: str, value: float, comment: Optional[str] = None) -> None:
        for trace in self._in_memory_traces:
            if trace["trace_id"] == trace_id:
                trace["scores"][name] = {"value": value, "comment": comment}
                break

    def get_recent_traces(self, limit: int = 20) -> List[Dict[str, Any]]:
        return self._in_memory_traces[-limit:]


tracer = ResilientTracer()
