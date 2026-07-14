"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { ConfirmLockActions } from "@/components/ConfirmLockActions";
import { GenerationReadinessPanel } from "@/components/GenerationReadinessPanel";
import { createVolume, listOutlines, listVolumes } from "@/lib/api";
import type { ConfirmStatus, LockStatus, Outline, Volume } from "@/lib/types";

export default function VolumesPage() {
  const params = useParams<{ projectId: string }>();
  const projectId = params.projectId;
  const [volumes, setVolumes] = useState<Volume[]>([]);
  const [outlines, setOutlines] = useState<Outline[]>([]);
  const [selectedOutlineId, setSelectedOutlineId] = useState<string>("");
  const [title, setTitle] = useState("");
  const [volumeNo, setVolumeNo] = useState(1);
  const [stageGoal, setStageGoal] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadData() {
      setLoading(true);
      try {
        const [volumeResponse, outlineResponse] = await Promise.all([
          listVolumes(projectId),
          listOutlines(projectId),
        ]);
        if (cancelled) return;
        setVolumes(volumeResponse.items);
        setOutlines(outlineResponse.items);
        const lockedOutline = outlineResponse.items.find(
          (item) => item.confirm_status === "locked" || item.lock_status === "locked",
        );
        if (lockedOutline) {
          setSelectedOutlineId(lockedOutline.id);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadData();
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  async function reloadVolumes() {
    const response = await listVolumes(projectId);
    setVolumes(response.items);
  }

  function handleReviewUpdated(
    volumeId: string,
    confirmStatus: ConfirmStatus,
    lockStatus: LockStatus,
  ) {
    setVolumes((prev) =>
      prev.map((item) =>
        item.id === volumeId
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
      await createVolume(projectId, {
        title,
        volume_no: volumeNo,
        stage_goal: stageGoal,
        outline_id: selectedOutlineId || null,
      });
      setTitle("");
      setStageGoal("");
      setVolumeNo((prev) => prev + 1);
      setMessage("故事卷草稿已创建");
      await reloadVolumes();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "创建失败");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-50">故事卷草稿</h2>
        <p className="mt-1 text-sm text-zinc-500">长篇项目可将大纲拆分为多个故事卷，草稿不会自动进入生成上下文。</p>
      </div>

      <form className="mb-8 grid max-w-2xl gap-4" onSubmit={handleCreate}>
        {outlines.length > 0 && (
          <label className="block text-sm">
            <span className="text-zinc-600 dark:text-zinc-300">关联大纲</span>
            <select
              value={selectedOutlineId}
              onChange={(e) => setSelectedOutlineId(e.target.value)}
              className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-950"
            >
              <option value="">未关联</option>
              {outlines.map((outline) => (
                <option key={outline.id} value={outline.id}>
                  {outline.title || "未命名大纲"}
                </option>
              ))}
            </select>
          </label>
        )}
        <label className="block text-sm">
          <span className="text-zinc-600 dark:text-zinc-300">卷号</span>
          <input
            type="number"
            min={1}
            value={volumeNo}
            onChange={(e) => setVolumeNo(Number(e.target.value))}
            className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-950"
          />
        </label>
        <label className="block text-sm">
          <span className="text-zinc-600 dark:text-zinc-300">卷标题</span>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-950"
          />
        </label>
        <label className="block text-sm">
          <span className="text-zinc-600 dark:text-zinc-300">阶段目标</span>
          <textarea
            value={stageGoal}
            onChange={(e) => setStageGoal(e.target.value)}
            rows={4}
            className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-950"
          />
        </label>
        <div className="flex items-center gap-3">
          <button
            type="submit"
            disabled={saving}
            className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-60 dark:bg-zinc-100 dark:text-zinc-900"
          >
            {saving ? "创建中…" : "创建故事卷草稿"}
          </button>
          {message && <span className="text-sm text-zinc-500">{message}</span>}
        </div>
      </form>

      <section>
        <h3 className="mb-3 text-sm font-medium text-zinc-500">已有故事卷</h3>
        {loading ? (
          <p className="text-sm text-zinc-500">加载中…</p>
        ) : volumes.length === 0 ? (
          <p className="text-sm text-zinc-500">暂无故事卷草稿</p>
        ) : (
          <div className="space-y-3">
            {volumes.map((volume) => (
              <article
                key={volume.id}
                className="rounded-xl border border-zinc-200 p-4 dark:border-zinc-700"
              >
                <h4 className="font-medium text-zinc-900 dark:text-zinc-50">
                  第 {volume.volume_no} 卷 · {volume.title || "未命名"}
                </h4>
                {volume.stage_goal && (
                  <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-300">{volume.stage_goal}</p>
                )}
                <div className="mt-3">
                  <ConfirmLockActions
                    targetType="volume"
                    targetId={volume.id}
                    confirmStatus={volume.confirm_status}
                    lockStatus={volume.lock_status}
                    onUpdated={(confirmStatus, lockStatus) =>
                      handleReviewUpdated(volume.id, confirmStatus, lockStatus)
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
        targetStage="volumes"
        outlineId={selectedOutlineId || undefined}
        actionLabel="AI 生成故事卷"
        onGenerated={() => void reloadVolumes()}
      />
    </div>
  );
}
