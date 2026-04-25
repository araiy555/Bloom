from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import ChatMessage, MessageRole, Project, User
from app.models.project import ProjectStatus
from app.schemas.chat import AssistReport, ChatMessageOut, ChatRequest, ChatResponse
from app.services import ai

router = APIRouter(prefix="/projects/{project_id}", tags=["chat"])

DEFAULT_SYSTEM = (
    "あなたはユーザが Bloom 上で作成したカスタム AI です。"
    "提供されたデータセットの内容に基づいて、専門用語を避けて分かりやすく回答してください。"
)


def _get_owned_project(db: Session, user: User, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if not project or project.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


def _build_messages(project: Project, history: list[ChatMessage], user_msg: str) -> list[dict]:
    system = (project.system_prompt or DEFAULT_SYSTEM).strip()
    excerpts = [(f.filename, f.extracted_text or "") for f in project.files]
    context = ai.build_rag_context(excerpts)
    if context:
        system = (
            system
            + "\n\n以下は参考データセットの抜粋です。回答の根拠として活用してください:\n"
            + context
        )

    messages: list[dict] = [{"role": "system", "content": system}]
    for m in history[-12:]:
        messages.append({"role": m.role, "content": m.content})
    messages.append({"role": "user", "content": user_msg})
    return messages


@router.get("/messages", response_model=list[ChatMessageOut])
def list_messages(
    project_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> list[ChatMessageOut]:
    project = _get_owned_project(db, current, project_id)
    msgs = sorted(project.messages, key=lambda m: m.id)
    return [ChatMessageOut.model_validate(m) for m in msgs]


@router.post("/chat", response_model=ChatResponse)
def chat(
    project_id: int,
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> ChatResponse:
    project = _get_owned_project(db, current, project_id)

    history = sorted(project.messages, key=lambda m: m.id)
    messages = _build_messages(project, history, payload.message)

    reply = ai.chat(messages)

    user_record = ChatMessage(
        project_id=project.id, role=MessageRole.USER.value, content=payload.message
    )
    assistant_record = ChatMessage(
        project_id=project.id, role=MessageRole.ASSISTANT.value, content=reply
    )
    db.add_all([user_record, assistant_record])

    if project.status == ProjectStatus.DRAFT.value:
        project.status = ProjectStatus.READY.value

    db.commit()
    db.refresh(user_record)
    db.refresh(assistant_record)

    return ChatResponse(
        user_message=ChatMessageOut.model_validate(user_record),
        assistant_message=ChatMessageOut.model_validate(assistant_record),
    )


@router.post("/assist", response_model=AssistReport)
def assist(
    project_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> AssistReport:
    project = _get_owned_project(db, current, project_id)
    summaries = [
        {
            "filename": f.filename,
            "kind": f.kind,
            "size_bytes": f.size_bytes,
            "preview": (f.extracted_text or "")[:300],
        }
        for f in project.files
    ]
    report = ai.assist_report(project.type, project.purpose, summaries)
    return AssistReport(**report)
