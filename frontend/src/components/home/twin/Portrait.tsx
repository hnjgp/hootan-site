import type { Dictionary } from "@/i18n";
import type { Phase } from "./useTwinChat";

const IMAGES = ["me_listen", "me_think", "me_talk"];
const IMAGE_OF: Record<Phase, number> = { listen: 0, search: 1, think: 1, talk: 2 };

/** Hootan at the desk; the picture and the label follow the chat phase. */
export function Portrait({ t, phase, word, file }: { t: Dictionary["twin"]; phase: Phase; word: number; file?: string }) {
  const shown = IMAGE_OF[phase];
  const words = phase === "listen" ? null : t.words[phase];
  const [label, meaning] = words ? words[word % words.length] : [t.listen, ""];

  return (
    <div className="relative aspect-square w-full overflow-hidden bg-paper">
      <div className="breathe absolute inset-0 origin-[50%_80%]">
        {IMAGES.map((name, k) => (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            key={name}
            src={`/assets/${name}.jpg`}
            alt={k === shown ? t.alt[k] : ""}
            aria-hidden={k !== shown}
            className="absolute inset-0 h-full w-full object-cover transition-opacity duration-500"
            style={{ opacity: k === shown ? 1 : 0 }}
          />
        ))}
      </div>
      <div className="absolute start-4 top-4 flex max-w-[calc(100%-2rem)] flex-wrap items-center gap-x-2.5 gap-y-1 rounded-2xl border-2 border-orange bg-[#1e1c1a] px-4 py-2.5 text-[20px] font-bold text-[#f3ebdd] shadow-[4px_4px_0_var(--orange)] sm:text-[22px]">
        <span aria-hidden="true" className="pulse h-3 w-3 rounded-full bg-orange" />
        <span>{label}</span>
        {meaning && <span className="text-[15px] font-normal text-[#f3ebdd]/75">({meaning})</span>}
      </div>
      {phase === "search" && file && (
        <div className="pop absolute start-4 bottom-4 flex items-center gap-2 rounded-[10px] border-[1.5px] border-[#1e1c1a] bg-[#fffdf8] px-3.5 py-2.5 font-mono text-[14px] text-[#1e1c1a]">
          <span className="dots" aria-hidden="true">
            <span />
            <span />
            <span />
          </span>
          {t.searching} {file}
        </div>
      )}
    </div>
  );
}
