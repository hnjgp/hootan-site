/** A section title with an orange hand-drawn line under it that draws itself as the title scrolls into view. */
export function Underlined({ children }: { children: string }) {
  return (
    <span className="relative inline-block">
      {children}
      <svg
        aria-hidden="true"
        viewBox="0 0 200 12"
        preserveAspectRatio="none"
        className="hand-underline pointer-events-none absolute inset-x-0 -bottom-2 h-[10px] w-full overflow-visible"
      >
        <path
          d="M3 8 C 40 3, 85 11, 120 6 S 175 4, 197 7"
          pathLength={100}
          fill="none"
          stroke="var(--orange)"
          strokeWidth="3"
          strokeLinecap="round"
          vectorEffect="non-scaling-stroke"
        />
      </svg>
    </span>
  );
}
