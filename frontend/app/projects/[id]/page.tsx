"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Nav } from "@/components/Nav";
import { Protected } from "@/components/Protected";
import {
  api,
  type AssistReport,
  type ChatMessage,
  type DatasetFile,
  type Project,
} from "@/lib/api";

const TYPE_LABEL: Record<string, string> = {
  manga: "🎨 漫画",
  excel: "📊 Excel / 表",
  sales: "💼 営業",
  other: "✨ その他",
};

const STATUS_LABEL: Record<string, string> = {
  draft: "未作成",
  training: "学習中",
  ready: "完成",
};

function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

export default function ProjectPage({ params }: { params: { id: string } }) {
  return (
    <Protected>
      <Nav />
      <ProjectInner projectId={Number(params.id)} />
    </Protected>
  );
}

function ProjectInner({ projectId }: { projectId: number }) {
  const router = useRouter();
  const [project, setProject] = useState<Project | null>(null);
  const [files, setFiles] = useState<DatasetFile[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [chatBusy, setChatBusy] = useState(false);
  const [report, setReport] = useState<AssistReport | null>(null);
  const [reportBusy, setReportBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const refresh = useCallback(async () => {
    setErr(null);
    try {
      const [p, fs, ms] = await Promise.all([
        api<Project>(`/projects/${projectId}`),
        api<DatasetFile[]>(`/projects/${projectId}/files`),
        api<ChatMessage[]>(`/projects/${projectId}/messages`),
      ]);
      setProject(p);
      setFiles(fs);
      setMessages(ms);
    } catch (e: any) {
      setErr(e.message);
    }
  }, [projectId]);

  useEffect(() => { refresh(); }, [refresh]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function onUpload(filesToUpload: FileList | null) {
    if (!filesToUpload || filesToUpload.length === 0) return;
    setErr(null);
    for (const file of Array.from(filesToUpload)) {
      const fd = new FormData();
      fd.append("upload", file);
      try {
        await api(`/projects/${projectId}/files`, {
          method: "POST",
          body: fd,
          raw: true,
        });
      } catch (e: any) {
        setErr(`${file.name}: ${e.message}`);
      }
    }
    if (fileInputRef.current) fileInputRef.current.value = "";
    refresh();
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault();
    onUpload(e.dataTransfer.files);
  }

  async function deleteFile(fileId: number) {
    if (!confirm("削除しますか？")) return;
    await api(`/projects/${projectId}/files/${fileId}`, { method: "DELETE" });
    refresh();
  }

  async function deleteProject() {
    if (!confirm("このAIを削除します。元に戻せません。よろしいですか？")) return;
    await api(`/projects/${projectId}`, { method: "DELETE" });
    router.push("/projects");
  }

  async function sendMessage(e: React.FormEvent) {
    e.preventDefault();
    if (!chatInput.trim() || chatBusy) return;
    setChatBusy(true);
    setErr(null);
    const text = chatInput;
    setChatInput("");
    try {
      const res = await api<{ user_message: ChatMessage; assistant_message: ChatMessage }>(
        `/projects/${projectId}/chat`,
        { method: "POST", body: { message: text } }
      );
      setMessages((m) => [...m, res.user_message, res.assistant_message]);
    } catch (e: any) {
      setErr(e.message);
      setChatInput(text);
    } finally {
      setChatBusy(false);
    }
  }

  async function runAssist() {
    setReportBusy(true);
    setErr(null);
    try {
      const r = await api<AssistReport>(`/projects/${projectId}/assist`, { method: "POST" });
      setReport(r);
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setReportBusy(false);
    }
  }

  if (!project) {
    return <main className="p-8 text-slate-500">読み込み中…</main>;
  }

  return (
    <main className="max-w-6xl mx-auto px-6 py-8 space-y-6">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <Link href="/projects" className="text-sm text-slate-500 hover:underline">
            ← プロジェクト一覧
          </Link>
          <h1 className="text-2xl font-bold mt-1">{project.name}</h1>
          <p className="text-sm text-slate-500">
            {TYPE_LABEL[project.type] ?? project.type} ・ ステータス:{" "}
            <span className="font-medium">{STATUS_LABEL[project.status] ?? project.status}</span>
          </p>
        </div>
        <button onClick={deleteProject} className="btn-outline text-red-600 border-red-200">
          AIを削除
        </button>
      </div>

      {err && <p className="text-sm text-red-600">{err}</p>}

      <div className="grid lg:grid-cols-3 gap-6">
        <section className="lg:col-span-1 space-y-4">
          <div className="card space-y-3">
            <h2 className="font-semibold flex items-center gap-2">📥 データセット</h2>
            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={onDrop}
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-slate-300 rounded-xl p-6 text-center text-sm text-slate-600 cursor-pointer hover:bg-slate-50"
            >
              ここにドラッグ＆ドロップ、またはクリックして選択
              <input
                type="file"
                multiple
                ref={fileInputRef}
                className="hidden"
                onChange={(e) => onUpload(e.target.files)}
              />
            </div>
            {files.length === 0 ? (
              <p className="text-sm text-slate-500">まだファイルがありません。</p>
            ) : (
              <ul className="space-y-2">
                {files.map((f) => (
                  <li key={f.id} className="flex items-center justify-between gap-2 text-sm">
                    <div className="min-w-0">
                      <div className="truncate font-medium">{f.filename}</div>
                      <div className="text-xs text-slate-500">
                        {f.kind} ・ {formatBytes(f.size_bytes)}
                      </div>
                    </div>
                    <button
                      className="text-xs text-red-600 hover:underline"
                      onClick={() => deleteFile(f.id)}
                    >
                      削除
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="card space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold flex items-center gap-2">🤖 AIアシスト</h2>
              <button onClick={runAssist} disabled={reportBusy} className="btn-outline text-sm">
                {reportBusy ? "分析中…" : "診断する"}
              </button>
            </div>
            {report ? (
              <div className="text-sm space-y-2">
                <p>
                  <span className="text-slate-500">分類:</span>{" "}
                  <span className="font-medium">{report.classification}</span>
                </p>
                <p>
                  <span className="text-slate-500">品質スコア:</span>{" "}
                  <span className="font-medium">{report.quality_score} / 100</span>
                </p>
                <p>
                  <span className="text-slate-500">学習可能性:</span>{" "}
                  <span className="font-medium">{report.feasibility}</span>
                </p>
                <p className="text-slate-700">{report.summary}</p>
                {report.suggestions.length > 0 && (
                  <ul className="list-disc list-inside text-slate-700 space-y-1">
                    {report.suggestions.map((s, i) => (
                      <li key={i}>{s}</li>
                    ))}
                  </ul>
                )}
              </div>
            ) : (
              <p className="text-sm text-slate-500">
                データを評価し、足りないものや改善点を提案します。
              </p>
            )}
          </div>
        </section>

        <section className="lg:col-span-2 card flex flex-col h-[70vh] min-h-[480px]">
          <h2 className="font-semibold flex items-center gap-2 mb-3">💬 AIに話しかける</h2>
          <div className="flex-1 overflow-y-auto space-y-3 pr-1">
            {messages.length === 0 && (
              <p className="text-sm text-slate-500">
                データセットの内容に基づいて答えてくれます。試しに質問してみましょう。
              </p>
            )}
            {messages.map((m) => (
              <div
                key={m.id}
                className={`max-w-[85%] rounded-2xl px-4 py-2 text-sm whitespace-pre-wrap ${
                  m.role === "user"
                    ? "bg-bloom-500 text-white ml-auto"
                    : "bg-slate-100 text-slate-800"
                }`}
              >
                {m.content}
              </div>
            ))}
            <div ref={chatEndRef} />
          </div>
          <form onSubmit={sendMessage} className="mt-3 flex gap-2">
            <input
              className="input flex-1"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              placeholder="質問を入力…"
              disabled={chatBusy}
            />
            <button className="btn-primary" disabled={chatBusy || !chatInput.trim()}>
              {chatBusy ? "…" : "送信"}
            </button>
          </form>
        </section>
      </div>
    </main>
  );
}
