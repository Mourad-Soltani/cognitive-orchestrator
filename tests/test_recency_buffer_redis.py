"""Tests for the Redis-backed recency buffer."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.recency_buffer_redis import RecencyBufferRedis


@pytest.mark.asyncio
async def test_buffer_add_and_get():
    buffer = RecencyBufferRedis(redis_url="redis://fake", maxlen=3)

    mock_redis = AsyncMock()
    mock_redis.rpush = AsyncMock()
    mock_redis.llen = AsyncMock(return_value=1)
    mock_redis.lrange = AsyncMock(return_value=[
        '{"user_input": "hello"}',
        '{"user_input": "world"}',
    ])
    mock_redis.delete = AsyncMock()
    mock_redis.lpop = AsyncMock()
    mock_redis.close = AsyncMock()

    buffer._client = mock_redis

    await buffer.add("session1", {"user_input": "hello"})
    await buffer.add("session1", {"user_input": "world"})

    items = await buffer.get("session1")
    assert len(items) == 2
    assert items[0]["user_input"] == "hello"
    assert items[1]["user_input"] == "world"

    await buffer.clear("session1")
    mock_redis.delete.assert_called_once_with("buffer:session1")


@pytest.mark.asyncio
async def test_buffer_compression_on_eviction():
    buffer = RecencyBufferRedis(redis_url="redis://fake", maxlen=2)

    mock_redis = AsyncMock()
    mock_redis.rpush = AsyncMock()
    mock_redis.llen = AsyncMock(side_effect=[1, 2, 3])  # third add triggers eviction
    mock_redis.lpop = AsyncMock(return_value='{"user_input": "old text that is very long and needs compression because it exceeds the fifty word limit set by the configuration"}')
    mock_redis.close = AsyncMock()

    buffer._client = mock_redis

    await buffer.add("session1", {"user_input": "first"})
    await buffer.add("session1", {"user_input": "second"})
    await buffer.add("session1", {"user_input": "third"})  # triggers eviction

    assert mock_redis.lpop.called


@pytest.mark.asyncio
async def test_buffer_close():
    buffer = RecencyBufferRedis(redis_url="redis://fake")
    mock_redis = AsyncMock()
    mock_redis.close = AsyncMock()
    buffer._client = mock_redis
    await buffer.close()
    mock_redis.close.assert_called_once()
