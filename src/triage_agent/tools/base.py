"""Base tool contract with automated telemetry and timing."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, Dict

from triage_agent.core.models import ToolCallRecord


class BaseTool(ABC):
    name: str
    description: str

    @abstractmethod
    def run(self, **kwargs: Any) -> Dict[str, Any]:
        """Execute the tool logic."""
        pass

    def __call__(self, **kwargs: Any) -> tuple[Dict[str, Any], ToolCallRecord]:
        """Invoke tool with standardized timing and error isolation."""
        start_time = time.perf_counter()
        status = "SUCCESS"
        result: Dict[str, Any] = {}
        try:
            result = self.run(**kwargs)
        except Exception as exc:
            status = f"ERROR: {str(exc)}"
            result = {"error": str(exc), "success": False}
        finally:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            record = ToolCallRecord(
                tool_name=self.name,
                arguments=kwargs,
                result=result,
                latency_ms=latency_ms,
                status=status,
            )
        return result, record
