import type { Dictionary } from "@/i18n";
import type { Period, Row } from "./useGame";

/** The table by percent return, the AI team's row and the visitor's own row marked. */
export function Leaderboard({
  t,
  rows,
  period,
  setPeriod,
  nickname,
  loc,
}: {
  t: Dictionary["play"];
  rows: Row[] | null;
  period: Period;
  setPeriod: (p: Period) => void;
  nickname: string | null;
  loc: string;
}) {
  const pct = (n: number) =>
    new Intl.NumberFormat(loc, { signDisplay: "always", maximumFractionDigits: 2 }).format(n) + "%";

  return (
    <div className="flex min-h-[260px] flex-col overflow-hidden rounded-[20px] border-2 border-line bg-card shadow-[5px_5px_0_var(--line)] snap:min-h-0">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b-[1.5px] border-line px-4 py-2">
        <h3 className="m-0 text-[17px] font-bold">{t.boardTitle}</h3>
        <div className="flex gap-1">
          {(["month", "all"] as const).map((p) => (
            <button
              key={p}
              type="button"
              aria-pressed={period === p}
              onClick={() => setPeriod(p)}
              className="btn chip min-h-8 rounded-full border border-line px-2.5 text-[12px] aria-pressed:bg-inv aria-pressed:text-inv-ink"
            >
              {t[p]}
            </button>
          ))}
        </div>
      </div>
      <ol className="m-0 flex flex-1 list-none flex-col gap-1 overflow-y-auto p-2">
        {rows?.map((r) => {
          const own = r.nickname === nickname;
          return (
            <li
              key={r.nickname}
              className={`flex items-center gap-2.5 rounded-xl px-2.5 py-1.5 text-[14px] ${r.is_ai ? "border-[1.5px] border-orange bg-orange/15" : own ? "bg-soft" : ""}`}
            >
              <span className="w-6 font-mono text-[13px] text-muted">{r.rank}</span>
              {r.is_ai && (
                // eslint-disable-next-line @next/next/no-img-element
                <img src="/assets/av_pm.jpg" alt="" className="h-6 w-6 rounded-full border-[1.5px] border-line" />
              )}
              <span dir="auto" className="min-w-0 flex-1 truncate font-semibold">
                {r.is_ai ? t.ai : r.nickname}
                {own && <span className="font-normal text-muted"> ({t.you})</span>}
              </span>
              <span dir="ltr" className={`font-mono text-[13px] font-bold ${r.return_pct < 0 ? "text-accent" : "text-green"}`}>
                {pct(r.return_pct)}
              </span>
            </li>
          );
        })}
      </ol>
      <p className="m-0 border-t-[1.5px] border-line px-4 py-2 text-[12px] text-muted">{t.entry}</p>
    </div>
  );
}
