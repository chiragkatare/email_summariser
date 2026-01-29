import json
from typing import Any

from redis.asyncio import ConnectionPool, Redis


class CacheService:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def get(self, key: str) -> dict | None:
        raw = await self.redis.get(key)
        return json.loads(raw) if raw else None

    async def set(self, key: str, value: dict, ttl: int = 3600):
        await self.redis.set(
            key,
            json.dumps(value),
            ex=ttl,
        )

    async def delete(self, key: str):
        await self.redis.delete(key)
