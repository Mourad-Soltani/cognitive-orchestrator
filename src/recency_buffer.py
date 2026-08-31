"""The Recency Buffer — Bounded State Management.

Uses collections.deque(maxlen=3) to hold last 3 interactions.
When full, the oldest item is compressed into a 50-word thesis
and the true oldest is discarded (with telemetry).

See PDF §3.4 (Recency Buffer) for derivation.
"""

import asyncio
from collections import deque
from typing import Optional

from openai import AsyncOpenAI

from src.models import Thesis, DialecticOutput
from src.config import settings
from src.telemetry import emit_event, emit_forget_event


COMPRESSION_PROMPT = """Compress the following debate into a single thesis of at most {max_words} words.
Preserve the core decision, the winning intuition, and any constraints.

Debate:
{debate_text}

Thesis:"""


class RecencyBuffer:
    """Bounded recall buffer with intentional forgetting."""

    def __init__(self, client: AsyncOpenAI | None = None):
        self._buffer: deque[Thesis] = deque(maxlen=settings.buffer_maxlen)
        self.client = client or AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        self.model = settings.openai_model

    @property
    def state(self) -> list[Thesis]:
        """Current buffer state (newest first)."""
        return list(self._buffer)

    @property
    def context_string(self) -> str | None:
        """Concatenated context for injection into prompts."""
        if not self._buffer:
            return None
        return " | ".join(t.content for t in self._buffer)

    async def push(
        self,
        debate: DialecticOutput,
        session_id: str,
    ) -> Thesis:
        """Compress a debate and push into the buffer.

        If the buffer is full, the oldest item is evicted.
        The eviction is logged as proof of bounded recall.
        """
        # Check if we will evict
        will_evict = len(self._buffer) >= self._buffer.maxlen
        evicted: Optional[Thesis] = None
        if will_evict:
            evicted = self._buffer[0]  # oldest (leftmost)

        # Compress debate into thesis
        thesis = await self._compress(debate, session_id)

        # Push (eviction happens automatically via maxlen)
        self._buffer.append(thesis)

        # Log eviction if it happened
        if evicted:
            emit_forget_event(
                session_id=session_id,
                forgotten_thesis=evicted.model_dump(),
                buffer_state=[t.model_dump() for t in self.state],
            )

        emit_event(
            event_type="buffer_push",
            session_id=session_id,
            payload={
                "thesis": thesis.model_dump(),
                "buffer_len": len(self._buffer),
                "evicted": evicted.model_dump() if evicted else None,
            },
        )

        return thesis

    async def _compress(
        self,
        debate: DialecticOutput,
        session_id: str,
    ) -> Thesis:
        """Cheap LLM call to squash debate into ≤50 words."""
        debate_text = f"{debate.option_a_argument} vs {debate.option_b_counter} => {debate.synthesis}"

        prompt = COMPRESSION_PROMPT.format(
            max_words=settings.compression_max_words,
            debate_text=debate_text,
        )

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You compress debates into concise theses."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=100,
            temperature=0.3,
        )

        content = (response.choices[0].message.content or "").strip()
        # Hard truncate to word count
        words = content.split()
        if len(words) > settings.compression_max_words:
            content = " ".join(words[:settings.compression_max_words])

        thesis = Thesis(
            content=content,
            source_debate=debate_text[:300],
        )

        emit_event(
            event_type="compression_complete",
            session_id=session_id,
            payload={
                "original_length_chars": len(debate_text),
                "compressed_length_words": len(content.split()),
                "thesis_preview": content[:100],
            },
        )

        return thesis
