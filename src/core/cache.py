import redis
from src.configs.pipelines.settings import settings

redis_client = redis.Redis.from_url(settings.REDIS_URL)
