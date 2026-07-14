"use client";

import { useEffect, useState } from "react";

import { getSettings, patchPersonalSettings } from "@/lib/api";

export function SettingsProfilePage() {
  const [displayName, setDisplayName] = useState("");
  const [penName, setPenName] = useState("");
  const [bio, setBio] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      try {
        const settings = await getSettings();
        if (!cancelled) {
          setDisplayName(settings.personal.display_name ?? "");
          setPenName(settings.personal.pen_name ?? "");
          setBio(settings.personal.bio ?? "");
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "加载失败");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleSave(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setMessage(null);
    setError(null);
    try {
      await patchPersonalSettings({
        display_name: displayName.trim() || null,
        pen_name: penName.trim() || null,
        bio: bio.trim() || null,
      });
      setMessage("个人信息已保存");
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存失败");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <p className="text-sm text-zinc-500">加载中…</p>;
  }

  return (
    <form
      onSubmit={(e) => void handleSave(e)}
      className="max-w-xl rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-700 dark:bg-zinc-900"
    >
      <h2 className="text-base font-semibold text-zinc-900 dark:text-zinc-50">个人信息</h2>
      <p className="mt-1 text-sm text-zinc-500">本地单用户资料，可用于未来成稿署名与 EPUB 元数据。</p>

      <div className="mt-4 space-y-4">
        <label className="block text-sm">
          <span className="text-zinc-600 dark:text-zinc-300">显示名</span>
          <input
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-950"
            placeholder="在界面中显示的名称"
          />
        </label>
        <label className="block text-sm">
          <span className="text-zinc-600 dark:text-zinc-300">笔名</span>
          <input
            value={penName}
            onChange={(e) => setPenName(e.target.value)}
            className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-950"
            placeholder="作品署名使用的笔名"
          />
        </label>
        <label className="block text-sm">
          <span className="text-zinc-600 dark:text-zinc-300">简介</span>
          <textarea
            value={bio}
            onChange={(e) => setBio(e.target.value)}
            rows={4}
            className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-950"
            placeholder="可选：个人或创作简介"
          />
        </label>
      </div>

      <button
        type="submit"
        disabled={saving}
        className="mt-4 rounded-lg bg-zinc-900 px-4 py-2 text-sm text-white disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900"
      >
        {saving ? "保存中…" : "保存"}
      </button>

      {message && <p className="mt-3 text-sm text-emerald-700 dark:text-emerald-300">{message}</p>}
      {error && <p className="mt-3 text-sm text-red-600 dark:text-red-400">{error}</p>}
    </form>
  );
}
