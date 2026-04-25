"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Nav } from "@/components/Nav";
import { Protected } from "@/components/Protected";
import {
  api,
  type ChatMessage,
  type DatasetFile,
  type Project,
} from "@/lib/api";

const STATUS_LABEL: Record<string, string> = {
  draft: "作成中",
  ready: "準備完了",
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
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [renaming, setRenaming] = useState(false);
  const [nameDraft, setNameDraft] = useState("");
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

  async function uploadFiles(filesToUpload: FileList | File[] | null) {
    if (!filesToUpload) return;
    const arr = Array.from(filesToUpload);
    if (arr.length === 0) return;
    setUploading(true);
    setErr(null);
    const newlyUploaded: string[] = [];
    for (const file of arr) {
      const fd = new FormData();
      fd.append("upload", file);
      try {
        await api(`/projects/${projectId}/files`, {
          method: "POST",
          body: fd,
          raw: true,
        });
        newlyUploaded.push(file.name);
      } catch (e: any) {
        setErr(`${file.name}: ${e.message}`);
      }
    }
    if (fileInputRef.current) fileInputRef.current.value = "";
    setUploading(false);
    await refresh();

    if (newlyUploaded.length > 0) {
      const note =
        newlyUploaded.length === 1
          ? `「${newlyUploaded[0]}」をアップロードしました。確認して、次に必要なものを教えてください。`
          : `${newlyUploaded.length} 個のファイル（${newlyUploaded
              .slice(0, 3)
              .map((n) => `「${n}」`)
              .join("、")}${newlyUploaded.length > 3 ? " ほか" : ""}）をアップロードしました。確認して、次に必要なものを教えてください。`;
      await sendRaw(note);
    }
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
    uploadFiles(e.dataTransfer.files);
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

  async function sendRaw(text: string) {
    setChatBusy(true);
    try {
      const res = await api<{ user_message: ChatMessage; assistant_message: ChatMessage }>(
        `/projects/${projectId}/chat`,
        { method: "POST", body: { message: text } }
      );
      setMessages((m) => [...m, res.user_message, res.assistant_message]);
      // refresh project (status, goal may have changed)
      api<Project>(`/projects/${projectId}`).then(setProject).catch(() => {});
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setChatBusy(false);
    }
  }

  async function sendMessage(e: React.FormEvent) {
    e.preventDefault();
    if (!chatInput.trim() || chatBusy) return;
    const text = chatInput;
    setChatInput("");
    await sendRaw(text);
  }

  async function saveName() {
    if (!nameDraft.trim()) {
      setRenaming(false);
      return;
    }
    try {
      const updated = await api<Project>(`/projects/${projectId}`, {
        method: "PATCH",
        body: { name: nameDraft.trim() },
      });
      setProject(updated);
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setRenaming(false);
    }
  }

  if (!project) {
    return <main className="p-8 text-slate-500">読み込み中…</main>;
  }

  return (
    <main className="max-w-6xl mx-auto px-6 py-6 space-y-4">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="min-w-0">
          <Link href="/projects" className="text-sm text-slate-500 hover:underline">
            ← 一覧へ
          </Link>
          <div className="flex items-center gap-2 mt-1">
            {renaming ? (
              <input
                autoFocus
                className="input max-w-xs"
                value={nameDraft}
                onChange={(e) => setNameDraft(e.target.value)}
                onBlur={saveName}
                onKeyDown={(e) => {
                  if (e.key === "Enter") saveName();
                  if (e.key === "Escape") setRenaming(false);
                }}
              />
            ) : (
              <button
                onClick={() => {
                  setNameDraft(project.name);
                  setRenaming(true);
                }}
                className="text-2xl font-bold hover:underline"
                title="クリックで名前を変更"
              >
                {project.name}
              </button>
            )}
            <span className="text-xs px-2 py-1 rounded-full bg-bloom-100 text-bloom-700">
              {STATUS_LABEL[project.status] ?? project.status}
            </span>
          </div>
          {project.goal && (
            <p className="text-sm text-slate-500 mt-1 truncate max-w-xl">
              目的: {project.goal}
            </p>
          )}
        </div>
        <button onClick={deleteProject} className="btn-outline text-red-600 border-red-200">
          AIを削除
        </button>
      </div>

      {err && <p className="text-sm text-red-600">{err}</p>}

      <div className="grid lg:grid-cols-3 gap-4">
        <section
          className="lg:col-span-2 card flex flex-col h-[78vh] min-h-[520px] relative"
          onDragOver={(e) => {
            e.preventDefault();
            if (!dragOver) setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
        >
          {dragOver && (
            <div className="absolute inset-0 z-10 bg-bloom-100/80 border-2 border-dashed border-bloom-500 rounded-2xl flex items-center justify-center text-bloom-700 font-medium pointer-events-none">
              ここにドロップして追加
            </div>
          )}
          <div className="flex-1 overflow-y-auto space-y-3 pr-1">
            {messages.length === 0 && (
              <p className="text-sm text-slate-500">読み込み中…</p>
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
            {chatBusy && (
              <div className="bg-slate-100 text-slate-500 text-sm rounded-2xl px-4 py-2 max-w-[85%] animate-pulse">
                考え中…
              </div>
            )}
            <div ref={chatEndRef} />
          </div>
          <form onSubmit={sendMessage} className="mt-3 flex gap-2 items-end">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="btn-outline shrink-0"
              title="ファイルを添付"
              disabled={uploading}
            >
              📎
            </button>
            <input
              type="file"
              multiple
              ref={fileInputRef}
              className="hidden"
              onChange={(e) => uploadFiles(e.target.files)}
            />
            <input
              className="input flex-1"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              placeholder={uploading ? "アップロード中…" : "メッセージを入力 / ファイルをドロップ"}
              disabled={chatBusy || uploading}
            />
            <button className="btn-primary shrink-0" disabled={chatBusy || !chatInput.trim()}>
              送信
            </button>
          </form>
        </section>

        <aside className="card space-y-3 h-fit">
          <h2 className="font-semibold flex items-center gap-2">📦 アップロード済み</h2>
          {files.length === 0 ? (
            <p className="text-sm text-slate-500">
              まだ何も追加されていません。AIに聞かれたものをこの画面にドラッグ＆ドロップしてください。
            </p>
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
                    className="text-xs text-red-600 hover:underline shrink-0"
                    onClick={() => deleteFile(f.id)}
                  >
                    削除
                  </button>
                </li>
              ))}
            </ul>
          )}
        </aside>
      </div>
    </main>
  );
}
