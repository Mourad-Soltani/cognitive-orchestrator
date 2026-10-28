"""Insight Spike — Gaussian gate + content-aware logit bias.

Still intentionally stochastic (System-1 noise). When triggered, prefers
boosting a content-bearing token from the synthesis rather than a random
punctuation/stopword id.
"""

from __future__ import annotations

from typing import Dict

import numpy as np

try:
    import tiktoken
except Exception:  # pragma: no cover
    tiktoken = None  # type: ignore

_STOP = {
    "the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "is", "are",
    "be", "as", "at", "by", "it", "this", "that", "with", "from", "we", "you",
}


class InsightSpikeReal:
    def __init__(
        self,
        model_name: str = "gpt-4o-mini",
        noise_std: float = 0.1,
        threshold: float = 0.3,
        boost_value: float = 5.0,
    ):
        self.noise_std = noise_std
        self.threshold = threshold
        self.boost_value = boost_value
        self.encoder = None
        if tiktoken is not None:
            try:
                self.encoder = tiktoken.encoding_for_model(model_name)
            except KeyError:
                self.encoder = tiktoken.get_encoding("cl100k_base")

    def inject(self, prompt: str) -> Dict:
        z = float(np.random.normal(0, self.noise_std))
        insight_event = abs(z) > self.threshold

        logit_bias: dict = {}
        boosted_token = None

        if insight_event and prompt:
            words = [w.strip(".,;:!?\"'()[]{}") for w in prompt.split()]
            candidates = [w for w in words if len(w) > 3 and w.lower() not in _STOP]
            if not candidates:
                candidates = [w for w in words if w]
            if candidates:
                weights = np.array([len(w) for w in candidates], dtype=float)
                weights = weights / weights.sum()
                chosen = str(np.random.choice(candidates, p=weights))
                boosted_token = chosen
                if self.encoder is not None:
                    tokens = self.encoder.encode(chosen)
                    if tokens:
                        token_id = tokens[0]
                        logit_bias[str(token_id)] = self.boost_value
                        boosted_token = self.encoder.decode([token_id])
                else:
                    # Fallback id: stable hash bucket for offline/demo without tiktoken
                    logit_bias[str(abs(hash(chosen)) % 100000)] = self.boost_value

        return {
            "z": z,
            "insight_event": bool(insight_event),
            "logit_bias": logit_bias,
            "boosted_token": boosted_token,
        }

    def apply_to_kwargs(self, prompt: str, kwargs: Dict) -> tuple[Dict, Dict]:
        result = self.inject(prompt)
        if result["logit_bias"]:
            kwargs = {**kwargs, "logit_bias": result["logit_bias"]}
        return kwargs, result
