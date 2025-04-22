from .settings import settings
from langchain_groq import ChatGroq


class LanguageModel:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(LanguageModel, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            self.llama3_3 = ChatGroq(
                model_name="llama-3.3-70b-versatile",
                api_key=settings.GROQ_API_KEY,
            )
            self.initialized = True

    def get_llama3_3(self):
        return self.llama3_3
