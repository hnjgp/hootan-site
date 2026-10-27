"use client";

import { useEffect, useRef, useState } from "react";
import type { Locale } from "@/i18n";

const HEADLINE_FONT = { family: "'Vazirmatn Variable'", weight: 500 };

const IDS = ["twin", "job-fit", "trading", "projects", "how"] as const;

const L = {
  fa: {
    name: "هوتن سیفی",
    open: "آماده‌ی همکاری · حضوری، دورکاری، ترکیبی یا پروژه‌ای",
    contact: "تماس با من",
    resume: "دانلود رزومه",
    tag: "بفرمایید، بنشینید",
    h1: "سلام، من هوتنم. با هوش مصنوعی چیزهایی می‌سازم که واقعاً کار کنند.",
    buttons: ["مصاحبه با دوقلوی دیجیتال من", "میزان تناسب من با آگهی شغلی شما", "ایجنت‌های هوش مصنوعی تریدر", "پروژه‌ها", "این سایت را چطور ساختم"],
    hints: [
      "هر سؤال کاری دارید از دوقلوی من بپرسید.",
      "آگهی‌تان را بگذارید؛ یک نمره‌ی صادقانه با نقاط قوت و کمبودها.",
      "هفت ایجنت هر روز جلسه می‌گذارند؛ ببینید می‌توانید از آن‌ها جلو بزنید.",
      "کارهایی که ساخته‌ام، از ایده تا اجرا.",
      "معماری، تصمیم‌ها و هزینه‌ی ماهانه‌ی همین سایت.",
    ],
    soon: "این بخش بعد از انتخاب تو ساخته می‌شود.",
    steps: ["سؤال", "تفحّص", "تأمّل", "کتابت"],
    stepMeaning: ["رسیدن سؤال", "جست‌وجوی دقیق", "درنگ و فکر", "نوشتن جواب"],
    states: ["گوش می‌دهم…", "تأمّل (درنگ و فکر)…", "کتابت (نوشتن)…"],
    chat: [
      ["با LangGraph چه ساخته‌ای؟", "Astra: یک ایجنت با جست‌وجوی هوشمند روی pgvector و سرور MCP."],
      ["چطور می‌توانیم همکاری کنیم؟", "حضوری، دورکاری، ترکیبی یا پروژه‌ای؛ هر کدام برای شما بهتر است."],
    ],
    agents: ["تحلیلگر داده", "تحلیلگر خبر", "گاو", "خرس", "مدیر ریسک", "تریدر", "مدیر پرتفوی"],
    phone: "تلفن",
    email: "ایمیل",
  },
  en: {
    name: "Hootan Seifi",
    open: "Open to work · On-site, remote, hybrid or project-based",
    contact: "Contact me",
    resume: "Download résumé",
    tag: "come in, take a seat",
    h1: "Hi, I'm Hootan. I build things with AI that actually work.",
    buttons: ["Interview my digital twin", "How well I fit your job ad", "My AI trading agents", "Projects", "How I built this site"],
    hints: [
      "Ask my twin anything about my work.",
      "Paste your job ad; get an honest score with strengths and gaps.",
      "Seven agents meet every day. See if you can beat them.",
      "Things I've built, from idea to production.",
      "Architecture, decisions and the monthly bill of this very site.",
    ],
    soon: "This section is built after you choose.",
    steps: ["Ask", "Gleaning", "Pondering", "Scribing"],
    stepMeaning: ["question arrives", "gathering bit by bit", "thinking it over", "writing by hand"],
    states: ["Listening…", "Pondering (thinking it over)…", "Scribing (writing by hand)…"],
    chat: [
      ["What have you built with LangGraph?", "Astra: an agent with smart search on pgvector and an MCP server."],
      ["How can we work together?", "On-site, remote, hybrid or project-based, whichever suits you."],
    ],
    agents: ["Data analyst", "News analyst", "Bull", "Bear", "Risk manager", "Trader", "Portfolio manager"],
    phone: "Phone",
    email: "Email",
  },
};
type T = (typeof L)["fa"];

const DRAWINGS = [
  { id: "reject", fa: "الف: رد کردن رزومه" },
  { id: "bug", fa: "ب: باگ را بگیر" },
  { id: "dip", fa: "ج: در کف بخر" },
  { id: "robot", fa: "د: من ربات نیستم" },
];

const WINDOWS = [
  ["data", 23.92, 30.71, 10.05, 16.58],
  ["news", 38.04, 30.71, 9.99, 16.58],
  ["bull", 52.15, 30.71, 10.11, 16.58],
  ["bear", 66.09, 30.71, 10.05, 16.58],
  ["risk", 25.54, 59.09, 6.16, 18.28],
  ["trader", 31.94, 59.09, 6.22, 18.28],
  ["pm", 62.74, 59.09, 13.16, 18.28],
] as const;

/** Line icons for the five buttons, drawn on a 24 by 24 grid. */
function Icon({ i, size = 24, color = "currentColor" }: { i: number; size?: number; color?: string }) {
  const p = { fill: "none", stroke: color, strokeWidth: 2, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true">
      {i === 0 && <path {...p} d="M4 5h16v10H10l-5 4v-4H4z M8 10h.01 M12 10h.01 M16 10h.01" />}
      {i === 1 && (
        <>
          <circle {...p} cx="10" cy="10" r="6" />
          <path {...p} d="M14.5 14.5L20 20 M7.5 10l1.8 1.8L12.8 8" />
        </>
      )}
      {i === 2 && <path {...p} d="M3 20h18 M5 16l4-5 4 3 6-8 M15 6h4v4" />}
      {i === 3 && <path {...p} d="M3 7h6l2 2h10v10H3z" />}
      {i === 4 && <path {...p} d="M8 7l-5 5 5 5 M16 7l5 5-5 5 M13.5 5l-3 14" />}
    </svg>
  );
}

function useTick(ms: number, count: number) {
  const [i, setI] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setI((v) => (v + 1) % count), ms);
    return () => clearInterval(id);
  }, [ms, count]);
  return i;
}

const INK = "var(--line)";

const GAMES = {
  fa: {
    reject: {
      title: "این رزومه را رد کنید",
      hire: "استخدامش کن",
      no: "ردش کن",
      taunts: ["ردش کن… اگر می‌توانی", "نزدیک بود!", "دکمه‌ی رد هم طرفدار هوتن است.", "از نظر فنی غیرممکن است.", "خب، شاید وقتش است استخدامش کنید؟"],
      count: "تلاش",
    },
    bug: {
      title: "باگ را بگیر",
      taunts: ["یک باگ در صفحه هست. بگیرش!", "در رفت!", "یکی را درست کردی، دو تا شد.", "این باگ‌ها از تست‌های هوتن فرار کرده‌اند.", "حالا فهمیدی چرا هوتن تست می‌نویسد؟"],
      count: "باگ‌ها",
    },
    dip: {
      title: "در کف بخر!",
      taunts: ["روی نقطه‌ی نارنجی کلیک کن و در کف بخر.", "بازار منتظر تو نمی‌ماند.", "کف جدید! این بار حتماً…", "هوتن دو سال همین بازی را کرد.", "برای همین به ایجنت‌ها سپرد."],
      count: "کف‌های ازدست‌رفته",
    },
    robot: {
      title: "ثابت کن ربات نیستی",
      label: "من ربات نیستم",
      taunts: ["فقط یک تیک ساده.", "مطمئنی ربات نیستی؟", "ربات‌ها هم همین را می‌گفتند.", "حتی ایجنت‌های هوتن این را رد می‌کنند.", "باشد، قبول. تو هم ربات هستی."],
      count: "تلاش",
    },
  },
  en: {
    reject: {
      title: "Reject this résumé",
      hire: "Hire him",
      no: "Reject",
      taunts: ["Reject him… if you can", "So close!", "Even the reject button is a fan.", "Technically impossible.", "Maybe it's time to hire him?"],
      count: "Tries",
    },
    bug: {
      title: "Catch the bug",
      taunts: ["There's a bug on the page. Catch it!", "It got away!", "You fixed one, now there are two.", "These bugs escaped Hootan's tests.", "Now you see why Hootan writes tests."],
      count: "Bugs",
    },
    dip: {
      title: "Buy the dip!",
      taunts: ["Click the orange dot to buy the dip.", "The market doesn't wait for you.", "New low! This time for sure…", "Hootan played this game for two years.", "That's why he hired agents."],
      count: "Missed dips",
    },
    robot: {
      title: "Prove you're not a robot",
      label: "I'm not a robot",
      taunts: ["Just one little tick.", "Are you sure you're not a robot?", "That's what the robots said too.", "Even Hootan's agents fail this one.", "Fine. You're a robot too."],
      count: "Tries",
    },
  },
};

const AREA = "relative h-[360px] w-full touch-none select-none";

/** Local pointer position inside an element. */
function localPoint(e: React.PointerEvent, el: HTMLElement) {
  const r = el.getBoundingClientRect();
  return { x: e.clientX - r.left, y: e.clientY - r.top, w: r.width, h: r.height };
}

/** A random spot inside the box that is far enough from the pointer. */
function escapeTo(p: { x: number; y: number; w: number; h: number }, size: { w: number; h: number }) {
  let best = { x: 0, y: 0 };
  let bestD = -1;
  for (let i = 0; i < 24; i++) {
    const x = Math.random() * (p.w - size.w) + size.w / 2;
    const y = Math.random() * (p.h - size.h - 70) + size.h / 2 + 60;
    const d = Math.hypot(x - p.x, y - p.y);
    if (d > bestD) {
      best = { x, y };
      bestD = d;
    }
    if (d > 170) break;
  }
  return best;
}

function GameHeader({ title, taunt, count, n }: { title: string; taunt: string; count: string; n: number }) {
  return (
    <div className="pointer-events-none absolute inset-x-0 top-0 flex items-start justify-between gap-3">
      <div>
        <div className="font-hand text-[26px] leading-none text-accent">{title}</div>
        <div className="mt-1.5 text-[15px] text-muted">{taunt}</div>
      </div>
      <div className="flex-none rounded-full border-[1.5px] border-line px-3 py-1 font-mono text-[13px]">
        {count}: {n}
      </div>
    </div>
  );
}

/** Game A: the reject button runs away; the hire button stays put. */
function RejectGame({ lang }: { lang: Locale }) {
  const g = GAMES[lang].reject;
  const box = useRef<HTMLDivElement>(null);
  const [pos, setPos] = useState({ x: 300, y: 230 });
  const [n, setN] = useState(0);
  const flee = (e: React.PointerEvent) => {
    const p = localPoint(e, box.current!);
    if (Math.hypot(p.x - pos.x, p.y - pos.y) > 85) return;
    setPos(escapeTo(p, { w: 120, h: 50 }));
    setN((v) => v + 1);
  };
  return (
    <div ref={box} className={AREA} onPointerMove={flee} onPointerDown={flee}>
      <GameHeader title={g.title} taunt={g.taunts[Math.min(Math.floor(n / 3), 4)]} count={g.count} n={n} />
      <a href="#contact" className="btn absolute top-[230px] left-[90px] -translate-x-1/2 -translate-y-1/2 rounded-xl border-2 border-line bg-orange px-5 py-3 text-[16px] font-bold text-[#1e1c1a] no-underline shadow-[3px_3px_0_var(--line)]">
        {g.hire}
      </a>
      <button
        type="button"
        tabIndex={-1}
        className="absolute -translate-x-1/2 -translate-y-1/2 rounded-xl border-2 border-line bg-card px-5 py-3 text-[16px] font-semibold text-ink transition-[left,top] duration-200 ease-out"
        style={{ left: pos.x, top: pos.y }}
      >
        {g.no}
      </button>
    </div>
  );
}

type Bug = { id: number; x: number; y: number; a: number };

/** Game B: bugs wander and scurry away; touching one splits it in two. */
function BugGame({ lang }: { lang: Locale }) {
  const g = GAMES[lang].bug;
  const box = useRef<HTMLDivElement>(null);
  const pointer = useRef({ x: -999, y: -999 });
  const [bugs, setBugs] = useState<Bug[]>([{ id: 0, x: 200, y: 220, a: 0 }]);
  const [escapes, setEscapes] = useState(0);

  useEffect(() => {
    let raf = 0;
    const step = () => {
      const el = box.current;
      if (el) {
        const w = el.clientWidth;
        const h = el.clientHeight;
        setBugs((list) =>
          list.map((b) => {
            const dx = b.x - pointer.current.x;
            const dy = b.y - pointer.current.y;
            const d = Math.hypot(dx, dy);
            let a = b.a + (Math.random() - 0.5) * 0.35;
            let speed = 0.8;
            if (d < 110) {
              a = Math.atan2(dy, dx);
              speed = 6;
            }
            let x = b.x + Math.cos(a) * speed;
            let y = b.y + Math.sin(a) * speed;
            if (x < 15 || x > w - 15) a = Math.PI - a;
            if (y < 80 || y > h - 15) a = -a;
            x = Math.max(15, Math.min(w - 15, x));
            y = Math.max(80, Math.min(h - 15, y));
            return { ...b, x, y, a };
          }),
        );
      }
      raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, []);

  const move = (e: React.PointerEvent) => {
    const p = localPoint(e, box.current!);
    pointer.current = p;
    const hit = bugs.find((b) => Math.hypot(b.x - p.x, b.y - p.y) < 22);
    if (hit && bugs.length < 7) {
      setBugs((list) => [...list, { id: Date.now(), x: hit.x, y: hit.y, a: hit.a + Math.PI }]);
      setEscapes((v) => v + 1);
    }
  };

  return (
    <div ref={box} className={AREA} onPointerMove={move} onPointerDown={move} onPointerLeave={() => (pointer.current = { x: -999, y: -999 })}>
      <GameHeader title={g.title} taunt={g.taunts[Math.min(escapes, 4)]} count={g.count} n={bugs.length} />
      <svg className="absolute inset-0 h-full w-full overflow-visible">
        {bugs.map((b) => (
          <g key={b.id} transform={`translate(${b.x} ${b.y}) rotate(${(b.a * 180) / Math.PI + 90})`}>
            <g className="legs" fill="none" stroke={INK} strokeWidth="2" strokeLinecap="round">
              <path d="M-7 -4l-9 -6 M-7 2l-10 0 M-7 8l-9 6 M7 -4l9 -6 M7 2l10 0 M7 8l9 6" />
            </g>
            <ellipse cx="0" cy="3" rx="9" ry="12" fill="var(--orange)" stroke={INK} strokeWidth="2" />
            <path d="M0 -9v24" stroke={INK} strokeWidth="1.5" />
            <circle cx="0" cy="-12" r="5" fill="var(--bg)" stroke={INK} strokeWidth="2" />
            <path d="M-2 -16l-4 -6 M2 -16l4 -6" stroke={INK} strokeWidth="1.5" strokeLinecap="round" />
          </g>
        ))}
      </svg>
    </div>
  );
}

function randomWalk() {
  const pts: number[] = [];
  let v = 50;
  for (let i = 0; i < 24; i++) {
    v += (Math.random() - 0.5) * 22;
    v = Math.max(8, Math.min(92, v));
    pts.push(v);
  }
  return pts;
}

/** Game C: click the lowest point of the chart; the market always moves just before you do. */
function DipGame({ lang }: { lang: Locale }) {
  const g = GAMES[lang].dip;
  const box = useRef<HTMLDivElement>(null);
  const [pts, setPts] = useState<number[]>(() => Array.from({ length: 24 }, (_, i) => 50 + Math.sin(i / 2.5) * 30));
  const [n, setN] = useState(0);
  const W = 410;
  const top = 90;
  const H = 230;
  const xy = pts.map((v, i) => [10 + (i * (W - 20)) / (pts.length - 1), top + H - (v / 100) * H] as const);
  const low = xy.reduce((m, p) => (p[1] > m[1] ? p : m), xy[0]);
  const d = xy.map(([x, y], i) => `${i ? "L" : "M"}${x.toFixed(1)} ${y.toFixed(1)}`).join(" ");

  const move = (e: React.PointerEvent) => {
    const p = localPoint(e, box.current!);
    const sx = (p.x / p.w) * W;
    const sy = (p.y / p.h) * 360;
    if (Math.hypot(sx - low[0], sy - low[1]) > 45) return;
    setPts(randomWalk());
    setN((v) => v + 1);
  };

  return (
    <div ref={box} className={AREA} onPointerMove={move} onPointerDown={move}>
      <GameHeader title={g.title} taunt={g.taunts[Math.min(Math.floor(n / 2), 4)]} count={g.count} n={n} />
      <svg viewBox={`0 0 ${W} 360`} preserveAspectRatio="none" className="absolute inset-0 h-full w-full">
        <path d={`M10 ${top + H}H${W - 10}`} stroke={INK} strokeWidth="1.5" strokeDasharray="4 6" fill="none" />
        <path d={d} fill="none" stroke={INK} strokeWidth="2.5" strokeLinejoin="round" style={{ transition: "d .35s ease" }} />
        <circle cx={low[0]} cy={low[1]} r="9" fill="var(--orange)" stroke={INK} strokeWidth="2.5" className="pulse" style={{ transition: "cx .35s, cy .35s" }} />
      </svg>
    </div>
  );
}

/** Game D: the "I'm not a robot" box slides away every time you reach for it. */
function RobotGame({ lang }: { lang: Locale }) {
  const g = GAMES[lang].robot;
  const box = useRef<HTMLDivElement>(null);
  const [pos, setPos] = useState({ x: 200, y: 220 });
  const [n, setN] = useState(0);
  const flee = (e: React.PointerEvent) => {
    const p = localPoint(e, box.current!);
    if (Math.hypot(p.x - pos.x, p.y - pos.y) > 110) return;
    setPos(escapeTo(p, { w: 230, h: 70 }));
    setN((v) => v + 1);
  };
  return (
    <div ref={box} className={AREA} onPointerMove={flee} onPointerDown={flee}>
      <GameHeader title={g.title} taunt={g.taunts[Math.min(Math.floor(n / 3), 4)]} count={g.count} n={n} />
      <div
        className="absolute flex -translate-x-1/2 -translate-y-1/2 items-center gap-3 rounded-lg border-2 border-line bg-card px-4 py-3 shadow-[3px_3px_0_var(--line)] transition-[left,top,rotate] duration-200 ease-out"
        style={{ left: pos.x, top: pos.y, rotate: `${(n % 5) - 2}deg` }}
      >
        <span className="h-7 w-7 rounded border-2 border-line bg-input" />
        <span className="text-[16px] font-semibold whitespace-nowrap">{g.label}</span>
        <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
          <path d="M20 12a8 8 0 1 1-3-6.2 M20 4v5h-5" />
        </svg>
      </div>
    </div>
  );
}

function DeskAnim({ t }: { t: T }) {
  const i = useTick(2600, 3);
  const imgs = ["me_listen", "me_think", "me_talk"];
  return (
    <div dir="ltr" className="relative aspect-square w-full overflow-hidden rounded-[22px] border-2 border-line bg-paper shadow-[6px_6px_0_var(--line)]">
      {imgs.map((name, k) => (
        // eslint-disable-next-line @next/next/no-img-element
        <img key={name} src={`/assets/${name}.jpg`} alt="" className="absolute inset-0 h-full w-full object-cover transition-opacity duration-500" style={{ opacity: k === i ? 1 : 0 }} />
      ))}
      <span className="absolute top-4 left-4 rounded-full bg-[#1e1c1a] px-3 py-1.5 text-[14px] font-semibold text-[#f3ebdd]">{t.states[i]}</span>
    </div>
  );
}

function FlowAnim({ t }: { t: T }) {
  const i = useTick(1400, 4);
  return (
    <div dir="ltr" className="flex aspect-square w-full flex-col justify-center gap-6 rounded-[22px] border-2 border-line bg-card p-8 shadow-[6px_6px_0_var(--line)]">
      {t.steps.map((s, k) => (
        <div key={s} className="flex items-center gap-4">
          <div
            className="flex h-14 w-14 flex-none items-center justify-center rounded-full border-2 border-line text-[20px] font-bold transition-all duration-300"
            style={{ background: k === i ? "var(--orange)" : k < i ? "var(--soft)" : "var(--card)", transform: k === i ? "scale(1.12)" : "none", color: "#1e1c1a" }}
          >
            {k + 1}
          </div>
          <div className="flex-1" style={{ opacity: k <= i ? 1 : 0.4 }}>
            <div className="text-[22px] font-bold">{s}</div>
            <div className="text-[14px] text-muted">{t.stepMeaning[k]}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

function TypeAnim({ t, lang }: { t: T; lang: Locale }) {
  const [n, setN] = useState(0);
  const [pair, setPair] = useState(0);
  const [q, a] = t.chat[pair];
  useEffect(() => {
    const id = setTimeout(
      () => {
        if (n >= a.length + 30) {
          setPair((p) => (p + 1) % t.chat.length);
          setN(-12);
        } else setN(n + 1);
      },
      n < 0 ? 120 : 45,
    );
    return () => clearTimeout(id);
  }, [n, a.length, t.chat.length]);
  return (
    <div dir={lang === "fa" ? "rtl" : "ltr"} className="flex aspect-square w-full flex-col justify-end gap-3 rounded-[22px] border-2 border-line bg-card p-6 shadow-[6px_6px_0_var(--line)]">
      <div className="max-w-[85%] self-end rounded-[14px] rounded-ee-[4px] bg-inv px-3.5 py-2.5 text-[15px] text-inv-ink">{q}</div>
      <div className="min-h-[64px] max-w-[90%] self-start rounded-[14px] rounded-es-[4px] border-[1.5px] border-line bg-bg px-3.5 py-2.5 text-[15px] leading-[1.6]">
        {n < 0 ? <span className="text-muted">{t.states[1]}</span> : a.slice(0, n)}
      </div>
    </div>
  );
}

function OfficeAnim({ t }: { t: T }) {
  const i = useTick(1500, WINDOWS.length);
  const [name, left, top, width, height] = WINDOWS[i];
  return (
    <div dir="ltr" className="w-full overflow-hidden rounded-[22px] border-2 border-line bg-paper shadow-[6px_6px_0_var(--line)]">
      <div className="relative aspect-[1672/941] w-full">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/assets/office_idle.jpg" alt="" className="absolute inset-0 h-full w-full" />
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={`/assets/talk_${name}.jpg`} alt="" className="absolute rounded-[3px] outline-[3px] outline-orange" style={{ left: `${left}%`, top: `${top}%`, width: `${width}%`, height: `${height}%` }} />
      </div>
      <div className="border-t-[1.5px] border-line px-4 py-3 text-center text-[16px] font-semibold">{t.agents[i]}</div>
    </div>
  );
}

function WhatsApp() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 20l1.3-4A8 8 0 1 1 8 18.7z" />
      <path d="M9 9.5c0 3 2.5 5.5 5.5 5.5l1-1.5-2-1-1 .8a4 4 0 0 1-1.8-1.8l.8-1-1-2z" />
    </svg>
  );
}

function Telegram() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 4L3 11l6 2 2 6 3-4 5 4z M9 13l12-9" />
    </svg>
  );
}

function Contact({ t }: { t: T }) {
  const row = "flex items-center gap-2 rounded-lg px-2 py-2 text-ink no-underline hover:bg-soft";
  return (
    <details className="relative">
      <summary className="btn cursor-pointer list-none rounded-full border-[1.5px] border-line bg-card px-4 py-2.5 text-[15px] font-semibold text-ink">{t.contact}</summary>
      <div className="absolute end-0 top-[52px] z-30 flex w-[270px] flex-col gap-1 rounded-2xl border-2 border-line bg-card p-3 shadow-[5px_5px_0_var(--line)]">
        <a href="mailto:hootanseifi90@gmail.com" className={row}>
          <span className="text-muted">{t.email}</span>
          <span dir="ltr" className="ms-auto font-mono text-[13px]">hootanseifi90@gmail.com</span>
        </a>
        <a href="tel:+989357759499" className={row}>
          <span className="text-muted">{t.phone}</span>
          <span dir="ltr" className="ms-auto font-mono text-[14px]">+98 935 775 9499</span>
        </a>
        <div className="mt-1 flex gap-2">
          <a href="https://wa.me/989357759499" target="_blank" rel="noreferrer" aria-label="WhatsApp" className="btn flex flex-1 items-center justify-center gap-1.5 rounded-xl border-[1.5px] border-line py-2 text-[14px] text-ink no-underline">
            <WhatsApp /> WhatsApp
          </a>
          <a href="https://t.me/+989357759499" target="_blank" rel="noreferrer" aria-label="Telegram" className="btn flex flex-1 items-center justify-center gap-1.5 rounded-xl border-[1.5px] border-line py-2 text-[14px] text-ink no-underline">
            <Telegram /> Telegram
          </a>
        </div>
      </div>
    </details>
  );
}

/** Temporary page for choosing the new hero drawing; everything else follows Hootan's notes. */
export function HeroPreview({ lang }: { lang: Locale }) {
  const t = L[lang];
  const [drawing, setDrawing] = useState(DRAWINGS[0].id);
  const pick = (on: boolean) => `rounded-full border-[1.5px] border-line px-3 py-1.5 text-[13px] ${on ? "bg-inv text-inv-ink" : "bg-card text-ink"}`;

  const sectionBody = [
    <div key="twin" className="grid w-full gap-6 md:grid-cols-2">
      <DeskAnim t={t} />
      <TypeAnim t={t} lang={lang} />
    </div>,
    null,
    <div key="trading" className="w-full max-w-[760px]">
      <OfficeAnim t={t} />
    </div>,
    null,
    <div key="how" className="w-full max-w-[420px]">
      <FlowAnim t={t} />
    </div>,
  ];

  return (
    <>
      <div dir="rtl" className="fixed inset-x-0 bottom-0 z-30 flex flex-wrap items-center gap-1.5 border-t-2 border-dashed border-orange bg-soft px-4 py-3 font-fa text-[13px]">
        <b className="me-2">نقاشی کنار دکمه‌ها:</b>
        {DRAWINGS.map((d) => (
          <button key={d.id} type="button" className={pick(d.id === drawing)} onClick={() => setDrawing(d.id)}>
            {d.fa}
          </button>
        ))}
      </div>

      <header className="sticky top-0 z-20 border-b-[1.5px] border-line bg-head">
        <div className="mx-auto flex max-w-[1200px] flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6">
          <div className="flex items-center gap-2.5">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/assets/me_avatar_sm.jpg" alt="" className="h-[34px] w-[34px] rounded-full border-[1.5px] border-line" />
            <span className="text-[16px] font-semibold">{t.name}</span>
          </div>
          <div className="inline-flex items-center gap-2 text-[14px] font-semibold text-green">
            <span className="pulse h-2 w-2 rounded-full bg-green" aria-hidden="true" />
            {t.open}
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Contact t={t} />
            <a href="#resume" className="btn inline-flex min-h-11 items-center rounded-full border-[1.5px] border-line bg-orange px-[18px] text-[15px] font-bold text-[#1e1c1a] no-underline">
              {t.resume}
            </a>
          </div>
        </div>
      </header>

      <section className="mx-auto grid max-w-[1200px] items-center gap-8 px-4 pt-5 pb-16 sm:px-6 md:grid-cols-[1.15fr_1fr]">
        <div>
          <div className="font-hand text-[26px] text-accent">{t.tag}</div>
          <h1 className="mt-1 mb-5 text-[clamp(26px,3.2vw,38px)] leading-[1.45]" style={{ fontFamily: lang === "fa" ? HEADLINE_FONT.family : undefined, fontWeight: lang === "fa" ? HEADLINE_FONT.weight : 600 }}>
            {t.h1}
          </h1>
          <div className="flex flex-col gap-2">
            {t.buttons.map((b, k) => (
              <a
                key={b}
                href={`#${IDS[k]}`}
                className="hint btn group flex items-center gap-3 rounded-2xl border-2 border-line bg-card px-4 py-2 text-ink no-underline shadow-[3px_3px_0_var(--line)]"
              >
                <span className="flex h-9 w-9 flex-none items-center justify-center rounded-xl border-[1.5px] border-line bg-bg transition-colors group-hover:bg-orange group-focus-visible:bg-orange">
                  <Icon i={k} />
                </span>
                <span className="flex min-w-0 flex-1 flex-col">
                  <span className="text-[16px] font-semibold">{b}</span>
                  <span className="hint-text text-[14px] text-muted">{t.hints[k]}</span>
                </span>
                <span aria-hidden="true" className="text-accent">
                  {lang === "fa" ? "←" : "→"}
                </span>
              </a>
            ))}
          </div>
        </div>
        <div className="mx-auto w-full max-w-[480px]">
          {drawing === "reject" && <RejectGame lang={lang} />}
          {drawing === "bug" && <BugGame lang={lang} />}
          {drawing === "dip" && <DipGame lang={lang} />}
          {drawing === "robot" && <RobotGame lang={lang} />}
        </div>
      </section>

      {IDS.map((id, k) => (
        <section key={id} id={id} className="mx-auto max-w-[1200px] scroll-mt-[90px] px-4 pb-10 sm:px-6">
          <div className="flex min-h-[60vh] flex-col items-center justify-center gap-6 rounded-[22px] border-2 border-dashed border-line bg-card p-6">
            <h2 className="flex items-center gap-3 text-[30px] font-bold">
              <Icon i={k} size={30} color="var(--accent)" />
              {t.buttons[k]}
            </h2>
            {sectionBody[k] ?? <p className="text-muted">{t.soon}</p>}
          </div>
        </section>
      ))}
      <div className="h-24" />
    </>
  );
}
