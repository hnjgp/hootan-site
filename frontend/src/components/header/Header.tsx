import Link from "next/link";
import type { Dictionary, Locale } from "@/i18n";
import { LangSwitch } from "./LangSwitch";
import { ModeTabs } from "./ModeTabs";
import { ThemeToggle } from "./ThemeToggle";

/** Sticky header shared by every page: name, the two tabs, theme, language and résumé. */
export function Header({ lang, t }: { lang: Locale; t: Dictionary["header"] }) {
  return (
    <header className="sticky top-0 z-20 border-b-[1.5px] border-line bg-head">
      <div className="mx-auto flex max-w-[1200px] flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6">
        <Link href={`/${lang}`} className="flex items-center gap-2.5 text-ink no-underline">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/assets/me_avatar_sm.jpg" alt="" className="h-[34px] w-[34px] rounded-full border-[1.5px] border-line" />
          <span className="text-[16px] font-semibold">{t.name}</span>
        </Link>
        <ModeTabs lang={lang} label={t.modeLabel} portfolio={t.portfolio} trading={t.trading} />
        <div className="flex flex-wrap items-center gap-2">
          <Link href={`/${lang}#projects`} className="px-1.5 py-2.5 text-[15px] text-ink no-underline">
            {t.projects}
          </Link>
          <ThemeToggle label={t.themeLabel} />
          <LangSwitch lang={lang} label={t.langLabel} />
          <a
            href={`/assets/resume_${lang}.pdf`}
            download
            className="btn inline-flex min-h-11 items-center rounded-full border-[1.5px] border-line bg-orange px-[18px] text-[15px] font-bold text-[#1e1c1a] no-underline"
          >
            {t.resume}
          </a>
        </div>
      </div>
    </header>
  );
}
