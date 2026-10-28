"use client";

import { useEffect, useState } from "react";
import type { Dictionary, Locale } from "@/i18n";

export type FitResult = {
  strengths: { point: string; evidence: string }[];
  gaps: string[];
  summary: string;
  questions: string[];
  score: number;
};

const WORD_MS = 1800;

/** Sends the ad to the API; while waiting, an old word rotates; errors become friendly notes. */
export function useJobFit(t: Dictionary["jobfit"], lang: Locale) {
  const [busy, setBusy] = useState(false);
  const [word, setWord] = useState(0);
  const [result, setResult] = useState<FitResult | null>(null);
  const [note, setNote] = useState<string | null>(null);

  useEffect(() => {
    if (!busy) return;
    const id = setInterval(() => setWord((w) => w + 1), WORD_MS);
    return () => clearInterval(id);
  }, [busy]);

  async function check(ad: string) {
    if (busy) return;
    setBusy(true);
    setNote(null);
    setWord(Math.floor(Math.random() * t.words.length));
    try {
      const res = await fetch("/api/jobfit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_ad: ad, lang }),
      });
      if (res.ok) setResult(await res.json());
      else setNote(res.status === 429 ? t.limit : res.status === 503 ? t.off : t.error);
    } catch {
      setNote(t.error);
    } finally {
      setBusy(false);
    }
  }

  return { busy, word: t.words[word % t.words.length], result, note, check };
}
