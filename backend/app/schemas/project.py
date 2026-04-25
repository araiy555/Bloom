from datetime import datetime

from pydantic import BaseModel, Field

from app.models.project import ProjectStatus, ProjectType


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    type: ProjectType = ProjectType.OTHER
    purpose: str = ""


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    type: ProjectType | None = None
    purpose: str | None = None
    system_prompt: str | None = None
    status: ProjectStatus | None = None


class ProjectOut(BaseModel):
    id: int
    name: str
    type: str
    status: str
    purpose: str
    system_prompt: str
    created_at: datetime
    updated_at: datetime
    file_count: int = 0

    class Config:
        from_attributes = True
