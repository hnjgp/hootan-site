"use client";

import { useCallback, useEffect, useRef, useState } from "react";

/** How long each turn stays the newest line in a replay, and the pause on the final decision. */
const TURN_MS = 3200;
const END_MS = 30_000;
const POLL_MS = 2000;

export type Decision = "BUY" | "SELL" | "HOLD";
export type Event = { seq: number; agent: string; text_en: string; text_fa: string | null };
export type Summary = {
  today_status: string | null;
  today_started_at: string | null;
  start_usd: string;
  value_usd: string;
  hold_usd: string;
  last: { session_date: string; decision: Decision; events: Event[] } | null;
};
type Today = { session: { session_date: string; status: string; decision: Decision | null; events: Event[] } | null; trading_day: string };

/** The meeting shown in the dialog: the last one replayed in a loop, or today's one live while it runs. */
export function useMeeting() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [live, setLive] = useState<Event[] | null>(null);
  const [shown, setShown] = useState(0);
  const [failed, setFailed] = useState(false);
  const seq = useRef(0);

  const load = useCallback(async () => {
    const s: Summary = await (await fetch("/api/trading/summary")).json();
    setSummary(s);
    return s;
  }, []);

  const watch = useCallback(() => {
    setLive([]);
    seq.current = 0;
    const id = setInterval(async () => {
      const body: Today = await (await fetch(`/api/trading/sessions/today?after=${seq.current}`)).json();
      const row = body.session;
      if (!row || row.session_date !== body.trading_day) return;
      if (row.events.length) {
        seq.current = row.events.at(-1)!.seq;
        setLive((old) => [...(old ?? []), ...row.events]);
      }
      if (["done", "failed", "skipped"].includes(row.status)) {
        clearInterval(id);
        const s = await load();
        setLive(null);
        setShown(s.last?.events.length ?? 0);
      }
    }, POLL_MS);
  }, [load]);

  useEffect(() => {
    fetch("/api/trading/summary")
      .then((r) => r.json())
      .then((s: Summary) => {
        setSummary(s);
        if (s.today_status === "scheduled" || s.today_status === "running") watch();
      });
  }, [watch]);

  const events = live ?? summary?.last?.events ?? [];
  const done = !live && events.length > 0 && shown >= events.length;

  useEffect(() => {
    if (live) return;
    const id = setTimeout(() => setShown((n) => (done ? 1 : n + 1)), done ? END_MS : TURN_MS);
    return () => clearTimeout(id);
  }, [shown, done, live]);

  const start = async () => {
    setFailed(false);
    const r = await fetch("/api/trading/sessions/today/start", { method: "POST" });
    if (r.ok) watch();
    else setFailed(true);
  };

  return { summary, events: live ? events : events.slice(0, shown), live: !!live, done, failed, start };
}
