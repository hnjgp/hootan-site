import Link from "next/link";
import type { Dictionary, Locale } from "@/i18n";

function TwinBubble({ text }: { text: string }) {
  return (
    <div className="flex max-w-[92%] items-end gap-2.5 self-start">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src="/assets/me_avatar_sm.jpg" alt="" className="h-9 w-9 flex-none rounded-full border-[1.5px] border-line" />
      <div className="rounded-[14px] rounded-es-[4px] border-[1.5px] border-line bg-bg px-3.5 py-2.5 text-[15px] leading-[1.6]">
        {text}
      </div>
    </div>
  );
}

/**
 * The big two-part card: a sample twin conversation with a question box on one side,
 * the drawing of Hootan at his desk on the other. Asking sends the visitor to the twin page.
 */
export function InterviewDesk({ lang, t }: { lang: Locale; t: Dictionary["main"] }) {
  const twin = `/${lang}/twin`;
  const chip =
    "btn chip rounded-full border border-line px-3 py-[7px] text-[13px] text-ink no-underline";

  return (
    <section aria-label={t.desk} className="mx-auto max-w-[1200px] px-4 pt-7 pb-12 sm:px-6">
      <div className="flex flex-wrap overflow-hidden rounded-[22px] border-2 border-line bg-card shadow-[6px_6px_0_var(--line)]">
        <div className="flex min-w-0 flex-[1_1_380px] flex-col gap-3.5 p-6 sm:p-8">
          <div className="font-hand text-[25px] text-accent">{t.desk}</div>
          <TwinBubble text={t.b1} />
          <div className="max-w-[80%] self-end rounded-[14px] rounded-ee-[4px] bg-inv px-3.5 py-2.5 text-[15px] leading-[1.55] text-inv-ink">
            {t.q1}
          </div>
          <TwinBubble text={t.a1} />
          <form action={twin} className="mt-1.5 flex gap-2">
            <label htmlFor="desk-q" className="sr-only">
              {t.desk}
            </label>
            <input
              id="desk-q"
              name="q"
              type="text"
              maxLength={500}
              required
              placeholder={t.ph}
              className="min-h-12 min-w-0 flex-auto rounded-xl border-[1.5px] border-line bg-input px-3.5 text-[15px] text-ink"
            />
            <button
              type="submit"
              className="btn inline-flex min-h-12 items-center rounded-xl border-[1.5px] border-line bg-orange px-5 text-[15px] font-bold text-[#1e1c1a]"
            >
              {t.ask}
            </button>
          </form>
          <div className="flex flex-wrap gap-1.5">
            <Link href={`${twin}?q=${encodeURIComponent(t.c1)}`} className={chip}>
              {t.c1}
            </Link>
            <Link href={`${twin}?q=${encodeURIComponent(t.c2)}`} className={chip}>
              {t.c2}
            </Link>
            <Link href={`/${lang}/job-fit`} className={chip}>
              {t.c3}
            </Link>
          </div>
        </div>
        <Link
          href={twin}
          dir="ltr"
          className="swap relative block aspect-square min-w-0 flex-[1_1_460px] border-line bg-paper max-[891px]:border-t-[1.5px] min-[892px]:border-s-[1.5px]"
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/assets/me_smile.jpg" alt={t.alt} className="absolute inset-0 h-full w-full object-cover" />
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/assets/me_talk.jpg" alt="" className="alt absolute inset-0 h-full w-full object-cover" />
          <span
            dir={lang === "fa" ? "rtl" : "ltr"}
            className="alt absolute top-4 left-4 rounded-full bg-[#1e1c1a] px-3 py-1.5 text-[13px] font-semibold text-[#f3ebdd]"
          >
            {t.hover}
          </span>
        </Link>
      </div>
    </section>
  );
}
