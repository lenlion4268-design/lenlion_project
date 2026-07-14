"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { HomeNav } from "@/components/HomeNav";
import { ReferenceUploadForm } from "@/components/ReferenceUploadForm";
import { analyzeReference, listReferences } from "@/lib/api";
import {
  labelOrRaw,
  MATERIAL_SOURCE_LABELS,
  REFERENCE_WORK_STATUS_LABELS,
  STYLE_ANALYSIS_JOB_STATUS_LABELS,
} from "@/lib/labels";
import type { ReferenceWork } from "@/lib/types";

export function MaterialsLibraryPage() {
  const [references, setReferences] = useState<ReferenceWork[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const refs = await listReferences();
        if (!cancelled) {
          setReferences(refs.items);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "加载素材库失败");
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
  }, [reloadToken]);

  async function handleAnalyze(referenceId: string) {
    setMessage(null);
    setError(null);
    try {
      const job = await analyzeReference(referenceId);
      setMessage(
        job.status === "succeeded"
          ? "文风分析完成，请前往 设置 > 技能库 查看与管理"
          : `分析状态：${labelOrRaw(STYLE_ANALYSIS_JOB_STATUS_LABELS, job.status)}`,
      );
      setReloadToken((value) => value + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "分析失败");
    }
  }

  return (
    <div className="min-h-full bg-zinc-50 dark:bg-zinc-950">
      <header className="border-b border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
        <div className="mx-auto max-w-6xl px-6 py-5">
          <HomeNav />
          <h1 className="mt-4 text-2xl font-semibold text-zinc-900 dark:text-zinc-50">我的素材库</h1>
          <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
            上传参考小说并触发文风分析；技能管理请前往
            <Link href="/settings/skills" className="mx-1 underline">
              设置 &gt; 技能库
            </Link>
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-6xl space-y-8 px-6 py-8">
        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300">
            {error}
          </div>
        )}

        <ReferenceUploadForm onUploaded={() => setReloadToken((value) => value + 1)} />

        <section>
          <h2 className="text-base font-semibold text-zinc-900 dark:text-zinc-50">素材列表</h2>
          {loading ? (
            <p className="mt-3 text-sm text-zinc-500">加载中…</p>
          ) : references.length === 0 ? (
            <p className="mt-3 text-sm text-zinc-500">还没有素材，请使用上方表单上传参考小说。</p>
          ) : (
            <ul className="mt-3 space-y-2">
              {references.map((item) => (
                <li
                  key={item.id}
                  className="rounded-lg border border-zinc-200 bg-white px-4 py-3 dark:border-zinc-700 dark:bg-zinc-900"
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="font-medium text-zinc-900 dark:text-zinc-50">{item.author}</p>
                      <p className="text-sm text-zinc-500">
                        《{item.title}》 · {item.word_count} 字 ·{" "}
                        {labelOrRaw(REFERENCE_WORK_STATUS_LABELS, item.status)}
                      </p>
                      <p className="text-xs text-zinc-400">
                        类型：{labelOrRaw(MATERIAL_SOURCE_LABELS, item.source_type)}
                      </p>
                    </div>
                    {item.source_type === "reference_parse" && item.status === "ingested" && (
                      <button
                        type="button"
                        onClick={() => void handleAnalyze(item.id)}
                        className="text-sm font-medium underline"
                      >
                        分析文风
                      </button>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>

        {message && <p className="text-sm text-emerald-700 dark:text-emerald-300">{message}</p>}
      </main>
    </div>
  );
}
