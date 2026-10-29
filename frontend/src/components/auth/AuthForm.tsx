"use client";

import { useState } from "react";
import type { Dictionary } from "@/i18n";
import { useAuth, type Failure } from "./AuthProvider";

export type Mode = "login" | "signup";

/** Log-in form with a link to the sign-up form below it (and back); used in the header and the game. */
export function AuthForm({
  t,
  title,
  start = "login",
  onDone,
}: {
  t: Dictionary["auth"];
  title?: string;
  start?: Mode;
  onDone?: () => void;
}) {
  const { logIn, signUp } = useAuth();
  const [mode, setMode] = useState<Mode>(start);
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState<Failure>(null);
  const signup = mode === "signup";
  const errors: Record<number, string> = signup
    ? { 409: t.errTaken, 422: t.errBad, 429: t.errLimit }
    : { 401: t.errLogin, 422: t.errLogin, 429: t.errLimit };
  const input = "min-h-10 w-full min-w-0 rounded-xl border-[1.5px] border-line bg-input px-3 text-[15px] text-ink placeholder:text-muted";
  // The label sits inside the field as its placeholder, so the form fits in the game box.
  const field = (name: string, text: string, props: React.InputHTMLAttributes<HTMLInputElement>) => (
    <label className="min-w-0">
      <span className="sr-only">{text}</span>
      <input name={name} placeholder={text} className={input} {...props} />
    </label>
  );

  const submit = async (form: FormData) => {
    const value = (k: string) => String(form.get(k) ?? "").trim() || null;
    setBusy(true);
    const out = signup
      ? await signUp({ nickname: value("nickname")!, password: String(form.get("password")), email: value("email"), phone: value("phone") })
      : await logIn(value("nickname")!, String(form.get("password")));
    setBusy(false);
    setFailure(out);
    if (out === null) onDone?.();
  };

  return (
    <form
      className="flex flex-col gap-1.5"
      onSubmit={(e) => {
        e.preventDefault();
        submit(new FormData(e.currentTarget));
      }}
    >
      <b className="text-[16px]">{signup ? t.signupTitle : (title ?? t.login)}</b>
      {signup && (
        <div className="grid grid-cols-2 gap-2">
          {field("email", t.email, { type: "email", dir: "auto", autoComplete: "email" })}
          {field("phone", t.phone, { type: "tel", dir: "auto", autoComplete: "tel" })}
        </div>
      )}
      {field("nickname", t.nickname, { dir: "auto", required: true, minLength: 3, maxLength: 20, autoComplete: "username" })}
      {field("password", t.password, {
        type: "password",
        dir: "auto",
        required: true,
        maxLength: 128,
        autoComplete: signup ? "new-password" : "current-password",
      })}
      {signup && <span className="text-[12px] text-muted">{t.passwordHint}</span>}
      <button
        type="submit"
        disabled={busy}
        className="btn min-h-11 w-full rounded-xl border-[1.5px] border-line bg-orange text-[15px] font-bold text-[#1e1c1a] disabled:opacity-50"
      >
        {signup ? t.signup : t.login}
      </button>
      {failure !== null && (
        <p role="alert" className="m-0 text-[13px] text-accent">
          {errors[failure] ?? t.errOther}
        </p>
      )}
      <p className="m-0 text-[13px] text-muted">
        {signup ? t.haveAccount : t.noAccount}{" "}
        <button
          type="button"
          onClick={() => {
            setMode(signup ? "login" : "signup");
            setFailure(null);
          }}
          className="font-bold text-accent underline"
        >
          {signup ? t.login : t.signup}
        </button>
      </p>
    </form>
  );
}
