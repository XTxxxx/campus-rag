import redis

from campus_rag.constants.redis import REDIS_PORT

redis_client = redis.Redis(
  host="localhost", port=REDIS_PORT, password="123456", decode_responses=True
)
