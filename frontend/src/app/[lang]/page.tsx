import { notFound } from "next/navigation";
import { Header } from "@/components/header/Header";
import { SectionIcon } from "@/components/icons";
import { Hero, SECTION_IDS } from "@/components/home/Hero";
import { Twin } from "@/components/home/twin/Twin";
import { getDictionary, hasLocale } from "@/i18n";

export default async function Home({ params }: PageProps<"/[lang]">) {
  const { lang } = await params;
  if (!hasLocale(lang)) notFound();
  const t = getDictionary(lang);

  return (
    <>
      <Header lang={lang} t={t.header} />
      <main>
        <Hero lang={lang} t={t.main} game={t.game} />
        {SECTION_IDS.map((id, k) => (
          <section key={id} id={id} className="mx-auto max-w-[1200px] scroll-mt-[90px] px-4 pb-10 sm:px-6">
            {id === "twin" ? (
              <Twin t={t.twin} />
            ) : (
              <div className="flex min-h-[50vh] items-center justify-center gap-3 rounded-[22px] border-2 border-dashed border-line text-[28px] font-bold">
                <span className="text-accent">
                  <SectionIcon i={k} size={30} />
                </span>
                {t.main.buttons[k]}
              </div>
            )}
          </section>
        ))}
      </main>
    </>
  );
}
