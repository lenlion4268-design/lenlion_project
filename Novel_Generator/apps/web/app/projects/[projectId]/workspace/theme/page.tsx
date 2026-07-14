"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { ConfirmLockActions } from "@/components/ConfirmLockActions";
import { getThemeProfile, saveThemeProfile } from "@/lib/api";
import { GENRE_OPTIONS } from "@/lib/labels";
import type { ConfirmStatus, LockStatus, ThemeProfile } from "@/lib/types";

const EMPTY: Omit<
  ThemeProfile,
  "id" | "project_id" | "confirm_status" | "lock_status" | "created_at" | "updated_at"
> = {
  genre: "",
  theme: "",
  target_readers: "",
  narrative_style: "",
  emotional_tone: "",
  pleasure_points: "",
  forbidden_content: "",
};

export default function ThemePage() {
  const params = useParams<{ projectId: string }>();
  const projectId = params.projectId;
  const [form, setForm] = useState(EMPTY);
  const [assetId, setAssetId] = useState<string | null>(null);
  const [status, setStatus] = useState<ConfirmStatus | null>(null);
  const [lockStatus, setLockStatus] = useState<LockStatus>("unlocked");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadTheme() {
      setLoading(true);
      try {
        const profile = await getThemeProfile(projectId);
        if (cancelled) return;
        setAssetId(profile.id);
        setForm({
          genre: profile.genre,
          theme: profile.theme,
          target_readers: profile.target_readers,
          narrative_style: profile.narrative_style,
          emotional_tone: profile.emotional_tone,
          pleasure_points: profile.pleasure_points,
          forbidden_content: profile.forbidden_content,
        });
        setStatus(profile.confirm_status);
        setLockStatus(profile.lock_status);
      } catch {
        if (!cancelled) {
          setForm(EMPTY);
          setAssetId(null);
          setStatus(null);
          setLockStatus("unlocked");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadTheme();
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  async function handleSave(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setMessage(null);
    try {
      const saved = await saveThemeProfile(projectId, form);
      setAssetId(saved.id);
      setStatus(saved.confirm_status);
      setLockStatus(saved.lock_status);
      setMessage("已保存");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "保存失败");
    } finally {
      setSaving(false);
    }
  }

  const isLocked = status === "locked" || lockStatus === "locked";

  if (loading) {
    return <p className="text-sm text-zinc-500">加载中…</p>;
  }

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-50">主题与题材</h2>
        <p className="mt-1 text-sm text-zinc-500">定义创作方向、读者定位与内容边界。</p>
        {assetId && status && (
          <div className="mt-4">
            <ConfirmLockActions
              targetType="theme_profile"
              targetId={assetId}
              confirmStatus={status}
              lockStatus={lockStatus}
              onUpdated={(nextStatus, nextLock) => {
                setStatus(nextStatus);
                setLockStatus(nextLock);
              }}
            />
          </div>
        )}
      </div>

      <form className="grid max-w-2xl gap-4" onSubmit={handleSave}>
        <fieldset disabled={isLocked} className="grid gap-4 disabled:opacity-60">
        <label className="block text-sm">
          <span className="text-zinc-600 dark:text-zinc-300">题材分类</span>
          <select
            value={form.genre}
            onChange={(e) => setForm((prev) => ({ ...prev, genre: e.target.value }))}
            className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-950"
          >
            <option value="">未选择</option>
            {GENRE_OPTIONS.map((genre) => (
              <option key={genre} value={genre}>
                {genre}
              </option>
            ))}
          </select>
        </label>

        {(
          [
            ["theme", "主题描述"],
            ["target_readers", "目标读者"],
            ["narrative_style", "叙事风格"],
            ["emotional_tone", "情绪基调"],
            ["pleasure_points", "爽点类型"],
            ["forbidden_content", "禁忌内容"],
          ] as const
        ).map(([key, label]) => (
          <label key={key} className="block text-sm">
            <span className="text-zinc-600 dark:text-zinc-300">{label}</span>
            <textarea
              value={form[key]}
              onChange={(e) => setForm((prev) => ({ ...prev, [key]: e.target.value }))}
              rows={3}
              className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-950"
            />
          </label>
        ))}

        </fieldset>

        <div className="flex items-center gap-3">
          <button
            type="submit"
            disabled={saving || isLocked}
            className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-60 dark:bg-zinc-100 dark:text-zinc-900"
          >
            {saving ? "保存中…" : "保存主题题材"}
          </button>
          {message && <span className="text-sm text-zinc-500">{message}</span>}
        </div>
      </form>
    </div>
  );
}
