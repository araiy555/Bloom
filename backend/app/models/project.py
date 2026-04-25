from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class ProjectType(str, Enum):
    MANGA = "manga"
    EXCEL = "excel"
    SALES = "sales"
    OTHER = "other"


class ProjectStatus(str, Enum):
    DRAFT = "draft"
    TRAINING = "training"
    READY = "ready"


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    type: Mapped[str] = mapped_column(String(32), default=ProjectType.OTHER.value)
    status: Mapped[str] = mapped_column(String(32), default=ProjectStatus.DRAFT.value)
    purpose: Mapped[str] = mapped_column(Text, default="")
    system_prompt: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    owner: Mapped["User"] = relationship(back_populates="projects")  # type: ignore[name-defined]
    files: Mapped[list["DatasetFile"]] = relationship(  # type: ignore[name-defined]
        back_populates="project",
        cascade="all, delete-orphan",
    )
    messages: Mapped[list["ChatMessage"]] = relationship(  # type: ignore[name-defined]
        back_populates="project",
        cascade="all, delete-orphan",
    )
