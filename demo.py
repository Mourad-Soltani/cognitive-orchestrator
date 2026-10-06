"""Offline live demo and latency harness.

Runs the real orchestrator pipeline with mocked LLM stages and an in-memory
buffer so latency can be measured without API keys or Redis.

This measures orchestration overhead, not provider round-trip time.
"""

from __future__ import annotations

import asyncio
import json
import statistics
import time
from pathlib import Path
from unittest.mock import AsyncMock

from src.models import ArticulationChunk, DialecticOutput, Intuition, OrchestratorRequest
from src.orchestrator import CognitiveOrchestrator


CASES = [
    "Should I pivot my startup?",
    "Is this vendor safe to onboard?",
    "Cut the roadmap to one bet.",
    "Respond to an angry enterprise customer.",
    "Choose between speed and auditability.",
]


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


def _intuitions() -> list[Intuition]:
    return [
        Intuition(mode="Logical", score=0.9, one_liner="Break it into verifiable steps", urgency=0.8, risk=0.2, novelty=0.1),
        Intuition(mode="Cautious", score=0.8, one_liner="Verify assumptions before acting", urgency=0.6, risk=0.1, novelty=0.1),
        Intuition(mode="Empathetic", score=0.7, one_liner="Name the constraint the user feels", urgency=0.5, risk=0.3, novelty=0.2),
        Intuition(mode="Creative", score=0.5, one_liner="Reframe the constraint as a feature", urgency=0.3, risk=0.6, novelty=0.8),
        Intuition(mode="Opportunistic", score=0.4, one_liner="Use the decision to narrow scope", urgency=0.2, risk=0.4, novelty=0.3),
    ]


async def run_demo(iterations: int = 50) -> dict:
    orchestrator = CognitiveOrchestrator()
    orchestrator.buffer = MemoryBuffer()
    orchestrator.arbiter.generate = AsyncMock(return_value=_intuitions())
    orchestrator.council.debate = AsyncMock(
        return_value=DialecticOutput(
            option_a_argument="Speed preserves the window.",
            option_b_counter="Unchecked speed creates rollback cost.",
            synthesis="Ship the narrowest reversible version and measure it.",
        )
    )

    async def articulate(*args, **kwargs):
        yield ArticulationChunk(index=0, text="Ship the narrowest reversible version", temperature=1.1)
        yield ArticulationChunk(index=1, text="and measure it.", temperature=0.6)

    orchestrator.cortex.articulate = articulate

    samples = []
    preview = None
    for i in range(iterations):
        request = OrchestratorRequest(user_input=CASES[i % len(CASES)], session_id="demo-session")
        started = time.perf_counter()
        response = await orchestrator.process(request)
        elapsed = (time.perf_counter() - started) * 1000
        samples.append(elapsed)
        if preview is None:
            preview = {
                "input": request.user_input,
                "output": response.final_output,
                "top_modes": [p.intuition.mode for p in response.top_intuitions],
                "insight_triggered": response.insight_event.triggered,
                "reported_latency_ms": response.latency_ms,
            }

    samples_sorted = sorted(samples)
    def pct(p: float) -> float:
        idx = min(len(samples_sorted) - 1, max(0, int(round(p * (len(samples_sorted) - 1)))))
        return samples_sorted[idx]

    report = {
        "mode": "offline_mocked_llm",
        "iterations": iterations,
        "note": "Measures local pipeline overhead with mocked arbiter, council, and cortex. Does not include provider network time.",
        "preview": preview,
        "latency_ms": {
            "min": round(min(samples), 3),
            "mean": round(statistics.mean(samples), 3),
            "median": round(statistics.median(samples), 3),
            "p95": round(pct(0.95), 3),
            "p99": round(pct(0.99), 3),
            "max": round(max(samples), 3),
        },
    }
    return report


def main() -> None:
    report = asyncio.run(run_demo())
    out = Path("reports")
    out.mkdir(exist_ok=True)
    (out / "latency.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
