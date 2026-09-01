"""The Core Orchestrator — The 150ms Clock.

Now with:
- Pluggable LLM client (OpenAI / Groq)
- Redis-backed recency buffer
- Real tiktoken insight spike
- Graceful fallback on failure
"""

import asyncio
import time
import uuid
from datetime import datetime, timezone
from typing import Sequence, Optional

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
from src.llm_client import OpenAIClient, GroqClient, BaseLLMClient
from src.recency_buffer_redis import RecencyBufferRedis
from src.insight_spike_real import InsightSpikeReal
from src.articulation_cortex import ArticulationCortex
from src.fallback import get_fallback_response


class CognitiveOrchestrator:
    """Main orchestrator managing the full cognitive pipeline."""

    def __init__(self, client: Optional[AsyncOpenAI] = None):
        # --- NEW: Abstracted LLM layer ---
        if settings.llm_provider == "groq" and settings.groq_api_key:
            self.llm: BaseLLMClient = GroqClient(
                api_key=settings.groq_api_key,
                model=settings.groq_model,
                timeout=settings.orchestrator_timeout_ms / 1000,
            )
        else:
            self.llm = OpenAIClient(
                api_key=settings.openai_api_key,
                model=settings.openai_model,
                timeout=settings.orchestrator_timeout_ms / 1000,
            )

        # Legacy components still expect AsyncOpenAI; extract it when using OpenAI
        openai_client = None
        if isinstance(self.llm, OpenAIClient):
            openai_client = self.llm.client
        elif client:
            openai_client = client

        self.arbiter = SomaticArbiter(client=openai_client)
        self.council = DialecticCouncil(client=openai_client)
        self.cortex = ArticulationCortex(client=openai_client)

        # --- NEW: Redis buffer + real insight spike ---
        self.buffer = RecencyBufferRedis(
            redis_url=settings.redis_url,
            maxlen=settings.buffer_maxlen,
        )
        self.spike = InsightSpikeReal(
            model_name=settings.openai_model,
            noise_std=settings.insight_noise_std,
            threshold=settings.insight_threshold,
        )

    async def process(self, request: OrchestratorRequest) -> OrchestratorResponse:
        """Process a user request through the full cognitive pipeline."""
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

        try:
            # --- Step 1: Somatic Arbiter (with timeout) ---
            intuitions = await self._run_arbiter(
                request.user_input,
                session_id,
                request.context_override,
            )

            # --- Step 2: Pruner ---
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
                    context=await self._get_context(session_id),
                )
            else:
                debate = DialecticOutput(
                    option_a_argument="Single intuition dominant",
                    option_b_counter="No counter available",
                    synthesis=top_intuitions[0].intuition.one_liner if top_intuitions else "No output",
                )

            # --- Step 4: Recency Buffer (Redis) ---
            await self.buffer.add(session_id, {
                "user_input": request.user_input,
                "final_output": debate.synthesis,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

            # --- Step 5: Insight Spike (real logit bias ready) ---
            insight_data = self.spike.inject(debate.synthesis)
            insight_boost = abs(insight_data["z"]) * 2.0 if insight_data["insight_event"] else 0.0

            insight_event = InsightEvent(
                triggered=insight_data["insight_event"],
                noise_vector_sample=[insight_data["z"]],
                first_token_prob=None,
                flagged_token=insight_data.get("boosted_token"),
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

            latency_ms = (time.perf_counter() - start_time) * 1000

            emit_event(
                event_type="orchestrator_complete",
                session_id=session_id,
                payload={
                    "latency_ms": round(latency_ms, 2),
                    "final_output_length": len(final_output),
                    "chunks_count": len(chunks),
                    "insight_z": insight_data["z"],
                    "boosted_token": insight_data.get("boosted_token"),
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

        except Exception as e:
            emit_event(
                event_type="orchestrator_error",
                session_id=session_id,
                payload={"error": str(e)},
                log_id=log_id,
            )
            fallback = get_fallback_response(e)
            return OrchestratorResponse(
                final_output=fallback["final_output"],
                top_intuitions=[],
                dialectic_summary=fallback["error"],
                insight_event=InsightEvent(triggered=False, noise_vector_sample=[]),
                session_id=session_id,
                latency_ms=round((time.perf_counter() - start_time) * 1000, 2),
                log_id=log_id,
            )
        finally:
            await self.buffer.close()

    async def _run_arbiter(
        self,
        user_input: str,
        session_id: str,
        context_override: str | None,
    ) -> Sequence[Intuition]:
        timeout_sec = settings.orchestrator_timeout_ms / 1000.0
        context = context_override or await self._get_context(session_id)

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

    async def _get_context(self, session_id: str) -> str | None:
        items = await self.buffer.get(session_id)
        if not items:
            return None
        parts = []
        for item in items:
            text = item.get("user_input", "") or item.get("final_output", "")
            parts.append(str(text)[:200])
        return " | ".join(parts)

    def _safe_defaults(self) -> Sequence[Intuition]:
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
