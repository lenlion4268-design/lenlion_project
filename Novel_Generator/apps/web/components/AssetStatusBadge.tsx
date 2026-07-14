import type { ConfirmStatus } from "@/lib/types";
import { CONFIRM_STATUS_LABELS } from "@/lib/labels";

const STATUS_STYLES: Record<ConfirmStatus, string> = {
  draft: "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300",
  pending_confirm: "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200",
  confirmed: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200",
  locked: "bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-200",
  rejected: "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-200",
  archived: "bg-zinc-200 text-zinc-600 dark:bg-zinc-700 dark:text-zinc-300",
};

export function AssetStatusBadge({ status }: { status: ConfirmStatus }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_STYLES[status]}`}
    >
      {CONFIRM_STATUS_LABELS[status]}
    </span>
  );
}
