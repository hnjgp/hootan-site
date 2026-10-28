"use client";

import { useEffect, useRef, useState } from "react";
import type { Dictionary } from "@/i18n";
import { LeadForm } from "./LeadForm";
import { Portrait } from "./Portrait";
import { useTwinChat } from "./useTwinChat";

/** The twin section: Hootan's portrait on one side, a live chat with his digital twin on the other. */
export function Twin({ t }: { t: Dictionary["twin"] }) {
  const { msgs, shown, files, word, busy, limit, phase, ask } = useTwinChat(t);
  const closed = busy || !!limit;
  const [input, setInput] = useState("");
  const list = useRef<HTMLDivElement>(null);

  useEffect(() => {
    list.current?.scrollTo({ top: list.current.scrollHeight });
  }, [msgs, shown, limit]);

  const bubble = "rounded-[14px] px-3.5 py-2.5 text-[15px] leading-[1.6] whitespace-pre-line";

  return (
    <div className="float-big grid overflow-hidden rounded-[22px] snap:h-full snap:max-h-[680px] border-2 border-line bg-card shadow-[6px_6px_0_var(--line)] md:grid-cols-2">
      <div className="border-b-[1.5px] border-line md:border-e-[1.5px] md:border-b-0">
        <Portrait t={t} phase={phase} word={word} file={files.at(-1)} />
      </div>

      <div className="relative flex min-h-[520px] flex-col md:min-h-0">
        <div className="flex flex-col md:absolute md:inset-0">
          <div className="border-b-[1.5px] border-line px-5 py-4">
            <h2 className="m-0 text-[24px] font-bold">{t.h2}</h2>
            <p className="m-0 mt-1 text-[14px] text-muted">{t.sub}</p>
          </div>

          <div ref={list} aria-live="polite" className="flex h-[340px] flex-col gap-3.5 overflow-y-auto px-5 py-4 md:h-auto md:flex-1">
            <div className={`pop max-w-[92%] self-start rounded-es-[4px] border-[1.5px] border-line bg-bg ${bubble}`}>{t.greet}</div>
            {msgs.map((m, i) =>
              m.role === "user" ? (
                <div key={i} className={`pop max-w-[80%] self-end rounded-ee-[4px] bg-inv text-inv-ink ${bubble}`}>
                  {m.text}
                </div>
              ) : (
                <div key={i} className="pop flex max-w-[92%] flex-col gap-1.5 self-start">
                  <div className={`rounded-es-[4px] border-[1.5px] border-line bg-bg ${bubble}`}>
                    {m.typed && i === msgs.length - 1 ? m.text.slice(0, shown) : m.text}
                  </div>
                  {m.sources && !(i === msgs.length - 1 && busy) && (
                    <div className="font-mono text-[12px] text-muted">
                      {t.sources} {m.sources.join(" · ")}
                    </div>
                  )}
                  {m.lead && <LeadForm t={t} question={m.lead} />}
                </div>
              ),
            )}
            {limit && !busy && (
              <div className="pop self-stretch rounded-[14px] border-2 border-orange bg-orange/15 px-4 py-3 text-[17px] font-bold">{limit}</div>
            )}
            {(phase === "search" || phase === "think") && (
              <div className="pop dots self-start rounded-[14px] rounded-es-[4px] border-[1.5px] border-line bg-bg px-4 py-3" aria-hidden="true">
                <span />
                <span />
                <span />
              </div>
            )}
          </div>

          <div className="flex flex-wrap gap-1.5 px-5 pb-3">
            {t.chips.map((c) => (
              <button
                key={c}
                type="button"
                disabled={closed}
                onClick={() => ask(c)}
                className="btn chip min-h-10 rounded-full border border-line bg-card px-3.5 text-[14px] text-ink disabled:opacity-50"
              >
                {c}
              </button>
            ))}
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (closed) return;
              ask(input);
              setInput("");
            }}
            className="flex gap-2 border-t-[1.5px] border-line px-5 py-3.5"
          >
            <input
              aria-label={t.askLabel}
              value={input}
              maxLength={500}
              disabled={!!limit}
              onChange={(e) => setInput(e.target.value)}
              placeholder={t.placeholder}
              className="min-h-12 min-w-0 flex-1 rounded-xl border-[1.5px] border-line bg-input px-3.5 text-[15px] text-ink"
            />
            <button
              type="submit"
              disabled={closed}
              className="btn min-h-12 rounded-xl border-[1.5px] border-line bg-orange px-5 text-[15px] font-bold text-[#1e1c1a] disabled:opacity-50"
            >
              {t.ask}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
