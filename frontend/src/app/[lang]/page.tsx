import { notFound } from "next/navigation";
import { Header } from "@/components/header/Header";
import { SectionIcon } from "@/components/icons";
import { Hero, SECTION_IDS } from "@/components/home/Hero";
import { JobFit } from "@/components/home/jobfit/JobFit";
import { Twin } from "@/components/home/twin/Twin";
import { SectionScroller } from "@/components/SectionScroller";
import { getDictionary, hasLocale } from "@/i18n";

export default async function Home({ params }: PageProps<"/[lang]">) {
  const { lang } = await params;
  if (!hasLocale(lang)) notFound();
  const t = getDictionary(lang);

  return (
    <>
      <Header lang={lang} t={t.header} />
      <SectionScroller />
      <main>
        <Hero lang={lang} t={t.main} game={t.game} />
        {SECTION_IDS.map((id, k) => (
          <section key={id} id={id} className="page-section mx-auto flex max-w-[1200px] flex-col justify-center px-4 pb-10 sm:px-6 snap:py-5 snap:pb-5">
            {id === "twin" ? (
              <Twin t={t.twin} />
            ) : id === "job-fit" ? (
              <JobFit t={t.jobfit} lang={lang} />
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
