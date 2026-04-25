from datetime import datetime

from pydantic import BaseModel


class DatasetFileOut(BaseModel):
    id: int
    project_id: int
    filename: str
    kind: str
    size_bytes: int
    created_at: datetime
    extracted_preview: str = ""

    class Config:
        from_attributes = True
