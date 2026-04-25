# Bloom — アーキテクチャ概要（MVP）

```
┌──────────────────┐        ┌──────────────────┐        ┌──────────────────┐
│   Next.js (UI)   │  HTTPS │  FastAPI (API)   │  SQL   │ PostgreSQL / SQLite│
│  app/ pages      ├───────►│  app/api/*       ├───────►│ users / projects   │
│  components/     │        │  app/services/*  │        │ dataset_files      │
│  lib/api.ts      │        │  app/models/*    │        │ chat_messages      │
└──────────────────┘        └────────┬─────────┘        └──────────────────┘
                                     │
                                     ▼
                            ┌──────────────────┐
                            │  Local / S3 互換 │
                            │   uploads/       │
                            └──────────────────┘
                                     │
                                     ▼
                            ┌──────────────────┐
                            │ OpenAI / Anthropic│
                            │   (chat / RAG)   │
                            └──────────────────┘
```

## ディレクトリ

- `backend/app/api/` — REST エンドポイント (auth, projects, datasets, chat)
- `backend/app/models/` — SQLAlchemy ORM
- `backend/app/schemas/` — Pydantic 入出力モデル
- `backend/app/services/` — ファイル処理 / AI 呼び出し
- `frontend/app/` — Next.js App Router ページ
- `frontend/components/` — 共通コンポーネント (`AuthProvider`, `Nav`, `Protected`)
- `frontend/lib/api.ts` — JWT付き fetch ラッパー

## データモデル

- **User**: id, email, name, hashed_password
- **Project**: id, owner_id, name, type, status, purpose, system_prompt
- **DatasetFile**: id, project_id, filename, kind, size_bytes, storage_path, extracted_text
- **ChatMessage**: id, project_id, role, content

## AI 戦略（MVP）

PRD の「学習方式（抽象化）」の方針に沿い、ユーザにはモデル選択を見せません。

- 取り込み時に PDF / CSV / Excel / テキストから本文抜粋を抽出して保存
- チャット時に抜粋を**システムプロンプトに連結（軽量 RAG）**
- 画像・大規模埋め込み・ベクター DB は将来導入（pgvector / Qdrant 等）

## エンドポイント

| 用途 | メソッド | パス |
| --- | --- | --- |
| 登録 | POST | `/api/auth/register` |
| ログイン | POST | `/api/auth/login` |
| 自分の情報 | GET | `/api/auth/me` |
| プロジェクト一覧 | GET | `/api/projects` |
| プロジェクト作成 | POST | `/api/projects` |
| プロジェクト取得/更新/削除 | GET / PATCH / DELETE | `/api/projects/{id}` |
| ファイル一覧 | GET | `/api/projects/{id}/files` |
| ファイルアップロード | POST | `/api/projects/{id}/files` |
| ファイル削除 | DELETE | `/api/projects/{id}/files/{file_id}` |
| メッセージ履歴 | GET | `/api/projects/{id}/messages` |
| チャット送信 | POST | `/api/projects/{id}/chat` |
| AIアシスト診断 | POST | `/api/projects/{id}/assist` |

## 今後の拡張ロードマップ

1. **ベクター検索**: pgvector で `dataset_files` の埋め込みインデックス
2. **画像 LoRA**: 画像系プロジェクトでの軽量学習パイプライン
3. **共有 / マーケット**: 公開フラグと URL 共有 → 課金統合
4. **OAuth**: Google / GitHub ログイン
5. **S3 ストレージ**: `UPLOAD_DIR` を boto3 ベースに差し替え
