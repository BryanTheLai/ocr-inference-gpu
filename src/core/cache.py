"""Shared Redis client used by the API layer."""

import redis
from src.configs.pipelines.settings import settings

redis_client = redis.Redis.from_url(settings.REDIS_URL)
