"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { Locale } from "@/i18n";

/** The fixed Portfolio | AI Trading Floor switch; the active tab follows the URL. */
export function ModeTabs({
  lang,
  label,
  portfolio,
  trading,
}: {
  lang: Locale;
  label: string;
  portfolio: string;
  trading: string;
}) {
  const onTrading = usePathname().startsWith(`/${lang}/trading`);
  const base = "flex min-h-10 items-center gap-2 rounded-full px-[18px] text-[14px] font-semibold no-underline";
  const active = "bg-inv text-inv-ink";
  const idle = "btn text-ink";

  return (
    <nav aria-label={label} className="flex rounded-full border-[1.5px] border-line bg-card p-1">
      <Link href={`/${lang}`} aria-current={onTrading ? undefined : "page"} className={`${base} ${onTrading ? idle : active}`}>
        {portfolio}
      </Link>
      <Link href={`/${lang}/trading`} aria-current={onTrading ? "page" : undefined} className={`${base} ${onTrading ? active : idle}`}>
        <span className="pulse h-2 w-2 rounded-full bg-orange" aria-hidden="true" />
        {trading}
      </Link>
    </nav>
  );
}
