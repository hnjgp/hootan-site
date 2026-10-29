"use client";

import type { Dictionary, Locale } from "@/i18n";
import { Leaderboard } from "./Leaderboard";
import { Move } from "./Move";
import { PriceChart } from "./PriceChart";
import { useGame } from "./useGame";

/**
 * The prediction game against the AI trading team on one screen: the rules in one card,
 * the visitor's move, the team's numbers with the price chart, and the leaderboard.
 */
export function Play({ t, lang }: { t: Dictionary["play"]; lang: Locale }) {
  const game = useGame();
  const { summary: s, stats } = game;
  const loc = lang === "fa" ? "fa-IR-u-nu-latn" : "en-US";
  const pct = (n: number) =>
    new Intl.NumberFormat(loc, { signDisplay: "always", maximumFractionDigits: 2 }).format(n) + "%";
  const ret = (v: string) => (s ? (Number(v) / Number(s.start_usd) - 1) * 100 : 0);
  const tiles: [string, string | null, string?][] = [
    [t.stats.team, s && pct(ret(s.value_usd)), s ? (ret(s.value_usd) < 0 ? "text-accent" : "text-green") : ""],
    [t.stats.hold, s && pct(ret(s.hold_usd)), s ? (ret(s.hold_usd) < 0 ? "text-accent" : "text-green") : ""],
    [t.stats.accuracy, stats && (stats.accuracy_pct === null ? t.stats.none : `${stats.accuracy_pct}%`)],
    [t.stats.ahead, stats && (stats.ahead_pct === null ? t.stats.none : `${stats.ahead_pct}%`)],
  ];

  return (
    <div className="flex min-h-0 flex-col snap:h-full">
      <div className="mb-3">
        <div className="font-hand text-[24px] leading-none text-accent">{t.tag}</div>
        <h2 className="mt-1 mb-1 text-[30px] leading-[1.15] font-bold sm:text-[34px]">{t.h2}</h2>
        <p className="m-0 max-w-[860px] text-[15px] leading-[1.6] text-muted">{t.sub}</p>
      </div>

      <section aria-label={t.rulesTitle} className="mb-4 rounded-[18px] border-[1.5px] border-line bg-card px-4 py-2.5">
        <ol className="m-0 grid list-none gap-x-5 gap-y-1.5 p-0 sm:grid-cols-2 lg:grid-cols-4">
          {t.rules.map((rule, k) => (
            <li key={rule} className="flex items-start gap-2 text-[13px] leading-[1.55]">
              <span className="flex h-6 w-6 flex-none items-center justify-center rounded-full border-[1.5px] border-line bg-orange font-mono text-[12px] font-bold text-[#1e1c1a]">
                {k + 1}
              </span>
              {rule}
            </li>
          ))}
        </ol>
      </section>

      <div className="flex flex-col gap-5 md:grid md:grid-cols-[1fr_1.2fr_0.9fr] snap:min-h-0 snap:flex-1">
        <div className="flex min-h-0 flex-col gap-2.5 overflow-y-auto rounded-[20px] border-2 border-line bg-card p-4 shadow-[5px_5px_0_var(--line)]">
          <h3 className="m-0 text-[17px] font-bold">
            {t.yourMove}
            {game.me && (
              <span dir="auto" className="ms-2 rounded-full bg-soft px-2.5 py-0.5 text-[13px] font-semibold">{game.me.nickname}</span>
            )}
          </h3>
          <Move t={t} lang={lang} loc={loc} {...game} />
        </div>

        <div className="flex min-h-0 flex-col gap-3">
          <div className="grid grid-cols-2 gap-2">
            {tiles.map(([label, value, tone]) => (
              <div key={label} className="rounded-[14px] border-[1.5px] border-line bg-card px-3 py-1.5">
                <div className="truncate text-[12px] text-muted">{label}</div>
                <div dir="ltr" className={`text-[17px] font-bold rtl:text-right ${value === t.stats.none ? "text-muted" : "font-mono"} ${tone ?? ""}`}>
                  {value ?? "…"}
                </div>
              </div>
            ))}
          </div>
          <PriceChart t={t} trades={stats?.trades ?? []} loc={loc} />
        </div>

        <Leaderboard
          t={t}
          rows={game.rows}
          period={game.period}
          setPeriod={game.setPeriod}
          nickname={game.me?.nickname ?? null}
          loc={loc}
        />
      </div>

      <p className="mt-3 mb-0 text-[13px] text-muted">{t.virtual}</p>
    </div>
  );
}
