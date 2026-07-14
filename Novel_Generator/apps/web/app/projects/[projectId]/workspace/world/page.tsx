"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { ConfirmLockActions } from "@/components/ConfirmLockActions";
import { getWorldSetting, saveWorldSetting } from "@/lib/api";
import type { ConfirmStatus, LockStatus, WorldBackground } from "@/lib/types";

const EMPTY: WorldBackground = {
  era: "",
  geography: "",
  institutions: "",
  power_system: "",
  historical_events: "",
  society: "",
  technology_level: "",
  culture: "",
  conflicts: "",
};

export default function WorldPage() {
  const params = useParams<{ projectId: string }>();
  const projectId = params.projectId;
  const [form, setForm] = useState<WorldBackground>(EMPTY);
  const [assetId, setAssetId] = useState<string | null>(null);
  const [status, setStatus] = useState<ConfirmStatus | null>(null);
  const [lockStatus, setLockStatus] = useState<LockStatus>("unlocked");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadWorld() {
      setLoading(true);
      try {
        const setting = await getWorldSetting(projectId);
        if (cancelled) return;
        setAssetId(setting.id);
        setForm({ ...EMPTY, ...setting.background_json });
        setStatus(setting.confirm_status);
        setLockStatus(setting.lock_status);
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

    void loadWorld();
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  async function handleSave(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setMessage(null);
    try {
      const saved = await saveWorldSetting(projectId, { background_json: form });
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
        <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-50">世界观与背景</h2>
        <p className="mt-1 text-sm text-zinc-500">维护时代、地理、制度、力量体系等基础设定。</p>
        {assetId && status && (
          <div className="mt-4">
            <ConfirmLockActions
              targetType="world_setting"
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
          {(
            [
              ["era", "时代背景"],
              ["geography", "地理环境"],
              ["institutions", "社会制度"],
              ["power_system", "力量体系"],
              ["technology_level", "科技水平"],
              ["culture", "文化习俗"],
              ["historical_events", "历史事件"],
              ["conflicts", "主要冲突"],
              ["society", "社会结构"],
            ] as const
          ).map(([key, label]) => (
            <label key={key} className="block text-sm">
              <span className="text-zinc-600 dark:text-zinc-300">{label}</span>
              <textarea
                value={form[key] ?? ""}
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
            {saving ? "保存中…" : "保存世界观"}
          </button>
          {message && <span className="text-sm text-zinc-500">{message}</span>}
        </div>
      </form>
    </div>
  );
}
