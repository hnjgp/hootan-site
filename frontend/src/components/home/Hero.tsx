import type { Dictionary } from "@/i18n";

/** Top of the home page: handwritten welcome, headline, one-line pitch and availability. */
export function Hero({ t }: { t: Dictionary["main"] }) {
  return (
    <section className="relative overflow-hidden">
      <div className="relative mx-auto max-w-[1200px] px-4 pt-16 pb-2 text-center sm:px-6">
        <div className="font-hand text-[30px] text-accent">{t.tag}</div>
        <h1 className="mx-auto mt-1 mb-4 max-w-[920px] text-[clamp(34px,6vw,56px)] leading-[1.06] font-bold tracking-[-1px]">
          {t.h1}
        </h1>
        <p className="mx-auto max-w-[660px] text-[18px] leading-[1.7] text-muted">{t.sub}</p>
        <div className="mt-[18px] inline-flex items-center gap-2 text-[14px] font-semibold text-green">
          <span className="pulse h-2 w-2 shrink-0 rounded-full bg-green" aria-hidden="true" />
          {t.open}
        </div>
      </div>
    </section>
  );
}
