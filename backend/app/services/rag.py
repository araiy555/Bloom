"""Vector retrieval pipeline for Bloom.

When OpenAI embeddings are available, files are chunked and embedded on upload,
then retrieved by cosine similarity at chat time. When no embedding provider
is configured, callers should fall back to a non-vector strategy (concat
extracted_text into the prompt) so the MVP keeps working.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models import DatasetChunk, DatasetFile
from app.services import ai
from app.services.file_processor import chunk_text


@dataclass
class RetrievedChunk:
    filename: str
    text: str
    score: float


def index_file(db: Session, file: DatasetFile) -> int:
    """Chunk + embed + persist a file. Returns the number of chunks stored.

    Replaces any existing chunks for this file so re-indexing is idempotent.
    Quietly stores zero chunks (and returns 0) if no embedding provider
    is available — the chat layer will fall back to non-vector retrieval.
    """
    # Wipe previous chunks for this file (re-index path)
    db.query(DatasetChunk).filter(DatasetChunk.file_id == file.id).delete()

    if not file.extracted_text:
        db.commit()
        return 0

    pieces = chunk_text(file.extracted_text)
    if not pieces:
        db.commit()
        return 0

    embeddings = ai.embed_texts(pieces)
    if embeddings is None:
        # No embedding provider configured — leave chunks unindexed.
        db.commit()
        return 0

    for idx, (text, vec) in enumerate(zip(pieces, embeddings)):
        db.add(
            DatasetChunk(
                project_id=file.project_id,
                file_id=file.id,
                chunk_index=idx,
                text=text,
                embedding=json.dumps(vec),
            )
        )
    db.commit()
    return len(pieces)


def search(db: Session, project_id: int, query: str, top_k: int = 6) -> list[RetrievedChunk]:
    """Return top-k chunks for the project most relevant to the query."""
    if not query.strip():
        return []
    query_vec = ai.embed_texts([query])
    if query_vec is None or not query_vec:
        return []
    qv = query_vec[0]

    rows = (
        db.query(DatasetChunk, DatasetFile.filename)
        .join(DatasetFile, DatasetChunk.file_id == DatasetFile.id)
        .filter(DatasetChunk.project_id == project_id)
        .all()
    )

    scored: list[tuple[float, DatasetChunk, str]] = []
    for chunk, filename in rows:
        try:
            vec = json.loads(chunk.embedding)
        except Exception:
            continue
        if not vec:
            continue
        score = ai.cosine_similarity(qv, vec)
        scored.append((score, chunk, filename))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [
        RetrievedChunk(filename=fn, text=chunk.text, score=score)
        for score, chunk, fn in scored[:top_k]
    ]


def build_context(retrieved: list[RetrievedChunk], max_chars: int = 6000) -> str:
    """Format retrieved chunks as a single context block for the system prompt."""
    if not retrieved:
        return ""
    out: list[str] = []
    used = 0
    for r in retrieved:
        header = f"\n--- {r.filename} (score={r.score:.2f}) ---\n"
        block = header + r.text
        if used + len(block) > max_chars:
            block = block[: max_chars - used]
            out.append(block)
            break
        out.append(block)
        used += len(block)
    return "".join(out)
