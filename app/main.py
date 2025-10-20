from prometheus_fastapi_instrumentator import Instrumentator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .youtube_api import YoutubeAPI
from .llm import LanguageModel
from .redis import RedisClient
from .routers import comment_sentiment
from .routers import videos
app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:3001",
    "https://brotube.borborah.xyz",
    "https://bro-tube.vercel.app/",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- singleton initialization -----------------
YoutubeAPI()
LanguageModel()
RedisClient()
# redis_client = RedisClient().get_redis_client()
# redis_client.flushall()

# ---------------- prometheus ----------------- 
Instrumentator().instrument(app).expose(app)

app.include_router(comment_sentiment.router)
app.include_router(videos.router)

@app.get("/")
async def root():
    return "BroTube Server is running..."



