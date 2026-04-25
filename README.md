# Bloom

> AIを作るのではなく、AIを育てて使う。

Bloom は、ユーザがデータをアップロードして用途を選ぶだけで、AI（またはAIエージェント）を
作成・利用・共有できる、ノーコード AI 作成インターフェースです。

PRD: [docs/PRD.md](docs/PRD.md)
無料デプロイ手順: [docs/DEPLOY.md](docs/DEPLOY.md)

## 構成

```
Bloom/
├── docs/          # PRD・設計ドキュメント
├── backend/       # FastAPI (Python 3.11+)
├── frontend/      # Next.js 14 (App Router)
└── docker-compose.yml
```

- フロントエンド: Next.js 14 / React / TypeScript / Tailwind
- バックエンド: FastAPI / SQLAlchemy / Pydantic
- DB: PostgreSQL（MVP は SQLite でも起動可）
- ストレージ: ローカル（MVP）/ S3互換（将来）
- AI: OpenAI / Anthropic API

## クイックスタート

### Docker で一括起動

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

- フロント: http://localhost:3000
- API: http://localhost:8000/docs

### ローカル起動（バックエンド）

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

### ローカル起動（フロントエンド）

```bash
cd frontend
npm install
npm run dev
```

## MVP 機能

- ユーザ登録 / ログイン（JWT）
- プロジェクト作成（漫画 / Excel / 営業 / その他）
- データアップロード（画像 / PDF / CSV / Excel / テキスト）
- AIアシスト（データ品質評価・最適化提案）
- AI実行（チャットUI、RAG ベース）

## ライセンス

未定（社内検討中）。
