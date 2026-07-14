"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { createProject, listProjects } from "@/lib/api";
import { HomeNav } from "@/components/HomeNav";
import {
  formatDateTime,
  GENRE_OPTIONS,
  MODE_LABELS,
  STAGE_LABELS,
  STATUS_LABELS,
} from "@/lib/labels";
import type { NovelProject, ProjectMode, ProjectStatus } from "@/lib/types";

export function BookshelfPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<NovelProject[]>([]);
  const [statusFilter, setStatusFilter] = useState<ProjectStatus | "all">("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({
    title: "",
    genre: GENRE_OPTIONS[0],
    mode: "long" as ProjectMode,
  });

  useEffect(() => {
    let cancelled = false;

    async function loadProjects() {
      setLoading(true);
      setError(null);
      try {
        const response = await listProjects(
          statusFilter === "all" ? undefined : statusFilter,
        );
        if (!cancelled) {
          setProjects(response.items);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "加载项目失败");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadProjects();
    return () => {
      cancelled = true;
    };
  }, [statusFilter]);

  async function handleCreate(event: React.FormEvent) {
    event.preventDefault();
    if (!form.title.trim()) return;
    setCreating(true);
    setError(null);
    try {
      const project = await createProject({
        title: form.title.trim(),
        genre: form.genre,
        mode: form.mode,
      });
      setShowCreate(false);
      setForm({ title: "", genre: GENRE_OPTIONS[0], mode: "long" });
      router.push(`/projects/${project.id}/workspace/characters`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "创建项目失败");
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="min-h-full bg-zinc-50 dark:bg-zinc-950">
      <header className="border-b border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
        <div className="mx-auto max-w-6xl px-6 py-5">
          <HomeNav />
          <div className="mt-4 flex items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-50">我的书架</h1>
              <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
                创建并管理你的小说创作项目
              </p>
            </div>
            <button
              type="button"
              onClick={() => setShowCreate(true)}
              className="shrink-0 rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200"
            >
              新建项目
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-8">
        <div className="mb-6 flex items-center gap-3">
          <span className="text-sm text-zinc-500 dark:text-zinc-400">状态筛选</span>
          {(["all", "active", "archived"] as const).map((value) => (
            <button
              key={value}
              type="button"
              onClick={() => setStatusFilter(value)}
              className={`rounded-full px-3 py-1 text-sm ${
                statusFilter === value
                  ? "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
                  : "bg-white text-zinc-600 ring-1 ring-zinc-200 dark:bg-zinc-900 dark:text-zinc-300 dark:ring-zinc-700"
              }`}
            >
              {value === "all" ? "全部" : STATUS_LABELS[value]}
            </button>
          ))}
        </div>

        {error && (
          <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300">
            {error}
          </div>
        )}

        {loading ? (
          <p className="text-sm text-zinc-500">加载中…</p>
        ) : projects.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-zinc-300 bg-white p-12 text-center dark:border-zinc-700 dark:bg-zinc-900">
            <p className="text-zinc-600 dark:text-zinc-300">还没有项目，点击「新建项目」开始创作。</p>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {projects.map((project) => (
              <Link
                key={project.id}
                href={`/projects/${project.id}/workspace`}
                className="group rounded-2xl border border-zinc-200 bg-white p-5 shadow-sm transition hover:border-zinc-300 hover:shadow-md dark:border-zinc-800 dark:bg-zinc-900 dark:hover:border-zinc-700"
              >
                <div className="flex items-start justify-between gap-3">
                  <h2 className="text-lg font-semibold text-zinc-900 group-hover:text-zinc-700 dark:text-zinc-50">
                    {project.title}
                  </h2>
                  <span className="shrink-0 rounded-full bg-zinc-100 px-2 py-0.5 text-xs text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300">
                    {MODE_LABELS[project.mode]}
                  </span>
                </div>
                <p className="mt-2 text-sm text-zinc-500 dark:text-zinc-400">
                  题材：{project.genre || "未设置"}
                </p>
                <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
                  当前阶段：{STAGE_LABELS[project.current_stage]}
                </p>
                <div className="mt-4 flex items-center justify-between text-xs text-zinc-400">
                  <span>{STATUS_LABELS[project.status]}</span>
                  <span>{formatDateTime(project.updated_at)}</span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </main>

      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl dark:bg-zinc-900">
            <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">新建小说项目</h2>
            <form className="mt-4 space-y-4" onSubmit={handleCreate}>
              <label className="block text-sm">
                <span className="text-zinc-600 dark:text-zinc-300">书名</span>
                <input
                  required
                  value={form.title}
                  onChange={(e) => setForm((prev) => ({ ...prev, title: e.target.value }))}
                  className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-950"
                  placeholder="输入书名"
                />
              </label>
              <label className="block text-sm">
                <span className="text-zinc-600 dark:text-zinc-300">题材</span>
                <select
                  value={form.genre}
                  onChange={(e) => setForm((prev) => ({ ...prev, genre: e.target.value }))}
                  className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-950"
                >
                  {GENRE_OPTIONS.map((genre) => (
                    <option key={genre} value={genre}>
                      {genre}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block text-sm">
                <span className="text-zinc-600 dark:text-zinc-300">创作模式</span>
                <select
                  value={form.mode}
                  onChange={(e) =>
                    setForm((prev) => ({ ...prev, mode: e.target.value as ProjectMode }))
                  }
                  className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-950"
                >
                  <option value="long">长篇</option>
                  <option value="short">短篇</option>
                </select>
              </label>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreate(false)}
                  className="rounded-lg px-4 py-2 text-sm text-zinc-600 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-zinc-800"
                >
                  取消
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-60 dark:bg-zinc-100 dark:text-zinc-900"
                >
                  {creating ? "创建中…" : "创建"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
