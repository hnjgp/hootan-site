"use client";

import { Underlined } from "@/components/HandUnderline";
import { useState } from "react";
import { CONTACT } from "@/contact";
import type { Dictionary, Locale } from "@/i18n";
import { ScoreRing } from "./ScoreRing";
import { useJobFit } from "./useJobFit";

const MIN = 50;
const MAX = 6000;

/** Job fit section: paste an ad on one side, get an honest score with strengths, gaps and questions on the other. */
export function JobFit({ t, lang }: { t: Dictionary["jobfit"]; lang: Locale }) {
  const { busy, word, result, note, check } = useJobFit(t, lang);
  const [ad, setAd] = useState("");
  const short = ad.trim().length < MIN;
  const num = (n: number) => n.toLocaleString(lang === "fa" ? "fa-IR-u-nu-latn" : "en-US");

  const card = "rounded-2xl border-[1.5px] border-line p-5";
  const hand = lang === "fa" ? "text-[17px] font-bold" : "font-hand text-[23px]";
  const list = "m-0 flex flex-col gap-2 ps-5 text-[15px] leading-[1.55]";

  return (
    <div className="flex min-h-0 flex-col snap:h-full">
      <div className="font-hand text-[25px] text-accent">{t.tag}</div>
      <h2 className="m-0 text-[30px] leading-[1.15] font-bold sm:text-[36px]">
        <Underlined>{t.h2}</Underlined>
      </h2>
      <p className="mt-2 mb-5 max-w-[760px] text-[16px] leading-[1.6] text-muted">{t.sub}</p>

      <div className="flex flex-col gap-6 md:grid md:grid-cols-[minmax(320px,400px)_1fr] snap:min-h-0 snap:flex-1">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (!short) check(ad);
          }}
          className="flex min-h-0 min-w-0 flex-col gap-3 rounded-[18px] border-[1.5px] border-line bg-card p-5"
        >
          <div className="flex flex-wrap items-center justify-between gap-2">
            <label htmlFor="jd" className="text-[15px] font-bold">
              {t.label}
            </label>
            <button type="button" onClick={() => setAd(t.sampleAd)} className="btn chip min-h-9 rounded-full border border-line bg-card px-3 text-[13px] text-ink">
              {t.sample}
            </button>
          </div>
          <textarea
            id="jd"
            rows={12}
            value={ad}
            maxLength={MAX}
            onChange={(e) => setAd(e.target.value)}
            placeholder={t.placeholder}
            className="w-full resize-y rounded-xl snap:min-h-0 snap:flex-1 snap:resize-none border-[1.5px] border-line bg-input p-3.5 text-[14px] leading-[1.7] text-ink"
          />
          <div className="flex justify-between font-mono text-[12px] text-muted">
            <span>{short ? t.min : ""}</span>
            <span dir="ltr">
              {num(ad.length)} / {num(MAX)}
            </span>
          </div>
          {busy ? (
            <div className="flex min-h-[50px] flex-wrap items-center justify-center gap-x-2.5 rounded-xl bg-inv px-3 text-inv-ink">
              <span aria-hidden="true" className="pulse h-2.5 w-2.5 rounded-full bg-orange" />
              <span key={word[0]} className="pop text-[17px] font-bold">
                {word[0]}
              </span>
              <span className="text-[13px] opacity-75">({word[1]})</span>
            </div>
          ) : (
            <button
              type="submit"
              disabled={short}
              className="btn min-h-[50px] w-full rounded-xl border-[1.5px] border-line bg-orange text-[16px] font-bold text-[#1e1c1a] disabled:opacity-50"
            >
              {t.check}
            </button>
          )}
          <div className="text-[13px] leading-[1.6] text-muted">{t.note}</div>
        </form>

        <section aria-label={t.resultLabel} aria-live="polite" className="flex min-h-0 min-w-0 flex-col gap-4">
          <div className="flex flex-none flex-wrap items-center gap-[22px] float-c rounded-[18px] border-2 border-line bg-card p-5 shadow-[5px_5px_0_var(--line)]">
            <ScoreRing score={result?.score ?? null} of={t.of} lang={lang} />
            <div className="min-w-0 flex-[1_1_260px]">
              {note ? (
                <div className="pop rounded-[14px] border-2 border-orange bg-orange/15 px-4 py-3 text-[17px] font-bold">{note}</div>
              ) : result ? (
                <>
                  <div className="font-mono text-[12px] text-muted">{t.result}</div>
                  <div className="mt-1.5 text-[18px] leading-[1.6] font-bold">{result.summary}</div>
                </>
              ) : (
                <div className="text-[15px] leading-[1.7] text-muted">{t.empty}</div>
              )}
            </div>
          </div>

          {!result && (
            <div aria-hidden="true" className="grid min-h-0 flex-1 auto-rows-[minmax(0,1fr)] gap-4 opacity-60 sm:grid-cols-2">
              {[
                [t.strengths, "text-green"],
                [t.gaps, "text-accent"],
                [t.ask, "", "sm:col-span-2"],
              ].map(([title, color, span]) => (
                <div key={title} className={`flex min-h-0 flex-col gap-2.5 overflow-hidden border-dashed ${card} ${span}`}>
                  <div className={`${hand} ${color}`}>{title}</div>
                  {[80, 60, 70].map((w) => (
                    <div key={w} className="h-2.5 flex-none rounded-full bg-soft" style={{ width: `${w}%` }} />
                  ))}
                </div>
              ))}
            </div>
          )}
          {result && (
            <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto p-1">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className={`pop bg-card ${card}`}>
                  <div className={`${hand} mb-1.5 text-green`}>{t.strengths}</div>
                  <ul className={list}>
                    {result.strengths.map((s) => (
                      <li key={s.point}>
                        {s.point}
                        <div className="text-[13px] text-muted">{s.evidence}</div>
                      </li>
                    ))}
                  </ul>
                </div>
                <div className={`pop bg-card ${card}`} style={{ animationDelay: "0.15s" }}>
                  <div className={`${hand} mb-1.5 text-accent`}>{t.gaps}</div>
                  <ul className={list}>
                    {result.gaps.map((g) => (
                      <li key={g}>{g}</li>
                    ))}
                  </ul>
                </div>
              </div>
              {result.questions.length > 0 && (
                <div className={`pop border-dashed ${card}`} style={{ animationDelay: "0.3s" }}>
                  <div className={`${hand} mb-1.5`}>{t.ask}</div>
                  <ol className={list}>
                    {result.questions.map((q) => (
                      <li key={q}>{q}</li>
                    ))}
                  </ol>
                </div>
              )}
              <div className="flex flex-wrap gap-3">
                <a href="#twin" className="btn chip inline-flex min-h-[46px] items-center rounded-full border-[1.5px] border-line px-[18px] text-[15px] text-ink no-underline">
                  {t.follow}
                </a>
                <a
                  href={`mailto:${CONTACT.email}`}
                  className="btn inline-flex min-h-[46px] items-center rounded-full bg-inv px-[18px] text-[15px] font-bold text-inv-ink no-underline"
                >
                  {t.email}
                </a>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
