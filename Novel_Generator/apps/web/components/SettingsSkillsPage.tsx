"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  confirmStyleProfile,
  deleteStyleProfile,
  downloadStyleSkill,
  listStyleProfiles,
  lockStyleProfile,
  unlockStyleProfile,
  updateStyleProfile,
} from "@/lib/api";
import { CONFIRM_STATUS_LABELS, LOCK_STATUS_LABELS } from "@/lib/labels";
import type { StyleProfile } from "@/lib/types";

export function SettingsSkillsPage() {
  const [profiles, setProfiles] = useState<StyleProfile[]>([]);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [voiceSummary, setVoiceSummary] = useState("");
  const [skillMarkdown, setSkillMarkdown] = useState("");
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let cancelled = false;

    async function loadProfiles() {
      setLoading(true);
      try {
        const response = await listStyleProfiles();
        if (!cancelled) {
          setProfiles(response.items);
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

    void loadProfiles();
    return () => {
      cancelled = true;
    };
  }, [reloadToken]);

  function startEdit(profile: StyleProfile) {
    setEditingId(profile.id);
    setVoiceSummary(profile.voice_summary);
    setSkillMarkdown(profile.skill_markdown);
  }

  async function saveEdit(profileId: string) {
    setMessage(null);
    setError(null);
    try {
      await updateStyleProfile(profileId, {
        voice_summary: voiceSummary,
        skill_markdown: skillMarkdown,
      });
      setEditingId(null);
      setMessage("技能已更新");
      setReloadToken((token) => token + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存失败");
    }
  }

  async function runAction(action: () => Promise<unknown>, success: string) {
    setMessage(null);
    setError(null);
    try {
      await action();
      setMessage(success);
      setReloadToken((token) => token + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "操作失败");
    }
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-zinc-500">
        管理从素材库分析得到的写作技能。上传参考小说请前往
        <Link href="/materials" className="mx-1 underline">
          我的素材库
        </Link>
        。
      </p>

      {loading ? (
        <p className="text-sm text-zinc-500">加载中…</p>
      ) : profiles.length === 0 ? (
        <div className="rounded-xl border border-dashed border-zinc-300 p-8 text-center text-sm text-zinc-500 dark:border-zinc-700">
          还没有写作技能。请先在素材库上传参考小说并完成文风分析。
        </div>
      ) : (
        <ul className="space-y-3">
          {profiles.map((item) => (
            <li
              key={item.id}
              className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-700 dark:bg-zinc-900"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="font-semibold text-zinc-900 dark:text-zinc-50">{item.author} 文风</p>
                  <p className="text-sm text-zinc-500">《{item.reference_title}》</p>
                  <p className="text-xs text-zinc-400">
                    {CONFIRM_STATUS_LABELS[item.confirm_status]} / {LOCK_STATUS_LABELS[item.lock_status]}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2 text-sm">
                  {item.lock_status !== "locked" && (
                    <>
                      <button type="button" className="underline" onClick={() => startEdit(item)}>
                        编辑
                      </button>
                      <button
                        type="button"
                        className="underline"
                        onClick={() => void runAction(() => confirmStyleProfile(item.id), "已确认")}
                      >
                        确认
                      </button>
                      <button
                        type="button"
                        className="underline"
                        onClick={() => void runAction(() => lockStyleProfile(item.id), "已锁定")}
                      >
                        锁定
                      </button>
                      <button
                        type="button"
                        className="underline text-red-600"
                        onClick={() =>
                          void runAction(() => deleteStyleProfile(item.id), "已删除")
                        }
                      >
                        删除
                      </button>
                    </>
                  )}
                  {item.lock_status === "locked" && (
                    <button
                      type="button"
                      className="underline"
                      onClick={() => void runAction(() => unlockStyleProfile(item.id), "已解锁")}
                    >
                      解锁
                    </button>
                  )}
                  <a href={downloadStyleSkill(item.id)} className="underline">
                    导出
                  </a>
                </div>
              </div>

              {editingId === item.id ? (
                <div className="mt-4 space-y-3 border-t border-zinc-100 pt-4 dark:border-zinc-800">
                  <label className="block text-sm">
                    <span className="text-zinc-600 dark:text-zinc-300">文风摘要</span>
                    <textarea
                      value={voiceSummary}
                      onChange={(e) => setVoiceSummary(e.target.value)}
                      rows={3}
                      className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-950"
                    />
                  </label>
                  <label className="block text-sm">
                    <span className="text-zinc-600 dark:text-zinc-300">Skill Markdown</span>
                    <textarea
                      value={skillMarkdown}
                      onChange={(e) => setSkillMarkdown(e.target.value)}
                      rows={8}
                      className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 font-mono text-xs dark:border-zinc-700 dark:bg-zinc-950"
                    />
                  </label>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => void saveEdit(item.id)}
                      className="rounded-lg bg-zinc-900 px-3 py-1.5 text-sm text-white dark:bg-zinc-100 dark:text-zinc-900"
                    >
                      保存
                    </button>
                    <button type="button" className="text-sm underline" onClick={() => setEditingId(null)}>
                      取消
                    </button>
                  </div>
                </div>
              ) : (
                <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-300">
                  {item.voice_summary || item.name}
                </p>
              )}
            </li>
          ))}
        </ul>
      )}

      {message && <p className="text-sm text-emerald-700 dark:text-emerald-300">{message}</p>}
      {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}
    </div>
  );
}
