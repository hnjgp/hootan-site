"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { Dictionary, Locale } from "@/i18n";
import { ASTRA } from "./diagrams/Astra";
import { BEHENGAM } from "./diagrams/Behengam";
import { NOTES } from "./diagrams/Notes";
import { SITE } from "./diagrams/Site";

const IDS = ["astra", "notes", "behengam", "site"] as const;
type Id = (typeof IDS)[number];
type T = Dictionary["projects"];

const PROFILE = "https://github.com/hnjgp";
/** Behengam has no public repository yet. */
const REPOS: Record<Id, string | null> = {
  astra: "https://github.com/hnjgp/astra-ai-platform",
  notes: "https://github.com/hnjgp/ai-medical-notes-saas",
  behengam: null,
  site: "https://github.com/hnjgp/hootan-site",
};

/** Line icons: an agent graph, a note, a pulse line and a browser window. */
const ICONS: Record<Id, string> = {
  astra: "M6 6h.01M18 6h.01M12 18h.01M6 6l6 12 6-12M6 6h12",
  notes: "M7 3h7l4 4v14H7zM14 3v4h4M10 12h5M10 15h5M10 18h3",
  behengam: "M3 12h4l2-5 4 10 2-5h6",
  site: "M3 5h18v14H3zM3 9h18M6 7h.01M9 7h.01",
};

function Icon({ id }: { id: Id }) {
  return (
    <span className="flex h-10 w-10 flex-none items-center justify-center rounded-xl border-[1.5px] border-line bg-bg text-accent">
      <svg width={22} height={22} viewBox="0 0 24 24" aria-hidden="true">
        <path
          d={ICONS[id]}
          fill="none"
          stroke="currentColor"
          strokeWidth={1.8}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </span>
  );
}

/** The diagram `name` of project `id`. */
function Diagram({
  id,
  name,
  t,
  agents,
}: {
  id: Id;
  name: string;
  t: T;
  agents: string[];
}) {
  if (id === "astra") {
    const C = ASTRA[name as keyof typeof ASTRA];
    return <C d={t.items.astra.d} />;
  }
  if (id === "notes") {
    const C = NOTES[name as keyof typeof NOTES];
    return <C d={t.items.notes.d} />;
  }
  if (id === "behengam") {
    const C = BEHENGAM[name as keyof typeof BEHENGAM];
    return <C d={t.items.behengam.d} />;
  }
  const C = SITE[name as keyof typeof SITE];
  return <C d={t.items.site.d} agents={agents} />;
}

/** The open project: a large scrollable box with the full story, diagrams and the GitHub link. */
function Detail({
  id,
  t,
  agents,
  lang,
  onClose,
}: {
  id: Id;
  t: T;
  agents: string[];
  lang: Locale;
  onClose: () => void;
}) {
  const p = t.items[id];
  const closeButton = useRef<HTMLButtonElement>(null);
  const repo = REPOS[id];

  useEffect(() => {
    closeButton.current?.focus();
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    addEventListener("keydown", onKey);
    return () => removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div
      data-panel
      role="region"
      aria-labelledby={`project-${id}-title`}
      className="pop flex max-h-[85vh] min-h-0 flex-1 flex-col overflow-hidden rounded-[20px] border-2 border-line bg-card shadow-[5px_5px_0_var(--line)] snap:max-h-none"
    >
      <div className="flex items-center gap-3 border-b-[1.5px] border-line px-4 py-3 sm:px-6">
        <Icon id={id} />
        <div className="min-w-0 flex-1">
          <h3
            id={`project-${id}-title`}
            className="m-0 text-[20px] leading-tight font-bold"
          >
            {p.title}
          </h3>
          <div className="text-[13px] text-muted">
            {p.kind} · {p.status}
          </div>
        </div>
        <button
          ref={closeButton}
          type="button"
          onClick={onClose}
          aria-label={t.close}
          title={t.close}
          className="btn flex h-11 w-11 flex-none items-center justify-center rounded-full border-[1.5px] border-line bg-bg text-ink"
        >
          <svg width={18} height={18} viewBox="0 0 24 24" aria-hidden="true">
            <path
              d="M5 5l14 14M19 5L5 19"
              stroke="currentColor"
              strokeWidth={2.4}
              strokeLinecap="round"
            />
          </svg>
        </button>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-5 sm:px-7">
        <p className="mt-0 mb-5 max-w-[860px] text-[16px] leading-[1.8]">
          {p.lead}
        </p>

        <div className="mb-7 flex flex-wrap gap-3">
          {p.stats.map(([value, label]) => (
            <div
              key={label}
              className="flex min-w-[130px] flex-1 flex-col gap-1 rounded-2xl border-[1.5px] border-line bg-bg px-4 py-3"
            >
              <span className="font-mono text-[24px] leading-none font-bold text-accent">
                <bdi dir="ltr">{value}</bdi>
              </span>
              <span className="text-[13px] text-muted">{label}</span>
            </div>
          ))}
        </div>

        {p.sections.map((s) => (
          <section key={s.h} className="mb-7">
            <h4 className="mt-0 mb-2 text-[18px] font-bold">{s.h}</h4>
            <p className="mt-0 mb-3 max-w-[860px] text-[15px] leading-[1.8] text-muted">
              {s.p}
            </p>
            {"dia" in s && s.dia && (
              <Diagram id={id} name={s.dia} t={t} agents={agents} />
            )}
          </section>
        ))}

        <h4 className="mt-0 mb-2 text-[18px] font-bold">{t.stack}</h4>
        <div
          dir="ltr"
          className={`mb-6 flex flex-wrap gap-2 ${lang === "fa" ? "justify-end" : ""}`}
        >
          {p.stack.map((s) => (
            <span
              key={s}
              className="rounded-full border-[1.5px] border-line px-3 py-1 font-mono text-[12.5px]"
            >
              {s}
            </span>
          ))}
        </div>

        <div className="flex flex-wrap items-center gap-3 border-t-[1.5px] border-dashed border-line pt-5">
          {!repo && <span className="text-[14px] text-muted">{t.private}</span>}
          <a
            href={repo ?? PROFILE}
            target="_blank"
            rel="noopener noreferrer"
            className="btn inline-flex min-h-[44px] items-center gap-2 rounded-full border-[1.5px] border-line bg-orange px-5 text-[15px] font-bold text-[#1e1c1a] no-underline"
          >
            <svg width={18} height={18} viewBox="0 0 24 24" aria-hidden="true">
              <path
                fill="currentColor"
                d="M12 2a10 10 0 0 0-3.16 19.49c.5.09.68-.22.68-.48v-1.7c-2.78.6-3.37-1.34-3.37-1.34-.45-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.9 1.52 2.34 1.08 2.91.83.09-.65.35-1.08.63-1.33-2.22-.25-4.55-1.11-4.55-4.94 0-1.09.39-1.98 1.03-2.68-.1-.25-.45-1.27.1-2.64 0 0 .84-.27 2.75 1.02a9.5 9.5 0 0 1 5 0c1.91-1.29 2.75-1.02 2.75-1.02.55 1.37.2 2.39.1 2.64.64.7 1.03 1.59 1.03 2.68 0 3.84-2.34 4.68-4.57 4.93.36.31.68.92.68 1.85v2.74c0 .27.18.58.69.48A10 10 0 0 0 12 2Z"
              />
            </svg>
            {repo ? t.github : t.profile}
          </a>
        </div>
      </div>
    </div>
  );
}

/**
 * Projects: four cards with a short description; a card opens its full story in a large box
 * in their place. Links to `#project-<id>` (like the hero's "How I built this site") open one directly.
 */
export function Projects({
  t,
  agents,
  lang,
}: {
  t: T;
  agents: string[];
  lang: Locale;
}) {
  const [open, setOpen] = useState<Id | null>(null);
  const opener = useRef<HTMLElement | null>(null);

  const show = useCallback((id: Id) => {
    setOpen(id);
    document.getElementById("projects")?.scrollIntoView({ behavior: "smooth" });
  }, []);

  const close = useCallback(() => {
    setOpen(null);
    requestAnimationFrame(() => opener.current?.focus());
  }, []);

  useEffect(() => {
    const idOf = (hash: string) => IDS.find((id) => hash === `#project-${id}`);
    const first = idOf(location.hash);
    if (first) requestAnimationFrame(() => show(first));
    const onClick = (e: MouseEvent) => {
      const a = (e.target as Element).closest<HTMLAnchorElement>(
        'a[href^="#project-"]',
      );
      const id = a && idOf(a.hash);
      if (!id) return;
      e.preventDefault();
      opener.current = a;
      show(id);
    };
    document.addEventListener("click", onClick);
    return () => document.removeEventListener("click", onClick);
  }, [show]);

  return (
    <div className="flex min-h-0 flex-col snap:h-full">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-x-6 gap-y-3">
        <div>
          <div className="font-hand text-[24px] leading-none text-accent">
            {t.tag}
          </div>
          <h2 className="mt-1 mb-1.5 text-[30px] leading-[1.15] font-bold sm:text-[34px]">
            {t.h2}
          </h2>
          <p className="m-0 text-[15px] leading-[1.7] text-muted">{t.sub}</p>
        </div>
        <div className="flex items-center gap-2 rounded-full border-[1.5px] border-dashed border-line px-4 py-2 text-[13.5px] font-semibold">
          <span
            aria-hidden="true"
            className="pulse h-2 w-2 flex-none rounded-full bg-orange"
          />
          {t.soon}
        </div>
      </div>

      {open ? (
        <Detail
          key={open}
          id={open}
          t={t}
          agents={agents}
          lang={lang}
          onClose={close}
        />
      ) : (
        <div className="grid min-h-0 flex-1 gap-4 sm:grid-cols-2 snap:auto-rows-[minmax(0,1fr)]">
          {IDS.map((id, k) => {
            const p = t.items[id];
            return (
              <button
                key={id}
                type="button"
                onClick={(e) => {
                  opener.current = e.currentTarget;
                  show(id);
                }}
                className="btn pop group flex min-h-0 flex-col gap-2.5 overflow-hidden rounded-[20px] border-2 border-line bg-card p-4 text-start text-ink shadow-[5px_5px_0_var(--line)] sm:p-5"
                style={{ animationDelay: `${k * 0.08}s` }}
              >
                <span className="flex w-full items-center gap-3">
                  <Icon id={id} />
                  <span className="flex min-w-0 flex-1 flex-col">
                    <span className="text-[19px] leading-tight font-bold">
                      {p.title}
                    </span>
                    <span className="truncate text-[13px] text-muted">
                      {p.kind}
                    </span>
                  </span>
                  <span className="flex-none rounded-full border-[1.5px] border-line px-2.5 py-0.5 text-[12px] font-semibold">
                    {p.status}
                  </span>
                </span>
                <span className="line-clamp-3 text-[14px] leading-[1.65] text-muted">
                  {p.short}
                </span>
                <span className="mt-auto flex w-full items-center justify-between gap-3">
                  <span
                    className={`rounded-md border-[1.5px] border-line px-2 py-0.5 text-[13px] font-bold ${lang === "fa" ? "" : "font-mono"}`}
                  >
                    {p.key}
                  </span>
                  <span className="text-[14px] font-bold text-accent group-hover:underline">
                    {t.more} {lang === "fa" ? "←" : "→"}
                  </span>
                </span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
