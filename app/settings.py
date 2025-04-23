from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()


class Settings(BaseSettings):
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY")
    BRAVE_SEARCH_API_KEY: str = os.getenv("BRAVE_SEARCH_API_KEY")
    YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY")

    class Config:
        env_file = "./env"


settings = Settings()


class Config(BaseSettings):
    MAX_RESULTS: int = 20
    MAX_RESULTS_SEARCH: int = 20
    MAX_CONCURRENT_REQUESTS: int = 20
    REDIS_CACHE_EXPIRATION: int = 60*60*24
    # Batch size for grouping analysis requests
    BATCH_SIZE: int = 5


config = Config()
