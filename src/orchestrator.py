"""The Core Orchestrator — The 150ms Clock.

Spawns 5 sub-agent calls concurrently using asyncio.gather().
Enforces asyncio.timeout(0.15) on the entire first pass.
If the Somatic Arbiter doesn't finish, defaults to safe options.

See PDF §3.1 (Core Orchestrator) for derivation.
"""

import asyncio
import time
import uuid
from typing import Sequence

from openai import AsyncOpenAI

from src.models import (
    Intuition,
    PrunedIntuition,
    DialecticOutput,
    InsightEvent,
    OrchestratorRequest,
    OrchestratorResponse,
)
from src.config import settings
from src.telemetry import emit_event
from src.pruner import prune_intuitions
from src.somatic_arbiter import SomaticArbiter
from src.dialectic_council import DialecticCouncil
from src.recency_buffer import RecencyBuffer
from src.insight_spike import InsightSpike
from src.articulation_cortex import ArticulationCortex


class CognitiveOrchestrator:
    """Main orchestrator managing the full cognitive pipeline."""

    def __init__(self, client: AsyncOpenAI | None = None):
        self.client = client or AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        self.arbiter = SomaticArbiter(client=self.client)
        self.council = DialecticCouncil(client=self.client)
        self.buffer = RecencyBuffer(client=self.client)
        self.spike = InsightSpike()
        self.cortex = ArticulationCortex(client=self.client)

    async def process(self, request: OrchestratorRequest) -> OrchestratorResponse:
        """Process a user request through the full cognitive pipeline.

        Pipeline:
        1. Somatic Arbiter (batched, 5 intuitions)
        2. Pruner (deterministic, top-2)
        3. Dialectic Council (constrained debate)
        4. Recency Buffer (compression + state update)
        5. Insight Spike (noise injection)
        6. Articulation Cortex (paced output)

        Args:
            request: Validated user request

        Returns:
            OrchestratorResponse with full telemetry
        """
        session_id = request.session_id or str(uuid.uuid4())
        log_id = str(uuid.uuid4())
        start_time = time.perf_counter()

        emit_event(
            event_type="orchestrator_start",
            session_id=session_id,
            payload={
                "user_input": request.user_input,
                "log_id": log_id,
                "context_override": request.context_override is not None,
            },
            log_id=log_id,
        )

        # --- Step 1: Somatic Arbiter (with 150ms timeout) ---
        intuitions = await self._run_arbiter(
            request.user_input,
            session_id,
            request.context_override,
        )

        # --- Step 2: Pruner (deterministic, instant) ---
        top_intuitions = prune_intuitions(intuitions)

        emit_event(
            event_type="pruner_complete",
            session_id=session_id,
            payload={
                "top_k": len(top_intuitions),
                "pruned": [p.model_dump() for p in top_intuitions],
            },
        )

        # --- Step 3: Dialectic Council ---
        if len(top_intuitions) >= 2:
            debate = await self.council.debate(
                option_a=top_intuitions[0].intuition,
                option_b=top_intuitions[1].intuition,
                user_input=request.user_input,
                session_id=session_id,
                context=self.buffer.context_string,
            )
        else:
            # Fallback if pruning returned < 2
            debate = DialecticOutput(
                option_a_argument="Single intuition dominant",
                option_b_counter="No counter available",
                synthesis=top_intuitions[0].intuition.one_liner if top_intuitions else "No output",
            )

        # --- Step 4: Recency Buffer ---
        await self.buffer.push(debate, session_id)

        # --- Step 5: Insight Spike ---
        noise = self.spike.generate_noise(dim=5)
        insight_boost = self.spike.get_temperature_boost()

        # Evaluate first token (conceptual — in production, use logprobs)
        insight_event = InsightEvent(
            triggered=False,  # Will be updated if we get logprobs
            noise_vector_sample=noise,
        )

        # --- Step 6: Articulation Cortex ---
        chunks = []
        async for chunk in self.cortex.articulate(
            synthesis=debate.synthesis,
            session_id=session_id,
            insight_boost=insight_boost,
        ):
            chunks.append(chunk)

        final_output = " ".join(c.text for c in chunks)

        # Update insight event if first token was low probability
        # (In production, this would use the actual logprob from the API)
        # For RI, we simulate based on noise magnitude
        if insight_boost > 0.3:
            insight_event.triggered = True
            insight_event.first_token_prob = 0.25

        latency_ms = (time.perf_counter() - start_time) * 1000

        emit_event(
            event_type="orchestrator_complete",
            session_id=session_id,
            payload={
                "latency_ms": round(latency_ms, 2),
                "final_output_length": len(final_output),
                "chunks_count": len(chunks),
            },
            log_id=log_id,
        )

        return OrchestratorResponse(
            final_output=final_output,
            top_intuitions=top_intuitions,
            dialectic_summary=debate.synthesis,
            insight_event=insight_event,
            session_id=session_id,
            latency_ms=round(latency_ms, 2),
            log_id=log_id,
        )

    async def _run_arbiter(
        self,
        user_input: str,
        session_id: str,
        context_override: str | None,
    ) -> Sequence[Intuition]:
        """Run the Somatic Arbiter with a strict timeout.

        If the arbiter exceeds 150ms, return safe default intuitions.
        """
        timeout_sec = settings.orchestrator_timeout_ms / 1000.0
        context = context_override or self.buffer.context_string

        try:
            async with asyncio.timeout(timeout_sec):
                return await self.arbiter.generate(
                    user_input=user_input,
                    session_id=session_id,
                    context=context,
                )
        except asyncio.TimeoutError:
            emit_event(
                event_type="arbiter_timeout",
                session_id=session_id,
                payload={
                    "timeout_ms": settings.orchestrator_timeout_ms,
                    "fallback": "safe_defaults",
                },
            )
            return self._safe_defaults()

    def _safe_defaults(self) -> Sequence[Intuition]:
        """Pre-calculated safe options when arbiter times out."""
        return [
            Intuition(
                mode="Cautious",
                score=0.9,
                one_liner="Request clarification before proceeding",
                urgency=0.8,
                risk=0.1,
                novelty=0.1,
            ),
            Intuition(
                mode="Logical",
                score=0.8,
                one_liner="Break the request into verifiable steps",
                urgency=0.6,
                risk=0.2,
                novelty=0.1,
            ),
            Intuition(
                mode="Empathetic",
                score=0.7,
                one_liner="Acknowledge ambiguity and offer options",
                urgency=0.5,
                risk=0.3,
                novelty=0.2,
            ),
            Intuition(
                mode="Creative",
                score=0.4,
                one_liner="Reframe the problem from first principles",
                urgency=0.3,
                risk=0.6,
                novelty=0.8,
            ),
            Intuition(
                mode="Opportunistic",
                score=0.3,
                one_liner="Defer to user expertise",
                urgency=0.2,
                risk=0.4,
                novelty=0.3,
            ),
        ]
