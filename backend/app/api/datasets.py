import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.db.session import get_db
from app.models import DatasetFile, Project, User
from app.schemas.dataset import DatasetFileOut
from app.services import file_processor

settings = get_settings()
router = APIRouter(prefix="/projects/{project_id}/files", tags=["datasets"])

PREVIEW_CHARS = 200


def _to_out(f: DatasetFile) -> DatasetFileOut:
    out = DatasetFileOut.model_validate(f)
    out.extracted_preview = (f.extracted_text or "")[:PREVIEW_CHARS]
    return out


def _get_owned_project(db: Session, user: User, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if not project or project.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.get("", response_model=list[DatasetFileOut])
def list_files(
    project_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> list[DatasetFileOut]:
    project = _get_owned_project(db, current, project_id)
    return [_to_out(f) for f in project.files]


@router.post("", response_model=DatasetFileOut, status_code=status.HTTP_201_CREATED)
async def upload_file(
    project_id: int,
    upload: UploadFile = File(...),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> DatasetFileOut:
    project = _get_owned_project(db, current, project_id)
    if not upload.filename:
        raise HTTPException(status_code=400, detail="Filename required")

    safe_name = os.path.basename(upload.filename)
    unique = f"{uuid.uuid4().hex}_{safe_name}"
    project_dir = os.path.join(settings.UPLOAD_DIR, f"project_{project.id}")
    dest_path = os.path.join(project_dir, unique)

    size = file_processor.save_upload(upload.file, dest_path)
    kind = file_processor.classify(safe_name)
    text = file_processor.extract_text(kind, dest_path)

    record = DatasetFile(
        project_id=project.id,
        filename=safe_name,
        kind=kind.value,
        size_bytes=size,
        storage_path=dest_path,
        extracted_text=text,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _to_out(record)


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(
    project_id: int,
    file_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> None:
    _get_owned_project(db, current, project_id)
    record = db.get(DatasetFile, file_id)
    if not record or record.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    try:
        if record.storage_path and os.path.exists(record.storage_path):
            os.remove(record.storage_path)
    except OSError:
        pass
    db.delete(record)
    db.commit()
