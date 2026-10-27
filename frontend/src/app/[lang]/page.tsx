import { notFound } from "next/navigation";
import { Header } from "@/components/header/Header";
import { Hero } from "@/components/home/Hero";
import { InterviewDesk } from "@/components/home/InterviewDesk";
import { getDictionary, hasLocale } from "@/i18n";

export default async function Home({ params }: PageProps<"/[lang]">) {
  const { lang } = await params;
  if (!hasLocale(lang)) notFound();
  const t = getDictionary(lang);

  return (
    <>
      <Header lang={lang} t={t.header} />
      <main>
        <Hero t={t.main} />
        <InterviewDesk lang={lang} t={t.main} />
      </main>
    </>
  );
}
