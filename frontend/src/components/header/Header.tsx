import Link from "next/link";
import type { Dictionary, Locale } from "@/i18n";
import { Contact } from "./Contact";
import { LangSwitch } from "./LangSwitch";
import { ThemeToggle } from "./ThemeToggle";

/** Sticky header shared by every page: name, availability, contact, theme, language and résumé. */
export function Header({ lang, t }: { lang: Locale; t: Dictionary["header"] }) {
  return (
    <header className="sticky top-0 z-20 border-b-[1.5px] border-line bg-head">
      <div className="mx-auto flex max-w-[1200px] flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6">
        <Link href={`/${lang}`} className="flex items-center gap-2.5 text-ink no-underline">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/assets/me_avatar_sm.jpg" alt="" className="h-[34px] w-[34px] rounded-full border-[1.5px] border-line" />
          <span className="text-[16px] font-semibold">{t.name}</span>
        </Link>
        <div className="inline-flex items-center gap-2 text-[14px] font-semibold text-green">
          <span className="pulse h-2 w-2 shrink-0 rounded-full bg-green" aria-hidden="true" />
          {t.open}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Contact t={t} />
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
