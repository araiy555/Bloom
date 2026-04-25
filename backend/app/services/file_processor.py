"""Light-weight file ingestion: classify by extension and extract preview text."""

from __future__ import annotations

import csv
import io
import os
from typing import BinaryIO

from app.models.dataset import FileKind

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
PDF_EXT = {".pdf"}
CSV_EXT = {".csv", ".tsv"}
EXCEL_EXT = {".xls", ".xlsx"}
TEXT_EXT = {".txt", ".md", ".json", ".log"}

MAX_PREVIEW_CHARS = 200_000  # generous cap for full-document indexing
CHUNK_CHARS = 800
CHUNK_OVERLAP = 100


def chunk_text(text: str, chunk_size: int = CHUNK_CHARS, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into roughly fixed-size, overlapping chunks for embedding."""
    if not text:
        return []
    text = text.strip()
    if len(text) <= chunk_size:
        return [text]
    chunks: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + chunk_size, n)
        chunks.append(text[start:end])
        if end >= n:
            break
        start = max(end - overlap, start + 1)
    return chunks


def classify(filename: str) -> FileKind:
    ext = os.path.splitext(filename)[1].lower()
    if ext in IMAGE_EXT:
        return FileKind.IMAGE
    if ext in PDF_EXT:
        return FileKind.PDF
    if ext in CSV_EXT:
        return FileKind.CSV
    if ext in EXCEL_EXT:
        return FileKind.EXCEL
    if ext in TEXT_EXT:
        return FileKind.TEXT
    return FileKind.OTHER


def _truncate(text: str) -> str:
    return text[:MAX_PREVIEW_CHARS]


def extract_text(kind: FileKind, file_path: str) -> str:
    """Extract a small preview of text content for RAG context. Best-effort.

    For images, this calls the vision model to generate a Japanese description
    so downstream chat can reason about visual content.
    """

    try:
        if kind == FileKind.IMAGE:
            from app.services.ai import describe_image

            desc = describe_image(file_path)
            if desc:
                return f"[画像の自動説明]\n{desc}"
            return ""

        if kind == FileKind.TEXT:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                return _truncate(f.read())

        if kind == FileKind.CSV:
            with open(file_path, "r", encoding="utf-8", errors="replace", newline="") as f:
                reader = csv.reader(f)
                rows: list[str] = []
                for row in reader:
                    rows.append(", ".join(row))
                return _truncate("\n".join(rows))

        if kind == FileKind.PDF:
            try:
                from pypdf import PdfReader

                reader = PdfReader(file_path)
                pages: list[str] = []
                for page in reader.pages:
                    try:
                        pages.append(page.extract_text() or "")
                    except Exception:
                        continue
                return _truncate("\n".join(pages))
            except Exception:
                return ""

        if kind == FileKind.EXCEL:
            try:
                from openpyxl import load_workbook

                wb = load_workbook(file_path, read_only=True, data_only=True)
                lines: list[str] = []
                for sheet in wb.sheetnames:
                    ws = wb[sheet]
                    lines.append(f"# Sheet: {sheet}")
                    for row in ws.iter_rows(values_only=True):
                        lines.append(", ".join("" if v is None else str(v) for v in row))
                return _truncate("\n".join(lines))
            except Exception:
                return ""

        # Images and other: no text extraction in MVP
        return ""
    except Exception:
        return ""


def save_upload(stream: BinaryIO, dest_path: str) -> int:
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    size = 0
    with open(dest_path, "wb") as out:
        while True:
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            out.write(chunk)
    return size
