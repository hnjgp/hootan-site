"use client";

import { useEffect, useState, type ReactNode } from "react";
import type { Dictionary, Locale } from "@/i18n";

type Count = { today: number; month: number };
type Overview = {
  ai_enabled: boolean;
  caps: { monthly: number; trading_daily: number; public_daily: number };
  costs: { today: Record<string, number>; month: Record<string, number> };
  counts: Record<"chats" | "jobfits" | "positions" | "players" | "leads", Count>;
  meeting: { date: string; status: string; decision: string | null; cost_usd: number; finished_at: string | null } | null;
  last_price_at: string | null;
};
type Row = Record<string, string | number | null>;
type Data = { overview: Overview; players: Row[]; leads: Row[]; jobfits: Row[]; chats: Row[] };

const PATHS = ["overview", "players", "leads", "jobfits", "chats"] as const;

/** Hootan's admin page: AI costs against the caps, activity, the last meeting and the
 * latest players, emails, job-fit checks and twin questions. The API answers 404 to
 * anyone but the admin account. */
export function AdminPanel({ t, lang }: { t: Dictionary["admin"]; lang: Locale }) {
  const [data, setData] = useState<Data | null | undefined>(undefined);
  const loc = lang === "fa" ? "fa-IR-u-nu-latn" : "en-GB";
  const when = (iso: unknown) => (iso ? new Date(String(iso)).toLocaleString(loc, { dateStyle: "short", timeStyle: "short" }) : "-");
  const usd = (n: number) => `$${n.toFixed(4)}`;

  useEffect(() => {
    Promise.all(PATHS.map((p) => fetch(`/api/admin/${p}`).then((r) => (r.ok ? r.json() : Promise.reject(r.status)))))
      .then(([overview, players, leads, jobfits, chats]) => setData({ overview, players, leads, jobfits, chats }))
      .catch(() => setData(null));
  }, []);

  const back = (
    <a href={`/${lang}`} className="text-accent underline">
      {t.back}
    </a>
  );
  if (data === undefined) return <main className="p-6" />;
  if (data === null)
    return (
      <main className="mx-auto flex max-w-[700px] flex-col gap-3 p-6">
        <p className="m-0">{t.denied}</p>
        {back}
      </main>
    );

  const o = data.overview;
  const features = [...new Set([...Object.keys(o.costs.month), ...Object.keys(o.costs.today)])].sort();
  const total = (c: Record<string, number>) => Object.values(c).reduce((a, b) => a + b, 0);

  return (
    <main className="mx-auto flex max-w-[1200px] flex-col gap-5 p-4 sm:p-6">
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <h1 className="m-0 text-[28px] font-bold">{t.title}</h1>
        {back}
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card title={t.costs}>
          <Table
            head={["", t.today, t.month]}
            rows={[...features.map((f) => [f, usd(o.costs.today[f] ?? 0), usd(o.costs.month[f] ?? 0)]), ["=", usd(total(o.costs.today)), usd(total(o.costs.month))]]}
          />
          <p className="m-0 mt-2 text-[14px] text-muted">
            {t.ai}: <b className={o.ai_enabled ? "text-green" : "text-accent"}>{o.ai_enabled ? t.on : t.off}</b>
          </p>
        </Card>
        <Card title={t.caps}>
          <Table
            rows={[
              [t.capMonthly, `$${o.caps.monthly}`],
              [t.capTrading, `$${o.caps.trading_daily}`],
              [t.capPublic, `$${o.caps.public_daily}`],
            ]}
          />
        </Card>
        <Card title={t.activity}>
          <Table head={["", t.today, t.month]} rows={Object.entries(o.counts).map(([k, c]) => [t.counts[k as keyof typeof t.counts], c.today, c.month])} />
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card title={t.meeting}>
          {o.meeting ? (
            <p className="m-0" dir="ltr">
              {o.meeting.date} · {o.meeting.status} · {o.meeting.decision ?? "-"} · {usd(o.meeting.cost_usd)}
            </p>
          ) : (
            <p className="m-0">{t.noMeeting}</p>
          )}
        </Card>
        <Card title={t.lastPrice}>
          <p className="m-0">{when(o.last_price_at)}</p>
        </Card>
      </div>

      <Card title={`${t.players} (${data.players.length})`}>
        <Table
          head={[t.nickname, t.password, t.email, t.phone, t.date]}
          rows={data.players.map((p) => [p.nickname, p.password, p.email, p.phone, when(p.created_at)])}
          empty={t.empty}
        />
      </Card>
      <Card title={`${t.leads} (${data.leads.length})`}>
        <Table head={[t.email, t.context, t.date]} rows={data.leads.map((l) => [l.email, l.context, when(l.created_at)])} empty={t.empty} />
      </Card>
      <Card title={t.jobfits}>
        <div className="flex flex-col gap-2">
          {data.jobfits.length === 0 && <p className="m-0 text-muted">{t.empty}</p>}
          {data.jobfits.map((j, i) => (
            <details key={i} className="rounded-lg border border-line p-2">
              <summary className="cursor-pointer">
                {t.score} {j.score} · {when(j.created_at)}
              </summary>
              <pre dir="auto" className="m-0 mt-2 max-h-64 overflow-auto text-[13px] whitespace-pre-wrap">
                {j.jd_text}
              </pre>
            </details>
          ))}
        </div>
      </Card>
      <Card title={t.chats}>
        <Table head={[t.question, t.answer, t.date]} rows={data.chats.map((c) => [c.question, c.answer, when(c.created_at)])} empty={t.empty} />
      </Card>
    </main>
  );
}

function Card({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-2xl border-2 border-line bg-card p-4 shadow-[5px_5px_0_var(--line)]">
      <h2 className="m-0 mb-3 text-[18px] font-bold">{title}</h2>
      {children}
    </section>
  );
}

function Table({ head, rows, empty }: { head?: string[]; rows: (string | number | null)[][]; empty?: string }) {
  if (rows.length === 0) return <p className="m-0 text-muted">{empty}</p>;
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-[14px]">
        {head && (
          <thead>
            <tr>
              {head.map((h, i) => (
                <th key={i} className="border-b border-line px-2 py-1 text-start font-semibold">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
        )}
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="align-top">
              {r.map((c, j) => (
                <td key={j} dir="auto" className="max-w-[420px] border-b border-soft px-2 py-1 break-words">
                  {c ?? "-"}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
