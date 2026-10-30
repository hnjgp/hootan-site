import { CONTACT } from "@/contact";
import type { Dictionary } from "@/i18n";
import { TelegramIcon, WhatsAppIcon } from "../icons";

/** "Contact me" button that opens a small card with email, phone, WhatsApp and Telegram (no JavaScript). */
export function Contact({ t }: { t: Dictionary["header"] }) {
  const row = "flex min-h-11 items-center gap-2 rounded-lg px-2 py-2 text-ink no-underline hover:bg-soft";
  const app = "btn flex flex-1 items-center justify-center gap-1.5 rounded-xl border-[1.5px] border-line py-2 text-[14px] text-ink no-underline";
  return (
    <details className="relative">
      <summary className="btn flex min-h-11 cursor-pointer list-none items-center rounded-full border-[1.5px] border-line bg-card px-4 text-[15px] font-semibold text-ink">
        {t.contact}
      </summary>
      <div className="absolute end-0 top-[52px] z-30 flex w-[280px] flex-col gap-1 rounded-2xl border-2 border-line bg-card p-3 shadow-[5px_5px_0_var(--line)]">
        <a href={`mailto:${CONTACT.email}`} className={row}>
          <span className="text-muted">{t.email}</span>
          <span dir="ltr" className="ms-auto font-mono text-[13px]">
            {CONTACT.email}
          </span>
        </a>
        <a href={`tel:${CONTACT.phone}`} className={row}>
          <span className="text-muted">{t.phone}</span>
          <span dir="ltr" className="ms-auto font-mono text-[14px]">
            {CONTACT.phoneDisplay}
          </span>
        </a>
        <div className="mt-1 flex gap-2">
          <a href={CONTACT.whatsapp} target="_blank" rel="noreferrer" className={app}>
            <WhatsAppIcon /> WhatsApp
          </a>
          <a href={CONTACT.telegram} target="_blank" rel="noreferrer" className={app}>
            <TelegramIcon /> Telegram
          </a>
        </div>
      </div>
    </details>
  );
}
