"use client";

import { useState } from "react";

import { uploadReference } from "@/lib/api";

type ReferenceUploadFormProps = {
  disabled?: boolean;
  className?: string;
  onUploaded?: () => void;
};

export function ReferenceUploadForm({
  disabled = false,
  className = "",
  onUploaded,
}: ReferenceUploadFormProps) {
  const [author, setAuthor] = useState("");
  const [title, setTitle] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  async function handleUpload() {
    if (!file || !author.trim()) {
      setError("请填写作者并选择文件");
      return;
    }
    setUploading(true);
    setError(null);
    setMessage(null);
    try {
      await uploadReference({
        author: author.trim(),
        title: title.trim() || undefined,
        file,
      });
      setMessage("参考小说已上传并完成采样");
      setAuthor("");
      setTitle("");
      setFile(null);
      onUploaded?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "上传失败");
    } finally {
      setUploading(false);
    }
  }

  return (
    <section
      className={`rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-700 dark:bg-zinc-900 ${className}`.trim()}
    >
      <h2 className="text-base font-semibold text-zinc-900 dark:text-zinc-50">上传参考小说</h2>
      <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
        素材库独立于创作项目。上传后将自动采样，可用于文风分析与章节生成绑定。
      </p>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <label className="block text-sm">
          <span className="text-zinc-600 dark:text-zinc-300">作者（必填）</span>
          <input
            value={author}
            onChange={(e) => setAuthor(e.target.value)}
            disabled={disabled || uploading}
            className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 disabled:opacity-60 dark:border-zinc-700 dark:bg-zinc-950"
            placeholder="例如：刘慈欣"
          />
        </label>
        <label className="block text-sm">
          <span className="text-zinc-600 dark:text-zinc-300">作品名（可选）</span>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            disabled={disabled || uploading}
            className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 disabled:opacity-60 dark:border-zinc-700 dark:bg-zinc-950"
            placeholder="默认使用文件名"
          />
        </label>
        <label className="block text-sm sm:col-span-2">
          <span className="text-zinc-600 dark:text-zinc-300">素材文件</span>
          <input
            type="file"
            accept=".txt,.md,.epub"
            disabled={disabled || uploading}
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="mt-1 block w-full text-sm disabled:opacity-60"
          />
        </label>
      </div>
      <button
        type="button"
        disabled={disabled || uploading}
        onClick={() => void handleUpload()}
        className="mt-4 rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900"
      >
        {uploading ? "上传中…" : "上传并采样"}
      </button>
      {message && <p className="mt-3 text-sm text-emerald-700 dark:text-emerald-300">{message}</p>}
      {error && <p className="mt-3 text-sm text-red-600 dark:text-red-400">{error}</p>}
    </section>
  );
}
