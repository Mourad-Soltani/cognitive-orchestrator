"""The Articulation Cortex — The Pacing Engine.

Instead of streaming raw output, implements a buffered streamer
with logistic temperature decay and human-like pauses.

temp(chunk) = 1.2 - (1.2 - 0.3) / (1 + exp(0.5 * (chunk_index - 5)))

See PDF §3.6 (Articulation Cortex) for derivation.
"""

import math
import asyncio
from typing import AsyncIterator

from openai import AsyncOpenAI

from src.models import ArticulationChunk
from src.config import settings
from src.telemetry import emit_event


class ArticulationCortex:
    """Paced output generator with logistic temperature decay."""

    def __init__(self, client: AsyncOpenAI | None = None):
        self.client = client or AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        self.model = settings.openai_model

    async def articulate(
        self,
        synthesis: str,
        session_id: str,
        insight_boost: float = 0.0,
    ) -> AsyncIterator[ArticulationChunk]:
        """Generate paced, temperature-modulated output chunks.

        Yields ArticulationChunk objects with per-chunk temperature
        and optional human-like delays.

        Args:
            synthesis: The merged stance from the Dialectic Council
            session_id: For telemetry
            insight_boost: Additional temperature from Insight Spike

        Yields:
            ArticulationChunk with text, temperature, and delay info
        """
        # For the RI, we simulate chunking by generating the full
        # response and then splitting it. In production, this would
        # use the streaming API with real-time temperature switching.

        full_text = await self._generate_full(synthesis, insight_boost, session_id)
        chunks = self._chunk_text(full_text, chunk_size=8)

        for idx, chunk_text in enumerate(chunks):
            temp = self._compute_temperature(idx) + insight_boost
            temp = max(0.0, min(2.0, temp))

            delay = None
            if idx == 3:  # Human pause between 3rd and 4th chunk
                delay = 0.2
                await asyncio.sleep(delay)

            chunk = ArticulationChunk(
                index=idx,
                text=chunk_text,
                temperature=round(temp, 4),
                delay_ms=round(delay * 1000, 1) if delay else None,
            )

            emit_event(
                event_type="articulation_chunk",
                session_id=session_id,
                payload=chunk.model_dump(),
            )

            yield chunk

    async def _generate_full(
        self,
        synthesis: str,
        insight_boost: float,
        session_id: str,
    ) -> str:
        """Generate the full response text.

        Uses the starting temperature (highest) for the API call.
        In production, this would be replaced with per-token
        temperature control via logit_bias or multiple API calls.
        """
        temp = settings.articulation_temp_start + insight_boost
        temp = max(0.0, min(2.0, temp))

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are the Articulation Cortex. "
                        "Speak clearly, with human-like pacing. "
                        "Do not use bullet points. Write flowing prose."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Articulate this synthesis naturally:\n{synthesis}",
                },
            ],
            temperature=temp,
            max_tokens=settings.articulation_max_tokens,
        )

        text = response.choices[0].message.content or ""

        emit_event(
            event_type="articulation_complete",
            session_id=session_id,
            payload={
                "temperature_used": temp,
                "insight_boost": insight_boost,
                "output_length_chars": len(text),
            },
        )

        return text

    def _chunk_text(self, text: str, chunk_size: int = 8) -> list[str]:
        """Split text into word chunks."""
        words = text.split()
        if not words:
            return [""]
        chunks = []
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i : i + chunk_size])
            chunks.append(chunk)
        return chunks

    def _compute_temperature(self, chunk_index: int) -> float:
        """Logistic decay function for per-chunk temperature.

        temp = T_start - (T_start - T_end) / (1 + exp(k * (chunk_index - midpoint)))

        Where:
        - T_start = 1.2 (high creativity at start)
        - T_end = 0.3 (low creativity / high coherence at end)
        - k = 0.5 (steepness)
        - midpoint = 5 (inflection point)
        """
        t_start = settings.articulation_temp_start
        t_end = settings.articulation_temp_end
        k = 0.5
        midpoint = 5

        decay = (t_start - t_end) / (1 + math.exp(k * (chunk_index - midpoint)))
        temp = t_start - decay
        return temp
