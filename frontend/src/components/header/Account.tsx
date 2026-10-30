"use client";

import { useState } from "react";
import type { Dictionary, Locale } from "@/i18n";
import { AuthForm, type Mode } from "../auth/AuthForm";
import { useAuth } from "../auth/AuthProvider";

/** The visitor's corner of the header: log-in and sign-up buttons, or their photo and
 * username with a menu to set a photo or log out. */
export function Account({ t, lang }: { t: Dictionary["auth"]; lang: Locale }) {
  const { me, photo, logOut, setPhoto } = useAuth();
  const [open, setOpen] = useState<Mode | "menu" | null>(null);
  const [photoFailed, setPhotoFailed] = useState(false);
  const panel = "absolute start-0 top-[52px] z-30 w-[300px] max-w-[calc(100vw-32px)] rounded-2xl border-2 border-line bg-card p-4 shadow-[5px_5px_0_var(--line)]";
  const pill = "btn min-h-11 rounded-full border-[1.5px] border-line px-4 text-[15px] font-semibold";

  if (me === undefined) return <div className="h-11" />;

  return (
    <div className="relative" onKeyDown={(e) => e.key === "Escape" && setOpen(null)}>
      {open && <button type="button" aria-hidden="true" tabIndex={-1} onClick={() => setOpen(null)} className="fixed inset-0 z-20 cursor-default" />}
      {me ? (
        <button
          type="button"
          aria-expanded={open === "menu"}
          aria-label={t.account}
          onClick={() => setOpen(open ? null : "menu")}
          className="relative z-30 flex items-center gap-2.5 text-ink"
        >
          {me.avatar ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={`/api/game/me/avatar?v=${photo}`} alt="" className="h-[34px] w-[34px] rounded-full border-[1.5px] border-line object-cover" />
          ) : (
            <span className="flex h-[34px] w-[34px] items-center justify-center rounded-full border-[1.5px] border-line bg-orange text-[16px] font-bold text-[#1e1c1a] uppercase">
              {me.nickname[0]}
            </span>
          )}
          <span dir="auto" className="text-[16px] font-semibold">{me.nickname}</span>
        </button>
      ) : (
        <div className="relative z-30 flex gap-2">
          <button type="button" onClick={() => setOpen(open === "login" ? null : "login")} className={`${pill} bg-card text-ink`}>
            {t.login}
          </button>
          <button type="button" onClick={() => setOpen(open === "signup" ? null : "signup")} className={`${pill} bg-inv text-inv-ink`}>
            {t.signup}
          </button>
        </div>
      )}

      {open === "menu" && me && (
        <div className={`${panel} flex flex-col gap-1`}>
          <label className="btn chip cursor-pointer rounded-lg px-2 py-2 text-[15px] hover:bg-soft">
            {t.photo}
            <input
              type="file"
              accept="image/*"
              className="sr-only"
              onChange={async (e) => {
                const file = e.target.files?.[0];
                if (!file) return;
                const ok = await setPhoto(file);
                setPhotoFailed(!ok);
                if (ok) setOpen(null);
              }}
            />
          </label>
          {photoFailed && <p role="alert" className="m-0 px-2 text-[13px] text-accent">{t.errPhoto}</p>}
          {me.admin && (
            <a href={`/${lang}/admin`} className="btn chip rounded-lg px-2 py-2 text-[15px] hover:bg-soft">
              {t.adminLink}
            </a>
          )}
          <button
            type="button"
            onClick={() => {
              logOut();
              setOpen(null);
            }}
            className="btn chip rounded-lg px-2 py-2 text-start text-[15px] hover:bg-soft"
          >
            {t.logout}
          </button>
        </div>
      )}
      {(open === "login" || open === "signup") && (
        <div className={panel}>
          <AuthForm key={open} t={t} start={open} onDone={() => setOpen(null)} />
        </div>
      )}
    </div>
  );
}
