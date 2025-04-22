from .settings import settings
from googleapiclient.discovery import build


class YoutubeAPI:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(YoutubeAPI, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            self.api_service_name = "youtube"
            self.api_version = "v3"
            self.developer_key = settings.YOUTUBE_API_KEY
            self.initialized = True
            self.youtube = build(
                self.api_service_name, self.api_version, developerKey=self.developer_key
            )

    def get_youtube_client(self):
        return self.youtube
