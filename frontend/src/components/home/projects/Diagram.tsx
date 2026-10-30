import type { Dictionary } from "@/i18n";
import { ASTRA } from "./diagrams/Astra";
import { BEHENGAM } from "./diagrams/Behengam";
import { NOTES } from "./diagrams/Notes";
import { PRICE } from "./diagrams/Price";
import { SITE } from "./diagrams/Site";

export type ProjectId = "astra" | "notes" | "price" | "behengam" | "site";
type Id = ProjectId;
type T = Dictionary["projects"];

/** The diagram `name` of project `id`. */
export function Diagram({
  id,
  name,
  t,
  agents,
}: {
  id: Id;
  name: string;
  t: T;
  agents: string[];
}) {
  if (id === "astra") {
    const C = ASTRA[name as keyof typeof ASTRA];
    return <C d={t.items.astra.d} />;
  }
  if (id === "notes") {
    const C = NOTES[name as keyof typeof NOTES];
    return <C d={t.items.notes.d} />;
  }
  if (id === "price") {
    const C = PRICE[name as keyof typeof PRICE];
    return <C d={t.items.price.d} />;
  }
  if (id === "behengam") {
    const C = BEHENGAM[name as keyof typeof BEHENGAM];
    return <C d={t.items.behengam.d} />;
  }
  const C = SITE[name as keyof typeof SITE];
  return <C d={t.items.site.d} agents={agents} />;
}
