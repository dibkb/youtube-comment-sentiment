import json
from .analyze import batch_analyze_sentiments
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from .youtube_api import YoutubeAPI
from .llm import LanguageModel
from .redis import RedisClient
from .settings import config
from .models import CleanedComment
import hashlib

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
    try:
        hash_key = hashlib.sha256((video_id + token).encode("utf-8")).hexdigest()

    # Check if complete response is cached
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

        # Use batch processing instead of individual processing
        await batch_analyze_sentiments(comments, batch_size=config.MAX_CONCURRENT_REQUESTS)

        # Use Redis pipeline for bulk operations
        pipe = redis_client.pipeline()
        for rc in raw_comments:
            comment_id = rc["snippet"]["topLevelComment"]["id"]
            pipe.hget("comments", comment_id)

        sentiments = pipe.execute()

        # Apply sentiments to raw comments
        for i, rc in enumerate(raw_comments):
            sentiment_bytes = sentiments[i]
            if sentiment_bytes:
                rc["snippet"]["topLevelComment"]["snippet"]["sentiment"] = (
                    sentiment_bytes.decode("utf-8")
                )

        # Cache the final result
        response["items"] = raw_comments
        redis_client.setex(hash_key, config.REDIS_CACHE_EXPIRATION, json.dumps(response))

        return response
    
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
