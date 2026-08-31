"""Tests for the Articulation Cortex."""

import pytest
import math
from unittest.mock import AsyncMock, MagicMock, patch

from src.articulation_cortex import ArticulationCortex
from src.config import settings


class TestArticulationCortex:
    """Unit tests for temperature decay and chunking."""

    @pytest.fixture
    def cortex(self, mock_openai_client):
        return ArticulationCortex(client=mock_openai_client)

    def test_temperature_decay_formula(self, cortex):
        """Verify logistic decay produces expected curve shape."""
        t0 = cortex._compute_temperature(0)
        t5 = cortex._compute_temperature(5)
        t10 = cortex._compute_temperature(10)

        # At start, temp should be near T_start
        assert t0 > 1.0
        # At inflection point, temp should be midpoint
        assert abs(t5 - (settings.articulation_temp_start + settings.articulation_temp_end) / 2) < 0.2
        # At end, temp should approach T_end
        assert t10 < settings.articulation_temp_start
        assert t10 > settings.articulation_temp_end

    def test_temperature_monotonically_decreasing(self, cortex):
        """Each subsequent chunk should have temp ≤ previous."""
        temps = [cortex._compute_temperature(i) for i in range(20)]
        for i in range(1, len(temps)):
            assert temps[i] <= temps[i-1] + 0.01  # small tolerance for float

    def test_chunk_text_splits_correctly(self, cortex):
        text = "one two three four five six seven eight nine ten"
        chunks = cortex._chunk_text(text, chunk_size=3)
        assert len(chunks) == 4  # 10 words / 3 per chunk = 4 chunks
        assert chunks[0] == "one two three"
        assert chunks[-1] == "ten"

    def test_empty_text_returns_single_empty_chunk(self, cortex):
        chunks = cortex._chunk_text("", chunk_size=5)
        assert len(chunks) == 1
        assert chunks[0] == ""

    @pytest.mark.asyncio
    async def test_articulate_yields_chunks(self, cortex, mock_openai_client):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "This is a test response with many words"
        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)

        chunks = []
        async for chunk in cortex.articulate(
            synthesis="Test synthesis",
            session_id="sess-test",
        ):
            chunks.append(chunk)

        assert len(chunks) > 0
        assert all(hasattr(c, "temperature") for c in chunks)
        assert all(hasattr(c, "index") for c in chunks)
