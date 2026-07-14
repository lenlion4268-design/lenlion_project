"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { ConfirmLockActions } from "@/components/ConfirmLockActions";
import { GenerationReadinessPanel } from "@/components/GenerationReadinessPanel";
import { createOutline, listOutlines } from "@/lib/api";
import type { ConfirmStatus, LockStatus, Outline } from "@/lib/types";

export default function OutlinePage() {
  const params = useParams<{ projectId: string }>();
  const projectId = params.projectId;
  const [outlines, setOutlines] = useState<Outline[]>([]);
  const [title, setTitle] = useState("");
  const [summary, setSummary] = useState("");
  const [endingDirection, setEndingDirection] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadOutlines() {
      setLoading(true);
      try {
        const response = await listOutlines(projectId);
        if (!cancelled) {
          setOutlines(response.items);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadOutlines();
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  async function reloadOutlines() {
    const response = await listOutlines(projectId);
    setOutlines(response.items);
  }

  function handleReviewUpdated(
    outlineId: string,
    confirmStatus: ConfirmStatus,
    lockStatus: LockStatus,
  ) {
    setOutlines((prev) =>
      prev.map((item) =>
        item.id === outlineId
          ? { ...item, confirm_status: confirmStatus, lock_status: lockStatus }
          : item,
      ),
    );
  }

  async function handleCreate(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setMessage(null);
    try {
      await createOutline(projectId, {
        title,
        summary,
        ending_direction: endingDirection,
      });
      setTitle("");
      setSummary("");
      setEndingDirection("");
      setMessage("大纲草稿已创建");
      await reloadOutlines();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "创建失败");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-50">大纲草稿</h2>
        <p className="mt-1 text-sm text-zinc-500">长篇项目可创建多个大纲草稿，默认不会进入生成上下文。</p>
      </div>

      <form className="mb-8 grid max-w-2xl gap-4" onSubmit={handleCreate}>
        <label className="block text-sm">
          <span className="text-zinc-600 dark:text-zinc-300">标题</span>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-950"
          />
        </label>
        <label className="block text-sm">
          <span className="text-zinc-600 dark:text-zinc-300">主线摘要</span>
          <textarea
            value={summary}
            onChange={(e) => setSummary(e.target.value)}
            rows={4}
            className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-950"
          />
        </label>
        <label className="block text-sm">
          <span className="text-zinc-600 dark:text-zinc-300">结局方向</span>
          <textarea
            value={endingDirection}
            onChange={(e) => setEndingDirection(e.target.value)}
            rows={3}
            className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-950"
          />
        </label>
        <div className="flex items-center gap-3">
          <button
            type="submit"
            disabled={saving}
            className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-60 dark:bg-zinc-100 dark:text-zinc-900"
          >
            {saving ? "创建中…" : "创建大纲草稿"}
          </button>
          {message && <span className="text-sm text-zinc-500">{message}</span>}
        </div>
      </form>

      <section>
        <h3 className="mb-3 text-sm font-medium text-zinc-500">已有大纲</h3>
        {loading ? (
          <p className="text-sm text-zinc-500">加载中…</p>
        ) : outlines.length === 0 ? (
          <p className="text-sm text-zinc-500">暂无大纲草稿</p>
        ) : (
          <div className="space-y-3">
            {outlines.map((outline) => (
              <article
                key={outline.id}
                className="rounded-xl border border-zinc-200 p-4 dark:border-zinc-700"
              >
                <h4 className="font-medium text-zinc-900 dark:text-zinc-50">
                  {outline.title || "未命名大纲"}
                </h4>
                {outline.summary && (
                  <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-300">{outline.summary}</p>
                )}
                <div className="mt-3">
                  <ConfirmLockActions
                    targetType="outline"
                    targetId={outline.id}
                    confirmStatus={outline.confirm_status}
                    lockStatus={outline.lock_status}
                    onUpdated={(confirmStatus, lockStatus) =>
                      handleReviewUpdated(outline.id, confirmStatus, lockStatus)
                    }
                  />
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      <GenerationReadinessPanel
        projectId={projectId}
        targetStage="outline"
        actionLabel="AI 生成大纲"
        onGenerated={() => void reloadOutlines()}
      />
    </div>
  );
}
