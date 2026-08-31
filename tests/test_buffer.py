"""Tests for the Recency Buffer."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.recency_buffer import RecencyBuffer
from src.models import DialecticOutput, Thesis


class TestRecencyBuffer:
    """Unit tests for bounded recall and compression."""

    @pytest.fixture
    def buffer(self, mock_openai_client):
        return RecencyBuffer(client=mock_openai_client)

    def test_buffer_initially_empty(self, buffer):
        assert len(buffer.state) == 0
        assert buffer.context_string is None

    @pytest.mark.asyncio
    async def test_push_increases_buffer_size(self, buffer, sample_debate):
        with patch.object(buffer, "_compress", return_value=Thesis(content="Compressed")):
            await buffer.push(sample_debate, "sess-1")
        assert len(buffer.state) == 1

    @pytest.mark.asyncio
    async def test_buffer_respects_maxlen(self, buffer, sample_debate):
        """When maxlen is exceeded, oldest item is evicted."""
        with patch.object(buffer, "_compress", return_value=Thesis(content="T")):
            for i in range(5):
                debate = DialecticOutput(
                    option_a_argument=f"A{i}",
                    option_b_counter=f"B{i}",
                    synthesis=f"S{i}",
                )
                await buffer.push(debate, f"sess-{i}")

        assert len(buffer.state) == 3  # maxlen from settings

    @pytest.mark.asyncio
    async def test_compression_truncates_long_output(self, buffer, mock_openai_client):
        """Compression hard-truncates to max_words."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        # Return 100 words
        mock_response.choices[0].message.content = "word " * 100
        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)

        debate = DialecticOutput(
            option_a_argument="A", option_b_counter="B", synthesis="S",
        )
        thesis = await buffer._compress(debate, "sess-test")
        word_count = len(thesis.content.split())
        assert word_count <= 50  # compression_max_words default
