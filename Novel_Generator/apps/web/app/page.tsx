import { fetchHealth } from "@/lib/api";

export default async function Home() {
  const health = await fetchHealth();

  return (
    <div className="flex flex-1 flex-col items-center justify-center bg-zinc-50 px-6 py-16 dark:bg-zinc-950">
      <main className="w-full max-w-2xl rounded-2xl border border-zinc-200 bg-white p-10 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
        <h1 className="text-3xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
          AI 小说生成平台
        </h1>
        <p className="mt-3 text-zinc-600 dark:text-zinc-400">
          本地优先的单作者创作工作台。Phase 0 工程骨架已就绪。
        </p>

        <section className="mt-8 rounded-xl border border-zinc-200 bg-zinc-50 p-6 dark:border-zinc-700 dark:bg-zinc-800/50">
          <h2 className="text-sm font-medium uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
            API 健康状态
          </h2>
          <div className="mt-3 flex items-center gap-3">
            <span
              className={`inline-block h-3 w-3 rounded-full ${
                health?.status === "ok" ? "bg-emerald-500" : "bg-red-500"
              }`}
            />
            <span className="text-lg font-medium text-zinc-900 dark:text-zinc-50">
              {health?.status === "ok" ? "运行正常" : "无法连接 API"}
            </span>
          </div>
          {health && (
            <pre className="mt-4 rounded-lg bg-zinc-900 p-4 text-sm text-emerald-400">
              {JSON.stringify(health, null, 2)}
            </pre>
          )}
        </section>
      </main>
    </div>
  );
}
