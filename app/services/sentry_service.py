import os
import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("trailmates.sentry")

try:
    import sentry_sdk
    from sentry_sdk.integrations.logging import LoggingIntegration
    HAS_SENTRY = True
except ImportError:
    HAS_SENTRY = False

# Global list of in-memory traces for transparency / dev UI inspection
IN_MEMORY_TRACES = []

def init_sentry():
    dsn = os.getenv("SENTRY_DSN", "")
    if dsn and HAS_SENTRY:
        sentry_sdk.init(
            dsn=dsn,
            traces_sample_rate=1.0,
            profiles_sample_rate=1.0,
            environment=os.getenv("ENVIRONMENT", "development"),
            release="trailmates@1.0.0"
        )
        logger.info("Sentry initialized with live DSN — spans will be sent to Sentry.")
    else:
        logger.info("SENTRY_DSN not set — recording spans in-memory only (dev mode).")


class AgentSpan:
    def __init__(self, name: str, op: str, description: str = ""):
        self.name = name
        self.op = op
        self.description = description
        self.start_time = 0
        self.end_time = 0
        self.duration_ms = 0
        self.data: Dict[str, Any] = {}
        self.status = "ok"

    def __enter__(self):
        self.start_time = time.time()
        return self

    def set_data(self, key: str, value: Any):
        self.data[key] = value

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.duration_ms = round((self.end_time - self.start_time) * 1000, 2)
        if exc_type:
            self.status = "error"
            self.set_data("error.message", str(exc_val))

        trace_entry = {
            "span_name": self.name,
            "op": self.op,
            "description": self.description,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "metadata": self.data,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        IN_MEMORY_TRACES.append(trace_entry)
        # Keep max 50 recent spans
        if len(IN_MEMORY_TRACES) > 50:
            IN_MEMORY_TRACES.pop(0)

        logger.info(f"[Sentry Span] {self.op} | {self.name} | {self.duration_ms}ms | status={self.status}")
