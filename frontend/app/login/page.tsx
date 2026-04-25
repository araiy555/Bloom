"use client";

import { useState } from "react";
import Link from "next/link";
import { Nav } from "@/components/Nav";
import { useAuth } from "@/components/AuthProvider";

export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setBusy(true);
    try {
      await login(email, password);
    } catch (e: any) {
      setErr(e.message || "ログインに失敗しました");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <Nav />
      <main className="max-w-md mx-auto px-6 py-12">
        <div className="card space-y-4">
          <h1 className="text-2xl font-bold">ログイン</h1>
          <form onSubmit={onSubmit} className="space-y-3">
            <div>
              <label className="label">メール</label>
              <input className="input" type="email" required value={email}
                     onChange={(e) => setEmail(e.target.value)} />
            </div>
            <div>
              <label className="label">パスワード</label>
              <input className="input" type="password" required minLength={8}
                     value={password} onChange={(e) => setPassword(e.target.value)} />
            </div>
            {err && <p className="text-sm text-red-600">{err}</p>}
            <button className="btn-primary w-full" disabled={busy}>
              {busy ? "送信中…" : "ログイン"}
            </button>
          </form>
          <p className="text-sm text-slate-600 text-center">
            アカウントが無い方は <Link href="/register" className="text-bloom-600 underline">新規登録</Link>
          </p>
        </div>
      </main>
    </>
  );
}
