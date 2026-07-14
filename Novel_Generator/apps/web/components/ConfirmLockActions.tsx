"use client";

import { useState } from "react";

import { AssetStatusBadge } from "@/components/AssetStatusBadge";
import { submitReview } from "@/lib/api";
import { LOCK_STATUS_LABELS, REVIEW_ACTION_LABELS } from "@/lib/labels";
import type { ConfirmStatus, LockStatus, ReviewAction, ReviewTargetType } from "@/lib/types";

const ACTION_PROMPTS: Record<ReviewAction, string> = {
  confirm: "确认后该资产可用于下游生成准入检查。",
  lock: "锁定后不可直接编辑，需先解锁。",
  reject: "驳回后需要重新编辑并再次确认。",
  unlock: "解锁后可继续编辑，状态将回到已确认。",
};

export function ConfirmLockActions({
  targetType,
  targetId,
  confirmStatus,
  lockStatus,
  onUpdated,
}: {
  targetType: ReviewTargetType;
  targetId: string;
  confirmStatus: ConfirmStatus;
  lockStatus: LockStatus;
  onUpdated?: (confirmStatus: ConfirmStatus, lockStatus: LockStatus) => void;
}) {
  const [pendingAction, setPendingAction] = useState<ReviewAction | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isLocked = confirmStatus === "locked" || lockStatus === "locked";

  async function handleConfirmAction() {
    if (!pendingAction) return;
    setLoading(true);
    setError(null);
    try {
      const result = await submitReview(pendingAction, {
        target_type: targetType,
        target_id: targetId,
      });
      onUpdated?.(result.confirm_status, result.lock_status);
      setPendingAction(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "操作失败");
    } finally {
      setLoading(false);
    }
  }

  const availableActions: ReviewAction[] = isLocked
    ? ["unlock"]
    : ["confirm", "lock", "reject"];

  return (
    <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-4 dark:border-zinc-700 dark:bg-zinc-800/40">
      <div className="flex flex-wrap items-center gap-2">
        <AssetStatusBadge status={confirmStatus} />
        <span className="rounded-full bg-white px-2.5 py-0.5 text-xs text-zinc-600 ring-1 ring-zinc-200 dark:bg-zinc-900 dark:text-zinc-300 dark:ring-zinc-700">
          {LOCK_STATUS_LABELS[lockStatus]}
        </span>
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        {availableActions.map((action) => (
          <button
            key={action}
            type="button"
            onClick={() => setPendingAction(action)}
            className="rounded-lg border border-zinc-300 bg-white px-3 py-1.5 text-sm text-zinc-700 hover:bg-zinc-100 dark:border-zinc-600 dark:bg-zinc-900 dark:text-zinc-200 dark:hover:bg-zinc-800"
          >
            {REVIEW_ACTION_LABELS[action]}
          </button>
        ))}
      </div>

      {error && <p className="mt-2 text-sm text-red-600 dark:text-red-400">{error}</p>}

      {pendingAction && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
          <div className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-xl dark:bg-zinc-900">
            <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">
              确认{REVIEW_ACTION_LABELS[pendingAction]}？
            </h3>
            <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-300">
              {ACTION_PROMPTS[pendingAction]}
            </p>
            <div className="mt-5 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setPendingAction(null)}
                className="rounded-lg px-4 py-2 text-sm text-zinc-600 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-zinc-800"
              >
                取消
              </button>
              <button
                type="button"
                disabled={loading}
                onClick={() => void handleConfirmAction()}
                className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-60 dark:bg-zinc-100 dark:text-zinc-900"
              >
                {loading ? "处理中…" : "确认操作"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
