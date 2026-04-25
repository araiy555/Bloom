"use client";

import { useState } from "react";
import Link from "next/link";
import { Nav } from "@/components/Nav";
import { useAuth } from "@/components/AuthProvider";

export default function RegisterPage() {
  const { register } = useAuth();
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setBusy(true);
    try {
      await register(email, password, name);
    } catch (e: any) {
      setErr(e.message || "登録に失敗しました");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <Nav />
      <main className="max-w-md mx-auto px-6 py-12">
        <div className="card space-y-4">
          <h1 className="text-2xl font-bold">新規登録</h1>
          <form onSubmit={onSubmit} className="space-y-3">
            <div>
              <label className="label">表示名</label>
              <input className="input" value={name} onChange={(e) => setName(e.target.value)}
                     placeholder="例: たろう" />
            </div>
            <div>
              <label className="label">メール</label>
              <input className="input" type="email" required value={email}
                     onChange={(e) => setEmail(e.target.value)} />
            </div>
            <div>
              <label className="label">パスワード（8文字以上）</label>
              <input className="input" type="password" required minLength={8}
                     value={password} onChange={(e) => setPassword(e.target.value)} />
            </div>
            {err && <p className="text-sm text-red-600">{err}</p>}
            <button className="btn-primary w-full" disabled={busy}>
              {busy ? "送信中…" : "アカウント作成"}
            </button>
          </form>
          <p className="text-sm text-slate-600 text-center">
            既にアカウントをお持ちの方は <Link href="/login" className="text-bloom-600 underline">ログイン</Link>
          </p>
        </div>
      </main>
    </>
  );
}
