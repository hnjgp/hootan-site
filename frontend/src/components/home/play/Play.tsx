import type { Dictionary } from "@/i18n";

/**
 * The prediction game against the AI trading team: the rules in four cards, and the place
 * where the prediction box and the leaderboard are built in phase 10.
 */
export function Play({ t }: { t: Dictionary["play"] }) {
  return (
    <div className="flex min-h-0 flex-col snap:h-full">
      <div className="mb-4">
        <div className="font-hand text-[24px] leading-none text-accent">
          {t.tag}
        </div>
        <h2 className="mt-1 mb-1.5 text-[30px] leading-[1.15] font-bold sm:text-[34px]">
          {t.h2}
        </h2>
        <p className="m-0 max-w-[760px] text-[15px] leading-[1.7] text-muted">
          {t.sub}
        </p>
      </div>

      <ol className="m-0 grid list-none gap-4 p-0 sm:grid-cols-2 lg:grid-cols-4">
        {t.rules.map(([title, text], k) => (
          <li
            key={title}
            className="pop flex flex-col gap-2 rounded-[20px] border-2 border-line bg-card p-4 shadow-[5px_5px_0_var(--line)]"
            style={{ animationDelay: `${k * 0.08}s` }}
          >
            <span className="flex h-9 w-9 items-center justify-center rounded-full border-[1.5px] border-line bg-orange font-mono text-[16px] font-bold text-[#1e1c1a]">
              {k + 1}
            </span>
            <span className="text-[17px] leading-tight font-bold">{title}</span>
            <span className="text-[14px] leading-[1.65] text-muted">
              {text}
            </span>
          </li>
        ))}
      </ol>

      <div className="mt-4 flex min-h-[140px] flex-1 items-center justify-center gap-2.5 rounded-[20px] border-2 border-dashed border-line p-5 text-center text-[15px] font-semibold text-muted">
        <span
          aria-hidden="true"
          className="pulse h-2.5 w-2.5 flex-none rounded-full bg-orange"
        />
        {t.soon}
      </div>

      <p className="mt-3 mb-0 text-[13px] text-muted">{t.virtual}</p>
    </div>
  );
}
