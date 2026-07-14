"use client";

import { useParams } from "next/navigation";

import { WorkspaceShell } from "@/components/WorkspaceShell";

export default function WorkspaceLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const params = useParams<{ projectId: string }>();
  return <WorkspaceShell projectId={params.projectId}>{children}</WorkspaceShell>;
}
