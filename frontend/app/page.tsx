import Link from "next/link";
import { Nav } from "@/components/Nav";

export default function HomePage() {
  return (
    <>
      <Nav />
      <main className="max-w-5xl mx-auto px-6 py-16">
        <section className="text-center space-y-6">
          <h1 className="text-4xl sm:text-5xl font-bold text-slate-900">
            AIを<span className="text-bloom-500">作る</span>のではなく、
            <br className="hidden sm:block" />
            AIを<span className="text-bloom-500">育てて使う</span>。
          </h1>
          <p className="text-lg text-slate-600 max-w-2xl mx-auto">
            データをアップロードし、用途を選ぶだけ。専門知識ゼロでも、自分専用のAIを5分で作れます。
          </p>
          <div className="flex justify-center gap-3 pt-4">
            <Link href="/register" className="btn-primary">無料ではじめる</Link>
            <Link href="/login" className="btn-outline">ログイン</Link>
          </div>
        </section>

        <section className="grid sm:grid-cols-3 gap-4 mt-16">
          {[
            { icon: "💬", title: "話す", desc: "AIアシスタントが「何を作りたい？」と聞いてきます。" },
            { icon: "📥", title: "渡す", desc: "頼まれたデータを画面にドラッグ＆ドロップ。" },
            { icon: "🌱", title: "育つ", desc: "あなた専用のAIが完成。チャットで使い続けられます。" },
          ].map((f) => (
            <div key={f.title} className="card text-center">
              <div className="text-3xl mb-2" aria-hidden>{f.icon}</div>
              <h3 className="font-semibold text-lg">{f.title}</h3>
              <p className="text-sm text-slate-600 mt-1">{f.desc}</p>
            </div>
          ))}
        </section>
      </main>
    </>
  );
}
