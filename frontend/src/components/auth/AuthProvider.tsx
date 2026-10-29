"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

export type Position = {
  id: number;
  side: "long" | "short";
  entry_price: string;
  margin_usd: string;
  leverage: number;
  qty: string;
  tp_price: string | null;
  sl_price: string | null;
  liq_price: string;
  fee_usd: string;
  opened_at: string;
  closed_at: string | null;
  close_price: string | null;
  close_reason: "manual" | "tp" | "sl" | "liq" | "team" | null;
  /** Floating P&L before fees while open; the net result, fees included, once closed. */
  pnl_usd: string;
};
export type Me = {
  nickname: string;
  avatar: boolean;
  /** The BTC price the numbers below were valued at. */
  price: string;
  cash_usd: string;
  equity_usd: string;
  return_pct: number;
  /** What 10,000 USD in BTC bought at sign-up is worth now; null for old accounts. */
  hold_usd: string | null;
  ai_return_pct: number;
  open: Position[];
  closed: Position[];
};
export type LogIn = { nickname: string; password: string; remember: boolean };
export type SignUp = LogIn & { email: string; phone: string | null };
export type Reset = { email: string; code: string; password: string; remember: boolean };
/** The HTTP status of a failed request (0 when the network failed), "email" for an
 * email that already has an account, or null. */
export type Failure = number | "email" | null;

const PHOTO_PX = 128;

type Auth = {
  /** undefined while loading, null when nobody is logged in. */
  me: Me | null | undefined;
  setMe: (update: (me: Me | null | undefined) => Me | null | undefined) => void;
  /** Bumped after a new photo so the <img> reloads it. */
  photo: number;
  signUp: (body: SignUp) => Promise<Failure>;
  logIn: (body: LogIn) => Promise<Failure>;
  logOut: () => Promise<void>;
  /** Ask for a reset code by email; the answer is the same for unknown emails. */
  forgot: (email: string) => Promise<Failure>;
  reset: (body: Reset) => Promise<Failure>;
  setPhoto: (file: File) => Promise<boolean>;
};

const AuthContext = createContext<Auth | null>(null);

export const useAuth = () => useContext(AuthContext)!;

/** Send JSON; the logged-in player on success, the failure status otherwise. */
async function account(url: string, body: object): Promise<Me | Exclude<Failure, null>> {
  try {
    const r = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (r.ok) return r.json();
    if (r.status === 409 && (await r.json()).detail === "Email taken") return "email";
    return r.status;
  } catch {
    return 0;
  }
}

/** Square-crop and shrink a photo to a small JPEG in the browser, so the server stores a few KB. */
async function shrink(file: File): Promise<Blob> {
  const image = await createImageBitmap(file);
  const side = Math.min(image.width, image.height);
  const canvas = document.createElement("canvas");
  canvas.width = canvas.height = PHOTO_PX;
  canvas
    .getContext("2d")!
    .drawImage(image, (image.width - side) / 2, (image.height - side) / 2, side, side, 0, 0, PHOTO_PX, PHOTO_PX);
  return new Promise((done) => canvas.toBlob((b) => done(b!), "image/jpeg", 0.85));
}

/** Who is logged in, shared by the header and the game section. */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [me, setMe] = useState<Me | null | undefined>(undefined);
  const [photo, setPhotoVersion] = useState(0);

  useEffect(() => {
    fetch("/api/game/me")
      .then((r) => (r.ok ? r.json() : null))
      .then(setMe, () => setMe(null));
  }, []);

  const enter = async (url: string, body: object): Promise<Failure> => {
    const out = await account(url, body);
    if (typeof out !== "object") return out;
    setMe(out);
    return null;
  };

  const value: Auth = {
    me,
    setMe,
    photo,
    signUp: (body) => enter("/api/game/players", body),
    logIn: (body) => enter("/api/game/login", body),
    logOut: async () => {
      await fetch("/api/game/logout", { method: "POST" });
      setMe(null);
    },
    forgot: async (email) => {
      try {
        const r = await fetch("/api/game/password/forgot", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, lang: document.documentElement.lang }),
        });
        return r.ok ? null : r.status;
      } catch {
        return 0;
      }
    },
    reset: (body) => enter("/api/game/password/reset", body),
    setPhoto: async (file) => {
      try {
        const body = await shrink(file);
        const r = await fetch("/api/game/me/avatar", { method: "PUT", headers: { "Content-Type": "image/jpeg" }, body });
        if (!r.ok) return false;
      } catch {
        return false;
      }
      setMe((m) => m && { ...m, avatar: true });
      setPhotoVersion((n) => n + 1);
      return true;
    },
  };

  return <AuthContext value={value}>{children}</AuthContext>;
}
