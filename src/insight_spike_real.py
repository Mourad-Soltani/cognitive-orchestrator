"""Real Insight Spike — tiktoken-based logit bias injection."""

import numpy as np
import tiktoken
from typing import Dict


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
        try:
            self.encoder = tiktoken.encoding_for_model(model_name)
        except KeyError:
            self.encoder = tiktoken.get_encoding("cl100k_base")

    def inject(self, prompt: str) -> Dict:
        z = float(np.random.normal(0, self.noise_std))
        insight_event = abs(z) > self.threshold

        logit_bias = {}
        boosted_token = None

        if insight_event and prompt:
            tokens = self.encoder.encode(prompt)
            if tokens:
                idx = int(np.random.randint(0, len(tokens)))
                token_id = tokens[idx]
                logit_bias[str(token_id)] = self.boost_value
                boosted_token = self.encoder.decode([token_id])

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
