from datetime import datetime

from pydantic import BaseModel, Field


class ChatMessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)


class ChatResponse(BaseModel):
    user_message: ChatMessageOut
    assistant_message: ChatMessageOut


class AssistReport(BaseModel):
    classification: str
    quality_score: int
    feasibility: str
    suggestions: list[str]
    summary: str
