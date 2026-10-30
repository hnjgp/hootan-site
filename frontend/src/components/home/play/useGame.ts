"use client";

import { useEffect, useRef, useState } from "react";
import { useAuth, type Me } from "../../auth/AuthProvider";

export type Row = { rank: number; nickname: string; return_pct: number; is_ai: boolean };
export type Live = { price: string; at: number };
export type Trade = { ts: string; side: "long" | "short" | "close"; price: string };
export type Period = "month" | "all";
export type Order = {
  side: "long" | "short";
  margin_usd: string;
  leverage: number;
  tp_price: string | null;
  sl_price: string | null;
};
/** Why an order failed: the server's short code (cash, tp, sl...), an HTTP status, or null. */
export type OrderFailure = string | number | null;

/** The server keeps the live price for 5 seconds; equity and P&L refresh at that pace. */
const LIVE_MS = 5_000;

const json = async <T>(url: string, init?: RequestInit): Promise<[number, T]> => {
  const r = await fetch(url, init);
  return [r.status, await r.json().catch(() => null)];
};

const post = (url: string, body?: object) =>
  json<Me & { detail?: string }>(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body && JSON.stringify(body),
  });

/** Everything the game section shows: the live price (inside the account when logged in),
 * the team's trades, the table, and placing or closing orders. */
export function useGame() {
  const { me, setMe } = useAuth();
  const [live, setLive] = useState<Live | null>(null);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [period, setPeriod] = useState<Period>("month");
  const [rows, setRows] = useState<Row[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState<OrderFailure>(null);
  const loggedIn = !!me;
  /** Count of orders and closes sent; a poll that overlaps one is stale and dropped. */
  const sends = useRef({ started: 0, running: 0 });

  useEffect(() => {
    json<Trade[]>("/api/trading/trades").then(([, body]) => setTrades(body ?? []));
  }, []);

  useEffect(() => {
    const tick = () => {
      const at = sends.current.started;
      const idle = !sends.current.running;
      const fresh = () => idle && !sends.current.running && sends.current.started === at;
      return loggedIn
        ? json<Me>("/api/game/me").then(([status, body]) => {
            if (status === 200 && body && fresh()) {
              setMe(() => body);
              setLive({ price: body.price, at: Date.now() });
            }
          })
        : json<{ price: string }>("/api/game/price").then(([, body]) => body && setLive({ price: body.price, at: Date.now() }));
    };
    tick();
    const id = setInterval(tick, LIVE_MS);
    return () => clearInterval(id);
  }, [loggedIn, setMe]);

  useEffect(() => {
    json<{ rows: Row[] }>(`/api/game/leaderboard?period=${period}`).then(([, body]) => setRows(body?.rows ?? []));
  }, [period, me?.open.length, me?.closed.length]);

  /** Send an order or a close; on success the answer is the whole account. */
  const send = async (url: string, body?: object): Promise<boolean> => {
    setBusy(true);
    setFailure(null);
    sends.current.started++;
    sends.current.running++;
    try {
      const [status, out] = await post(url, body);
      if (status === 200 || status === 201) {
        setMe(() => out);
        setLive({ price: out.price, at: Date.now() });
        return true;
      }
      setFailure(status === 422 && typeof out?.detail === "string" ? out.detail : status);
    } catch {
      setFailure(0);
    } finally {
      sends.current.running--;
      setBusy(false);
    }
    return false;
  };

  return {
    me,
    live,
    price: live?.price ?? null,
    trades,
    period,
    setPeriod,
    rows,
    busy,
    failure,
    open: (order: Order) => send("/api/game/positions", order),
    close: (id: number) => send(`/api/game/positions/${id}/close`),
  };
}
