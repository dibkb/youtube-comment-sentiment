from pydantic import BaseModel, Field
from typing import Literal, Dict


class CommentSentiment(BaseModel):
    sentiment: Literal["positive", "negative", "neutral"] = Field(
        description="The sentiment of the comment"
    )


class CleanedComment(BaseModel):
    id: str = Field(description="The id of the comment")
    cleanedComment: str = Field(description="The text of the comment")




