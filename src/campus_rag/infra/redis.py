import redis

redis_client = redis.Redis(
  host="localhost", port=6379, password="123456", decode_responses=True
)
