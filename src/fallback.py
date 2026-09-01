"""Graceful degradation for LLM failures."""

import logging
import random
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

FALLBACK_RESPONSES = [
    "I am experiencing high cognitive load. Let me think simply.",
    "My circuits are overloaded. Here's a simple, direct answer.",
    "I need a moment to integrate. For now, here is my core intuition.",
    "Cognitive bandwidth exceeded. Proceeding with a heuristic response.",
]


def get_fallback_response(error: Optional[Exception] = None) -> Dict[str, Any]:
    message = random.choice(FALLBACK_RESPONSES)
    logger.warning("Fallback triggered: %s", error)
    return {
        "final_output": message,
        "error": str(error) if error else "Timeout or LLM failure",
        "insight_event": False,
        "fallback": True,
    }
