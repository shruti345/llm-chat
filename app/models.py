
from pydantic import BaseModel, Field
from typing import Literal


class ChatRequest(BaseModel):
    user_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    message: str = Field(min_length=1, max_length=10000)


class ChatResponse(BaseModel):
    response: str
    user_id: str
    session_id: str
    context_used: list[str] = Field(default_factory=list)

class MemoryCreateRequest(BaseModel):
    user_id: str = Field(min_length=1)
    text: str = Field(min_length=1, max_length=2000)
    category: Literal[
        "career",
        "preference",
        "interest",
        "profile",
        "astrology",
        "other",
    ] = "other"
    timeframe: str | None = None


class MemoryItem(BaseModel):
    text: str
    category: str
    timeframe: str | None = None
    memory_key: str | None = None



class MemoryListResponse(BaseModel):
    user_id: str
    memories: list[MemoryItem]
