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
        # Check if sentiment is already cached in Redis
        cached_sentiment = redis_client.hget("comments", comment.id)
        if cached_sentiment:
            return
            
        llm_with_structure = llama.with_structured_output(CommentSentiment)
        response = await llm_with_structure.ainvoke(
            [
                SystemMessage(
                    content="Analyze the sentiment of the following comment. Return the sentiment as a string. Only return the sentiment, no other text. The sentiment should be one of the following: positive, negative, neutral."
                ),
                HumanMessage(content=f"Here is the comment: {comment.cleanedComment}"),
            ]
        )

        # Store in Redis
        redis_client.hset("comments", comment.id, str(response.sentiment))


async def batch_analyze_sentiments(comments: list[CleanedComment], batch_size: int = 5):
    """Analyze sentiments in batches with pre-filtering of cached results"""
    
    # Filter out comments that already have sentiment stored
    pipe = redis_client.pipeline()
    for comment in comments:
        pipe.hexists("comments", comment.id)
    results = pipe.execute()
    
    comments_to_analyze = [
        comment for i, comment in enumerate(comments) if not results[i]
    ]
    
    if not comments_to_analyze:
        return
    
    # Process in batches using semaphore to control concurrency
    semaphore = asyncio.Semaphore(min(len(comments_to_analyze), batch_size))
    await asyncio.gather(
        *[analyze_sentiment(comment, semaphore) for comment in comments_to_analyze]
    )
    
    # Could implement batch LLM calls here if the API supports it
