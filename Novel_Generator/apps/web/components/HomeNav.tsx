"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export function HomeNav() {
  const pathname = usePathname();
  const onBookshelf = pathname === "/";
  const onMaterials = pathname === "/materials" || pathname.startsWith("/materials/");
  const onSettings = pathname === "/settings" || pathname.startsWith("/settings/");

  function tabClass(active: boolean) {
    return `rounded-lg px-4 py-2 text-sm font-medium ${
      active
        ? "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
        : "text-zinc-600 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-zinc-800"
    }`;
  }

  return (
    <nav className="flex gap-1">
      <Link href="/" className={tabClass(onBookshelf)}>
        我的书架
      </Link>
      <Link href="/materials" className={tabClass(onMaterials)}>
        我的素材库
      </Link>
      <Link href="/settings/models" className={tabClass(onSettings)}>
        设置
      </Link>
    </nav>
  );
}
