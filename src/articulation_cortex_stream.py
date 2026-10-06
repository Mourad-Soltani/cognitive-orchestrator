"""True Streaming Articulation — per-chunk logistic decay."""

import asyncio
import math
from typing import AsyncGenerator, List, Optional


class ArticulationCortexStream:
    """Paced token streamer with logistic temperature decay and human-like pauses.

    Temperature schedule (matches ArticulationCortex):
        temp(step) = T_end + (T_start - T_end) / (1 + exp(k * (step - midpoint)))

    At step=0 → ≈ T_start (creative). At midpoint → halfway. As step→∞ → T_end (coherent).
    """

    def __init__(
        self,
        temp_start: float = 1.2,
        temp_end: float = 0.3,
        midpoint: float = 5.0,
        steepness: float = 0.5,
        human_pause_chunk: int = 3,
        pause_duration: float = 0.2,
        word_chunk_size: int = 8,
    ):
        self.temp_start = temp_start
        self.temp_end = temp_end
        self.midpoint = midpoint
        self.steepness = steepness
        self.human_pause_chunk = human_pause_chunk
        self.pause_duration = pause_duration
        self.word_chunk_size = word_chunk_size

    def logistic_temp(self, step: int) -> float:
        """Logistic decay: high creativity early, high coherence later."""
        return self.temp_end + (self.temp_start - self.temp_end) / (
            1 + math.exp(self.steepness * (step - self.midpoint))
        )

    async def stream(
        self,
        token_generator: AsyncGenerator[str, None],
        word_chunk_size: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        """Yield paced text chunks from an upstream token generator.

        Args:
            token_generator: Async generator yielding token/word strings.
            word_chunk_size: Override default chunk size (words per yield).
        """
        size = word_chunk_size if word_chunk_size is not None else self.word_chunk_size
        buffer: List[str] = []
        word_count = 0
        chunk_index = 0

        async for token in token_generator:
            buffer.append(token)
            if token.endswith((" ", "\n")) or " " in token:
                word_count += max(1, token.count(" "))

            if word_count >= size or len(buffer) > 80:
                chunk_text = "".join(buffer)
                yield chunk_text
                buffer = []
                word_count = 0
                chunk_index += 1

                if chunk_index == self.human_pause_chunk and self.pause_duration > 0:
                    await asyncio.sleep(self.pause_duration)

        if buffer:
            yield "".join(buffer)
