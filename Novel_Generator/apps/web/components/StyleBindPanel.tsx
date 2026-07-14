"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { bindStyleProfile, getActiveStyle, listStyleProfiles } from "@/lib/api";
import { LOCK_STATUS_LABELS } from "@/lib/labels";
import type { ActiveStyle, StyleProfile } from "@/lib/types";

export function StyleBindPanel({ projectId }: { projectId: string }) {
  const [profiles, setProfiles] = useState<StyleProfile[]>([]);
  const [activeStyle, setActiveStyle] = useState<ActiveStyle | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [profs, active] = await Promise.all([
          listStyleProfiles(),
          getActiveStyle(projectId),
        ]);
        if (!cancelled) {
          setProfiles(profs.items.filter((item) => item.lock_status === "locked"));
          setActiveStyle(active);
        }
      } catch {
        if (!cancelled) {
          setProfiles([]);
          setActiveStyle(null);
        }
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, [projectId, reloadToken]);

  async function handleBind(profileId: string) {
    setMessage(null);
    setError(null);
    try {
      const active = await bindStyleProfile(projectId, profileId);
      setActiveStyle(active);
      setMessage(`已绑定文风：${active.author ?? ""}`);
      setReloadToken((value) => value + 1);
      setOpen(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "绑定失败");
    }
  }

  return (
    <div className="mt-3 rounded-lg border border-zinc-200 bg-zinc-50 px-4 py-3 dark:border-zinc-700 dark:bg-zinc-950/40">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm text-zinc-600 dark:text-zinc-300">
          {activeStyle?.author ? (
            <>
              当前文风：<strong>{activeStyle.author}</strong>
            </>
          ) : (
            "未绑定文风"
          )}
        </p>
        <div className="flex items-center gap-3 text-sm">
          <Link href="/materials" className="underline">
            素材库
          </Link>
          <button type="button" className="underline" onClick={() => setOpen((value) => !value)}>
            {open ? "收起" : "从素材库选用"}
          </button>
        </div>
      </div>
      {open && (
        <ul className="mt-3 space-y-2 border-t border-zinc-200 pt-3 dark:border-zinc-700">
          {profiles.length === 0 ? (
            <li className="text-sm text-zinc-500">
              素材库中还没有已锁定的文风，请先在
              <Link href="/materials" className="mx-1 underline">
                我的素材库
              </Link>
              上传并锁定。
            </li>
          ) : (
            profiles.map((item) => (
              <li
                key={item.id}
                className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-zinc-200 bg-white px-3 py-2 dark:border-zinc-700 dark:bg-zinc-900"
              >
                <div>
                  <p className="font-medium text-zinc-900 dark:text-zinc-50">{item.author} 文风</p>
                  <p className="text-xs text-zinc-400">
                    {LOCK_STATUS_LABELS[item.lock_status]} · 《{item.reference_title}》
                  </p>
                </div>
                {activeStyle?.active_style_profile_id === item.id ? (
                  <span className="text-xs text-emerald-600 dark:text-emerald-300">已绑定</span>
                ) : (
                  <button
                    type="button"
                    className="text-sm underline"
                    onClick={() => void handleBind(item.id)}
                  >
                    绑定
                  </button>
                )}
              </li>
            ))
          )}
        </ul>
      )}
      {message && <p className="mt-2 text-sm text-emerald-700 dark:text-emerald-300">{message}</p>}
      {error && <p className="mt-2 text-sm text-red-600 dark:text-red-400">{error}</p>}
    </div>
  );
}
