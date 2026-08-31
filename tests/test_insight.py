"""Tests for the Insight Spike."""

import pytest
import math

from src.insight_spike import InsightSpike
from src.config import settings


class TestInsightSpike:
    """Unit tests for noise generation and insight detection."""

    def test_noise_vector_length(self):
        spike = InsightSpike(seed=42)
        noise = spike.generate_noise(dim=5)
        assert len(noise) == 5

    def test_noise_is_gaussian(self):
        """Statistical sanity: mean ≈ 0, std ≈ σ over many samples."""
        spike = InsightSpike(seed=123)
        samples = []
        for _ in range(1000):
            noise = spike.generate_noise(dim=1)
            samples.append(noise[0])

        mean = sum(samples) / len(samples)
        variance = sum((x - mean) ** 2 for x in samples) / len(samples)
        std = math.sqrt(variance)

        assert abs(mean) < 0.1  # Should be close to 0
        assert abs(std - settings.insight_noise_std) < 0.05

    def test_insight_triggered_on_low_probability(self):
        spike = InsightSpike(seed=42)
        spike.generate_noise(dim=5)
        event = spike.evaluate_first_token(
            token="unexpected",
            token_prob=0.2,  # Below threshold 0.3
            session_id="sess-test",
        )
        assert event.triggered is True
        assert event.flagged_token == "unexpected"

    def test_insight_not_triggered_on_high_probability(self):
        spike = InsightSpike(seed=42)
        spike.generate_noise(dim=5)
        event = spike.evaluate_first_token(
            token="the",
            token_prob=0.95,  # Well above threshold
            session_id="sess-test",
        )
        assert event.triggered is False
        assert event.flagged_token is None

    def test_temperature_boost_positive(self):
        spike = InsightSpike(seed=42)
        spike.generate_noise(dim=5)
        boost = spike.get_temperature_boost()
        assert boost >= 0.0
        assert boost <= 0.5  # Capped

    def test_deterministic_with_same_seed(self):
        spike1 = InsightSpike(seed=42)
        spike2 = InsightSpike(seed=42)
        n1 = spike1.generate_noise(dim=5)
        n2 = spike2.generate_noise(dim=5)
        assert n1 == n2
