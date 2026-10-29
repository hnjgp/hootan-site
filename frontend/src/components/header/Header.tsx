import type { Dictionary, Locale } from "@/i18n";
import { Account } from "./Account";
import { Contact } from "./Contact";
import { LangSwitch } from "./LangSwitch";
import { ThemeToggle } from "./ThemeToggle";

/** Header shared by every page: the visitor's account, availability, contact, theme, language and résumé; sticky from tablet width up. */
export function Header({ lang, t, auth }: { lang: Locale; t: Dictionary["header"]; auth: Dictionary["auth"] }) {
  return (
    <header className="z-20 border-b-[1.5px] border-line bg-head md:sticky md:top-0">
      <div className="mx-auto flex max-w-[1200px] flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6">
        <Account t={auth} />
        <div className="inline-flex items-center gap-2 text-[14px] font-semibold text-green md:max-xl:hidden">
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
