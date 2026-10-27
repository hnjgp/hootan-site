"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { Locale } from "@/i18n";

const options: { code: Locale; text: string; fa: boolean }[] = [
  { code: "en", text: "EN", fa: false },
  { code: "fa", text: "فا", fa: true },
];

/** EN / فا pill; links to the same page in the other language and remembers the choice in a cookie. */
export function LangSwitch({ lang, label }: { lang: Locale; label: string }) {
  const pathname = usePathname();
  const rest = pathname.split("/").slice(2).join("/");

  return (
    <div role="group" aria-label={label} className="flex rounded-full border-[1.5px] border-line bg-card p-[3px]">
      {options.map((o) => {
        const on = o.code === lang;
        return (
          <Link
            key={o.code}
            href={`/${o.code}${rest ? `/${rest}` : ""}`}
            aria-current={on ? "true" : undefined}
            onClick={() => {
              document.cookie = `lang=${o.code}; path=/; max-age=31536000; SameSite=Lax`;
            }}
            className={`flex min-h-[34px] min-w-[40px] items-center justify-center rounded-full font-bold no-underline ${
              o.fa ? "font-fa text-[14px]" : "font-sans text-[13px]"
            } ${on ? "bg-inv text-inv-ink" : "btn text-ink"}`}
          >
            {o.text}
          </Link>
        );
      })}
    </div>
  );
}
