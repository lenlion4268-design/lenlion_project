import { redirect } from "next/navigation";

export default async function LegacyMaterialsRedirect() {
  redirect("/materials");
}
