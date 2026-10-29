"use client";

import { useEffect, useState } from "react";
import type { Dictionary } from "@/i18n";
import type { Live, Trade } from "./useGame";

type Range = "24h" | "7d" | "season";
type Point = { ts: string; price: number };
const RANGES: Range[] = ["24h", "7d", "season"];
/** New 5-minute samples arrive this often; the live price moves the line's end in between. */
const SERIES_MS = 5 * 60_000;

/** Hand-drawn BTC line for one range ending at the live price, with the AI team's buys and sells on it.
 * The line is a stretched SVG; the markers are positioned in percent so they stay round. */
export function PriceChart({
  t,
  trades,
  live,
  loc,
}: {
  t: Dictionary["play"];
  trades: Trade[];
  live: Live | null;
  loc: string;
}) {
  const [range, setRange] = useState<Range>("24h");
  const [points, setPoints] = useState<Point[] | null>(null);

  useEffect(() => {
    const load = () =>
      fetch(`/api/market/btc?range=${range}`)
        .then((r) => r.json())
        .then((body: { points: Point[] }) => setPoints(body.points));
    load();
    const id = setInterval(load, SERIES_MS);
    return () => clearInterval(id);
  }, [range]);

  const series = points && live ? [...points, { ts: new Date(live.at).toISOString(), price: Number(live.price) }] : points;
  const times = series?.map((p) => Date.parse(p.ts)) ?? [];
  const [t0, t1] = [times[0], times.at(-1)! + 1];
  const marks = trades
    .map((tr) => ({ ...tr, x: Date.parse(tr.ts), y: Number(tr.price) }))
    .filter((m) => m.x >= t0 && m.x <= t1 + 3_600_000);
  const ys = [...(series ?? []).map((p) => p.price), ...marks.map((m) => m.y)];
  const [lo, hi] = [Math.min(...ys), Math.max(...ys)];
  const pad = (hi - lo) * 0.12 || 1;
  const sx = (x: number) => ((x - t0) / Math.max(t1 - t0, 1)) * 100;
  const sy = (y: number) => 100 - ((y - lo + pad) / (hi - lo + 2 * pad)) * 100;
  const line = (series ?? [])
    .map((p, k) => `${k ? "L" : "M"}${sx(times[k]).toFixed(2)},${sy(p.price).toFixed(2)}`)
    .join(" ");
  const usd = (v: number) => "$" + Math.round(v).toLocaleString(loc);

  return (
    <div className="flex min-h-[200px] flex-1 flex-col rounded-[18px] border-[1.5px] border-line bg-card p-3 snap:min-h-0">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <h3 className="m-0 text-[15px] font-bold">
          {t.chartTitle}
          {series?.length ? (
            <span dir="ltr" className="mx-2 inline-flex items-center gap-1.5 font-mono text-[13px] font-normal text-muted">
              {live && <span aria-hidden="true" className="pulse h-2 w-2 rounded-full bg-orange" />}
              {usd(series.at(-1)!.price)}
            </span>
          ) : null}
        </h3>
        <div className="flex gap-1">
          {RANGES.map((r) => (
            <button
              key={r}
              type="button"
              aria-pressed={range === r}
              onClick={() => setRange(r)}
              className="btn chip min-h-8 rounded-full border border-line px-2.5 text-[12px] aria-pressed:bg-inv aria-pressed:text-inv-ink"
            >
              {t.ranges[r]}
            </button>
          ))}
        </div>
      </div>

      <div dir="ltr" className="relative min-h-[110px] flex-1">
        {series && series.length > 1 ? (
          <>
            <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="absolute inset-0 h-full w-full overflow-visible" aria-hidden="true">
              {[25, 50, 75].map((y) => (
                <line key={y} x1="0" x2="100" y1={y} y2={y} className="stroke-soft" strokeWidth="1" vectorEffect="non-scaling-stroke" />
              ))}
              <path d={line} fill="none" className="stroke-blue" strokeWidth="2" strokeLinejoin="round" vectorEffect="non-scaling-stroke" />
            </svg>
            <span className="absolute top-0 left-0 font-mono text-[11px] text-muted">{usd(hi)}</span>
            <span className="absolute bottom-0 left-0 font-mono text-[11px] text-muted">{usd(lo)}</span>
            {marks.map((m) => (
              <span
                key={m.ts}
                title={`${m.side === "BUY" ? t.buy : t.sell} · ${usd(m.y)}`}
                className={`absolute h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-line ${m.side === "BUY" ? "bg-green" : "bg-orange"}`}
                style={{ left: `${Math.min(sx(m.x), 100)}%`, top: `${sy(m.y)}%` }}
              />
            ))}
          </>
        ) : (
          <div className="flex h-full items-center justify-center text-[13px] text-muted">
            {points ? t.noData : ""}
          </div>
        )}
      </div>

      <div className="mt-2 flex gap-4 text-[12px] text-muted">
        <span className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full border-[1.5px] border-line bg-green" />
          {t.buy}
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full border-[1.5px] border-line bg-orange" />
          {t.sell}
        </span>
      </div>
    </div>
  );
}
