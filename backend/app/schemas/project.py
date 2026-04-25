from datetime import datetime

from pydantic import BaseModel, Field

from app.models.project import ProjectStatus


class ProjectCreate(BaseModel):
    name: str = Field(default="新しいAI", min_length=1, max_length=120)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    goal: str | None = None
    system_prompt: str | None = None
    status: ProjectStatus | None = None


class ProjectOut(BaseModel):
    id: int
    name: str
    status: str
    goal: str
    system_prompt: str
    created_at: datetime
    updated_at: datetime
    file_count: int = 0

    class Config:
        from_attributes = True
