"use client";

import { useState } from "react";
import type { Dictionary } from "@/i18n";
import { signedUsd } from "@/lib/digits";
import type { Position } from "../../auth/AuthProvider";

/** Open positions with their floating P&L and a close button, and a tab of the latest closed ones. */
export function Positions({
  t,
  loc,
  open,
  closed,
  busy,
  close,
}: {
  t: Dictionary["play"];
  loc: string;
  open: Position[];
  closed: Position[];
  busy: boolean;
  close: (id: number) => void;
}) {
  const [tab, setTab] = useState<"open" | "closed">("open");
  const usd = (v: string | number) => "$" + Number(v).toLocaleString(loc, { maximumFractionDigits: 0 });
  const rows = tab === "open" ? open : closed;

  return (
    <div className="flex min-h-[150px] flex-col rounded-[18px] border-[1.5px] border-line bg-card snap:h-[30%] snap:min-h-[104px] snap:flex-none">
      <div className="flex gap-1 border-b-[1.5px] border-line px-3 py-1.5">
        {(["open", "closed"] as const).map((k) => (
          <button
            key={k}
            type="button"
            aria-pressed={tab === k}
            onClick={() => setTab(k)}
            className="btn chip min-h-8 rounded-full border border-line px-2.5 text-[12px] aria-pressed:bg-inv aria-pressed:text-inv-ink"
          >
            {k === "open" ? `${t.positions} (${open.length})` : t.history}
          </button>
        ))}
      </div>
      <ul aria-label={tab === "open" ? t.positions : t.history} className="m-0 flex min-h-0 flex-1 list-none flex-col gap-1 overflow-y-auto p-2">
        {rows.length === 0 && (
          <li className="py-3 text-center text-[13px] text-muted">{tab === "open" ? t.noPositions : t.noHistory}</li>
        )}
        {rows.map((p) => {
          const pnl = Number(p.pnl_usd);
          return (
            <li key={p.id} className="flex items-center gap-2 rounded-xl bg-soft px-2.5 py-1.5 text-[13px]">
              <span
                className={`flex-none rounded-full px-2 py-0.5 text-[12px] font-bold text-[#1e1c1a] ${p.side === "long" ? "bg-[#6fd3a8]" : "bg-orange"}`}
              >
                {p.side === "long" ? t.long : t.short} <span dir="ltr">{p.leverage}x</span>
              </span>
              <span className="min-w-0 flex-1 truncate text-[12px] text-muted">
                <bdi className="font-mono">{usd(p.margin_usd)}</bdi> · {t.entryAt} <bdi className="font-mono">{usd(p.entry_price)}</bdi>
                {p.closed_at ? (
                  <bdi className="font-mono"> → {usd(p.close_price!)}</bdi>
                ) : (
                  <>
                    {" "}· {t.liq} <bdi className="font-mono">{usd(p.liq_price)}</bdi>
                  </>
                )}
              </span>
              <span dir="ltr" className={`flex-none font-mono font-bold ${pnl < 0 ? "text-accent" : "text-green"}`}>
                {signedUsd(pnl, loc)}
              </span>
              {p.closed_at ? (
                <span className="flex-none text-[12px] text-muted">{t.reasons[p.close_reason!]}</span>
              ) : (
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => close(p.id)}
                  className="btn min-h-8 flex-none rounded-lg border-[1.5px] border-line px-2 text-[12px] font-bold disabled:opacity-50"
                >
                  {t.close}
                </button>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
