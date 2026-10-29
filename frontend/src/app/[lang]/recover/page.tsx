import { notFound } from "next/navigation";
import { getDictionary, hasLocale } from "@/i18n";
import { Recover } from "./Recover";

/** The recovery link from the game: brings a player to this device, then back to the game. */
export default async function RecoverPage({ params }: PageProps<"/[lang]/recover">) {
  const { lang } = await params;
  if (!hasLocale(lang)) notFound();
  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <Recover t={getDictionary(lang).play} lang={lang} />
    </main>
  );
}
