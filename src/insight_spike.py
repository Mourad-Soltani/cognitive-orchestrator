"""The Insight Spike — Noise Injection.

Before the final output stream, generate a random latent vector
z ~ N(0, 0.1). During the Articulation Cortex call, this noise
is used to skew the first 5 tokens via logit_bias.

If the generated first token has probability < 0.3, flag as Insight.

See PDF §3.5 (Insight Spike) for mathematical derivation.
"""

import math
import random
from typing import Optional

import numpy as np

from src.models import InsightEvent
from src.config import settings
from src.telemetry import emit_event


class InsightSpike:
    """Generates and evaluates noise-induced insight events."""

    def __init__(self, seed: int | None = None):
        self.rng = random.Random(seed)
        self._noise: list[float] = []

    def generate_noise(self, dim: int = 5) -> list[float]:
        """Sample z ~ N(0, σ²) where σ = insight_noise_std.

        Args:
            dim: Dimensionality of the noise vector (matches token skew count)

        Returns:
            List of float noise values
        """
        std = settings.insight_noise_std
        self._noise = [self.rng.gauss(0, std) for _ in range(dim)]
        return self._noise

    def build_logit_bias(self, vocab_size: int = 100256) -> dict[str, int]:
        """Build a logit_bias dict for OpenAI API.

        Since we cannot know token IDs ahead of time, this returns
        a conceptual bias map. In production, you would map noise
        to specific token IDs via the tokenizer.

        For the RI, we return an empty bias and rely on temperature
        manipulation in the Articulation Cortex to achieve the
        same stochastic effect.
        """
        # Reference implementation: conceptual bias
        # Production would use tiktoken to map noise to token IDs
        return {}

    def evaluate_first_token(
        self,
        token: str,
        token_prob: float | None,
        session_id: str,
    ) -> InsightEvent:
        """Evaluate whether the first token qualifies as an Insight.

        Args:
            token: The generated first token string
            token_prob: Log-probability of the token (if available)
            session_id: For telemetry

        Returns:
            InsightEvent with triggered flag
        """
        triggered = False
        if token_prob is not None and token_prob < settings.insight_threshold:
            triggered = True

        event = InsightEvent(
            triggered=triggered,
            noise_vector_sample=self._noise[:5] if self._noise else [],
            first_token_prob=token_prob,
            flagged_token=token if triggered else None,
        )

        emit_event(
            event_type="insight_spike",
            session_id=session_id,
            payload=event.model_dump(),
        )

        return event

    def get_temperature_boost(self) -> float:
        """Return a temporary temperature boost based on noise magnitude.

        Higher noise → higher temperature for first few tokens.
        """
        if not self._noise:
            return 0.0
        magnitude = math.sqrt(sum(n * n for n in self._noise)) / len(self._noise)
        return min(magnitude * 2.0, 0.5)  # cap at +0.5
