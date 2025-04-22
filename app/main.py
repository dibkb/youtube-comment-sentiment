import json
from fastapi import FastAPI
from .youtube_api import YoutubeAPI
from .llm import LanguageModel
from .settings import config
import redis
import hashlib

app = FastAPI()

# ---------------- singleton initialization -----------------
YoutubeAPI()
LanguageModel()
llama = LanguageModel().get_llama3_3()
youtube_client = YoutubeAPI().get_youtube_client()
redis_client = redis.Redis(host="redis", port=6379, db=0)
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
    redis_client.setex(hash_key, 3600, json.dumps(response))

    return response
