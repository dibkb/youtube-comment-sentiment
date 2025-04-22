from fastapi import FastAPI
from .youtube_api import YoutubeAPI
from .llm import LanguageModel
from .settings import config

app = FastAPI()


# singleton initialization
YoutubeAPI()
LanguageModel()

@app.get("/")
async def root():
    return "Comment sentiment v1"



@app.post("/get-comments/{video_id}")
async def get_comments(video_id: str):
    youtube_client = YoutubeAPI().get_youtube_client()

    request = youtube_client.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=config.MAX_RESULTS,
        textFormat="plainText",
        order="relevance"
    )
    response = request.execute()

    return response
