"use client";

import { Underlined } from "@/components/HandUnderline";
import { useEffect, useRef } from "react";
import type { Dictionary, Locale } from "@/i18n";
import { latinDigits } from "@/lib/digits";
import { NightSky } from "./NightSky";
import { useMeeting } from "./useMeeting";

/** Each agent's window on office_idle.jpg in percent: left, top, width, height (CLAUDE.md 15.7). */
const WINDOWS = [
  ["data", 23.92, 30.71, 10.05, 16.58],
  ["news", 38.04, 30.71, 9.99, 16.58],
  ["bull", 52.15, 30.71, 10.11, 16.58],
  ["bear", 66.09, 30.71, 10.05, 16.58],
  ["risk", 25.54, 59.09, 6.16, 18.28],
  ["trader", 31.94, 59.09, 6.22, 18.28],
  ["pm", 62.74, 59.09, 13.16, 18.28],
] as const;

/** First sentence of a turn, so every line of the meeting fits in the dialog. */
const firstSentence = (text: string) => text.split(/(?<=[.؛;])\s/)[0];
const indexOf = (agent: string) =>
  Math.max(
    WINDOWS.findIndex((w) => w[0] === agent),
    0,
  );

/** A number in the intro, boxed so it stands out from the sentence. */
function Num({
  children,
  tone = "text-ink",
}: {
  children: string;
  tone?: string;
}) {
  return (
    <span
      dir="ltr"
      className={`inline-block rounded-md border-[1.5px] border-line px-1.5 font-mono text-[14px] leading-[1.5] font-bold whitespace-nowrap ${tone}`}
    >
      {children}
    </span>
  );
}

/** Trading floor: the team's money, the building with the speaking agent, and the meeting's dialog beside it. */
export function Trading({
  t,
  lang,
}: {
  t: Dictionary["trading"];
  lang: Locale;
}) {
  const { summary: s, events, live, done, failed, start } = useMeeting();
  const dialog = useRef<HTMLDivElement>(null);
  const loc = lang === "fa" ? "fa-IR-u-nu-latn" : "en-US";

  useEffect(() => {
    dialog.current?.scrollTo({
      top: dialog.current.scrollHeight,
      behavior: "smooth",
    });
  }, [events.length, done]);

  const speaker = events.length ? indexOf(events.at(-1)!.agent) : 0;
  const [name, left, top, width, height] = WINDOWS[speaker];
  const usd = (v: string) => "$" + Math.round(Number(v)).toLocaleString(loc);
  const change = (v: string) => {
    const n = (Number(v) / Number(s!.start_usd) - 1) * 100;
    return (
      new Intl.NumberFormat(loc, {
        signDisplay: "always",
        maximumFractionDigits: 2,
      }).format(n) + "%"
    );
  };
  const tone = (v: string) =>
    Number(v) < Number(s!.start_usd) ? "text-accent" : "text-green";
  const [before, after] = t.started.split("{start}");
  const day = (d: string) =>
    new Date(d + "T12:00:00").toLocaleDateString(loc, {
      day: "numeric",
      month: "long",
    });
  const time = (iso: string) =>
    new Date(iso).toLocaleTimeString(loc, {
      hour: "2-digit",
      minute: "2-digit",
      timeZone: "Asia/Tehran",
    });

  const status = !s ? null : live ? (
    <span className="flex items-center gap-2 font-semibold">
      <span
        aria-hidden="true"
        className="pulse h-2 w-2 rounded-full bg-orange"
      />
      {events.length ? t.running : t.starting}
    </span>
  ) : s.today_status === null ? (
    <span className="flex flex-wrap items-center gap-x-3 gap-y-1.5">
      <b>{t.first}</b>
      <button
        type="button"
        onClick={start}
        className="btn min-h-10 rounded-full border-[1.5px] border-line bg-orange px-4 text-[14px] font-bold text-[#1e1c1a]"
      >
        {t.start}
      </button>
      {failed && <span className="text-accent">{t.error}</span>}
    </span>
  ) : s.today_status === "done" && s.today_started_at ? (
    t.heldAt.replace("{time}", time(s.today_started_at))
  ) : (
    t.closed
  );
  const today = live || (s?.last && s.today_status === "done");

  return (
    <div className="flex min-h-0 flex-col snap:h-full">
      <h2 className="m-0 text-[30px] leading-[1.15] font-bold sm:text-[34px]">
        <Underlined>{t.h2}</Underlined>
      </h2>
      <p className="mt-1.5 mb-3 text-[15px] leading-[1.7] text-muted">
        {t.sub}{" "}
        {s && (
          <>
            {before}
            <Num>{usd(s.start_usd).slice(1)}</Num>
            {after} <Num>{usd(s.value_usd)}</Num>{" "}
            <Num tone={tone(s.value_usd)}>{change(s.value_usd)}</Num> {t.has}{" "}
            {t.hold} <Num>{usd(s.hold_usd)}</Num>{" "}
            <Num tone={tone(s.hold_usd)}>{change(s.hold_usd)}</Num>
          </>
        )}
      </p>

      <div className="flex flex-col gap-5 md:grid md:grid-cols-[0.72fr_1.28fr] md:[@media(min-height:820px)]:grid-cols-2 snap:min-h-0 snap:flex-1">
        <div className="flex min-h-0 flex-col gap-3">
          {/* On one-screen layouts the building fills the free height; the sides (trees, sky) get cropped, the windows never. */}
          <a
            href="#play"
            dir="ltr"
            className="float-a relative block aspect-[1672/941] w-full overflow-hidden rounded-[20px] border-2 border-line bg-paper shadow-[5px_5px_0_var(--line)] snap:aspect-auto snap:min-h-0 snap:flex-1 snap:[container-type:size]"
          >
            <div className="absolute inset-0 snap:inset-auto snap:top-1/2 snap:left-1/2 snap:aspect-[1672/941] snap:w-[min(max(100cqw,100cqh*1.7768),100cqw/0.62)] snap:-translate-x-1/2 snap:-translate-y-1/2">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src="/assets/office_idle.jpg"
                alt={t.alt}
                className="absolute inset-0 h-full w-full"
              />
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                key={`${name}-${events.length}`}
                src={`/assets/talk_${name}.jpg`}
                alt=""
                className="pop absolute rounded-[3px] outline-[3px] outline-orange"
                style={{
                  left: `${left}%`,
                  top: `${top}%`,
                  width: `${width}%`,
                  height: `${height}%`,
                }}
              />
              <NightSky />
            </div>
            <span className="absolute top-2.5 left-2.5 flex items-center gap-2 rounded-full bg-[#1e1c1a] px-3 py-1 text-[13px] font-semibold text-[#f3ebdd]">
              <span
                aria-hidden="true"
                className="pulse h-2 w-2 rounded-full bg-orange"
              />
              {t.live}
            </span>
            <span
              dir={lang === "fa" ? "rtl" : "ltr"}
              className="absolute inset-x-2.5 bottom-2.5 rounded-xl border-[1.5px] border-line bg-card/95 px-3 py-1.5 text-center text-[14px] text-ink"
            >
              <b>{t.agents[speaker]}</b>
              <span className="text-muted"> · {t.roles[speaker]}</span>
            </span>
          </a>

          <div className="flex flex-col gap-2">
            <p className="m-0 text-[14px] leading-[1.6]">
              <b className="text-[16px]">{t.ch3}:</b> {t.you}
            </p>
            <a
              href="#play"
              className="btn inline-flex min-h-[44px] items-center self-start rounded-full border-[1.5px] border-line bg-orange px-5 text-[15px] font-bold text-[#1e1c1a] no-underline"
            >
              {t.play}
            </a>
          </div>
        </div>

        <div className="float-b flex min-h-[420px] flex-col overflow-hidden rounded-[20px] border-2 border-line bg-card shadow-[5px_5px_0_var(--line)] md:min-h-0">
          <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1 border-b-[1.5px] border-line px-4 py-2">
            <h3 className="m-0 text-[17px] font-bold">
              {today ? t.todayTitle : t.ch2}
              {live ? (
                <span className="text-[14px] font-normal text-accent">
                  {" "}
                  · {t.liveTitle}
                </span>
              ) : (
                s?.last && (
                  <span className="text-[14px] font-normal text-muted">
                    {" "}
                    · {day(s.last.session_date)}
                  </span>
                )
              )}
            </h3>
            {status && <div className="text-[13px] text-muted">{status}</div>}
          </div>
          <div
            ref={dialog}
            aria-live="polite"
            className="flex flex-1 flex-col gap-1.5 overflow-y-auto px-4 py-2"
          >
            {events.map((e, k) => (
              <div key={e.seq} className="pop flex items-start gap-2">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={`/assets/av_${e.agent}.jpg`}
                  alt=""
                  className="h-7 w-7 shrink-0 rounded-full border-[1.5px] border-line"
                />
                <p
                  className={`m-0 rounded-[12px] rounded-ss-[4px] border-[1.5px] px-3 py-1 text-[13.5px] leading-[1.5] ${k === events.length - 1 && !done ? "border-orange" : "border-line"}`}
                >
                  <b>{t.agents[indexOf(e.agent)]}:</b>{" "}
                  {latinDigits(
                    firstSentence((lang === "fa" && e.text_fa) || e.text_en),
                  )}
                </p>
              </div>
            ))}
            {done && s?.last && (
              <div className="pop flex items-center gap-2 self-center rounded-full border-2 border-orange px-4 py-1 text-[15px] font-bold">
                {t.final}:
                <span className="rounded-full bg-inv px-3 py-0.5 text-inv-ink">
                  {t.decisions[s.last.decision]}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
