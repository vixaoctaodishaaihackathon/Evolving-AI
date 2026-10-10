import time
import logging
from typing import Dict, Any, List
from config import settings

logger = logging.getLogger("ObservabilityTracer")

class AgentExecutionTracer:
    """
    Observability & Tracing Provider compatible with Arize Phoenix and OpenTelemetry.
    Captures agent reasoning trajectories, tool invocations, token spend, and latency.
    """
    def __init__(self):
        self.traces: List[Dict[str, Any]] = []
        self.active_spans: Dict[str, Dict[str, Any]] = {}
        self.phoenix_endpoint = settings.phoenix_endpoint
        self._test_phoenix_connection()

    def _test_phoenix_connection(self):
        try:
            import httpx
            resp = httpx.get(f"http://localhost:6006/", timeout=1.0)
            logger.info("Arize Phoenix collector detected on port 6006.")
        except Exception:
            logger.info("Arize Phoenix container not reachable locally; buffering telemetry traces in local observer.")

    def start_span(self, trace_id: str, span_name: str, attributes: Dict[str, Any]) -> str:
        span_id = f"{trace_id}_{span_name}_{int(time.time() * 1000)}"
        self.active_spans[span_id] = {
            "span_id": span_id,
            "trace_id": trace_id,
            "name": span_name,
            "start_time": time.time(),
            "attributes": attributes,
            "status": "RUNNING"
        }
        return span_id

    def end_span(self, span_id: str, output: Any = None, error: Any = None):
        span = self.active_spans.pop(span_id, None)
        if not span:
            return
        latency_ms = round((time.time() - span["start_time"]) * 1000, 2)
        span["duration_ms"] = latency_ms
        span["output"] = output
        span["error"] = str(error) if error else None
        span["status"] = "ERROR" if error else "SUCCESS"
        self.traces.append(span)

        if len(self.traces) > 200:
            self.traces.pop(0)

        logger.debug("Trace [%s]: completed in %sms with status %s", span["name"], latency_ms, span["status"])

    def get_recent_traces(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self.traces[-limit:]

agent_tracer = AgentExecutionTracer()
