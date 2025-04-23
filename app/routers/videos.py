from ..youtube_api import YoutubeAPI
from ..redis import RedisClient
from fastapi import APIRouter
import json
from fastapi.responses import JSONResponse
from ..youtube_api import YoutubeAPI
from ..redis import RedisClient
from ..settings import config
import hashlib
youtube_client = YoutubeAPI().get_youtube_client()
redis_client = RedisClient().get_redis_client()


router = APIRouter(
    prefix="/videos",
    tags=["videos"],
    responses={404: {"description": "Not found"}},
)

@router.get("/search")
async def search_videos(query: str):
    try:
        hash_key = hashlib.sha256((query).encode("utf-8")).hexdigest()
        cached_response = redis_client.get(hash_key)
        if cached_response:
            return json.loads(cached_response)
        request = youtube_client.search().list(
            part="snippet",
            q=query,
            maxResults=config.MAX_RESULTS_SEARCH,
            order="relevance",
        )
        response = request.execute()
        if "items" in response:
            redis_client.setex(hash_key, config.REDIS_CACHE_EXPIRATION, json.dumps(response["items"]))
            return response["items"]
        else:
            return []
    
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})