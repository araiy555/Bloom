from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class FileKind(str, Enum):
    IMAGE = "image"
    PDF = "pdf"
    CSV = "csv"
    EXCEL = "excel"
    TEXT = "text"
    OTHER = "other"


class DatasetFile(Base):
    __tablename__ = "dataset_files"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    filename: Mapped[str] = mapped_column(String(255))
    kind: Mapped[str] = mapped_column(String(32), default=FileKind.OTHER.value)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    storage_path: Mapped[str] = mapped_column(String(512))
    extracted_text: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped["Project"] = relationship(back_populates="files")  # type: ignore[name-defined]
    chunks: Mapped[list["DatasetChunk"]] = relationship(
        back_populates="file",
        cascade="all, delete-orphan",
    )


class DatasetChunk(Base):
    """A small piece of text from a DatasetFile, paired with its vector embedding.

    Embeddings are stored as JSON-encoded list[float] in a Text column so the same
    schema works on both SQLite (dev) and PostgreSQL (prod). When we move to
    pgvector for scale we can add a real vector column and migrate without
    changing the public retrieval API.
    """

    __tablename__ = "dataset_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    file_id: Mapped[int] = mapped_column(
        ForeignKey("dataset_files.id", ondelete="CASCADE"), index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    file: Mapped["DatasetFile"] = relationship(back_populates="chunks")
