"""Distributed Recency Buffer — Redis-backed with compression."""

import json
from datetime import datetime, timezone
from typing import List, Dict, Optional

import redis.asyncio as redis

from src.config import settings


class RecencyBufferRedis:
    def __init__(self, redis_url: Optional[str] = None, maxlen: int = 3):
        self.redis_url = redis_url or settings.redis_url or "redis://localhost:6379/0"
        self.maxlen = maxlen
        self._client: Optional[redis.Redis] = None

    async def _get_client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.from_url(self.redis_url, decode_responses=True)
        return self._client

    async def add(self, session_id: str, entry: Dict) -> None:
        client = await self._get_client()
        key = f"buffer:{session_id}"
        payload = {
            **entry,
            "timestamp": entry.get("timestamp") or datetime.now(timezone.utc).isoformat(),
        }
        await client.rpush(key, json.dumps(payload))
        length = await client.llen(key)
        if length > self.maxlen:
            old = await client.lpop(key)
            if old:
                summary = await self._compress(json.loads(old))
                await client.rpush(key, json.dumps({"compressed": summary, "evicted": True}))

    async def get(self, session_id: str) -> List[Dict]:
        client = await self._get_client()
        key = f"buffer:{session_id}"
        items = await client.lrange(key, 0, -1)
        return [json.loads(item) for item in items]

    async def clear(self, session_id: str) -> None:
        client = await self._get_client()
        await client.delete(f"buffer:{session_id}")

    async def _compress(self, entry: Dict) -> str:
        text = entry.get("user_input", "") or entry.get("final_output", "")
        words = text.split()
        truncated = words[: settings.compression_max_words]
        suffix = "..." if len(words) > settings.compression_max_words else ""
        return " ".join(truncated) + suffix

    async def close(self) -> None:
        if self._client:
            await self._client.close()
