import { redirect } from "next/navigation";

export default async function LegacyProjectMaterialsRedirect() {
  redirect("/materials");
}
