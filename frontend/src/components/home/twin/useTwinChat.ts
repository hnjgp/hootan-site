"use client";

import { useEffect, useRef, useState } from "react";
import type { Dictionary } from "@/i18n";
import { latinDigits } from "@/lib/digits";
import { sseParser } from "@/lib/sse";

export type Phase = "listen" | "search" | "think" | "talk";

export type Msg = {
  role: "user" | "bot";
  text: string;
  /** Streamed answer, revealed letter by letter. */
  typed?: boolean;
  sources?: string[];
  /** The question to send with the email form when the twin hands off. */
  lead?: string;
  /** Not part of the conversation sent back to the API (limits, errors). */
  note?: boolean;
};

const HISTORY = 6;
const REVEAL_STEP = 3;
const REVEAL_MS = 20;

/**
 * Chat state for the twin. Phases follow the API events:
 * searching sources, then thinking, then writing tokens, then back to listening
 * once the stream is done and the last answer is fully revealed.
 */
export function useTwinChat(t: Dictionary["twin"]) {
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [phase, setPhase] = useState<Exclude<Phase, "listen">>("search");
  const [word, setWord] = useState(0);
  const [files, setFiles] = useState<string[]>([]);
  const [streaming, setStreaming] = useState(false);
  const [shown, setShown] = useState(0);
  /** Set once today's questions are used up; the chat then stays closed. */
  const [limit, setLimit] = useState<string | null>(null);
  const phaseRef = useRef(phase);
  const answerOpen = useRef(false);

  const last = msgs.at(-1);
  const revealing = !!last?.typed && shown < last.text.length;
  const busy = streaming || revealing;

  useEffect(() => {
    if (!revealing) return;
    const id = setTimeout(() => setShown((s) => s + REVEAL_STEP), REVEAL_MS);
    return () => clearTimeout(id);
  }, [revealing, shown]);

  function enter(p: Exclude<Phase, "listen">) {
    phaseRef.current = p;
    setPhase(p);
    setWord(Math.floor(Math.random() * 100));
  }

  const add = (m: Msg) => setMsgs((list) => [...list, m]);

  function onEvent(name: string, data: unknown, question: string) {
    const d = data as Record<string, string>;
    if (name === "status" && d.state === "thinking" && d.step?.includes(": ")) {
      setFiles((f) => [...f, d.step.split(": ")[1]]);
    } else if (name === "status" && d.state === "answering") {
      enter("think");
    } else if (name === "token") {
      d.text = latinDigits(d.text);
      const open = answerOpen.current;
      answerOpen.current = true;
      setMsgs((list) =>
        open ? [...list.slice(0, -1), { ...list.at(-1)!, text: list.at(-1)!.text + d.text }] : [...list, { role: "bot", text: d.text, typed: true }],
      );
      if (phaseRef.current !== "talk") enter("talk");
    } else if (name === "sources") {
      const titles = (data as { title: string }[]).map((s) => s.title);
      setMsgs((list) => [...list.slice(0, -1), { ...list.at(-1)!, sources: titles }]);
    } else if (name === "handoff") {
      add({ role: "bot", text: d.message, lead: question });
    } else if (name === "fallback") {
      add({ role: "bot", text: t.off, note: true });
    } else if (name === "done" && (data as { left: number }).left === 0) {
      setLimit(t.limit);
    }
  }

  async function ask(question: string) {
    question = question.trim();
    if (!question || busy || limit) return;
    const history = msgs
      .filter((m) => !m.note)
      .slice(-HISTORY)
      .map((m) => ({ role: m.role === "user" ? "user" : "assistant", content: m.text }));
    add({ role: "user", text: question });
    setFiles([]);
    setShown(0);
    answerOpen.current = false;
    enter("search");
    setStreaming(true);
    try {
      const res = await fetch("/api/twin/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, history }),
      });
      if (!res.ok || !res.body) {
        if (res.status === 429) setLimit(t.limitAgain);
        else add({ role: "bot", text: t.error, note: true });
        return;
      }
      const push = sseParser((name, data) => onEvent(name, data, question));
      const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
      for (;;) {
        const { value, done } = await reader.read();
        if (done) break;
        push(value);
      }
    } catch {
      add({ role: "bot", text: t.error, note: true });
    } finally {
      setStreaming(false);
    }
  }

  return {
    msgs,
    shown,
    files,
    word,
    busy,
    limit,
    phase: (busy ? phase : "listen") as Phase,
    ask,
  };
}
