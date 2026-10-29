import { dirOf, type Dictionary, type Locale } from "@/i18n";
import { SectionIcon } from "../icons";
import { HeroScene } from "./HeroScene";
import { RobotGame } from "./RobotGame";

export const SECTION_IDS = ["twin", "job-fit", "trading", "projects"] as const;
/** The last button opens the "this site" project inside the projects section. */
const TARGETS = [...SECTION_IDS.map((id) => `#${id}`), "#project-site"];

/**
 * Top of the home page: the drawing with the headline as a thought cloud on one side;
 * on the other, five buttons that jump to the sections below (each shows a hint on hover)
 * and the runaway "I'm not a robot" box.
 */
export function Hero({ lang, t, game }: { lang: Locale; t: Dictionary["main"]; game: Dictionary["game"] }) {
  return (
    <section className="page-section mx-auto grid max-w-[1200px] items-center gap-8 px-4 pt-5 pb-16 sm:px-6 snap:pb-5 md:grid-cols-[1.1fr_1fr]">
      <HeroScene tag={t.tag} title={t.h1} dir={dirOf(lang)} />
      <div className="flex flex-col gap-5">
        <nav className="flex flex-col gap-2">
          {t.buttons.map((label, k) => (
            <a
              key={label}
              href={TARGETS[k]}
              className="hint btn group flex items-center gap-3 rounded-2xl border-2 border-line bg-card px-4 py-2 text-ink no-underline shadow-[3px_3px_0_var(--line)]"
            >
              <span className="flex h-9 w-9 flex-none items-center justify-center rounded-xl border-[1.5px] border-line bg-bg transition-colors group-hover:bg-orange group-hover:text-[#1e1c1a] group-focus-visible:bg-orange">
                <SectionIcon i={k} />
              </span>
              <span className="flex min-w-0 flex-1 flex-col">
                <span className="text-[16px] font-semibold">{label}</span>
                <span className="hint-text text-[14px] text-muted">{t.hints[k]}</span>
              </span>
              <span aria-hidden="true" className="text-accent">
                {lang === "fa" ? "←" : "→"}
              </span>
            </a>
          ))}
        </nav>
        <RobotGame g={game} />
      </div>
    </section>
  );
}
