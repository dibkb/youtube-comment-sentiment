import redis


# Initialize Redis client
class RedisClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(RedisClient, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "redis_client"):
            self.redis_client = redis.Redis(host="redis", port=6379, db=0)

    def get_redis_client(self):
        return self.redis_client
