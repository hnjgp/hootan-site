"use client";

import { useEffect, useState } from "react";
import type { Dictionary, Locale } from "@/i18n";

/** Send the token once; on success go to the game, otherwise say the link is not valid. */
export function Recover({ t, lang }: { t: Dictionary["play"]; lang: Locale }) {
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    const token = new URLSearchParams(location.search).get("token") ?? "";
    fetch("/api/game/recover", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token }),
    }).then((r) => (r.ok ? location.replace(`/${lang}#play`) : setFailed(true)));
  }, [lang]);

  return (
    <div className="flex flex-col items-center gap-4 rounded-[20px] border-2 border-line bg-card p-8 text-center shadow-[5px_5px_0_var(--line)]">
      <p role="status" className="m-0 text-[17px] font-bold">
        {failed ? t.recoverFail : t.recovering}
      </p>
      {failed && (
        <a href={`/${lang}#play`} className="btn rounded-full border-[1.5px] border-line bg-orange px-5 py-2.5 font-bold text-[#1e1c1a] no-underline">
          {t.back}
        </a>
      )}
    </div>
  );
}
