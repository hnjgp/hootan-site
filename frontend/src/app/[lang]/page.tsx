import { notFound } from "next/navigation";
import { AuthProvider } from "@/components/auth/AuthProvider";
import { Header } from "@/components/header/Header";
import { Hero, SECTION_IDS } from "@/components/home/Hero";
import { JobFit } from "@/components/home/jobfit/JobFit";
import { Play } from "@/components/home/play/Play";
import { Projects } from "@/components/home/projects/Projects";
import { Trading } from "@/components/home/trading/Trading";
import { Twin } from "@/components/home/twin/Twin";
import { SectionScroller } from "@/components/SectionScroller";
import { getDictionary, hasLocale } from "@/i18n";

export default async function Home({ params }: PageProps<"/[lang]">) {
  const { lang } = await params;
  if (!hasLocale(lang)) notFound();
  const t = getDictionary(lang);

  return (
    <AuthProvider>
      <Header lang={lang} t={t.header} auth={t.auth} />
      <SectionScroller />
      <main>
        <Hero lang={lang} t={t.main} game={t.game} />
        {SECTION_IDS.map((id) => (
          <section key={id} id={id} className="page-section mx-auto flex max-w-[1200px] flex-col justify-center px-4 pb-10 sm:px-6 snap:py-5 snap:pb-5">
            {id === "twin" ? (
              <Twin t={t.twin} />
            ) : id === "job-fit" ? (
              <JobFit t={t.jobfit} lang={lang} />
            ) : id === "trading" ? (
              <Trading t={t.trading} lang={lang} />
            ) : id === "play" ? (
              <Play t={t.play} auth={t.auth} lang={lang} />
            ) : (
              <Projects t={t.projects} agents={t.trading.agents} lang={lang} />
            )}
          </section>
        ))}
      </main>
    </AuthProvider>
  );
}
