"""True Streaming Articulation — per-chunk logistic decay."""

import asyncio
import math
from typing import AsyncGenerator, List


class ArticulationCortexStream:
    def __init__(
        self,
        temp_start: float = 1.2,
        temp_end: float = 0.3,
        midpoint: float = 5.0,
        steepness: float = 0.5,
        human_pause_chunk: int = 3,
        pause_duration: float = 0.2,
    ):
        self.temp_start = temp_start
        self.temp_end = temp_end
        self.midpoint = midpoint
        self.steepness = steepness
        self.human_pause_chunk = human_pause_chunk
        self.pause_duration = pause_duration

    def logistic_temp(self, step: int) -> float:
        return self.temp_start - (self.temp_start - self.temp_end) / (
            1 + math.exp(self.steepness * (step - self.midpoint))
        )

    async def stream(
        self,
        token_generator: AsyncGenerator[str, None],
        word_chunk_size: int = 8,
    ) -> AsyncGenerator[str, None]:
        buffer: List[str] = []
        word_count = 0
        chunk_index = 0

        async for token in token_generator:
            buffer.append(token)
            if token.endswith((" ", "\n")):
                word_count += 1

            if word_count >= word_chunk_size or len(buffer) > 80:
                chunk_text = "".join(buffer)
                yield chunk_text
                buffer = []
                word_count = 0
                chunk_index += 1

                if chunk_index == self.human_pause_chunk:
                    await asyncio.sleep(self.pause_duration)

        if buffer:
            yield "".join(buffer)
