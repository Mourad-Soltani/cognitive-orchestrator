"""Structured JSON logging — the Behavioral Black Box.

Every decision the Agent makes emits a structured JSON log
(timestamp, tensors, pruned options, temperature values).
"""

import structlog
import uuid
from datetime import datetime, timezone
from typing import Any

from src.config import settings


structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer() if settings.log_format == "json" else structlog.dev.ConsoleRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger("cognitive_orchestrator")


def emit_event(
    event_type: str,
    session_id: str,
    payload: dict[str, Any],
    log_id: str | None = None,
) -> str:
    """Emit a structured telemetry event.

    Args:
        event_type: Category of event (e.g., "intuition_pruned", "insight_spike")
        session_id: Unique session identifier
        payload: Arbitrary JSON-serializable data
        log_id: Optional explicit log ID

    Returns:
        The log_id used for this event
    """
    lid = log_id or str(uuid.uuid4())
    logger.info(
        event_type,
        log_id=lid,
        session_id=session_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        payload=payload,
    )
    return lid


def emit_forget_event(
    session_id: str,
    forgotten_thesis: dict[str, Any],
    buffer_state: list[dict[str, Any]],
) -> str:
    """Log the exact memory dump that was discarded.

    This proves bounded recall is intentional, not hallucination.
    """
    return emit_event(
        event_type="memory_forgotten",
        session_id=session_id,
        payload={
            "forgotten": forgotten_thesis,
            "buffer_after": buffer_state,
            "reason": "bounded_recall_maxlen_exceeded",
        },
    )
