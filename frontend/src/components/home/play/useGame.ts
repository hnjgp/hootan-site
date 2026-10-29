"use client";

import { useEffect, useState } from "react";
import type { Decision, Summary } from "../trading/useMeeting";

export type Result = "win" | "lose" | "draw";
export type Prediction = {
  game_date: string;
  direction: "up" | "down";
  stake_pct: number;
  stake_usd: string;
  ref_price: string;
  result: Result | null;
  pnl_usd: string | null;
};
export type Me = {
  nickname: string;
  balance_usd: string;
  streak: number;
  today: Prediction | null;
  predictions: Prediction[];
  recovery_token?: string;
};
export type Row = { rank: number; nickname: string; return_pct: number; is_ai: boolean };
export type Stats = {
  accuracy_pct: number | null;
  ahead_pct: number | null;
  trades: { ts: string; side: "BUY" | "SELL"; price: string }[];
};
export type Period = "month" | "all";
/** Why a request failed, as the HTTP status (0 when the network failed). */
export type Failure = number | null;

const json = async <T>(url: string, init?: RequestInit): Promise<[number, T]> => {
  const r = await fetch(url, init);
  return [r.status, r.ok ? await r.json() : null];
};
const post = (body: object): RequestInit => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

/** Everything the game section shows: the player, the live price, the team, the table. */
export function useGame() {
  const [me, setMe] = useState<Me | null | undefined>(undefined);
  const [price, setPrice] = useState<string | null>(null);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [period, setPeriod] = useState<Period>("month");
  const [rows, setRows] = useState<Row[] | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState<Failure>(null);

  useEffect(() => {
    json<Me>("/api/game/me").then(([, body]) => setMe(body));
    json<Summary>("/api/trading/summary").then(([, body]) => setSummary(body));
    json<Stats>("/api/game/stats").then(([, body]) => setStats(body));
    json<{ price: string }>("/api/game/price").then(([, body]) => setPrice(body?.price ?? null));
  }, []);

  useEffect(() => {
    json<{ rows: Row[] }>(`/api/game/leaderboard?period=${period}`).then(([, body]) =>
      setRows(body?.rows ?? []),
    );
  }, [period]);

  /** Run one request; keep its failure status for the message under the form. */
  const act = async <T>(url: string, body: object): Promise<T | null> => {
    setBusy(true);
    setFailure(null);
    try {
      const [status, out] = await json<T>(url, post(body));
      if (!out) setFailure(status);
      return out;
    } catch {
      setFailure(0);
      return null;
    } finally {
      setBusy(false);
    }
  };

  const join = async (nickname: string) => {
    const out = await act<Me>("/api/game/players", { nickname });
    if (out) {
      setToken(out.recovery_token ?? null);
      setMe(out);
    }
  };

  const predict = async (direction: "up" | "down", stake_pct: number) => {
    const out = await act<Prediction>("/api/game/predictions", { direction, stake_pct });
    if (out) setMe((m) => m && { ...m, today: out, predictions: [out, ...m.predictions] });
    else json<{ price: string }>("/api/game/price").then(([, body]) => setPrice(body?.price ?? null));
  };

  const teamToday: Decision | null =
    summary?.today_status === "done" ? (summary.last?.decision ?? null) : null;

  return {
    me,
    price,
    summary,
    stats,
    teamToday,
    period,
    setPeriod,
    rows,
    token,
    clearToken: () => setToken(null),
    busy,
    failure,
    join,
    predict,
  };
}
