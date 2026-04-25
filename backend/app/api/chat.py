from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import ChatMessage, MessageRole, Project, User
from app.models.project import ProjectStatus
from app.schemas.chat import AssistReport, ChatMessageOut, ChatRequest, ChatResponse
from app.services import ai

router = APIRouter(prefix="/projects/{project_id}", tags=["chat"])

INTERVIEWER_PROMPT = """\
あなたは「Bloom」というプラットフォーム上の AI 制作アシスタントです。
ユーザは自分専用の AI（または AI エージェント）を作ろうとしています。
あなたのゴールは、ユーザに会話で必要なものを聞き出し、データを集めて、
最終的にそのユーザだけの AI として振る舞えるようにすることです。

進め方:
1. まずユーザに「何ができる AI が欲しいか（目的・用途）」を聞きます。すでに分かっていれば飛ばしてください。
2. 目的が分かったら、その目的を達成するために必要なデータを 1〜3 種類に分けて、具体的にお願いしてください。
   例: 「過去のお問い合わせメール（CSV か txt）」「商品リスト（Excel）」「作風が分かる画像 5〜10 枚」
3. ユーザがファイルをアップロードしたら、内容を確認してください。種類・量・質が足りなければ追加でお願いします。
4. 必要なものが揃ったら、「準備できました」と伝え、それ以降は実際の AI として質問に答えてください。
5. 既に十分な準備ができている場合は、ユーザの質問に普通に答えるアシスタントとして振る舞ってください。

ルール:
- 専門用語は使わず、子供でも分かる優しい日本語で。
- 一度にたくさん聞きすぎない。1〜2 個ずつ。
- ファイルのアップロードは画面のドラッグ＆ドロップ or 添付ボタンで出来ることを案内してOK。
- データセット抜粋を渡された場合は、その内容を根拠として使ってください。
"""

DATA_INVENTORY_HEADER = "現在ユーザがアップロード済みのファイル一覧:"
DATA_EMPTY_NOTE = "まだファイルは1つもアップロードされていません。"


def _get_owned_project(db: Session, user: User, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if not project or project.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


def _file_inventory(project: Project) -> str:
    if not project.files:
        return DATA_EMPTY_NOTE
    lines = []
    for f in project.files:
        lines.append(f"- {f.filename} (種類: {f.kind}, サイズ: {f.size_bytes} bytes)")
    return "\n".join(lines)


def _build_messages(project: Project, history: list[ChatMessage], user_msg: str) -> list[dict]:
    base = (project.system_prompt or "").strip() or INTERVIEWER_PROMPT

    sections: list[str] = [base]
    if project.goal:
        sections.append(f"ユーザが宣言した目的: {project.goal}")
    sections.append(DATA_INVENTORY_HEADER + "\n" + _file_inventory(project))

    excerpts = [(f.filename, f.extracted_text or "") for f in project.files]
    context = ai.build_rag_context(excerpts)
    if context:
        sections.append("以下はファイルの中身の抜粋です。回答の根拠として使ってください:\n" + context)

    system = "\n\n".join(sections)
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

    # First user message captures the goal
    if not project.goal and not any(m.role == MessageRole.USER.value for m in history):
        project.goal = payload.message.strip()[:500]

    messages = _build_messages(project, history, payload.message)
    reply = ai.chat(messages)

    user_record = ChatMessage(
        project_id=project.id, role=MessageRole.USER.value, content=payload.message
    )
    assistant_record = ChatMessage(
        project_id=project.id, role=MessageRole.ASSISTANT.value, content=reply
    )
    db.add_all([user_record, assistant_record])

    if project.status == ProjectStatus.DRAFT.value and project.files:
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
    report = ai.assist_report(project.goal or project.name, project.goal, summaries)
    return AssistReport(**report)
