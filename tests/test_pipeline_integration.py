"""End-to-end pipeline with deterministic stub LLM stages (no network)."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock

from src.models import (
    ArticulationChunk,
    DialecticOutput,
    Intuition,
    OrchestratorRequest,
)
from src.orchestrator import CognitiveOrchestrator


class MemoryBuffer:
    def __init__(self):
        self.store: dict[str, list] = {}

    async def add(self, session_id: str, entry: dict) -> None:
        self.store.setdefault(session_id, []).append(entry)

    async def push(self, session_id: str, entry: dict) -> None:
        await self.add(session_id, entry)

    async def get(self, session_id: str):
        return self.store.get(session_id, [])

    async def close(self) -> None:
        return None


def _intuitions():
    return [
        Intuition(mode="Logical", score=0.9, one_liner="Ship a reversible slice", urgency=0.8, risk=0.2, novelty=0.1),
        Intuition(mode="Cautious", score=0.8, one_liner="Verify assumptions", urgency=0.6, risk=0.1, novelty=0.1),
        Intuition(mode="Empathetic", score=0.7, one_liner="Name the constraint", urgency=0.5, risk=0.3, novelty=0.2),
        Intuition(mode="Creative", score=0.5, one_liner="Reframe the constraint", urgency=0.3, risk=0.6, novelty=0.8),
        Intuition(mode="Opportunistic", score=0.4, one_liner="Narrow scope", urgency=0.2, risk=0.4, novelty=0.3),
    ]


@pytest.mark.asyncio
async def test_full_pipeline_stub_llm():
    orch = CognitiveOrchestrator()
    orch.buffer = MemoryBuffer()
    orch.arbiter.generate = AsyncMock(return_value=_intuitions())
    orch.council.debate = AsyncMock(
        return_value=DialecticOutput(
            option_a_argument="Speed preserves the window.",
            option_b_counter="Unchecked speed creates rollback cost.",
            synthesis="Ship the narrowest reversible version and measure it.",
        )
    )

    async def articulate(*args, **kwargs):
        yield ArticulationChunk(index=0, text="Ship the narrowest reversible version", temperature=1.1)
        yield ArticulationChunk(index=1, text="and measure it.", temperature=0.6)

    orch.cortex.articulate = articulate

    resp = await orch.process(OrchestratorRequest(user_input="Should I pivot?", session_id="itest"))
    assert resp.final_output
    assert len(resp.top_intuitions) >= 1
    assert resp.top_intuitions[0].intuition.mode in {
        "Logical", "Cautious", "Empathetic", "Creative", "Opportunistic"
    }
    assert resp.latency_ms >= 0
    assert resp.session_id == "itest"
