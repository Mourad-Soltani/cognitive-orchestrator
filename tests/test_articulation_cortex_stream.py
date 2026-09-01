"""Tests for the true streaming articulation cortex."""

import pytest
from src.articulation_cortex_stream import ArticulationCortexStream


@pytest.mark.asyncio
async def test_stream_emits_chunks():
    cortex = ArticulationCortexStream(word_chunk_size=2)

    async def mock_tokens():
        for word in ["one", "two", "three", "four", "five"]:
            yield word + " "

    chunks = []
    async for chunk in cortex.stream(mock_tokens()):
        chunks.append(chunk)

    assert len(chunks) >= 1
    combined = "".join(chunks)
    assert "one" in combined
    assert "two" in combined


@pytest.mark.asyncio
async def test_stream_with_human_pause():
    cortex = ArticulationCortexStream(
        word_chunk_size=1,
        human_pause_chunk=2,
        pause_duration=0.05,
    )

    async def mock_tokens():
        for word in ["a", "b", "c", "d"]:
            yield word + " "

    chunks = []
    async for chunk in cortex.stream(mock_tokens()):
        chunks.append(chunk)

    # Should still emit all content despite the pause
    combined = "".join(chunks)
    assert "a" in combined
    assert "b" in combined
    assert "c" in combined
    assert "d" in combined


def test_logistic_temp_start():
    cortex = ArticulationCortexStream(temp_start=1.2, temp_end=0.3)
    t0 = cortex.logistic_temp(0)
    assert 1.1 < t0 < 1.3


def test_logistic_temp_end():
    cortex = ArticulationCortexStream(temp_start=1.2, temp_end=0.3)
    t10 = cortex.logistic_temp(10)
    assert 0.2 < t10 < 0.5


def test_logistic_temp_midpoint():
    cortex = ArticulationCortexStream(temp_start=1.2, temp_end=0.3, midpoint=5.0)
    t5 = cortex.logistic_temp(5)
    # At midpoint, should be roughly halfway
    assert 0.6 < t5 < 0.9
