"use client";

import { useEffect, useState } from "react";
import { useAuth, type Failure, type Prediction } from "../../auth/AuthProvider";
import type { Decision, Summary } from "../trading/useMeeting";

export type Row = { rank: number; nickname: string; return_pct: number; is_ai: boolean };
export type Live = { price: string; at: number };
export type Trade = { ts: string; side: "BUY" | "SELL"; price: string };
export type Period = "month" | "all";

/** The server keeps the live price for 10 seconds; asking more often gains nothing. */
const PRICE_MS = 10_000;

const json = async <T>(url: string, init?: RequestInit): Promise<[number, T]> => {
  const r = await fetch(url, init);
  return [r.status, r.ok ? await r.json() : null];
};

const livePrice = () =>
  json<{ price: string }>("/api/game/price").then(([, body]) => (body ? { price: body.price, at: Date.now() } : null));

/** Everything the game section shows besides the account: live price, the team, its trades, the table. */
export function useGame() {
  const { me, setMe } = useAuth();
  const [live, setLive] = useState<Live | null>(null);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [period, setPeriod] = useState<Period>("month");
  const [rows, setRows] = useState<Row[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState<Failure>(null);


  useEffect(() => {
    json<Summary>("/api/trading/summary").then(([, body]) => setSummary(body));
    json<Trade[]>("/api/trading/trades").then(([, body]) => setTrades(body ?? []));
    livePrice().then(setLive);
    const id = setInterval(() => livePrice().then(setLive), PRICE_MS);
    return () => clearInterval(id);
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
        livePrice().then(setLive);
      }
    } catch {
      setFailure(0);
    } finally {
      setBusy(false);
    }
  };

  const teamToday: Decision | null = summary?.today_status === "done" ? (summary.last?.decision ?? null) : null;

  return { me, live, price: live?.price ?? null, summary, trades, teamToday, period, setPeriod, rows, busy, failure, predict };
}
