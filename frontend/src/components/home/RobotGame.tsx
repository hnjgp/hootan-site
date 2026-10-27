"use client";

import { useRef, useState } from "react";
import type { Dictionary } from "@/i18n";

const SIZE = { w: 230, h: 64 };

/** The "I'm not a robot" box slides away whenever the pointer comes close; the taunts grow with each try. */
export function RobotGame({ g }: { g: Dictionary["game"] }) {
  const box = useRef<HTMLDivElement>(null);
  const [pos, setPos] = useState({ x: 200, y: 75 });
  const [n, setN] = useState(0);

  const flee = (e: React.PointerEvent) => {
    const r = box.current!.getBoundingClientRect();
    const p = { x: e.clientX - r.left, y: e.clientY - r.top };
    if (Math.hypot(p.x - pos.x, p.y - pos.y) > 100) return;
    let best = pos;
    let bestD = -1;
    for (let i = 0; i < 24; i++) {
      const x = SIZE.w / 2 + Math.random() * (r.width - SIZE.w);
      const y = SIZE.h / 2 + Math.random() * (r.height - SIZE.h);
      const d = Math.hypot(x - p.x, y - p.y);
      if (d > bestD) [best, bestD] = [{ x, y }, d];
      if (d > 160) break;
    }
    setPos(best);
    setN((v) => v + 1);
  };

  return (
    <div>
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="font-hand text-[24px] leading-none text-accent">{g.title}</div>
          <div aria-live="polite" className="mt-1 text-[14px] text-muted">
            {g.taunts[Math.min(Math.floor(n / 3), g.taunts.length - 1)]}
          </div>
        </div>
        <div className="flex-none rounded-full border-[1.5px] border-line px-3 py-1 font-mono text-[13px]">
          {g.count}: {n}
        </div>
      </div>
      <div ref={box} dir="ltr" className="relative mt-2 h-[150px] w-full touch-none select-none" onPointerMove={flee} onPointerDown={flee}>
        <div
          className="absolute flex -translate-x-1/2 -translate-y-1/2 items-center gap-3 rounded-lg border-2 border-line bg-card px-4 py-3 shadow-[3px_3px_0_var(--line)] transition-[left,top,rotate] duration-200 ease-out"
          style={{ left: pos.x, top: pos.y, rotate: `${(n % 5) - 2}deg` }}
        >
          <span className="h-7 w-7 rounded border-2 border-line bg-input" />
          <span className="text-[16px] font-semibold whitespace-nowrap">{g.label}</span>
          <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
            <path d="M20 12a8 8 0 1 1-3-6.2 M20 4v5h-5" />
          </svg>
        </div>
      </div>
    </div>
  );
}
