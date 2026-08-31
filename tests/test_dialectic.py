"""Tests for the Dialectic Council."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.dialectic_council import DialecticCouncil
from src.models import Intuition, DialecticOutput


class TestDialecticCouncil:
    """Unit tests for debate generation and parsing."""

    @pytest.fixture
    def council(self, mock_openai_client):
        return DialecticCouncil(client=mock_openai_client)

    def test_parse_debate_standard_format(self, council):
        raw = (
            "Option A says: Speed wins | "
            "Option B counters: Accuracy prevents rollback | "
            "Synthesis: Ship with feature flags |"
        )
        result = council._parse_debate(raw)
        assert result.option_a_argument == "Speed wins"
        assert result.option_b_counter == "Accuracy prevents rollback"
        assert result.synthesis == "Ship with feature flags"

    def test_parse_debate_fallback_on_malformed(self, council):
        raw = "This is just random text without the expected format"
        result = council._parse_debate(raw)
        assert result.synthesis == raw

    def test_parse_debate_partial_format(self, council):
        raw = "Option A says: Only A present | Synthesis: Merge anyway |"
        result = council._parse_debate(raw)
        assert result.option_a_argument == "Only A present"
        assert result.option_b_counter == "No counter extracted"
        assert result.synthesis == "Merge anyway"

    @pytest.mark.asyncio
    async def test_debate_calls_api_with_stop_sequence(self, council, mock_openai_client):
        """Verify the API is called with the configured stop sequence."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = (
            "Option A says: Test | Option B counters: Counter | Synthesis: Synth |"
        )
        mock_response.usage = MagicMock(total_tokens=42)
        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)

        option_a = Intuition(
            mode="Logical", score=0.9, one_liner="Be fast",
            urgency=0.8, risk=0.2, novelty=0.1,
        )
        option_b = Intuition(
            mode="Cautious", score=0.8, one_liner="Be safe",
            urgency=0.5, risk=0.1, novelty=0.1,
        )

        result = await council.debate(
            option_a=option_a,
            option_b=option_b,
            user_input="Test input",
            session_id="sess-test",
        )

        assert isinstance(result, DialecticOutput)
        call_kwargs = mock_openai_client.chat.completions.create.call_args.kwargs
        assert "stop" in call_kwargs
        assert "|" in call_kwargs["stop"]
