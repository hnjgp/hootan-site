/** Glass panes of the window behind Hootan in each 900x900 portrait: x, y, width, height of the upper and lower pane. */
export const PANES = {
  me_listen: [
    [760, 98, 140, 139],
    [761, 258, 129, 160],
  ],
  me_think: [
    [765, 98, 135, 137],
    [767, 255, 131, 167],
  ],
  me_talk: [
    [765, 98, 135, 135],
    [767, 253, 133, 172],
  ],
} as const;

type Pane = readonly [number, number, number, number];

const STARS = [
  [778, 118, 0.6],
  [822, 222, 0.5],
  [784, 292, 0.7],
  [818, 348, 0.6],
  [790, 400, 0.6],
  [826, 278, 0.5],
] as const;

/**
 * The view through the window behind Hootan: a sun and a small cloud by day,
 * a navy sky with a crescent moon and twinkling stars in the dark theme.
 * The SVG slices like the picture's object-cover, so the panes stay on the glass; the moon and sun sit
 * near the window's inner edge because wide layouts crop the picture's sides.
 */
export function WindowView({ id, panes }: { id: string; panes: readonly Pane[] }) {
  const glass = panes.map(([x, y, w, h]) => <rect key={y} x={x} y={y} width={w} height={h} />);
  return (
    <>
      <svg viewBox="0 0 900 900" preserveAspectRatio="xMidYMid slice" aria-hidden="true" className="night-only absolute inset-0 h-full w-full mix-blend-multiply">
        <g fill="#2A3152">{glass}</g>
      </svg>
      <svg viewBox="0 0 900 900" preserveAspectRatio="xMidYMid slice" aria-hidden="true" className="absolute inset-0 h-full w-full">
        <defs>
          <clipPath id={`glass-${id}`}>{glass}</clipPath>
          <mask id={`crescent-${id}`}>
            <circle cx="797" cy="165" r="22" fill="white" />
            <circle cx="807" cy="157" r="19" fill="black" />
          </mask>
        </defs>
        <g clipPath={`url(#glass-${id})`}>
          <g className="day-only">
            <g className="sun-rays" style={{ transformOrigin: "797px 165px" }} stroke="#E8692A" strokeWidth="4" strokeLinecap="round">
              {Array.from({ length: 8 }, (_, i) => {
                const a = (i * Math.PI) / 4;
                return <path key={i} d={`M${797 + Math.cos(a) * 26} ${165 + Math.sin(a) * 26}L${797 + Math.cos(a) * 36} ${165 + Math.sin(a) * 36}`} />;
              })}
            </g>
            <circle cx="797" cy="165" r="18" fill="#E8692A" />
            <path className="drift-slow" d="M772 330h58a10 10 0 0 0-3-19 14 14 0 0 0-26-4 11 11 0 0 0-20 5 9 9 0 0 0-9 18z" fill="#FFFDF8" stroke="#1E1C1A" strokeWidth="2.5" strokeLinejoin="round" />
          </g>
          <g className="night-only">
            <g className="moon-float">
              <circle className="moon-glow" cx="797" cy="165" r="36" fill="#FFD27A" fillOpacity="0.25" />
              <circle cx="797" cy="165" r="22" fill="#F3E3B0" mask={`url(#crescent-${id})`} />
            </g>
            <g className="stars" fill="#FFD27A">
              {STARS.map(([x, y, s], k) => (
                <path key={k} className="twinkle" style={{ animationDelay: `${k * 0.4}s` }} transform={`translate(${x} ${y}) scale(${s})`} d="M0 -12L3 -3L12 0L3 3L0 12L-3 3L-12 0L-3 -3Z" />
              ))}
            </g>
          </g>
        </g>
      </svg>
    </>
  );
}
