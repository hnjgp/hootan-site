"use client";

import { useState } from "react";
import type { Dictionary } from "@/i18n";
import { AuthForm } from "../../auth/AuthForm";
import type { Failure, Me } from "../../auth/AuthProvider";
import type { Decision } from "../trading/useMeeting";

const BONUS_FOR: Partial<Record<Decision, "up" | "down">> = { BUY: "down", SELL: "up" };

/** The visitor's side of the game: log in (or sign up), then one prediction a day and its result. */
export function Move({
  t,
  auth,
  loc,
  me,
  price,
  teamToday,
  busy,
  failure,
  predict,
}: {
  t: Dictionary["play"];
  auth: Dictionary["auth"];
  loc: string;
  me: Me | null | undefined;
  price: string | null;
  teamToday: Decision | null;
  busy: boolean;
  failure: Failure;
  predict: (direction: "up" | "down", pct: number) => void;
}) {
  const [direction, setDirection] = useState<"up" | "down" | null>(null);
  const [pct, setPct] = useState(50);

  const usd = (v: string | number) => "$" + Number(v).toLocaleString(loc, { maximumFractionDigits: 0 });
  const signed = (v: string) =>
    new Intl.NumberFormat(loc, { style: "currency", currency: "USD", signDisplay: "always", maximumFractionDigits: 0 }).format(Number(v));
  const dirWord = (d: "up" | "down") => (d === "up" ? t.up : t.down);
  const error = (codes: Record<number, string>) =>
    failure !== null && <p role="alert" className="m-0 text-[13px] text-accent">{codes[failure] ?? auth.errOther}</p>;
  const cta = "btn min-h-11 w-full rounded-xl border-[1.5px] border-line bg-orange text-[15px] font-bold text-[#1e1c1a] disabled:opacity-50";

  if (me === undefined) return <div className="flex-1" />;
  if (me === null) return <AuthForm t={auth} title={auth.loginTitle} />;


  const last = me.predictions.find((p) => p.result);
  const bonus = teamToday && BONUS_FOR[teamToday];

  return (
    <div className="flex min-h-0 flex-col gap-2">
      <div className="flex flex-wrap items-baseline justify-between gap-x-3 rounded-xl bg-soft px-3 py-1.5 text-[12px] text-muted">
        <span>
          {t.wallet} <b dir="ltr" className="inline-block font-mono text-[15px] text-ink">{usd(me.balance_usd)}</b>
        </span>
        <span>
          {t.streak} <b className="font-mono text-[15px] text-ink">{me.streak}</b>
        </span>
      </div>

      {me.today ? (
        <div className="pop flex flex-col gap-1 rounded-xl border-2 border-line p-3 text-[14px]">
          <b>{t.today}</b>
          <span>
            {t.todayLine.split(/(\{\w+\})/).map((part, k) => {
              const vars: Record<string, string> = {
                "{dir}": dirWord(me.today!.direction),
                "{stake}": usd(me.today!.stake_usd),
                "{price}": usd(me.today!.ref_price),
              };
              return part in vars ? (
                <bdi key={k} className={part === "{dir}" ? "font-bold" : "font-mono font-bold"}>
                  {vars[part]}
                </bdi>
              ) : (
                part
              );
            })}
          </span>
          <span className="text-[13px] text-muted">{t.resultAt}</span>
        </div>
      ) : (
        <form
          className="flex flex-col gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            if (direction) predict(direction, pct);
          }}
        >
          <div className="text-[13px] leading-[1.5]">
            <b>{t.teamToday}: </b>
            {teamToday ? (
              <span className="rounded-full bg-inv px-2 py-0.5 text-inv-ink">{t.decisions[teamToday]}</span>
            ) : null}{" "}
            <span className="text-muted">
              {bonus ? t.bonus.replace("{dir}", dirWord(bonus)) : teamToday ? t.teamHold : t.teamNone}
            </span>
          </div>
          <div className="text-[14px] font-bold">
            {t.question}{" "}
            <span dir="ltr" className="font-mono">{price ? usd(price) : "…"}</span>
          </div>
          <div className="grid grid-cols-2 gap-2">
            {(["up", "down"] as const).map((d) => (
              <button
                key={d}
                type="button"
                aria-pressed={direction === d}
                onClick={() => setDirection(d)}
                className={`btn min-h-10 rounded-xl border-[1.5px] border-line text-[15px] font-bold aria-pressed:text-[#1e1c1a] ${d === "up" ? "aria-pressed:bg-[#6fd3a8]" : "aria-pressed:bg-orange"}`}
              >
                {d === "up" ? "▲" : "▼"} {dirWord(d)}
              </button>
            ))}
          </div>
          <label className="flex flex-col text-[13px]">
            <span className="flex justify-between">
              <span className="text-muted">{t.stake}</span>
              <span dir="ltr" className="font-mono font-bold">
                {pct}% · {usd((Number(me.balance_usd) * pct) / 100)}
              </span>
            </span>
            <input
              type="range"
              min={10}
              max={100}
              step={10}
              value={pct}
              onChange={(e) => setPct(Number(e.target.value))}
              className="accent-[#e8692a]"
            />
          </label>
          <button type="submit" disabled={busy || !direction} className={cta}>{t.submit}</button>
          {error({ 503: t.errPrice })}
        </form>
      )}

      {last && (
        <div className="text-[13px] text-muted">
          {t.last}: <b className={last.result === "lose" ? "text-accent" : last.result === "win" ? "text-green" : "text-ink"}>{t.results[last.result!]}</b>{" "}
          <span dir="ltr" className="font-mono">{signed(last.pnl_usd!)}</span>
        </div>
      )}
    </div>
  );
}
