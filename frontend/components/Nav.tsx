"use client";

import Link from "next/link";
import { useAuth } from "@/components/AuthProvider";

export function Nav() {
  const { user, logout } = useAuth();
  return (
    <nav className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-white/70 backdrop-blur sticky top-0 z-10">
      <Link href="/" className="flex items-center gap-2 font-bold text-xl text-bloom-600">
        <span aria-hidden>🌱</span>
        <span>Bloom</span>
      </Link>
      <div className="flex items-center gap-3 text-sm">
        {user ? (
          <>
            <Link href="/projects" className="btn-ghost">プロジェクト</Link>
            <span className="text-slate-500 hidden sm:inline">{user.email}</span>
            <button onClick={logout} className="btn-outline">ログアウト</button>
          </>
        ) : (
          <>
            <Link href="/login" className="btn-ghost">ログイン</Link>
            <Link href="/register" className="btn-primary">はじめる</Link>
          </>
        )}
      </div>
    </nav>
  );
}
