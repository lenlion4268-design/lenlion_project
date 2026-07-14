"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { ConfirmLockActions } from "@/components/ConfirmLockActions";
import { GenerationReadinessPanel } from "@/components/GenerationReadinessPanel";
import { StyleBindPanel } from "@/components/StyleBindPanel";
import { downloadManuscript, downloadPublication, exportManuscript, getSettings, listChapters, listPublications, listVolumes, publishManuscript, retryPublicationDelivery, updateChapter } from "@/lib/api";
import type { Chapter, ConfirmStatus, ExportFormat, LockStatus, ModelProfile, Publication, PublishChannel, Volume } from "@/lib/types";

export default function ChaptersPage() {
  const params = useParams<{ projectId: string }>();
  const projectId = params.projectId;
  const [volumes, setVolumes] = useState<Volume[]>([]);
  const [selectedVolumeId, setSelectedVolumeId] = useState("");
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [selectedChapterId, setSelectedChapterId] = useState("");
  const [editorTitle, setEditorTitle] = useState("");
  const [editorContent, setEditorContent] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [chapterRefreshKey, setChapterRefreshKey] = useState(0);
  const [batchCount, setBatchCount] = useState(1);
  const [modelProfile, setModelProfile] = useState<ModelProfile>("default");
  const [asyncMode, setAsyncMode] = useState(false);
  const [exportInfo, setExportInfo] = useState<string | null>(null);
  const [publications, setPublications] = useState<Publication[]>([]);
  const [publishChannel, setPublishChannel] = useState<PublishChannel>("local");
  const [publishFormat, setPublishFormat] = useState<ExportFormat>("markdown");
  const [publishMessage, setPublishMessage] = useState<string | null>(null);

  useEffect(() => {
    void getSettings()
      .then((settings) => setModelProfile(settings.models.default_model_profile))
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadVolumes() {
      setLoading(true);
      try {
        const response = await listVolumes(projectId);
        if (cancelled) return;
        setVolumes(response.items);
        if (response.items.length > 0) {
          setSelectedVolumeId(response.items[0].id);
        }
      } catch {
        if (!cancelled) {
          setVolumes([]);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadVolumes();
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  useEffect(() => {
    if (!selectedVolumeId) {
      return;
    }

    let cancelled = false;

    async function loadChapters() {
      try {
        const response = await listChapters(projectId, selectedVolumeId);
        if (cancelled) return;
        setChapters(response.items);
        if (response.items.length > 0) {
          const first = response.items[0];
          setSelectedChapterId(first.id);
          setEditorTitle(first.title);
          setEditorContent(first.content);
        } else {
          setSelectedChapterId("");
          setEditorTitle("");
          setEditorContent("");
        }
      } catch {
        if (!cancelled) {
          setChapters([]);
        }
      }
    }

    void loadChapters();
    return () => {
      cancelled = true;
    };
  }, [projectId, selectedVolumeId, chapterRefreshKey]);

  useEffect(() => {
    let cancelled = false;
    async function loadPublications() {
      try {
        const response = await listPublications(projectId);
        if (!cancelled) {
          setPublications(response.items);
        }
      } catch {
        if (!cancelled) {
          setPublications([]);
        }
      }
    }
    void loadPublications();
    return () => {
      cancelled = true;
    };
  }, [projectId, chapterRefreshKey]);

  function selectChapter(chapter: Chapter) {
    setSelectedChapterId(chapter.id);
    setEditorTitle(chapter.title);
    setEditorContent(chapter.content);
    setMessage(null);
  }

  function handleReviewUpdated(
    chapterId: string,
    confirmStatus: ConfirmStatus,
    lockStatus: LockStatus,
  ) {
    setChapters((prev) =>
      prev.map((item) =>
        item.id === chapterId
          ? { ...item, confirm_status: confirmStatus, lock_status: lockStatus }
          : item,
      ),
    );
  }

  async function handleSave(event: React.FormEvent) {
    event.preventDefault();
    if (!selectedChapterId) return;
    setSaving(true);
    setMessage(null);
    try {
      const updated = await updateChapter(selectedChapterId, {
        title: editorTitle,
        content: editorContent,
      });
      setChapters((prev) =>
        prev.map((item) => (item.id === updated.id ? updated : item)),
      );
      setMessage("章节已保存");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "保存失败");
    } finally {
      setSaving(false);
    }
  }

  async function handleExportPreview() {
    if (!selectedVolumeId) return;
    setExportInfo(null);
    try {
      const result = await exportManuscript(projectId, { volume_id: selectedVolumeId });
      const sizeHint = result.file_size ? `，约 ${result.file_size} 字节` : "";
      setExportInfo(`已锁定章节 ${result.chapter_count} 篇，可下载 Markdown 成稿${sizeHint}。`);
    } catch (err) {
      setExportInfo(err instanceof Error ? err.message : "导出失败");
    }
  }

  async function handleRetryDelivery(publicationId: string) {
    setPublishMessage(null);
    try {
      const result = await retryPublicationDelivery(publicationId);
      setPublishMessage(`重试投递成功（${result.delivery_status}）。`);
      const response = await listPublications(projectId);
      setPublications(response.items);
    } catch (err) {
      setPublishMessage(err instanceof Error ? err.message : "重试失败");
    }
  }

  async function handlePublish() {
    if (!selectedVolumeId) return;
    setPublishMessage(null);
    try {
      const result = await publishManuscript(projectId, {
        volume_id: selectedVolumeId,
        format: publishFormat,
        channel: publishChannel,
      });
      const channelLabel =
        publishChannel === "webhook"
          ? "Webhook"
          : publishChannel === "platform"
            ? "平台 API"
            : "本地归档";
      setPublishMessage(`${channelLabel} 发布成功（${result.delivery_status}，${result.format}）。`);
      const response = await listPublications(projectId);
      setPublications(response.items);
    } catch (err) {
      setPublishMessage(err instanceof Error ? err.message : "发布失败");
    }
  }

  const selectedChapter = chapters.find((item) => item.id === selectedChapterId);
  const isLocked =
    selectedChapter?.confirm_status === "locked" ||
    selectedChapter?.lock_status === "locked";

  return (
    <div>
      <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-50">章节</h2>
      <p className="mt-2 text-sm text-zinc-500">
        在满足准入条件后触发 AI 生成，并在下方编辑章节草稿。
      </p>
      <StyleBindPanel projectId={projectId} />

      {volumes.length > 0 && (
        <div className="mt-6 flex flex-wrap items-end gap-4">
          <label className="block max-w-md text-sm">
            <span className="text-zinc-600 dark:text-zinc-300">目标故事卷</span>
            <select
              value={selectedVolumeId}
              onChange={(e) => setSelectedVolumeId(e.target.value)}
              className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-950"
            >
              {volumes.map((volume) => (
                <option key={volume.id} value={volume.id}>
                  第 {volume.volume_no} 卷 · {volume.title || "未命名"}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm">
            <span className="text-zinc-600 dark:text-zinc-300">批量生成章数</span>
            <input
              type="number"
              min={1}
              max={5}
              value={batchCount}
              onChange={(e) => setBatchCount(Number(e.target.value) || 1)}
              className="mt-1 w-24 rounded-lg border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-950"
            />
          </label>
          <label className="block text-sm">
            <span className="text-zinc-600 dark:text-zinc-300">模型档位</span>
            <select
              value={modelProfile}
              onChange={(e) => setModelProfile(e.target.value as ModelProfile)}
              className="mt-1 w-32 rounded-lg border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-950"
            >
              <option value="default">默认</option>
              <option value="fast">快速</option>
              <option value="quality">高质量</option>
            </select>
          </label>
          <label className="flex items-center gap-2 pb-2 text-sm text-zinc-600 dark:text-zinc-300">
            <input
              type="checkbox"
              checked={asyncMode}
              onChange={(e) => setAsyncMode(e.target.checked)}
            />
            异步生成
          </label>
        </div>
      )}

      <GenerationReadinessPanel
        projectId={projectId}
        targetStage="chapters"
        volumeId={selectedVolumeId || undefined}
        batchCount={batchCount}
        modelProfile={modelProfile}
        asyncMode={asyncMode}
        actionLabel={batchCount > 1 ? `批量生成 ${batchCount} 章` : "AI 生成章节"}
        onGenerated={() => setChapterRefreshKey((value) => value + 1)}
      />

      {selectedVolumeId && (
        <section className="mt-6 rounded-xl border border-zinc-200 p-4 dark:border-zinc-700">
          <div className="flex flex-wrap items-center gap-3">
            <h3 className="text-sm font-medium text-zinc-900 dark:text-zinc-50">成稿导出与发布</h3>
            <button
              type="button"
              onClick={() => void handleExportPreview()}
              className="rounded-lg border border-zinc-300 px-3 py-1.5 text-sm dark:border-zinc-600"
            >
              检查可导出章节
            </button>
            <a
              href={downloadManuscript(projectId, { volume_id: selectedVolumeId, format: "markdown" })}
              className="rounded-lg border border-zinc-300 px-3 py-1.5 text-sm dark:border-zinc-600"
            >
              下载 Markdown
            </a>
            <a
              href={downloadManuscript(projectId, { volume_id: selectedVolumeId, format: "epub" })}
              className="rounded-lg border border-zinc-300 px-3 py-1.5 text-sm dark:border-zinc-600"
            >
              下载 EPUB
            </a>
            <button
              type="button"
              onClick={() => void handlePublish()}
              className="rounded-lg bg-zinc-900 px-3 py-1.5 text-sm text-white dark:bg-zinc-100 dark:text-zinc-900"
            >
              发布成稿
            </button>
            <label className="text-sm text-zinc-600 dark:text-zinc-300">
              格式
              <select
                value={publishFormat}
                onChange={(e) => setPublishFormat(e.target.value as ExportFormat)}
                className="ml-2 rounded-lg border border-zinc-300 px-2 py-1 dark:border-zinc-600 dark:bg-zinc-950"
              >
                <option value="markdown">Markdown</option>
                <option value="text">纯文本</option>
                <option value="epub">EPUB</option>
              </select>
            </label>
            <label className="text-sm text-zinc-600 dark:text-zinc-300">
              渠道
              <select
                value={publishChannel}
                onChange={(e) => setPublishChannel(e.target.value as PublishChannel)}
                className="ml-2 rounded-lg border border-zinc-300 px-2 py-1 dark:border-zinc-600 dark:bg-zinc-950"
              >
                <option value="local">本地归档</option>
                <option value="webhook">Webhook</option>
                <option value="platform">平台 API</option>
              </select>
            </label>
          </div>
          <p className="mt-2 text-xs text-zinc-500">
            本地归档写入 `LOCAL_STORAGE_DIR`；Webhook 需 `PUBLISH_WEBHOOK_URL`；平台 API 需 `PUBLISH_PLATFORM_API_URL` 与 Token。
          </p>
          {exportInfo && <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-300">{exportInfo}</p>}
          {publishMessage && <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-300">{publishMessage}</p>}
          {publications.length > 0 && (
            <ul className="mt-4 space-y-2 text-sm">
              {publications.map((item) => (
                <li key={item.id} className="flex flex-wrap items-center gap-3 rounded-lg border border-zinc-200 px-3 py-2 dark:border-zinc-700">
                  <span>{item.title}</span>
                  <span className="text-zinc-500">
                    {item.channel} · {item.format} · {item.chapter_count} 章 · {item.word_count} 字
                  </span>
                  {item.delivery_status !== "skipped" && (
                    <span className="text-zinc-500">投递 {item.delivery_status}</span>
                  )}
                  <a
                    href={downloadPublication(item.id)}
                    className="text-zinc-700 underline dark:text-zinc-300"
                  >
                    下载
                  </a>
                  {item.delivery_status === "failed" &&
                    (item.channel === "webhook" || item.channel === "platform") && (
                      <button
                        type="button"
                        onClick={() => void handleRetryDelivery(item.id)}
                        className="text-zinc-700 underline dark:text-zinc-300"
                      >
                        重试投递
                      </button>
                    )}
                </li>
              ))}
            </ul>
          )}
        </section>
      )}

      <section className="mt-8 grid gap-6 lg:grid-cols-[240px_minmax(0,1fr)]">
        <div>
          <h3 className="mb-3 text-sm font-medium text-zinc-500">章节列表</h3>
          {loading ? (
            <p className="text-sm text-zinc-500">加载中…</p>
          ) : chapters.length === 0 ? (
            <p className="text-sm text-zinc-500">暂无章节，请先生成或切换故事卷。</p>
          ) : (
            <ul className="space-y-2">
              {chapters.map((chapter) => (
                <li key={chapter.id}>
                  <button
                    type="button"
                    onClick={() => selectChapter(chapter)}
                    className={`w-full rounded-lg border px-3 py-2 text-left text-sm ${
                      chapter.id === selectedChapterId
                        ? "border-zinc-900 bg-zinc-900 text-white dark:border-zinc-100 dark:bg-zinc-100 dark:text-zinc-900"
                        : "border-zinc-200 bg-white text-zinc-700 hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-200"
                    }`}
                  >
                    {chapter.title || `第 ${chapter.chapter_no} 章`}
                    <span className="mt-1 block text-xs opacity-70">{chapter.word_count} 字</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {selectedChapter && (
          <div>
            <form className="space-y-4" onSubmit={handleSave}>
              <label className="block text-sm">
                <span className="text-zinc-600 dark:text-zinc-300">章节标题</span>
                <input
                  value={editorTitle}
                  onChange={(e) => setEditorTitle(e.target.value)}
                  disabled={isLocked}
                  className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 disabled:opacity-60 dark:border-zinc-700 dark:bg-zinc-950"
                />
              </label>
              <label className="block text-sm">
                <span className="text-zinc-600 dark:text-zinc-300">正文</span>
                <textarea
                  value={editorContent}
                  onChange={(e) => setEditorContent(e.target.value)}
                  disabled={isLocked}
                  rows={18}
                  className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 font-mono text-sm leading-6 disabled:opacity-60 dark:border-zinc-700 dark:bg-zinc-950"
                />
              </label>
              <div className="flex items-center gap-3">
                <button
                  type="submit"
                  disabled={saving || isLocked}
                  className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-60 dark:bg-zinc-100 dark:text-zinc-900"
                >
                  {saving ? "保存中…" : "保存章节"}
                </button>
                {message && <span className="text-sm text-zinc-500">{message}</span>}
              </div>
            </form>

            <div className="mt-6">
              <ConfirmLockActions
                targetType="chapter"
                targetId={selectedChapter.id}
                confirmStatus={selectedChapter.confirm_status}
                lockStatus={selectedChapter.lock_status}
                onUpdated={(confirmStatus, lockStatus) =>
                  handleReviewUpdated(selectedChapter.id, confirmStatus, lockStatus)
                }
              />
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
