
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    user_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    message: str = Field(min_length=1, max_length=10000)


class ChatResponse(BaseModel):
    response: str
    user_id: str
    session_id: str
    context_used: list[str] = Field(default_factory=list)
