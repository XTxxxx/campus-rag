import redis

from campus_rag.constants.redis import REDIS_PORT
from campus_rag.constants.redis import REDIS_PASSWD

redis_client = redis.Redis(
  host="localhost", port=REDIS_PORT, password=REDIS_PASSWD, decode_responses=True
)
