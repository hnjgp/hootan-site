"use client";

import { useEffect, useState } from "react";
import type { Locale } from "@/i18n";

const R = 50;
const LENGTH = 2 * Math.PI * R;
const COUNT_MS = 1200;

/** Score ring that counts up from 0 to the score; shows a dash when there is no score yet. */
export function ScoreRing({ score, of, lang }: { score: number | null; of: string; lang: Locale }) {
  const [shown, setShown] = useState(0);

  useEffect(() => {
    if (score === null) return;
    const start = performance.now();
    let frame = requestAnimationFrame(function step(now) {
      const k = Math.min(1, (now - start) / COUNT_MS);
      setShown(Math.round(score * (1 - (1 - k) ** 3)));
      if (k < 1) frame = requestAnimationFrame(step);
    });
    return () => cancelAnimationFrame(frame);
  }, [score]);

  const value = score === null ? 0 : shown;

  return (
    <div className="relative h-[120px] w-[120px] shrink-0">
      <svg viewBox="0 0 120 120" width="120" height="120" aria-hidden="true" className="-rotate-90">
        <circle cx="60" cy="60" r={R} fill="none" stroke="var(--soft)" strokeWidth="12" />
        <circle
          cx="60"
          cy="60"
          r={R}
          fill="none"
          stroke="var(--orange)"
          strokeWidth="12"
          strokeLinecap="round"
          strokeDasharray={LENGTH}
          strokeDashoffset={LENGTH * (1 - value / 100)}
          opacity={value ? 1 : 0}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <div className="text-[36px] leading-none font-bold">{score === null ? "—" : value.toLocaleString(lang === "fa" ? "fa-IR" : "en-US")}</div>
        <div className="mt-1 text-[12px] text-muted">{of}</div>
      </div>
    </div>
  );
}
