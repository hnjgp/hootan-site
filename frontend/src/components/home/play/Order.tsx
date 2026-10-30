"use client";

import { useState } from "react";
import type { Dictionary } from "@/i18n";
import { AuthForm } from "../../auth/AuthForm";
import type { Me } from "../../auth/AuthProvider";
import type { Order as OrderBody, OrderFailure } from "./useGame";

const FEE_RATE = 0.0005;

/** The order form: long or short, the amount invested in dollars, leverage,
 * optional take profit and stop loss, and what the order will cost. Logged-out visitors
 * see it dimmed; using it asks them to log in (or sign up). */
export function Order({
  t,
  auth,
  loc,
  me,
  price,
  busy,
  failure,
  open,
}: {
  t: Dictionary["play"];
  auth: Dictionary["auth"];
  loc: string;
  me: Me | null | undefined;
  price: string | null;
  busy: boolean;
  failure: OrderFailure;
  open: (order: OrderBody) => Promise<boolean>;
}) {
  const [side, setSide] = useState<"long" | "short">("long");
  const [amount, setAmount] = useState("1000");
  const [leverage, setLeverage] = useState(5);
  const [tp, setTp] = useState("");
  const [sl, setSl] = useState("");
  const [needLogin, setNeedLogin] = useState(false);

  if (me === undefined) return <div className="flex-1" />;
  if (me === null && needLogin)
    return (
      <div className="flex min-h-0 flex-col gap-2">
        <p role="alert" className="m-0 rounded-[12px] border-2 border-orange bg-orange/15 px-3 py-2 text-[15px] font-bold">
          {t.needLogin}
        </p>
        <AuthForm t={auth} />
      </div>
    );

  /** Logged out, every control just asks to log in. */
  const guard = (act: () => void) => () => (me ? act() : setNeedLogin(true));
  const margin = Number(amount) || 0;
  const now = Number(price) || 0;
  const liq = now && (side === "long" ? now * (1 - 1 / leverage) : now * (1 + 1 / leverage));
  const usd = (v: number) => "$" + v.toLocaleString(loc, { maximumFractionDigits: 2 });
  const sideWord = side === "long" ? t.long : t.short;
  const field = "min-h-9 w-full min-w-0 rounded-xl border-[1.5px] border-line bg-input px-3 font-mono text-[14px] text-ink placeholder:font-sans placeholder:text-muted";

  return (
    <form
      className="flex min-h-0 flex-col gap-1.5"
      onSubmit={(e) => {
        e.preventDefault();
        guard(async () => {
          const ok = await open({
            side,
            margin_usd: margin.toFixed(2),
            leverage,
            tp_price: tp || null,
            sl_price: sl || null,
          });
          if (ok) {
            setTp("");
            setSl("");
          }
        })();
      }}
    >
      <div className="grid grid-cols-2 gap-2">
        {(["long", "short"] as const).map((s) => (
          <button
            key={s}
            type="button"
            aria-pressed={side === s}
            onClick={guard(() => setSide(s))}
            className={`btn flex min-h-10 flex-col items-center justify-center rounded-xl border-[1.5px] border-line leading-tight aria-pressed:text-[#1e1c1a] ${s === "long" ? "aria-pressed:bg-[#6fd3a8]" : "aria-pressed:bg-orange"}`}
          >
            <b className="text-[15px]">
              {s === "long" ? "▲" : "▼"} {s === "long" ? t.long : t.short}
            </b>
            <span className="text-[11px]">{s === "long" ? t.longHint : t.shortHint}</span>
          </button>
        ))}
      </div>

      <label className="flex flex-col gap-1 text-[13px]">
        <span className="text-muted">{t.amount}</span>
        <input
          name="amount"
          type="number"
          inputMode="decimal"
          min="0"
          step="any"
          dir="ltr"
          value={amount}
          onChange={(e) => guard(() => setAmount(e.target.value))()}
          className={field}
        />
      </label>

      <label className="flex flex-col text-[13px]">
        <span className="flex justify-between">
          <span className="text-muted">{t.leverage}</span>
          <span dir="ltr" className="font-mono font-bold">{leverage}x</span>
        </span>
        <input
          type="range"
          min={1}
          max={100}
          value={leverage}
          onChange={(e) => guard(() => setLeverage(Number(e.target.value)))()}
          className="accent-[#e8692a]"
        />
      </label>

      <div className="grid grid-cols-2 gap-2">
        {([
          [t.tp, tp, setTp],
          [t.sl, sl, setSl],
        ] as const).map(([label, v, set]) => (
          <label key={label} className="min-w-0 text-[12px]">
            <span className="mb-0.5 block truncate text-muted">{label}</span>
            <input
              type="number"
              inputMode="decimal"
              min="0"
              step="any"
              dir="ltr"
              placeholder={price ? String(Math.round(now)) : ""}
              value={v}
              onChange={(e) => guard(() => set(e.target.value))()}
              className={field}
            />
          </label>
        ))}
      </div>

      <dl dir="ltr" className="m-0 grid grid-cols-3 gap-1 font-mono text-[12px] rtl:text-right">
        {([
          [t.size, usd(margin * leverage)],
          [t.fee, usd(margin * leverage * FEE_RATE)],
          [t.liq, liq ? usd(liq) : "—"],
        ] as const).map(([k, v]) => (
          <div key={k} className="min-w-0 rounded-lg bg-soft px-2 py-0.5">
            <dt className="truncate font-sans text-muted">{k}</dt>
            <dd className="m-0 truncate font-bold">{v}</dd>
          </div>
        ))}
      </dl>

      <button
        type="submit"
        disabled={busy || (!!me && margin < 1)}
        className="btn min-h-11 w-full rounded-xl border-[1.5px] border-line bg-orange text-[15px] font-bold text-[#1e1c1a] disabled:opacity-50"
      >
        {t.open.replace("{side}", sideWord)}
      </button>
      {failure !== null && (
        <p role="alert" className="m-0 text-[13px] text-accent">
          {failure === 503 ? t.errPrice : ((t.errors as Record<string, string>)[String(failure)] ?? auth.errOther)}
        </p>
      )}
    </form>
  );
}
