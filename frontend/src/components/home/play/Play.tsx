"use client";

import type { Dictionary, Locale } from "@/i18n";
import { signedUsd } from "@/lib/digits";
import { Leaderboard } from "./Leaderboard";
import { Order } from "./Order";
import { Positions } from "./Positions";
import { PriceChart } from "./PriceChart";
import { useGame } from "./useGame";

/**
 * The demo exchange against the AI trading team on one screen: the rules in one card, the
 * order form, the visitor's equity strip with the live chart and their positions, and the
 * leaderboard. Numbers refresh every 5 seconds.
 */
export function Play({ t, auth, lang }: { t: Dictionary["play"]; auth: Dictionary["auth"]; lang: Locale }) {
  const game = useGame();
  const me = game.me;
  const loc = lang === "fa" ? "fa-IR-u-nu-latn" : "en-US";
  const usd = (v: string) => "$" + Number(v).toLocaleString(loc, { maximumFractionDigits: 0 });
  const pnl = me ? Number(me.equity_usd) - 10_000 : 0;
  // The visitor's own numbers; a dash until they log in.
  const strip: [string, string | null, string][] = [
    [t.equity, me ? usd(me.equity_usd) : null, ""],
    [t.pnl, me ? signedUsd(pnl, loc, 0) : null, pnl < 0 ? "text-accent" : "text-green"],
    [t.cash, me ? usd(me.cash_usd) : null, ""],
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
          <Order t={t} auth={auth} loc={loc} me={me} price={game.price} busy={game.busy} failure={game.failure} open={game.open} />
        </div>

        <div className="flex min-h-0 flex-col gap-2.5">
          <div className="grid grid-cols-3 gap-2">
            {strip.map(([label, value, color]) => (
              <div key={label} className="min-w-0 rounded-[14px] border-[1.5px] border-line bg-card px-3 py-1">
                <div className="text-[12px] leading-tight text-muted">{label}</div>
                <div dir="ltr" className={`truncate font-mono text-[16px] font-bold rtl:text-right ${value ? color : "text-muted"}`}>
                  {value ?? "—"}
                </div>
              </div>
            ))}
          </div>
          <PriceChart t={t} trades={game.trades} live={game.live} loc={loc} />
          {me && <Positions t={t} loc={loc} open={me.open} closed={me.closed} busy={game.busy} close={game.close} />}
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

    </div>
  );
}
