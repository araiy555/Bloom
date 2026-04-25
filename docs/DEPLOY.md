# Bloom — 無料デプロイ手順（開発・お試し用）

3つの無料サービスを組み合わせて Bloom を全部公開します。**所要時間：約 15 分**。

| パーツ | サービス | 無料枠 |
|---|---|---|
| DB (PostgreSQL) | [Neon](https://neon.tech) | 0.5GB / 永久無料 |
| バックエンド (FastAPI) | [Render](https://render.com) | 永久無料、15分 idle で sleep |
| フロントエンド (Next.js) | [Vercel](https://vercel.com) | 個人なら永久無料 |

## ⚠ 事前に知っておくこと

- **バックエンドは 15 分使わないと寝ます**。再アクセス時、最初の応答に 30 秒ほどかかります。
- **アップロードしたファイルは再デプロイで消えます**（Render free tier は永続ディスクが有料）。
  本番で使う場合は Cloudflare R2 / Supabase Storage への切替えが必要です（後述）。
- **AI API 料金（OpenAI / Anthropic）は別途**。自分のキーを使います。

---

## 0. 準備

- GitHub に本リポジトリを push 済みであること
- 自分の OpenAI API キー（埋め込みも使うので OpenAI 推奨）

---

## 1. Neon で Postgres を用意（3分）

1. https://neon.tech にサインアップ（GitHub 連携が早い）
2. 「Create project」→ region は **AWS Tokyo** か **AWS Singapore** が日本から速い
3. 表示される **Connection string** をコピー（こんな形）：
   ```
   postgresql://user:password@ep-xxxx.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
   ```
4. これを後で Render の `DATABASE_URL` に貼ります

> Bloom は `postgres://` でも `postgresql://` でも自動で `psycopg` ドライバに変換するので、
> Neon の文字列をそのままコピペで OK です。

---

## 2. Render にバックエンドをデプロイ（5分）

1. https://render.com にサインアップ（GitHub 連携）
2. **New** → **Blueprint** → 本リポジトリを選択
3. リポジトリ直下の `render.yaml` を Render が自動検出します
4. 環境変数の入力を求められるので以下を入れる：

   | キー | 値 |
   |---|---|
   | `DATABASE_URL` | Neon でコピーした接続文字列 |
   | `OPENAI_API_KEY` | sk-... |
   | `ANTHROPIC_API_KEY` | （任意。空でも可） |
   | `CORS_ORIGINS` | あとで Vercel の URL を入れる。とりあえず `*` でも可 |

5. **Apply** → 数分でビルド & デプロイ
6. 完了したら `https://bloom-backend-xxxx.onrender.com/health` を開いて
   `{"status":"ok"}` が返ればOK
7. API ドキュメント: `https://bloom-backend-xxxx.onrender.com/docs`

---

## 3. Vercel にフロントをデプロイ（5分）

1. https://vercel.com にサインアップ（GitHub 連携）
2. **Add New** → **Project** → 本リポジトリをインポート
3. **Root Directory** を `frontend` に設定（重要）
4. **Environment Variables** に以下を1個追加：

   | Name | Value |
   |---|---|
   | `NEXT_PUBLIC_API_URL` | `https://bloom-backend-xxxx.onrender.com/api` |

5. **Deploy** → 1〜2分で完了
6. デプロイされた URL（例: `https://bloom-xxx.vercel.app`）を控える

---

## 4. CORS の最終調整（2分）

Vercel の URL を Render に教えます。

1. Render Dashboard → bloom-backend → **Environment** タブ
2. `CORS_ORIGINS` を Vercel の URL に書き換え：
   ```
   https://bloom-xxx.vercel.app
   ```
   複数許可する場合はカンマ区切り：
   ```
   https://bloom-xxx.vercel.app,http://localhost:3000
   ```
3. **Save Changes** で再デプロイされる

---

## 5. 動作確認

1. Vercel の URL を開く
2. 「+ 新しいAIを育てる」→ チャット画面
3. 「営業のメールを書くAIを作りたい」とか入力 → AI が必要なものを聞いてくる
4. ファイルをドラッグ＆ドロップ → 数秒で AI が反応
5. AI が答えるところまで動けば完成 🌱

---

## トラブルシュート

### 初回アクセスがめちゃ遅い
Render free tier の sleep 起き上がり。30 秒ほど我慢。常時起動したい場合は Render の Starter プラン（$7/月）に上げる。

### `Network error` / CORS エラー
Render の `CORS_ORIGINS` が Vercel の URL と完全一致しているか確認（末尾スラッシュ無し / https あり）。

### `database connection failed`
Neon は5分使わないと寝るが、`pool_pre_ping=True` を設定済みなので自動再接続するはず。
それでも失敗する場合は `DATABASE_URL` をコピペし直す。

### アップロードしたファイルが消える
Render free tier の既知の制約。永続化したい場合は：
- Render の永続ディスク（$0.25/GB/月）を有効化
- または Cloudflare R2 / Supabase Storage に切り替え（コード変更必要）

### Vision API（画像説明）が動かない
- `OPENAI_API_KEY` が設定されているか
- 画像が大きすぎないか（数MB以内推奨）
- Render free tier はリクエストタイムアウトが短いので、巨大画像はローカル開発で確認

---

## もっと安定させたい場合の選択肢

| やりたいこと | 推奨 |
|---|---|
| 24時間起動 | Render Starter ($7/月) または Fly.io |
| ファイル永続化 | Cloudflare R2（10GB無料/月）への差し替え |
| 完全無料・自前運用 | Oracle Cloud Always Free VM で `docker compose up` |
