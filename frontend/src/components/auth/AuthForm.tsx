"use client";

import { useState } from "react";
import type { Dictionary } from "@/i18n";
import { useAuth, type Failure } from "./AuthProvider";

export type Mode = "login" | "signup";
type Step = Mode | "forgot" | "reset";

/** Log-in form with links to sign up and to a forgotten password (a code by email,
 * then the code and a new password); used in the header and the game. */
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
  const { logIn, signUp, forgot, reset } = useAuth();
  const [step, setStep] = useState<Step>(start);
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState<Failure>(null);
  const signup = step === "signup";
  const errors: Record<Step, Record<string, string>> = {
    signup: { 409: t.errTaken, email: t.errEmailTaken, 422: t.errBad, 429: t.errLimit },
    login: { 401: t.errLogin, 422: t.errLogin, 429: t.errLimit },
    forgot: { 422: t.errBad, 429: t.errLimit },
    reset: { 400: t.errCode, 422: t.errCode, 429: t.errLimit },
  };
  const input = "min-h-10 w-full min-w-0 rounded-xl border-[1.5px] border-line bg-input px-3 text-[15px] text-ink placeholder:text-muted";
  // The label sits inside the field as its placeholder, so the form fits in the game box.
  const field = (name: string, text: string, props: React.InputHTMLAttributes<HTMLInputElement>) => (
    <label className="min-w-0">
      <span className="sr-only">{text}</span>
      <input name={name} placeholder={text} className={input} {...props} />
    </label>
  );
  const go = (next: Step) => {
    setStep(next);
    setFailure(null);
  };
  const link = (text: string, next: Step) => (
    <button type="button" onClick={() => go(next)} className="font-bold text-accent underline">
      {text}
    </button>
  );
  const remember = (
    <label className="flex items-center gap-2 text-[13px]">
      <input type="checkbox" name="remember" className="h-4 w-4 accent-[#e8692a]" />
      {t.remember}
    </label>
  );

  const submit = async (form: FormData) => {
    const value = (k: string) => String(form.get(k) ?? "").trim() || null;
    const keep = form.get("remember") === "on";
    setBusy(true);
    let out: Failure;
    if (step === "forgot") {
      const address = value("email")!;
      out = await forgot(address);
      if (out === null) {
        setEmail(address);
        setStep("reset");
      }
    } else if (step === "reset") {
      out = await reset({ email, code: value("code")!, password: String(form.get("password")), remember: keep });
    } else {
      const login = { nickname: value("nickname")!, password: String(form.get("password")), remember: keep };
      out = signup ? await signUp({ ...login, email: value("email")!, phone: value("phone") }) : await logIn(login);
    }
    setBusy(false);
    setFailure(out);
    if (out === null && step !== "forgot") onDone?.();
  };

  const password = (label: string, autoComplete: string) =>
    field("password", label, { type: "password", dir: "auto", required: true, maxLength: 128, autoComplete });
  const button = (text: string) => (
    <button
      type="submit"
      disabled={busy}
      className="btn min-h-11 w-full rounded-xl border-[1.5px] border-line bg-orange text-[15px] font-bold text-[#1e1c1a] disabled:opacity-50"
    >
      {text}
    </button>
  );

  return (
    <form
      key={step}
      className="flex flex-col gap-1.5"
      onSubmit={(e) => {
        e.preventDefault();
        submit(new FormData(e.currentTarget));
      }}
    >
      {step === "forgot" || step === "reset" ? (
        <>
          <b className="text-[16px]">{t.forgotTitle}</b>
          <p className="m-0 text-[13px] text-muted">{step === "forgot" ? t.forgotHint : t.sent}</p>
          {step === "forgot" ? (
            <>
              {field("email", t.email, { type: "email", dir: "ltr", required: true, autoComplete: "email" })}
              {button(t.send)}
            </>
          ) : (
            <>
              {field("code", t.code, {
                dir: "ltr",
                required: true,
                inputMode: "numeric",
                pattern: "[0-9]{6}",
                maxLength: 6,
                autoComplete: "one-time-code",
              })}
              {password(t.newPassword, "new-password")}
              {remember}
              {button(t.reset)}
            </>
          )}
        </>
      ) : (
        <>
          <b className="text-[16px]">{signup ? t.signupTitle : (title ?? t.login)}</b>
          {signup && (
            <div className="grid grid-cols-2 gap-2">
              {field("email", t.email, { type: "email", dir: "auto", required: true, autoComplete: "email" })}
              {field("phone", t.phone, { type: "tel", dir: "auto", autoComplete: "tel" })}
            </div>
          )}
          {field("nickname", t.nickname, { dir: "auto", required: true, maxLength: 20, autoComplete: "username" })}
          {password(t.password, signup ? "new-password" : "current-password")}
          {remember}
          {button(signup ? t.signup : t.login)}
        </>
      )}
      {failure !== null && (
        <p role="alert" className="m-0 text-[13px] text-accent">
          {errors[step][failure] ?? t.errOther}
        </p>
      )}
      <p className="m-0 flex flex-wrap gap-x-3 text-[13px] text-muted">
        {step === "login" && (
          <>
            <span>
              {t.noAccount} {link(t.signup, "signup")}
            </span>
            {link(t.forgot, "forgot")}
          </>
        )}
        {signup && (
          <span>
            {t.haveAccount} {link(t.login, "login")}
          </span>
        )}
        {(step === "forgot" || step === "reset") && link(t.back, "login")}
      </p>
    </form>
  );
}
