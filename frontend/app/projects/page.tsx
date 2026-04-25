"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Nav } from "@/components/Nav";
import { Protected } from "@/components/Protected";
import { api, type Project } from "@/lib/api";

const STATUS_LABEL: Record<string, string> = {
  draft: "作成中",
  ready: "準備完了",
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
  const router = useRouter();
  const [projects, setProjects] = useState<Project[] | null>(null);
  const [creating, setCreating] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    setErr(null);
    try {
      setProjects(await api<Project[]>("/projects"));
    } catch (e: any) {
      setErr(e.message);
    }
  }

  useEffect(() => { load(); }, []);

  async function startNew() {
    setCreating(true);
    setErr(null);
    try {
      const p = await api<Project>("/projects", {
        method: "POST",
        body: { name: "新しいAI" },
      });
      router.push(`/projects/${p.id}`);
    } catch (e: any) {
      setErr(e.message);
      setCreating(false);
    }
  }

  return (
    <main className="max-w-5xl mx-auto px-6 py-10 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">あなたのAI</h1>
        <button onClick={startNew} disabled={creating} className="btn-primary">
          {creating ? "作成中…" : "+ 新しいAIを育てる"}
        </button>
      </div>

      {err && <p className="text-sm text-red-600">{err}</p>}

      {projects === null ? (
        <p className="text-slate-500">読み込み中…</p>
      ) : projects.length === 0 ? (
        <div className="card text-center text-slate-600 space-y-3">
          <p className="text-3xl">🌱</p>
          <p>まだAIがありません。</p>
          <p className="text-sm">
            「+ 新しいAIを育てる」を押すと、AIアシスタントが対話で作り方を案内します。
          </p>
        </div>
      ) : (
        <ul className="grid sm:grid-cols-2 gap-4">
          {projects.map((p) => (
            <li key={p.id}>
              <Link href={`/projects/${p.id}`} className="card block hover:shadow-md transition">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <div className="text-3xl">🌱</div>
                    <h3 className="font-semibold mt-1 truncate">{p.name}</h3>
                    <p className="text-xs text-slate-500">
                      ファイル {p.file_count}
                    </p>
                  </div>
                  <span className="text-xs px-2 py-1 rounded-full bg-bloom-100 text-bloom-700 whitespace-nowrap">
                    {STATUS_LABEL[p.status] ?? p.status}
                  </span>
                </div>
                {p.goal && (
                  <p className="text-sm text-slate-600 mt-2 line-clamp-2">{p.goal}</p>
                )}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
