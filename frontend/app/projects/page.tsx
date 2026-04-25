"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Nav } from "@/components/Nav";
import { Protected } from "@/components/Protected";
import { api, type Project } from "@/lib/api";

const TYPE_OPTIONS = [
  { value: "manga", label: "漫画", emoji: "🎨" },
  { value: "excel", label: "Excel / 表", emoji: "📊" },
  { value: "sales", label: "営業", emoji: "💼" },
  { value: "other", label: "その他", emoji: "✨" },
];

const STATUS_LABEL: Record<string, string> = {
  draft: "未作成",
  training: "学習中",
  ready: "完成",
};

export default function ProjectsPage() {
  return (
    <Protected>
      <Nav />
      <ProjectsInner />
    </Protected>
  );
}

function ProjectsInner() {
  const [projects, setProjects] = useState<Project[] | null>(null);
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");
  const [type, setType] = useState("other");
  const [purpose, setPurpose] = useState("");
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    setErr(null);
    try {
      const list = await api<Project[]>("/projects");
      setProjects(list);
    } catch (e: any) {
      setErr(e.message);
    }
  }

  useEffect(() => { load(); }, []);

  async function create(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    try {
      await api<Project>("/projects", {
        method: "POST",
        body: { name, type, purpose },
      });
      setName(""); setPurpose(""); setType("other"); setCreating(false);
      load();
    } catch (e: any) {
      setErr(e.message);
    }
  }

  return (
    <main className="max-w-5xl mx-auto px-6 py-10 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">あなたのAI</h1>
        <button onClick={() => setCreating((v) => !v)} className="btn-primary">
          {creating ? "閉じる" : "+ 新しいAIを作る"}
        </button>
      </div>

      {creating && (
        <form onSubmit={create} className="card space-y-4">
          <div>
            <label className="label">AIの名前</label>
            <input className="input" required value={name}
                   onChange={(e) => setName(e.target.value)}
                   placeholder="例: 営業メールアシスタント" />
          </div>
          <div>
            <label className="label">タイプ</label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {TYPE_OPTIONS.map((t) => (
                <button type="button" key={t.value}
                        onClick={() => setType(t.value)}
                        className={`rounded-xl border p-3 text-sm font-medium transition ${
                          type === t.value
                            ? "border-bloom-500 bg-bloom-50"
                            : "border-slate-300 hover:bg-slate-50"
                        }`}>
                  <span className="text-2xl block">{t.emoji}</span>
                  {t.label}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="label">何に使いたい？（任意）</label>
            <textarea className="input min-h-[80px]" value={purpose}
                      onChange={(e) => setPurpose(e.target.value)}
                      placeholder="例: お客さんからの問い合わせメールに自動で返信したい" />
          </div>
          {err && <p className="text-sm text-red-600">{err}</p>}
          <button className="btn-primary w-full">作成する</button>
        </form>
      )}

      {projects === null ? (
        <p className="text-slate-500">読み込み中…</p>
      ) : projects.length === 0 ? (
        <div className="card text-center text-slate-600">
          まだAIがありません。「+ 新しいAIを作る」から始めましょう。
        </div>
      ) : (
        <ul className="grid sm:grid-cols-2 gap-4">
          {projects.map((p) => {
            const typeMeta = TYPE_OPTIONS.find((t) => t.value === p.type);
            return (
              <li key={p.id}>
                <Link href={`/projects/${p.id}`} className="card block hover:shadow-md transition">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="text-3xl">{typeMeta?.emoji ?? "✨"}</div>
                      <h3 className="font-semibold mt-1">{p.name}</h3>
                      <p className="text-xs text-slate-500">
                        {typeMeta?.label ?? p.type} ・ ファイル {p.file_count}
                      </p>
                    </div>
                    <span className="text-xs px-2 py-1 rounded-full bg-bloom-100 text-bloom-700">
                      {STATUS_LABEL[p.status] ?? p.status}
                    </span>
                  </div>
                  {p.purpose && (
                    <p className="text-sm text-slate-600 mt-2 line-clamp-2">{p.purpose}</p>
                  )}
                </Link>
              </li>
            );
          })}
        </ul>
      )}
    </main>
  );
}
