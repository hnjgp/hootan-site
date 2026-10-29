const INK = "var(--line)";

const FRONDS = [
  "M96 78C66 58 30 64 12 96C38 80 68 76 96 78Z",
  "M96 78C76 46 44 34 16 42C46 50 72 60 96 78Z",
  "M96 78C92 46 104 22 124 10C112 36 104 56 96 78Z",
  "M96 78C122 52 154 48 176 62C150 62 124 66 96 78Z",
  "M96 78C120 78 138 90 144 110C130 96 116 88 96 78Z",
];

/**
 * The hero drawing: Hootan sits under a palm by the sea typing on a laptop; the headline
 * is his thought cloud. Waves, small clouds, the palm and his hands move with CSS only.
 */
export function HeroScene({ tag, title, dir }: { tag: string; title: string; dir: "rtl" | "ltr" }) {
  return (
    // On one-screen layouts the scene is capped by the free height, so it never runs below the fold.
    <div dir="ltr" className="relative mx-auto w-full [container-type:inline-size] snap:max-w-[calc((100dvh-var(--head-h)-40px)*0.92)]">
      <div dir={dir} className="mb-2 px-2 text-start font-hand text-[30px] leading-none text-accent">
        {tag}
      </div>
      <div className="float-cloud relative z-10 ms-[16%] px-[15%] pt-[11%] pb-[14%]">
        <svg viewBox="0 0 400 200" preserveAspectRatio="none" className="absolute inset-0 h-full w-full overflow-visible" aria-hidden="true">
          <path
            d="M60 170C20 170 8 122 44 106C24 70 70 38 106 55C122 14 186 8 206 44C236 14 302 24 306 60C352 50 388 92 360 120C396 146 366 188 326 176C300 202 244 200 224 180C194 202 140 200 124 180C100 196 70 190 60 170Z"
            fill="var(--card)"
            stroke={INK}
            strokeWidth="2.5"
            vectorEffect="non-scaling-stroke"
          />
        </svg>
        <div dir={dir} className="relative text-center">
          <h1 className="text-[clamp(18px,4.9cqw,29px)] leading-[1.45] font-semibold whitespace-pre-line">{title}</h1>
        </div>
      </div>

      <svg viewBox="0 0 520 300" className="-mt-[9%] block h-auto w-full overflow-visible" aria-hidden="true">
        <defs>
          <clipPath id="sea">
            <rect x="0" y="196" width="520" height="104" />
          </clipPath>
        </defs>
        <g fill="none" stroke={INK} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <g className="sun-rays" style={{ transformOrigin: "478px 120px" }}>
            {Array.from({ length: 8 }, (_, i) => {
              const a = (i * Math.PI) / 4;
              return <path key={i} d={`M${478 + Math.cos(a) * 26} ${120 + Math.sin(a) * 26}L${478 + Math.cos(a) * 36} ${120 + Math.sin(a) * 36}`} stroke="var(--orange)" strokeWidth="3" />;
            })}
          </g>
          <circle cx="478" cy="120" r="18" fill="var(--orange)" />
          <g className="drift-slow">
            <path d="M320 128h52a9 9 0 0 0-3-17 13 13 0 0 0-23-4 10 10 0 0 0-18 5 8 8 0 0 0-8 16z" fill="var(--card)" />
          </g>
          <g className="drift-fast">
            <path d="M400 176h40a7 7 0 0 0-2-13 10 10 0 0 0-18-3 8 8 0 0 0-14 4 6 6 0 0 0-6 12z" fill="var(--card)" />
          </g>

          <path d="M210 196H520" />
          <g clipPath="url(#sea)">
            <g className="waves">
              <path d="M150 216q15-9 30 0t30 0 30 0 30 0 30 0 30 0 30 0 30 0 30 0 30 0 30 0 30 0 30 0" />
              <path d="M120 240q15-7 30 0t30 0 30 0 30 0 30 0 30 0 30 0 30 0 30 0 30 0 30 0 30 0 30 0 30 0" strokeWidth="1.5" />
              <path d="M150 266q15-7 30 0t30 0 30 0 30 0 30 0 30 0 30 0 30 0 30 0 30 0 30 0 30 0 30 0" strokeWidth="1.2" />
            </g>
          </g>
          <path d="M0 236C70 222 170 222 250 246C300 262 330 300 330 300H0z" fill="var(--bg)" />

          <path d="M56 236C60 180 68 128 90 76L102 80C84 132 78 182 76 236Z" fill="var(--bg)" />
          <path d="M60 206h16 M63 176h16 M68 146h15 M75 118h14 M83 94h13" strokeWidth="1.5" />
          <g className="palm" style={{ transformOrigin: "96px 78px" }}>
            {FRONDS.map((d) => (
              <path key={d} d={d} fill="var(--card)" />
            ))}
            <circle cx="92" cy="86" r="6" fill="var(--soft)" />
            <circle cx="103" cy="88" r="6" fill="var(--soft)" />
          </g>

          <circle cx="146" cy="150" r="5" fill="var(--card)" />
          <circle cx="166" cy="126" r="8" fill="var(--card)" />
          <circle cx="190" cy="96" r="11" fill="var(--card)" />
          <circle cx="216" cy="62" r="14" fill="var(--card)" />

          <circle cx="108" cy="170" r="14" fill="var(--paper)" />
          <path d="M94 166c0-16 28-18 28 0z" fill="var(--orange)" />
          <circle cx="114" cy="171" r="1.8" fill={INK} />
          <path d="M112 178q4 3 8 0" />
          <path d="M100 184l-8 46" />
          <path d="M92 230h50l46 4 M92 234h50l44 6" />
          <path d="M184 234v-8 M186 240l6 -6" />
          <path d="M126 228h44" strokeWidth="3" />
          <path d="M168 228l8-30 6 1-8 29z" fill="var(--orange)" />
          <path className="type-a" d="M98 194l18 18 18 12" />
          <path className="type-b" d="M100 198l24 14 16 12" />
          <path className="blink" d="M150 214h3 M156 214h3 M162 214h3" strokeWidth="2.5" />
        </g>
      </svg>
    </div>
  );
}
