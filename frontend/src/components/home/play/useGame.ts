"use client";

import { useEffect, useState } from "react";
import { useAuth, type Failure, type Prediction } from "../../auth/AuthProvider";
import type { Decision, Summary } from "../trading/useMeeting";

export type Row = { rank: number; nickname: string; return_pct: number; is_ai: boolean };
export type Stats = {
  accuracy_pct: number | null;
  ahead_pct: number | null;
  trades: { ts: string; side: "BUY" | "SELL"; price: string }[];
};
export type Period = "month" | "all";

const json = async <T>(url: string, init?: RequestInit): Promise<[number, T]> => {
  const r = await fetch(url, init);
  return [r.status, r.ok ? await r.json() : null];
};

/** Everything the game section shows besides the account: live price, the team, the table. */
export function useGame() {
  const { me, setMe } = useAuth();
  const [price, setPrice] = useState<string | null>(null);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [period, setPeriod] = useState<Period>("month");
  const [rows, setRows] = useState<Row[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState<Failure>(null);

  const loadPrice = () => json<{ price: string }>("/api/game/price").then(([, body]) => setPrice(body?.price ?? null));

  useEffect(() => {
    json<Summary>("/api/trading/summary").then(([, body]) => setSummary(body));
    json<Stats>("/api/game/stats").then(([, body]) => setStats(body));
    json<{ price: string }>("/api/game/price").then(([, body]) => setPrice(body?.price ?? null));
  }, []);

  useEffect(() => {
    json<{ rows: Row[] }>(`/api/game/leaderboard?period=${period}`).then(([, body]) => setRows(body?.rows ?? []));
  }, [period]);

  const predict = async (direction: "up" | "down", stake_pct: number) => {
    setBusy(true);
    setFailure(null);
    try {
      const [status, out] = await json<Prediction>("/api/game/predictions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ direction, stake_pct }),
      });
      if (out) setMe((m) => m && { ...m, today: out, predictions: [out, ...m.predictions] });
      else {
        setFailure(status);
        loadPrice();
      }
    } catch {
      setFailure(0);
    } finally {
      setBusy(false);
    }
  };

  const teamToday: Decision | null = summary?.today_status === "done" ? (summary.last?.decision ?? null) : null;

  return { me, price, summary, stats, teamToday, period, setPeriod, rows, busy, failure, predict };
}
