"""Tests for the real tiktoken-based insight spike."""

import pytest
from src.insight_spike_real import InsightSpikeReal


def test_insight_spike_injects_logit_bias_when_threshold_met():
    spike = InsightSpikeReal(noise_std=0.01, threshold=0.0)  # force insight
    result = spike.inject("Hello world, this is a test.")
    assert "logit_bias" in result
    assert result["insight_event"] is True
    assert isinstance(result["logit_bias"], dict)
    assert len(result["logit_bias"]) >= 1
    assert result["boosted_token"] is not None


def test_insight_spike_no_injection_when_threshold_not_met():
    spike = InsightSpikeReal(noise_std=0.01, threshold=10.0)  # never trigger
    result = spike.inject("Hello world, this is a test.")
    assert result["insight_event"] is False
    assert result["logit_bias"] == {}
    assert result["boosted_token"] is None


def test_insight_spike_empty_prompt():
    spike = InsightSpikeReal()
    result = spike.inject("")
    assert result["logit_bias"] == {}
    assert result["boosted_token"] is None
    assert isinstance(result["z"], float)


def test_insight_spike_apply_to_kwargs():
    spike = InsightSpikeReal(noise_std=0.01, threshold=0.0)
    kwargs = {"temperature": 0.7}
    new_kwargs, result = spike.apply_to_kwargs("test prompt", kwargs)
    assert "logit_bias" in new_kwargs
    assert new_kwargs["temperature"] == 0.7  # preserved
    assert result["insight_event"] is True
