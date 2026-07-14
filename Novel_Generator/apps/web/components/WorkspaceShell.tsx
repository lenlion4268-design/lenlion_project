"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { HomeNav } from "@/components/HomeNav";
import { getProject, updateProject } from "@/lib/api";
import { MODE_LABELS, STAGE_LABELS, STATUS_LABELS } from "@/lib/labels";
import type { NovelProject, ProjectStage } from "@/lib/types";

const STAGES: ProjectStage[] = [
  "characters",
  "theme",
  "world",
  "outline",
  "volumes",
  "chapters",
];

export function WorkspaceShell({
  projectId,
  children,
}: {
  projectId: string;
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const [project, setProject] = useState<NovelProject | null>(null);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  useEffect(() => {
    void getProject(projectId).then(setProject).catch(() => setProject(null));
  }, [projectId]);

  useEffect(() => {
    const stage = STAGES.find((item) => pathname.endsWith(`/${item}`));
    if (!stage || !project || project.current_stage === stage) return;
    void updateProject(projectId, { current_stage: stage })
      .then((updated) => {
        setProject(updated);
        setSaveMessage("阶段已同步");
      })
      .catch(() => setSaveMessage("阶段同步失败"));
  }, [pathname, project, projectId]);

  useEffect(() => {
    if (!saveMessage) return;
    const timer = window.setTimeout(() => setSaveMessage(null), 2000);
    return () => window.clearTimeout(timer);
  }, [saveMessage]);

  return (
    <div className="flex min-h-full flex-col bg-zinc-50 dark:bg-zinc-950">
      <header className="border-b border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
        <div className="mx-auto max-w-7xl px-6 py-4">
          <HomeNav />
          <div className="mt-4 flex items-start justify-between gap-4">
            <div className="min-w-0">
              <p className="text-xs text-zinc-500 dark:text-zinc-400">
                <Link
                  href="/"
                  className="hover:text-zinc-700 dark:text-zinc-400 dark:hover:text-zinc-200"
                >
                  我的书架
                </Link>
                <span className="mx-1">/</span>
                <span>{project?.title ?? "加载中…"}</span>
              </p>
              <h1 className="truncate text-xl font-semibold text-zinc-900 dark:text-zinc-50">
                创作工作台
              </h1>
              {project && (
                <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
                  {MODE_LABELS[project.mode]} · {project.genre || "未设置题材"} ·{" "}
                  {STATUS_LABELS[project.status]}
                </p>
              )}
            </div>
            <div className="text-right text-sm text-zinc-500 dark:text-zinc-400">
              <p>当前阶段：{project ? STAGE_LABELS[project.current_stage] : "—"}</p>
              <p className="mt-1">锁定状态：{project ? "见各资产卡片" : "—"}</p>
              <p className="mt-1">{saveMessage ?? "草稿自动保存"}</p>
            </div>
          </div>
        </div>
      </header>

      <div className="mx-auto flex w-full max-w-7xl flex-1 gap-0 px-0 py-0 lg:px-6 lg:py-6">
        <aside className="w-52 shrink-0 border-r border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900 lg:rounded-xl lg:border lg:shadow-sm">
          <p className="mb-3 text-xs font-medium uppercase tracking-wide text-zinc-400">
            创作阶段
          </p>
          <nav className="space-y-1">
            {STAGES.map((stage) => {
              const href = `/projects/${projectId}/workspace/${stage}`;
              const active = pathname.endsWith(`/${stage}`);
              return (
                <Link
                  key={stage}
                  href={href}
                  className={`block rounded-lg px-3 py-2 text-sm ${
                    active
                      ? "bg-zinc-900 font-medium text-white dark:bg-zinc-100 dark:text-zinc-900"
                      : "text-zinc-600 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-zinc-800"
                  }`}
                >
                  {STAGE_LABELS[stage]}
                </Link>
              );
            })}
          </nav>
        </aside>

        <main className="min-w-0 flex-1 bg-white p-6 dark:bg-zinc-900 lg:rounded-xl lg:border lg:border-zinc-200 lg:shadow-sm dark:lg:border-zinc-800">
          {children}
        </main>
      </div>
    </div>
  );
}
