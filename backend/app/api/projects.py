from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import ChatMessage, MessageRole, Project, User
from app.schemas.project import ProjectCreate, ProjectOut, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])

WELCOME_MESSAGE = (
    "こんにちは！🌱 これからあなた専用のAIを一緒に作っていきます。\n\n"
    "まず教えてください — **どんなことができるAIがほしいですか？**\n\n"
    "例:\n"
    "・お客さんからの問い合わせに自動で返事してほしい\n"
    "・社内ルールについて答えてくれるAIがほしい\n"
    "・写真を見て商品の説明文を書いてほしい\n\n"
    "やりたいことを自由に書いてもらえれば、必要なデータを順番にお願いしていきます。"
)


def _to_out(project: Project) -> ProjectOut:
    out = ProjectOut.model_validate(project)
    out.file_count = len(project.files)
    return out


def _get_owned(db: Session, user: User, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if not project or project.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.get("", response_model=list[ProjectOut])
def list_projects(
    db: Session = Depends(get_db), current: User = Depends(get_current_user)
) -> list[ProjectOut]:
    projects = (
        db.query(Project)
        .filter(Project.owner_id == current.id)
        .order_by(Project.updated_at.desc())
        .all()
    )
    return [_to_out(p) for p in projects]


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> ProjectOut:
    project = Project(owner_id=current.id, name=payload.name)
    db.add(project)
    db.flush()
    greeting = ChatMessage(
        project_id=project.id,
        role=MessageRole.ASSISTANT.value,
        content=WELCOME_MESSAGE,
    )
    db.add(greeting)
    db.commit()
    db.refresh(project)
    return _to_out(project)


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> ProjectOut:
    return _to_out(_get_owned(db, current, project_id))


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> ProjectOut:
    project = _get_owned(db, current, project_id)
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        if v is None:
            continue
        if hasattr(v, "value"):
            v = v.value
        setattr(project, k, v)
    db.commit()
    db.refresh(project)
    return _to_out(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> None:
    project = _get_owned(db, current, project_id)
    db.delete(project)
    db.commit()
