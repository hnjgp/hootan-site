import type { ReactNode } from "react";

/** Diagram colors; ink is the plain line color. */
export const COLOR = {
  orange: "var(--orange)",
  green: "var(--green)",
  blue: "var(--blue)",
  ink: "var(--line)",
} as const;
export type Tone = keyof typeof COLOR;

/** Persian text inside SVG needs right-to-left direction, or mixed words come out in the wrong order. */
export const dirOf = (text: string) => (/[؀-ۿ]/.test(text) ? "rtl" : "ltr");

/** A diagram drawn in a w by h box; on narrow screens it scrolls sideways instead of shrinking its text. */
export function Svg({
  w,
  h,
  label,
  children,
}: {
  w: number;
  h: number;
  label: string;
  children: ReactNode;
}) {
  return (
    <div
      dir="ltr"
      className="overflow-x-auto rounded-2xl border-[1.5px] border-line bg-bg p-3"
    >
      <svg
        viewBox={`0 0 ${w} ${h}`}
        role="img"
        aria-label={label}
        className="block w-full min-w-[560px] overflow-visible"
      >
        {children}
      </svg>
    </div>
  );
}

/** One component: a rounded box with a title and an optional second line; `glow` makes it pulse. */
export function Box({
  x,
  y,
  w,
  h = 46,
  title,
  sub,
  tone = "ink",
  glow = false,
  delay = 0,
}: {
  x: number;
  y: number;
  w: number;
  h?: number;
  title: string;
  sub?: string;
  tone?: Tone;
  glow?: boolean;
  delay?: number;
}) {
  const cx = x + w / 2;
  const cy = y + h / 2;
  return (
    <g>
      <rect
        x={x}
        y={y}
        width={w}
        height={h}
        rx={10}
        fill="var(--card)"
        stroke={COLOR[tone]}
        strokeWidth={tone === "ink" ? 1.5 : 2.2}
      />
      {glow && (
        <rect
          x={x}
          y={y}
          width={w}
          height={h}
          rx={10}
          fill={COLOR.orange}
          fillOpacity={0}
          className="glow"
          style={{ animationDelay: `${delay}s` }}
        />
      )}
      <text
        x={cx}
        y={sub ? cy - 4 : cy + 4.5}
        textAnchor="middle"
        direction={dirOf(title)}
        fontSize={13}
        fontWeight={700}
        fill="var(--ink)"
      >
        {title}
      </text>
      {sub && (
        <text
          x={cx}
          y={cy + 12}
          textAnchor="middle"
          direction={dirOf(sub)}
          fontSize={10.5}
          fill="var(--muted)"
        >
          {sub}
        </text>
      )}
    </g>
  );
}

/** A connection along path `d`, with a packet of `tone` color travelling from its start to its end. */
export function Edge({
  d,
  tone = "orange",
  delay = 0,
  dur = 2.4,
  dashed = false,
}: {
  d: string;
  tone?: Tone;
  delay?: number;
  dur?: number;
  dashed?: boolean;
}) {
  return (
    <g>
      <path
        d={d}
        fill="none"
        stroke="var(--muted)"
        strokeOpacity={0.6}
        strokeWidth={1.4}
        strokeDasharray={dashed ? "5 5" : undefined}
      />
      <path
        d={d}
        pathLength={100}
        fill="none"
        stroke={COLOR[tone]}
        className="packet"
        style={{ animationDelay: `${delay}s`, animationDuration: `${dur}s` }}
      />
    </g>
  );
}

/** Small text on the diagram, e.g. an edge label; `anchor` is visual: start keeps the text right of x. */
export function Label({
  x,
  y,
  children,
  anchor = "middle",
  tone,
}: {
  x: number;
  y: number;
  children: string;
  anchor?: "start" | "middle" | "end";
  tone?: Tone;
}) {
  const rtl = dirOf(children) === "rtl";
  // In right-to-left text SVG flips start and end, so they are swapped back here.
  const side =
    rtl && anchor !== "middle"
      ? anchor === "start"
        ? "end"
        : "start"
      : anchor;
  return (
    <text
      x={x}
      y={y}
      textAnchor={side}
      direction={dirOf(children)}
      fontSize={10.5}
      fontWeight={600}
      fill={tone ? COLOR[tone] : "var(--muted)"}
    >
      {children}
    </text>
  );
}

/** Horizontal bars that grow in turn; `value / max` sets each length. */
export function Bars({
  rows,
  label,
}: {
  rows: {
    name: string;
    value: number;
    max: number;
    text: string;
    tone: Tone;
  }[];
  label: string;
}) {
  const h = rows.length * 34 + 6;
  return (
    <Svg w={720} h={h} label={label}>
      {rows.map((r, k) => {
        const y = 8 + k * 34;
        return (
          <g key={r.name}>
            <text
              x={dirOf(r.name) === "rtl" ? 200 : 0}
              y={y + 15}
              direction={dirOf(r.name)}
              fontSize={12.5}
              fontWeight={600}
              fill="var(--ink)"
            >
              {r.name}
            </text>
            <rect
              x={210}
              y={y}
              width={420}
              height={20}
              rx={10}
              fill="var(--soft)"
            />
            <rect
              x={210}
              y={y}
              width={(420 * r.value) / r.max}
              height={20}
              rx={10}
              fill={COLOR[r.tone]}
              className="grow-bar"
              style={{ animationDelay: `${0.2 + k * 0.25}s` }}
            />
            <text
              x={640}
              y={y + 15}
              fontSize={12.5}
              fontWeight={700}
              fontFamily="var(--font-mono)"
              fill="var(--ink)"
            >
              {r.text}
            </text>
          </g>
        );
      })}
    </Svg>
  );
}
