"use client";

import { useEffect, useState } from "react";

import { createGenerationJob, getGenerationJob, getReadiness } from "@/lib/api";
import type { GenerationJob, ModelProfile, ReadinessResponse, ReadinessStage } from "@/lib/types";

async function waitForJobs(jobIds: string[]): Promise<GenerationJob[]> {
  const results: GenerationJob[] = [];
  for (const jobId of jobIds) {
    let latest = await getGenerationJob(jobId);
    for (let attempt = 0; attempt < 20 && latest.status === "queued"; attempt += 1) {
      await new Promise((resolve) => setTimeout(resolve, 300));
      latest = await getGenerationJob(jobId);
    }
    results.push(latest);
  }
  return results;
}

export function GenerationReadinessPanel({
  projectId,
  targetStage,
  outlineId,
  volumeId,
  batchCount = 1,
  modelProfile = "default",
  asyncMode = false,
  actionLabel = "AI 生成",
  onGenerated,
}: {
  projectId: string;
  targetStage: ReadinessStage;
  outlineId?: string;
  volumeId?: string;
  batchCount?: number;
  modelProfile?: ModelProfile;
  asyncMode?: boolean;
  actionLabel?: string;
  onGenerated?: (jobs: GenerationJob[]) => void;
}) {
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    let cancelled = false;

    async function loadReadiness() {
      setLoading(true);
      try {
        const result = await getReadiness(projectId, targetStage, {
          outline_id: outlineId,
          volume_id: volumeId,
        });
        if (!cancelled) {
          setReadiness(result);
        }
      } catch {
        if (!cancelled) {
          setReadiness(null);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadReadiness();
    return () => {
      cancelled = true;
    };
  }, [projectId, targetStage, outlineId, volumeId, refreshKey]);

  const ready = readiness?.ready ?? false;

  async function handleGenerate() {
    setGenerating(true);
    setError(null);
    setMessage(null);
    try {
      const result = await createGenerationJob(projectId, {
        target_stage: targetStage,
        outline_id: outlineId,
        volume_id: volumeId,
        batch_count: batchCount,
        model_profile: modelProfile,
        async_mode: asyncMode,
      });
      let jobs = result.jobs;
      if (asyncMode && jobs.some((job) => job.status === "queued")) {
        jobs = await waitForJobs(jobs.map((job) => job.id));
      }
      const failed = jobs.filter((job) => job.status === "failed");
      if (failed.length > 0) {
        setError(failed[0]?.error_message ?? "部分任务失败");
      } else {
        setMessage(
          jobs.length > 1
            ? `批量生成完成，共 ${jobs.length} 个草稿。`
            : asyncMode
              ? "异步任务已完成。"
              : "生成完成，已创建草稿资产。",
        );
      }
      onGenerated?.(jobs);
      setRefreshKey((value) => value + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "生成失败");
    } finally {
      setGenerating(false);
    }
  }

  return (
    <section className="mt-8 rounded-xl border border-zinc-200 bg-zinc-50 p-4 dark:border-zinc-700 dark:bg-zinc-800/40">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-medium text-zinc-900 dark:text-zinc-50">生成准入检查</h3>
          <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
            {loading
              ? "检查中…"
              : ready
                ? "已满足生成前置条件"
                : "尚未满足生成前置条件"}
          </p>
          <p className="mt-1 text-xs text-zinc-400">
            模型档位：{modelProfile}
            {asyncMode ? " · 异步执行" : " · 同步执行"}
          </p>
        </div>
        <button
          type="button"
          disabled={!ready || generating}
          onClick={() => void handleGenerate()}
          className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-40 dark:bg-zinc-100 dark:text-zinc-900"
        >
          {generating ? "生成中…" : actionLabel}
        </button>
      </div>

      {message && <p className="mt-3 text-sm text-emerald-700 dark:text-emerald-300">{message}</p>}
      {error && <p className="mt-3 text-sm text-red-600 dark:text-red-400">{error}</p>}

      {!loading && readiness && !ready && (
        <ul className="mt-3 space-y-1 text-sm text-amber-700 dark:text-amber-300">
          {readiness.blocked_reasons.map((reason) => (
            <li key={reason}>· {reason}</li>
          ))}
        </ul>
      )}
    </section>
  );
}
