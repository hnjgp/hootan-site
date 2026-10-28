"use client";

import { useState } from "react";
import type { Dictionary } from "@/i18n";

/** Email form shown when the twin hands a question off to the real Hootan. */
export function LeadForm({ t, question }: { t: Dictionary["twin"]; question: string }) {
  const [state, setState] = useState<"idle" | "sending" | "sent" | "bad" | "error">("idle");

  async function send(form: FormData) {
    setState("sending");
    const res = await fetch("/api/leads", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: form.get("email"), question }),
    }).catch(() => null);
    setState(res?.ok ? "sent" : res?.status === 422 ? "bad" : "error");
  }

  if (state === "sent")
    return <div className="pop rounded-[10px] border-[1.5px] border-green bg-green/15 px-3 py-2 text-[14px] font-semibold text-green">{t.sent}</div>;

  return (
    <form action={send} className="flex flex-wrap items-end gap-2">
      <label className="flex flex-[1_1_200px] flex-col gap-1 text-[13px] text-muted">
        {t.emailLabel}
        <input
          name="email"
          type="email"
          required
          dir="ltr"
          placeholder="name@company.com"
          className="min-h-11 rounded-[10px] border-[1.5px] border-line bg-input px-3 text-[15px] text-ink"
        />
      </label>
      <button
        type="submit"
        disabled={state === "sending"}
        className="btn min-h-11 rounded-[10px] border-[1.5px] border-line bg-[#1f6b4e] px-4 text-[15px] font-bold text-white"
      >
        {t.send}
      </button>
      {(state === "bad" || state === "error") && <div className="w-full text-[13px] text-accent">{state === "bad" ? t.badEmail : t.error}</div>}
    </form>
  );
}
