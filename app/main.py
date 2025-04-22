import json
from .analyze import analyze_sentiment
from fastapi import FastAPI
from .youtube_api import YoutubeAPI
from .llm import LanguageModel
from .redis import RedisClient
from .settings import config
from .models import CleanedComment
import hashlib
import asyncio

app = FastAPI()

# ---------------- singleton initialization -----------------
YoutubeAPI()
LanguageModel()
RedisClient()
youtube_client = YoutubeAPI().get_youtube_client()
redis_client = RedisClient().get_redis_client()
# redis_client.flushall()
# ------------------------------------------------------------


@app.get("/")
async def root():
    return "Comment sentiment v1"


@app.post("/get-comments/{video_id}")
async def get_comments(video_id: str, next_page_token: str = None):
    token = next_page_token or ""
    hash_key = hashlib.sha256((video_id + token).encode("utf-8")).hexdigest()

    cached_response = redis_client.get(hash_key)
    if cached_response:
        return json.loads(cached_response)

    request = youtube_client.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=config.MAX_RESULTS,
        textFormat="plainText",
        order="relevance",
        pageToken=next_page_token,
    )
    response = request.execute()

    comments = []
    raw_comments = []
    if "items" in response:
        raw_comments = response["items"]
        comments = [
            CleanedComment(
                id=item["snippet"]["topLevelComment"]["id"],
                cleanedComment=item["snippet"]["topLevelComment"]["snippet"][
                    "textDisplay"
                ],
            )
            for item in response["items"]
        ]

    semaphore = asyncio.Semaphore(config.MAX_CONCURRENT_REQUESTS)
    await asyncio.gather(
        *[analyze_sentiment(comment, semaphore) for comment in comments]
    )

    for rc in raw_comments:
        sentiment_bytes = redis_client.hget(
            "comments", rc["snippet"]["topLevelComment"]["id"]
        )
        if sentiment_bytes:
            rc["snippet"]["topLevelComment"]["snippet"]["sentiment"] = (
                sentiment_bytes.decode("utf-8")
            )

    redis_client.setex(hash_key, config.REDIS_CACHE_EXPIRATION, json.dumps(raw_comments))

    return raw_comments
