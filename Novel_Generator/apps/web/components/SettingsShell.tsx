"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { HomeNav } from "@/components/HomeNav";

const TABS = [
  { href: "/settings/models", label: "模型配置" },
  { href: "/settings/skills", label: "技能库" },
  { href: "/settings/profile", label: "个人信息" },
] as const;

export function SettingsShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  function tabClass(active: boolean) {
    return `block rounded-lg px-3 py-2 text-sm ${
      active
        ? "bg-zinc-900 font-medium text-white dark:bg-zinc-100 dark:text-zinc-900"
        : "text-zinc-600 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-zinc-800"
    }`;
  }

  return (
    <div className="min-h-full bg-zinc-50 dark:bg-zinc-950">
      <header className="border-b border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
        <div className="mx-auto max-w-6xl px-6 py-5">
          <HomeNav />
          <h1 className="mt-4 text-2xl font-semibold text-zinc-900 dark:text-zinc-50">设置</h1>
          <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
            管理模型、写作技能与个人资料
          </p>
        </div>
      </header>

      <div className="mx-auto flex max-w-6xl gap-6 px-6 py-8">
        <aside className="w-44 shrink-0">
          <nav className="space-y-1">
            {TABS.map((tab) => (
              <Link
                key={tab.href}
                href={tab.href}
                className={tabClass(pathname === tab.href)}
              >
                {tab.label}
              </Link>
            ))}
          </nav>
        </aside>
        <main className="min-w-0 flex-1">{children}</main>
      </div>
    </div>
  );
}
