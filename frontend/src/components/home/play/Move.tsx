"use client";

import { useState } from "react";
import type { Dictionary } from "@/i18n";
import { AuthForm } from "../../auth/AuthForm";
import type { Failure, Me } from "../../auth/AuthProvider";
import type { Decision } from "../trading/useMeeting";

const BONUS_FOR: Partial<Record<Decision, "up" | "down">> = { BUY: "down", SELL: "up" };
const START_USD = 100_000;

/** The visitor's side of the game: one prediction a day and its result. Logged-out visitors
 * see the same form dimmed; using it asks them to log in (or sign up). */
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
  const [needLogin, setNeedLogin] = useState(false);

  const usd = (v: string | number) => "$" + Number(v).toLocaleString(loc, { maximumFractionDigits: 0 });
  const signed = (v: string) =>
    new Intl.NumberFormat(loc, { style: "currency", currency: "USD", signDisplay: "always", maximumFractionDigits: 0 }).format(Number(v));
  const dirWord = (d: "up" | "down") => (d === "up" ? t.up : t.down);
  const cta = "btn min-h-11 w-full rounded-xl border-[1.5px] border-line bg-orange text-[15px] font-bold text-[#1e1c1a] disabled:opacity-50";

  if (me === undefined) return <div className="flex-1" />;
  if (me === null && needLogin) return <AuthForm t={auth} title={t.needLogin} />;

  /** Logged out, every control just asks to log in. */
  const guard = (act: () => void) => () => (me ? act() : setNeedLogin(true));
  const last = me?.predictions.find((p) => p.result);
  const bonus = teamToday && BONUS_FOR[teamToday];
  const balance = me ? Number(me.balance_usd) : START_USD;

  return (
    <div className="flex min-h-0 flex-col gap-2">
      {me?.today ? (
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
          className={`flex flex-col gap-2 ${me ? "" : "opacity-60"}`}
          onSubmit={(e) => {
            e.preventDefault();
            guard(() => direction && predict(direction, pct))();
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
                onClick={guard(() => setDirection(d))}
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
                {pct}% · {usd((balance * pct) / 100)}
              </span>
            </span>
            <input
              type="range"
              min={10}
              max={100}
              step={10}
              value={pct}
              onChange={(e) => guard(() => setPct(Number(e.target.value)))()}
              className="accent-[#e8692a]"
            />
          </label>
          <button type="submit" disabled={busy || (!!me && !direction)} className={cta}>{t.submit}</button>
          {failure !== null && (
            <p role="alert" className="m-0 text-[13px] text-accent">
              {failure === 503 ? t.errPrice : auth.errOther}
            </p>
          )}
        </form>
      )}

      {me && (last || me.streak > 0) && (
        <div className="flex flex-wrap justify-between gap-x-3 text-[13px] text-muted">
          {last && (
            <span>
              {t.last}: <b className={last.result === "lose" ? "text-accent" : last.result === "win" ? "text-green" : "text-ink"}>{t.results[last.result!]}</b>{" "}
              <span dir="ltr" className="font-mono">{signed(last.pnl_usd!)}</span>
            </span>
          )}
          <span>
            {t.streak} <b className="font-mono text-ink">{me.streak}</b>
          </span>
        </div>
      )}
    </div>
  );
}
