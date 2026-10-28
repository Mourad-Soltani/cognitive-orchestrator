"""Distributed Recency Buffer — Redis-backed with in-memory fallback.

If Redis is unavailable, falls back to a process-local deque so the
orchestrator remains production-usable without a hard Redis dependency.
"""

from __future__ import annotations

import json
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Dict, List, Optional

from src.config import settings

try:
    import redis.asyncio as redis
except Exception:  # pragma: no cover
    redis = None  # type: ignore


class RecencyBufferRedis:
    def __init__(self, redis_url: Optional[str] = None, maxlen: int = 3):
        self.redis_url = redis_url if redis_url is not None else settings.redis_url
        self.maxlen = maxlen
        self._client = None
        self._redis_ok: Optional[bool] = None
        self._memory: dict[str, deque] = defaultdict(lambda: deque(maxlen=self.maxlen))

    async def _get_client(self):
        if redis is None or not self.redis_url:
            self._redis_ok = False
            return None
        if self._client is None:
            self._client = redis.from_url(self.redis_url, decode_responses=True)
        return self._client

    async def _probe(self) -> bool:
        if self._redis_ok is not None:
            return self._redis_ok
        try:
            client = await self._get_client()
            if client is None:
                self._redis_ok = False
                return False
            await client.ping()
            self._redis_ok = True
            return True
        except Exception:
            self._redis_ok = False
            return False

    async def push(self, session_id: str, entry: Dict) -> None:
        await self.add(session_id, entry)

    async def add(self, session_id: str, entry: Dict) -> None:
        payload = {
            **entry,
            "timestamp": entry.get("timestamp") or datetime.now(timezone.utc).isoformat(),
        }
        if await self._probe():
            try:
                client = await self._get_client()
                key = f"buffer:{session_id}"
                await client.rpush(key, json.dumps(payload))
                length = await client.llen(key)
                if length > self.maxlen:
                    old = await client.lpop(key)
                    if old:
                        summary = await self._compress(json.loads(old))
                        await client.rpush(
                            key, json.dumps({"compressed": summary, "evicted": True})
                        )
                return
            except Exception:
                self._redis_ok = False
        # Memory fallback
        self._memory[session_id].append(payload)

    async def get(self, session_id: str) -> List[Dict]:
        if await self._probe():
            try:
                client = await self._get_client()
                key = f"buffer:{session_id}"
                items = await client.lrange(key, 0, -1)
                return [json.loads(item) for item in items]
            except Exception:
                self._redis_ok = False
        return list(self._memory.get(session_id, []))

    async def clear(self, session_id: str) -> None:
        if await self._probe():
            try:
                client = await self._get_client()
                await client.delete(f"buffer:{session_id}")
            except Exception:
                self._redis_ok = False
        self._memory.pop(session_id, None)

    async def _compress(self, entry: Dict) -> str:
        text = entry.get("user_input", "") or entry.get("final_output", "")
        words = str(text).split()
        truncated = words[: settings.compression_max_words]
        suffix = "..." if len(words) > settings.compression_max_words else ""
        return " ".join(truncated) + suffix

    async def close(self) -> None:
        if self._client:
            try:
                await self._client.close()
            except Exception:
                pass
            self._client = None

    @property
    def backend(self) -> str:
        if self._redis_ok is True:
            return "redis"
        if self._redis_ok is False:
            return "memory"
        return "unknown"
