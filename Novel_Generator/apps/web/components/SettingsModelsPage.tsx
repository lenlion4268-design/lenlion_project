"use client";

import { useEffect, useState } from "react";

import {
  getEffectiveModels,
  getSettings,
  patchModelSettings,
  testModelConnection,
} from "@/lib/api";
import type { EffectiveModelRow, ModelProfile, ModelSettings } from "@/lib/types";

const STAGE_LABELS: Record<string, string> = {
  outline: "大纲",
  volumes: "故事卷",
  chapters: "章节",
};

const PROFILE_LABELS: Record<string, string> = {
  default: "默认",
  fast: "快速",
  quality: "高质量",
};

export function SettingsModelsPage() {
  const [form, setForm] = useState<ModelSettings | null>(null);
  const [apiKey, setApiKey] = useState("");
  const [rows, setRows] = useState<EffectiveModelRow[]>([]);
  const [provider, setProvider] = useState("mock");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [settings, effective] = await Promise.all([getSettings(), getEffectiveModels()]);
        if (!cancelled) {
          setForm(settings.models);
          setProvider(effective.provider);
          setRows(effective.rows);
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
    if (!form) return;
    setSaving(true);
    setMessage(null);
    setError(null);
    try {
      const payload: Record<string, unknown> = { ...form };
      if (apiKey.trim()) {
        payload.openai_api_key = apiKey.trim();
      }
      delete payload.openai_api_key_masked;
      await patchModelSettings(payload);
      setApiKey("");
      setMessage("模型配置已保存并生效");
      const [settings, effective] = await Promise.all([getSettings(), getEffectiveModels()]);
      setForm(settings.models);
      setProvider(effective.provider);
      setRows(effective.rows);
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存失败");
    } finally {
      setSaving(false);
    }
  }

  async function handleTest() {
    setTesting(true);
    setMessage(null);
    setError(null);
    try {
      const result = await testModelConnection();
      setMessage(result.ok ? result.message : `测试未通过：${result.message}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "测试失败");
    } finally {
      setTesting(false);
    }
  }

  if (loading || !form) {
    return <p className="text-sm text-zinc-500">加载中…</p>;
  }

  return (
    <div className="space-y-6">
      {form.ai_provider === "mock" && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-200">
          当前为 Mock 模式，生成结果为本地模拟文本。配置 OpenAI 兼容 API 后可使用真实模型。
        </div>
      )}

      <form
        onSubmit={(e) => void handleSave(e)}
        className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-700 dark:bg-zinc-900"
      >
        <h2 className="text-base font-semibold text-zinc-900 dark:text-zinc-50">模型配置</h2>
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <label className="block text-sm">
            <span className="text-zinc-600 dark:text-zinc-300">Provider</span>
            <select
              value={form.ai_provider}
              onChange={(e) => setForm((prev) => prev && { ...prev, ai_provider: e.target.value })}
              className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-950"
            >
              <option value="mock">mock</option>
              <option value="openai">openai</option>
            </select>
          </label>
          <label className="block text-sm">
            <span className="text-zinc-600 dark:text-zinc-300">默认模型</span>
            <input
              value={form.ai_model}
              onChange={(e) => setForm((prev) => prev && { ...prev, ai_model: e.target.value })}
              className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-950"
            />
          </label>
          <label className="block text-sm sm:col-span-2">
            <span className="text-zinc-600 dark:text-zinc-300">Base URL</span>
            <input
              value={form.openai_base_url}
              onChange={(e) =>
                setForm((prev) => prev && { ...prev, openai_base_url: e.target.value })
              }
              className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-950"
            />
          </label>
          <label className="block text-sm sm:col-span-2">
            <span className="text-zinc-600 dark:text-zinc-300">API Key</span>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder={form.openai_api_key_masked ? `已配置 ${form.openai_api_key_masked}` : "留空则不修改"}
              className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-950"
            />
          </label>
          <label className="block text-sm">
            <span className="text-zinc-600 dark:text-zinc-300">默认生成档位</span>
            <select
              value={form.default_model_profile}
              onChange={(e) =>
                setForm(
                  (prev) =>
                    prev && { ...prev, default_model_profile: e.target.value as ModelProfile },
                )
              }
              className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-950"
            >
              <option value="default">默认</option>
              <option value="fast">快速</option>
              <option value="quality">高质量</option>
            </select>
          </label>
        </div>

        <button
          type="button"
          onClick={() => setShowAdvanced((value) => !value)}
          className="mt-4 text-sm underline"
        >
          {showAdvanced ? "收起高级配置" : "展开高级配置"}
        </button>

        {showAdvanced && (
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            {(
              [
                ["ai_model_outline", "大纲模型"],
                ["ai_model_volume", "故事卷模型"],
                ["ai_model_chapter", "章节模型"],
                ["ai_model_profile_fast", "快速档位模型"],
                ["ai_model_profile_quality", "高质量档位模型"],
              ] as const
            ).map(([key, label]) => (
              <label key={key} className="block text-sm">
                <span className="text-zinc-600 dark:text-zinc-300">{label}</span>
                <input
                  value={form[key] ?? ""}
                  onChange={(e) =>
                    setForm((prev) => prev && { ...prev, [key]: e.target.value || null })
                  }
                  className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-950"
                />
              </label>
            ))}
            <label className="block text-sm">
              <span className="text-zinc-600 dark:text-zinc-300">请求超时（秒）</span>
              <input
                type="number"
                min={10}
                max={600}
                value={form.ai_request_timeout_seconds}
                onChange={(e) =>
                  setForm((prev) =>
                    prev && { ...prev, ai_request_timeout_seconds: Number(e.target.value) },
                  )
                }
                className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-950"
              />
            </label>
            <label className="block text-sm">
              <span className="text-zinc-600 dark:text-zinc-300">批量章节上限</span>
              <input
                type="number"
                min={1}
                max={20}
                value={form.ai_batch_max_chapters}
                onChange={(e) =>
                  setForm((prev) =>
                    prev && { ...prev, ai_batch_max_chapters: Number(e.target.value) },
                  )
                }
                className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-950"
              />
            </label>
          </div>
        )}

        <div className="mt-4 flex flex-wrap gap-3">
          <button
            type="submit"
            disabled={saving}
            className="rounded-lg bg-zinc-900 px-4 py-2 text-sm text-white disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900"
          >
            {saving ? "保存中…" : "保存配置"}
          </button>
          <button
            type="button"
            disabled={testing}
            onClick={() => void handleTest()}
            className="rounded-lg border border-zinc-300 px-4 py-2 text-sm dark:border-zinc-700"
          >
            {testing ? "测试中…" : "测试连接"}
          </button>
        </div>
      </form>

      <section className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-700 dark:bg-zinc-900">
        <h2 className="text-base font-semibold">有效路由预览</h2>
        <p className="mt-1 text-sm text-zinc-500">当前 Provider：{provider}</p>
        <div className="mt-3 overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-zinc-500">
                <th className="py-2 pr-4">阶段</th>
                <th className="py-2 pr-4">档位</th>
                <th className="py-2">解析模型</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={`${row.target_stage}-${row.model_profile}`} className="border-t border-zinc-100 dark:border-zinc-800">
                  <td className="py-2 pr-4">{STAGE_LABELS[row.target_stage] ?? row.target_stage}</td>
                  <td className="py-2 pr-4">{PROFILE_LABELS[row.model_profile] ?? row.model_profile}</td>
                  <td className="py-2 font-mono text-xs">{row.model_name}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {message && <p className="text-sm text-emerald-700 dark:text-emerald-300">{message}</p>}
      {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}
    </div>
  );
}
