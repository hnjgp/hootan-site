import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { AdminPanel } from "@/components/admin/AdminPanel";
import { getDictionary, hasLocale } from "@/i18n";

export const metadata: Metadata = { robots: { index: false, follow: false } };

export default async function Admin({ params }: PageProps<"/[lang]/admin">) {
  const { lang } = await params;
  if (!hasLocale(lang)) notFound();
  return <AdminPanel t={getDictionary(lang).admin} lang={lang} />;
}
