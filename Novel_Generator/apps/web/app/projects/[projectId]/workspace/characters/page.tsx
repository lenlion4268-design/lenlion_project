"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { AssetStatusBadge } from "@/components/AssetStatusBadge";
import { ConfirmLockActions } from "@/components/ConfirmLockActions";
import {
  createCharacterCard,
  listCharacterCards,
  updateCharacterCard,
} from "@/lib/api";
import type { CharacterCard, CharacterProfile, ConfirmStatus, LockStatus } from "@/lib/types";

const EMPTY_PROFILE: CharacterProfile = {
  personality: "",
  abilities: "",
  goals: "",
  weaknesses: "",
  experiences: "",
  identity: "",
};

export default function CharactersPage() {
  const params = useParams<{ projectId: string }>();
  const projectId = params.projectId;
  const [cards, setCards] = useState<CharacterCard[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [profile, setProfile] = useState<CharacterProfile>(EMPTY_PROFILE);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadCards() {
      setLoading(true);
      try {
        const response = await listCharacterCards(projectId);
        if (cancelled) return;
        setCards(response.items);
        if (response.items.length > 0) {
          const card = response.items[0];
          setSelectedId(card.id);
          setName(card.name);
          setProfile({ ...EMPTY_PROFILE, ...card.profile_json });
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadCards();
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  async function reloadCards() {
    const response = await listCharacterCards(projectId);
    setCards(response.items);
  }

  function selectCard(card: CharacterCard) {
    setSelectedId(card.id);
    setName(card.name);
    setProfile({ ...EMPTY_PROFILE, ...card.profile_json });
  }

  function resetNewForm() {
    setSelectedId(null);
    setName("");
    setProfile(EMPTY_PROFILE);
  }

  async function handleSave(event: React.FormEvent) {
    event.preventDefault();
    if (!name.trim()) return;
    setSaving(true);
    setMessage(null);
    try {
      if (selectedId) {
        await updateCharacterCard(selectedId, { name: name.trim(), profile_json: profile });
      } else {
        await createCharacterCard(projectId, { name: name.trim(), profile_json: profile });
      }
      setMessage("已保存");
      await reloadCards();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "保存失败");
    } finally {
      setSaving(false);
    }
  }

  const selectedCard = cards.find((card) => card.id === selectedId);
  const isLocked =
    selectedCard?.confirm_status === "locked" || selectedCard?.lock_status === "locked";

  function handleReviewUpdated(confirmStatus: ConfirmStatus, lockStatus: LockStatus) {
    if (!selectedId) return;
    setCards((prev) =>
      prev.map((card) =>
        card.id === selectedId ? { ...card, confirm_status: confirmStatus, lock_status: lockStatus } : card,
      ),
    );
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-50">角色卡</h2>
          <p className="mt-1 text-sm text-zinc-500">维护主要角色、配角与势力的结构化设定。</p>
        </div>
        <button
          type="button"
          onClick={resetNewForm}
          className="rounded-lg bg-zinc-900 px-3 py-2 text-sm text-white dark:bg-zinc-100 dark:text-zinc-900"
        >
          新建角色
        </button>
      </div>

      <div className="grid gap-6 lg:grid-cols-[240px_1fr]">
        <aside className="space-y-2">
          {loading ? (
            <p className="text-sm text-zinc-500">加载中…</p>
          ) : cards.length === 0 ? (
            <p className="text-sm text-zinc-500">暂无角色卡</p>
          ) : (
            cards.map((card) => (
              <button
                key={card.id}
                type="button"
                onClick={() => selectCard(card)}
                className={`w-full rounded-lg border px-3 py-2 text-left text-sm ${
                  selectedId === card.id
                    ? "border-zinc-900 bg-zinc-50 dark:border-zinc-100 dark:bg-zinc-800"
                    : "border-zinc-200 dark:border-zinc-700"
                }`}
              >
                <div className="font-medium text-zinc-900 dark:text-zinc-50">{card.name}</div>
                <div className="mt-1">
                  <AssetStatusBadge status={card.confirm_status} />
                </div>
              </button>
            ))
          )}
        </aside>

        <form className="space-y-4" onSubmit={handleSave}>
          {selectedCard && (
            <>
              <ConfirmLockActions
                targetType="character_card"
                targetId={selectedCard.id}
                confirmStatus={selectedCard.confirm_status}
                lockStatus={selectedCard.lock_status}
                onUpdated={handleReviewUpdated}
              />
              <span className="block text-xs text-zinc-400">
                新建资产默认为草稿，不会进入生成上下文
              </span>
            </>
          )}

          <label className="block text-sm">
            <span className="text-zinc-600 dark:text-zinc-300">姓名</span>
            <input
              required
              disabled={isLocked}
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-950"
            />
          </label>

          {(
            [
              ["personality", "性格"],
              ["abilities", "能力特征"],
              ["goals", "人物目标"],
              ["weaknesses", "人物弱点"],
              ["experiences", "重要经历"],
              ["identity", "身份"],
            ] as const
          ).map(([key, label]) => (
            <label key={key} className="block text-sm">
              <span className="text-zinc-600 dark:text-zinc-300">{label}</span>
              <textarea
                disabled={isLocked}
                value={profile[key] ?? ""}
                onChange={(e) => setProfile((prev) => ({ ...prev, [key]: e.target.value }))}
                rows={3}
                className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-950"
              />
            </label>
          ))}

          <div className="flex items-center gap-3">
            <button
              type="submit"
              disabled={saving || isLocked}
              className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-60 dark:bg-zinc-100 dark:text-zinc-900"
            >
              {saving ? "保存中…" : "保存角色卡"}
            </button>
            {message && <span className="text-sm text-zinc-500">{message}</span>}
          </div>
        </form>
      </div>
    </div>
  );
}
