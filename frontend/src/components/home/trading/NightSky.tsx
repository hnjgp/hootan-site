/** Window rectangles on office_idle.jpg (1672x941 pixels) that stay lit at night: four upstairs, two downstairs, and the door. */
const LIT = [
  [392, 280, 182, 166],
  [630, 280, 181, 166],
  [867, 280, 181, 166],
  [1104, 280, 181, 166],
  [418, 547, 224, 184],
  [1049, 547, 229, 184],
  [740, 600, 192, 182],
] as const;

const STARS = [
  [120, 60, 1.1],
  [470, 50, 0.8],
  [610, 120, 1],
  [760, 40, 0.9],
  [1010, 90, 1.2],
  [1230, 50, 0.8],
  [1590, 70, 1],
  [80, 260, 0.7],
  [1620, 200, 0.8],
] as const;

/**
 * Dark-theme layer over the trading building (CLAUDE.md 15.4): a navy multiply over everything except the lit windows,
 * warm light in the windows, and a crescent moon with twinkling stars in place of the sun.
 */
export function NightSky() {
  return (
    <>
      <svg viewBox="0 0 1672 941" preserveAspectRatio="none" aria-hidden="true" className="night-only absolute inset-0 h-full w-full mix-blend-multiply">
        <defs>
          <mask id="night-windows">
            <rect width="1672" height="941" fill="white" />
            {LIT.map(([x, y, w, h]) => (
              <rect key={x + y} x={x} y={y} width={w} height={h} fill="black" />
            ))}
          </mask>
        </defs>
        <rect width="1672" height="941" fill="#2A3152" mask="url(#night-windows)" />
        {LIT.map(([x, y, w, h]) => (
          <rect key={x + y} x={x} y={y} width={w} height={h} fill="#FFD27A" fillOpacity="0.45" />
        ))}
      </svg>
      <svg viewBox="0 0 1672 941" preserveAspectRatio="none" aria-hidden="true" className="night-only absolute inset-0 h-full w-full">
        <circle cx="1432" cy="145" r="82" fill="#282E4A" />
        <path d="M1452 95 a52 52 0 1 0 22 92 a42 42 0 1 1 -22 -92 Z" fill="#F3E3B0" stroke="#1E1C1A" strokeWidth="3" strokeLinejoin="round" />
        {STARS.map(([x, y, s], k) => (
          <path
            key={x}
            className="twinkle"
            style={{ animationDelay: `${k * 0.37}s` }}
            transform={`translate(${x} ${y}) scale(${s})`}
            d="M0 -12 L3 -3 L12 0 L3 3 L0 12 L-3 3 L-12 0 L-3 -3 Z"
            fill="#FFD27A"
          />
        ))}
      </svg>
    </>
  );
}
