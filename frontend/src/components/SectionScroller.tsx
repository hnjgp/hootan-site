"use client";

import { useEffect, useRef } from "react";

const DURATION_MS = 1100;
/** A new step starts only after the wheel has been quiet this long, so one flick moves one section. */
const QUIET_MS = 250;
const LARGE = "(min-width: 768px) and (min-height: 640px)";
const NEXT_KEYS = ["ArrowDown", "PageDown", " "];
const PREV_KEYS = ["ArrowUp", "PageUp"];
/** How far a section shrinks and fades when it is one full screen away. */
const DEPTH_SCALE = 0.08;
const DEPTH_FADE = 0.65;

const ease = (k: number) => (k < 0.5 ? 4 * k ** 3 : 1 - (-2 * k + 2) ** 3 / 2);

/** True when an inner box under the pointer (chat, result list, textarea) can still scroll that way. */
function innerCanScroll(el: Element | null, dir: number) {
  for (; el && el !== document.documentElement; el = el.parentElement) {
    const { overflowY } = getComputedStyle(el);
    if (!/(auto|scroll)/.test(overflowY) || el.scrollHeight <= el.clientHeight) continue;
    if (dir > 0 ? el.scrollTop + el.clientHeight < el.scrollHeight - 1 : el.scrollTop > 0) return true;
  }
  return false;
}

/** A curly flight path across the screen, rising when going down the page and falling when going up. */
function flightPath(dir: number) {
  const w = innerWidth;
  const h = innerHeight;
  const y = (f: number) => (dir > 0 ? f : 1 - f) * h;
  return `M -60 ${y(0.8)} C ${0.3 * w} ${y(0.95)}, ${0.55 * w} ${y(0.15)}, ${0.45 * w} ${y(0.4)} S ${0.7 * w} ${y(0.65)}, ${w + 60} ${y(0.2)}`;
}

/**
 * On large screens, each wheel flick or arrow key glides the page one section up or down,
 * as if the section's button was pressed. Sections recede and come forward with the scroll,
 * and a paper plane flies across while the page moves. Small screens keep normal scrolling.
 */
export function SectionScroller() {
  const overlay = useRef<SVGSVGElement>(null);
  const path = useRef<SVGPathElement>(null);
  const trail = useRef<SVGPathElement>(null);
  const plane = useRef<SVGGElement>(null);

  useEffect(() => {
    const large = matchMedia(LARGE);
    const still = matchMedia("(prefers-reduced-motion: reduce)");
    let moving = false;
    let lastWheel = 0;
    const sections = () => [...document.querySelectorAll<HTMLElement>(".page-section")];
    const head = () => parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--head-h"));

    function depth() {
      const on = large.matches && !still.matches;
      for (const s of sections()) {
        const d = Math.min(1, Math.abs(s.offsetTop - head() - scrollY) / s.offsetHeight);
        s.style.transform = on && d > 0.001 ? `scale(${1 - DEPTH_SCALE * d})` : "";
        s.style.opacity = on && d > 0.001 ? String(1 - DEPTH_FADE * d) : "";
      }
    }

    function fly(k: number) {
      const p = path.current!;
      const total = p.getTotalLength();
      const len = total * k;
      const at = p.getPointAtLength(len);
      const before = p.getPointAtLength(Math.max(0, len - 2));
      const angle = (Math.atan2(at.y - before.y, at.x - before.x) * 180) / Math.PI;
      plane.current!.setAttribute("transform", `translate(${at.x} ${at.y}) rotate(${angle})`);
      trail.current!.style.strokeDasharray = `0 ${Math.max(0, len - 120)} ${Math.min(len, 120)} ${total}`;
      overlay.current!.style.opacity = String(k < 0.85 ? 1 : (1 - k) / 0.15);
    }

    function step(dir: number) {
      const list = sections().map((s) => s.offsetTop - head());
      const now = list.reduce((best, top, i) => (Math.abs(top - scrollY) < Math.abs(list[best] - scrollY) ? i : best), 0);
      const target = list[Math.min(list.length - 1, Math.max(0, now + dir))];
      if (target === undefined || Math.abs(target - scrollY) < 2) return;
      const from = scrollY;
      const start = performance.now();
      const duration = still.matches ? 0 : DURATION_MS;
      moving = true;
      path.current!.setAttribute("d", flightPath(dir));
      trail.current!.setAttribute("d", flightPath(dir));
      requestAnimationFrame(function frame(t) {
        const k = duration ? Math.min(1, Math.max(0, (t - start) / duration)) : 1;
        window.scrollTo({ top: from + (target - from) * ease(k), behavior: "instant" });
        if (duration) fly(k);
        if (k < 1) requestAnimationFrame(frame);
        else moving = false;
      });
    }

    function onWheel(e: WheelEvent) {
      if (!large.matches || e.ctrlKey || !e.deltaY) return;
      const dir = Math.sign(e.deltaY);
      if (innerCanScroll(e.target as Element, dir)) return;
      e.preventDefault();
      const now = performance.now();
      const quiet = now - lastWheel > QUIET_MS;
      lastWheel = now;
      if (!moving && quiet) step(dir);
    }

    function onKey(e: KeyboardEvent) {
      const dir = NEXT_KEYS.includes(e.key) ? 1 : PREV_KEYS.includes(e.key) ? -1 : 0;
      const typing = (e.target as Element).closest("input, textarea, button, a, [contenteditable]");
      if (!large.matches || !dir || typing) return;
      e.preventDefault();
      if (!moving) step(dir);
    }

    depth();
    addEventListener("scroll", depth, { passive: true });
    addEventListener("resize", depth);
    addEventListener("wheel", onWheel, { passive: false });
    addEventListener("keydown", onKey);
    return () => {
      removeEventListener("scroll", depth);
      removeEventListener("resize", depth);
      removeEventListener("wheel", onWheel);
      removeEventListener("keydown", onKey);
    };
  }, []);

  return (
    <svg ref={overlay} aria-hidden="true" className="pointer-events-none fixed inset-0 z-30 h-full w-full" style={{ opacity: 0 }}>
      <path ref={path} fill="none" stroke="none" />
      <path ref={trail} fill="none" stroke="var(--orange)" strokeWidth="2.5" strokeLinecap="round" />
      <g ref={plane}>
        <g transform="translate(-22 -12)">
          <path d="M0 0 L44 12 L0 24 L9 12 Z" fill="var(--card)" stroke="var(--line)" strokeWidth="2" strokeLinejoin="round" />
          <path d="M9 12 L44 12 L14 19" fill="none" stroke="var(--orange)" strokeWidth="2" strokeLinejoin="round" />
        </g>
      </g>
    </svg>
  );
}
