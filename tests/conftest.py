"""Pytest fixtures and configuration."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from openai import AsyncOpenAI

from src.orchestrator import CognitiveOrchestrator
from src.somatic_arbiter import SomaticArbiter
from src.dialectic_council import DialecticCouncil
from src.recency_buffer import RecencyBuffer
from src.insight_spike import InsightSpike
from src.articulation_cortex import ArticulationCortex
from src.models import Intuition, DialecticOutput, Thesis


@pytest.fixture
def mock_openai_client():
    """Return a fully mocked AsyncOpenAI client."""
    client = MagicMock(spec=AsyncOpenAI)
    client.chat = MagicMock()
    client.chat.completions = MagicMock()
    return client


@pytest.fixture
def sample_intuitions():
    """Return a diverse set of 5 intuitions for testing."""
    return [
        Intuition(
            mode="Logical", score=0.9,
            one_liner="Break into sub-tasks",
            urgency=0.8, risk=0.2, novelty=0.1,
        ),
        Intuition(
            mode="Empathetic", score=0.7,
            one_liner="Acknowledge frustration",
            urgency=0.6, risk=0.3, novelty=0.2,
        ),
        Intuition(
            mode="Creative", score=0.6,
            one_liner="Flip constraint to feature",
            urgency=0.4, risk=0.7, novelty=0.9,
        ),
        Intuition(
            mode="Cautious", score=0.8,
            one_liner="Verify assumptions",
            urgency=0.5, risk=0.1, novelty=0.1,
        ),
        Intuition(
            mode="Opportunistic", score=0.5,
            one_liner="Pivot to upsell",
            urgency=0.3, risk=0.8, novelty=0.6,
        ),
    ]


@pytest.fixture
def sample_debate():
    """Return a sample dialectic output."""
    return DialecticOutput(
        option_a_argument="Speed is critical for user retention",
        option_b_counter="But accuracy prevents costly rollbacks",
        synthesis="Ship fast with feature flags and rollback capability",
    )
