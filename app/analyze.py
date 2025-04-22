from .models import CleanedComment
from langchain_core.messages import SystemMessage, HumanMessage
import asyncio
from .llm import LanguageModel
from .models import CommentSentiment
from .redis import RedisClient

llama = LanguageModel().get_llama3_3()

redis_client = RedisClient().get_redis_client()


async def analyze_sentiment(comment: CleanedComment, semaphore: asyncio.Semaphore):
    async with semaphore:
        llm_with_structure = llama.with_structured_output(CommentSentiment)
        response = await llm_with_structure.ainvoke(
            [
                SystemMessage(
                    content="Analyze the sentiment of the following comment. Return the sentiment as a string. Only return the sentiment, no other text. The sentiment should be one of the following: positive, negative, neutral."
                ),
                HumanMessage(content=f"Here is the comment: {comment.cleanedComment}"),
            ]
        )

        # Store in Redis instead of in-memory hashmap
        redis_client.hset("comments", comment.id, str(response.sentiment))
